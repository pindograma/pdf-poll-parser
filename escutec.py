# escutec.py
# (c) 2020 CincoNoveSeis Jornalismo Ltda.
#
# This program is licensed under the GNU General Public License, version 3.
# See the LICENSE file for details.

from util import as_dec, is_number, generate_pairs
from interface import PollParser

from pdfminer.layout import LTTextBoxHorizontal
from itertools import combinations
from unidecode import unidecode

OFFSET = 10

class EscutecParser(PollParser):
    @classmethod
    def is_relevant_page(cls, text):
        text = unidecode(text).lower()
        return (('se as eleicoes para' in text or
                 'se as eleicoes fossem hoje' in text) and
                'nao' not in text)
    
    @classmethod
    def handle_relevant_page(cls, page, _):
        estimulada = True

        texts = {}
        for element in page:
            if isinstance(element, LTTextBoxHorizontal):
                text = element.get_text().strip()

                if 'espontanea' in unidecode(text).lower():
                    estimulada = False

                y = round(element.bbox[1], 4)
                if texts.get(y) is None:
                    texts[y] = []
                
                if 'Base:' not in text:
                    texts[y].append(text.replace('*', ''))

        c = combinations(texts.keys(), 2)
        c_tracker = [(a[0], a[1], abs(a[0] - a[1])) for a in c]
        c_tracker = [a for a in c_tracker if a[2] < OFFSET]
        
        for a in c_tracker:
            texts[a[0]].extend(texts[a[1]])
            del texts[a[1]]

        return (estimulada, 'p', generate_pairs(texts))
