# multidados.py
# (c) 2020 CincoNoveSeis Jornalismo Ltda.
#
# This program is licensed under the GNU General Public License, version 3.
# See the LICENSE file for details.

from util import as_dec, is_number, generate_pairs
from interface import PollParser

from pdfminer.layout import LTTextBoxHorizontal
from itertools import combinations
from unidecode import unidecode

OFFSET = 15

def is_proper_field(text):
    return ('DADOS ADICIONAIS' not in text and
            'Pagina' not in text and
            text != '1\n' and
            text.strip() != '' and
            'PERGUNTA' not in text and
            'candidato no municipio' not in text and
            'votaria se as eleicoes' not in text)

class MultidadosParser(PollParser):
    @classmethod
    def is_relevant_page(cls, text):
        text = unidecode(text).lower()
        return (('se a eleicao extemporanea' in text or
                 'qual o seu candidato' in text) and
                'nao votaria' not in text)
    
    @classmethod
    def handle_relevant_page(cls, page, _):
        estimulada = True

        texts = {}
        for element in page:
            if isinstance(element, LTTextBoxHorizontal):
                text = unidecode(element.get_text())

                if 'REJEICAO' in text:
                    return None

                if 'ESPONTANEA' in unidecode(text).lower():
                    estimulada = False

                y = round(element.bbox[1], 4)
                if is_proper_field(text) and element.bbox[1] > 111:
                    if 'vice' in text:
                        text = text.split('vice')[0]

                    target = text.replace('\n1', '').replace('1\n', '').strip().split('\n')

                    idx = len(target) - 1
                    for x in target:
                        if x == 'PMDB':
                            continue

                        y = element.bbox[1] + (abs(element.bbox[3] - element.bbox[1]) / len(target)) * idx
                        if texts.get(y) is None:
                            texts[y] = []
                        
                        texts[y].append(x)
                        idx -= 1

        c = combinations(texts.keys(), 2)
        c_tracker = [(a[0], a[1], abs(a[0] - a[1])) for a in c]
        c_tracker = [a for a in c_tracker if a[2] < OFFSET]
        
        for a in c_tracker:
            texts[a[0]].extend(texts[a[1]])
            del texts[a[1]]

        return (estimulada, 'p', generate_pairs(texts))
