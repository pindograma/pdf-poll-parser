# ibope.py
# (c) 2020 CincoNoveSeis Jornalismo Ltda.
#
# This program is licensed under the GNU General Public License, version 3.
# See the LICENSE file for details.

from util import as_dec, is_number
from interface import PollParser

from pdfminer.layout import LTTextBox, LTTextBoxHorizontal
from itertools import tee
from functools import reduce
from unidecode import unidecode
import re

class IbopeParser(PollParser):
    mayor_year = False

    @classmethod
    def page_numbers_for_id_search(cls):
        return [2]

    @classmethod
    def page_numbers_for_content_search(cls):
        return range(5, 200)

    @classmethod
    def is_relevant_page(cls, text):
        text = unidecode(text).lower()
        return ('votaria' in text and
                'nao votaria' not in text and
                'escolher entre' not in text and
                'com certeza' not in text)

    @classmethod
    def handle_relevant_page(cls, page, already_have):
        e = True
        p = None
        seg_turno = (already_have['pr'][True][False] or
            already_have['g'][True][False] or
            already_have['p'][True][False])
        
        tot_ref = None
        relevant_lists = []

        found_president = False
        found_governor = False
        found_senator = False

        total_page, page = tee(page)

        for element in total_page:
            if isinstance(element, LTTextBoxHorizontal):
                text = unidecode(element.get_text())
                if 'TOTAL' in text:
                    tot_ref = (element.bbox[2],
                               element.bbox[1],
                               abs(element.bbox[3] - element.bbox[1]))
                    break
        
        if tot_ref is None:
            return None

        for element in page:
            if isinstance(element, LTTextBoxHorizontal):
                text = unidecode(element.get_text()).lower()

                if 'votaria' in text:
                    if 'espontanea' in text:
                        e = False
                    
                    if 'segundo turno' in text:
                        seg_turno = True

                    if 'prefeito' in text:
                        p = 'p'
                    elif 'vereador' in text:
                        p = 'v'
                    elif 'senador' in text:
                        p = 's'
                    elif 'governador' in text:
                        p = 'g'
                    elif 'presidente' in text:
                        p = 'pr'

                    if already_have[p][seg_turno][e]:
                        return None

                    already_have[p][seg_turno][e] = True

                if tot_ref[2] > 30:
                    if element.bbox[0] < tot_ref[0] and not text.startswith('p.'):
                        relevant_lists.append({
                            'text': unidecode(element.get_text()),
                            'y': element.bbox[1],
                            'newlines': abs(element.bbox[3] - element.bbox[1]) > 20
                        })

                elif element.bbox[0] < tot_ref[0] and element.bbox[3] < tot_ref[1]:
                    if not text.startswith('obs:'):
                        relevant_lists.append({
                            'text': unidecode(element.get_text()),
                            'y': element.bbox[1],
                            'newlines': abs(element.bbox[3] - element.bbox[1]) > 20
                        })

        groups = []
        
        if len(relevant_lists) == 2 and relevant_lists[0]['newlines'] and relevant_lists[1]['newlines']:
            final_lists = [x['text'].strip().split('\n') for x in relevant_lists]
            groups = list(zip(final_lists[0], final_lists[1]))
        
        elif len(relevant_lists) >= 2 and reduce(lambda x, y: x+y['newlines'], relevant_lists, 0) == 0:
            relevant_lists = sorted(relevant_lists, key = lambda k: k['y'])
            v = [x['text'].strip().replace('\n', '') for x in relevant_lists]
            it = iter(v)
            groups = zip(it, it)
        
        groups = [sorted(x) for x in groups]
        groups = [x for x in groups if is_number(x[0])]
        groups = [x for x in groups if not is_number(x[1])]

        candidates = [x[1] for x in groups]
        numbers = [as_dec(x[0]) for x in groups]

        return (e, p, dict(zip(candidates, numbers)))

    @classmethod
    def should_stop(cls, ah, tse_ids):
        if cls.mayor_year:
            if (ah['p'][True][True] and
                ah['p'][True][False]):
                return True

            if (ah['p'][False][True] and
                ah['p'][False][False] and
                ah['v'][False][True] and
                ah['v'][False][False]):
                return True

        else:
            if (len(tse_ids) == 2 and
                ah['pr'][True][True] and
                ah['pr'][True][False] and
                ah['g'][True][True] and
                ah['g'][True][False]):
                return True

            if (len(tse_ids) == 2 and
                ah['pr'][False][True] and
                ah['pr'][False][False] and
                ah['g'][False][True] and
                ah['g'][False][False] and
                ah['s'][False][True] and
                ah['s'][False][False]):
                return True
            
            if (len(tse_ids) == 1 and
                tse_ids[0].startswith('BR') and
                ah['pr'][True][True] and
                ah['pr'][True][False]):
                return True
            
            if (len(tse_ids) == 1 and
                tse_ids[0].startswith('BR') and
                ah['pr'][False][True] and
                ah['pr'][False][False]):
                return True

            if (len(tse_ids) == 1 and
                not tse_ids[0].startswith('BR') and
                ah['g'][True][True] and
                ah['g'][True][False]):
                return True

            if (len(tse_ids) == 1 and
                not tse_ids[0].startswith('BR') and
                ah['g'][False][True] and
                ah['g'][False][False] and
                ah['s'][False][True] and
                ah['s'][False][False]):
                return True

        return False

class IbopeParser2012(IbopeParser):
    @classmethod
    def page_numbers_for_id_search(cls):
        return [1]
    
    @classmethod
    def find_ids(cls, page):
        for element in page:
            if isinstance(element, LTTextBox):
                text = unidecode(element.get_text())

                tse_ids = re.findall(cls.tse_id_rgx, text)
                if len(tse_ids) == 0:
                    match_est = re.search(r'TRE-(.{2})', text)
                    match_num = re.search(r'\d{5}[\s\/]*\d+', text)

                    if match_est is not None and match_num is not None:
                        tse_ids = [match_est.group(1) + '-' + match_num.group(0)]
                        return tse_ids

                    continue
                
                return tse_ids

        return None
