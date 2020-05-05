# ibope.py
# (c) 2020 CincoNoveSeis Jornalismo Ltda.
#
# This program is licensed under the GNU General Public License, version 3.
# See the LICENSE file for details.

from util import as_dec, is_number, normalize_ids, merge
from table import TableParser

from pdfminer.layout import LTTextBox
from functools import reduce
from unidecode import unidecode
import re

from itertools import groupby
from operator import itemgetter

class IbopeParser(TableParser):
    mayor_year = False

    @classmethod
    def page_numbers_for_id_search(cls):
        return [2]

    @classmethod
    def page_numbers_for_content_search(cls):
        return range(5, 200)

    @classmethod
    def is_relevant_page(cls, text):
        text = text.lower()
        return ('votaria' in text and
                'nao votaria' not in text and
                'jeito nenhum' not in text and
                'escolher entre' not in text and
                'com certeza' not in text and
                'nao concorresse' not in text and
                'apoio' not in text and
                'vice-presidente' not in text)
    
    @classmethod
    def get_pste(cls, text, ah):
        text = text.lower()

        if 'votaria' in text:
            e = False if 'espontanea' in text else True
            st = True if 'segundo turno' in text else (
                ah['pr'][True][False] or
                ah['g'][True][False] or
                ah['p'][True][False])
            
            p = None
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

            if p is not None:
                return (p, st, e)

        return None

    @classmethod
    def is_proper_field(cls, text):
        text = text.lower()
        return (not text.strip() == '' and
                not text.startswith('p.') and
                not text.startswith('obs:') and
                'pagina' not in text and
                'continua' not in text)

    @classmethod
    def field_has_newlines(cls, element):
        return abs(element.bbox[3] - element.bbox[1]) > 20
    
    @classmethod
    def postprocess(cls, oup):
        pp = []

        grouper = itemgetter('estimulada', 'tse_id', 'position')
        for k, grp in groupby(sorted(oup, key = grouper), grouper):
            polls = [x['poll_data'] for x in grp]
            
            if k[2] == 'v':
                pp.append({
                    'estimulada': k[0],
                    'tse_id': k[1],
                    'position': k[2],
                    'poll_data': merge(polls)
                })

            else:
                pp.extend([{
                    'estimulada': k[0],
                    'tse_id': k[1],
                    'position': k[2],
                    'poll_data': p
                } for p in polls])
        
        return [i for n, i in enumerate(pp) if i not in pp[n + 1:]]

class IbopeParser2012(IbopeParser):
    mayor_year = True

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
                        return normalize_ids(tse_ids)

                    continue
                
                return normalize_ids(tse_ids)

        return None
    
    @classmethod
    def is_stop_marker(cls, text):
        return 'jeito nenhum' in text

class IbopeParser2014(IbopeParser):
    @classmethod
    def is_stop_marker(cls, text):
        if 'classifica' in text:
            return True
