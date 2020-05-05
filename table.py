# table.py
# (c) 2020 CincoNoveSeis Jornalismo Ltda.
#
# This program is licensed under the GNU General Public License, version 3.
# See the LICENSE file for details.

from util import as_dec, is_number
from interface import PollParser

from pdfminer.layout import LTTextBoxHorizontal
from itertools import tee
from functools import reduce
from unidecode import unidecode

from pprint import pprint

LOG = 0

# TableParser deals with polls encoded into tables.
# PDF tables are annoying because they can have two layouts, rather
# arbitrarily, i.e.:
#
# (1) One textbox per column, with rows separated by \n;
# (2) One textbox per cell.
#
# TableParser tries to detect whether we're dealing with one or the other,
# and parses accordingly.

class TableParser(PollParser):
    @classmethod
    def handle_relevant_page(cls, page, already_have):
        p = None
        st = False
        e = None

        tot_ref = None
        relevant_lists = []

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
                if LOG:
                    print(element)
                text = unidecode(element.get_text())

                if cls.rule_out_page(text):
                    return None

                pste = cls.get_pste(text, already_have)
                if pste is not None:
                    (p, st, e) = pste
                    
                    #if already_have[p][st][e]:
                    #    return None

                    already_have[p][st][e] = True

                if cls.is_proper_field(text):
                    if tot_ref[2] > 20 and element.bbox[1] <= tot_ref[1]:
                        if element.bbox[0] < tot_ref[0]:
                            relevant_lists.append({
                                'text': text.strip(),
                                'y': element.bbox[1],
                                'newlines': cls.field_has_newlines(element),
                                'height': abs(element.bbox[3] - element.bbox[1])
                            })

                    elif element.bbox[0] < tot_ref[0] and element.bbox[3] < tot_ref[1]:
                        relevant_lists.append({
                            'text': text.strip(),
                            'y': element.bbox[1],
                            'newlines': cls.field_has_newlines(element),
                            'height': abs(element.bbox[3] - element.bbox[1])
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

        # TODO: This is buggy and should only be used when the two more reliable
        # methods above fail.
        elif len(relevant_lists) >= 2:
            print('WARNING: Operating on mixed mode. Verify results carefully.')
            
            for v in relevant_lists:
                if v['newlines']:
                    split = v['text'].strip().split('\n')
                    idx = len(split) - 1

                    for vv in split:
                        relevant_lists.append({
                            'text': vv,
                            'y': v['y'] + (v['height'] / len(split)) * idx,
                            'newlines': False
                        })

                        idx -= 1

            relevant_lists = [x for x in relevant_lists if not x['newlines']]
            relevant_lists = sorted(relevant_lists, key = lambda k: k['y'], reverse=True)

            final = [x['text'] for x in relevant_lists]
            if len(final) % 2 != 0:
                final = final[:-1]

            it = iter(final)
            groups = zip(it, it)

        if LOG:
            pprint(relevant_lists)
        groups = [sorted(x) for x in groups]
        groups = [x for x in groups if is_number(x[0])]
        groups = [x for x in groups if not is_number(x[1])]
        if LOG:
            pprint(groups)

        candidates = [x[1] for x in groups]
        numbers = [as_dec(x[0]) for x in groups]

        return (e, p, dict(zip(candidates, numbers)))
    
    @classmethod
    def is_proper_field(cls, text):
        return True

    @classmethod
    def rule_out_page(cls, text):
        return False
