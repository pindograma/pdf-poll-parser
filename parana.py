# parana.py
# (c) 2020 CincoNoveSeis Jornalismo Ltda.
#
# This program is licensed under the GNU General Public License, version 3.
# See the LICENSE file for details.

from util import as_dec, is_number, generate_pairs
from interface import PollParser

from pdfminer.layout import LTTextBoxHorizontal
from itertools import combinations
from unidecode import unidecode

def merge(ret):
    return {k: v for d in ret for k, v in d.items()}

def rule_out_mayor_page(text):
    text = unidecode(text)
    return ('Em funcao da questao' in text or
            'comparativa' in text)

class ParanaParser2016(PollParser):
    @classmethod
    def is_relevant_page(cls, text):
        text = unidecode(text)
        return (('Se o segundo turno da eleicao' in text or
            'Se as eleicoes para Prefeito' in text) and
            'Em funcao da questao' not in text and
            'JEITO NENHUM' not in text and
            'comparativa' not in text and
            'AGORA fossem' not in text)

    @classmethod
    def handle_relevant_page(cls, page, _):
        e = False

        texts = {}
        for element in page:
            if isinstance(element, LTTextBoxHorizontal):
                text = element.get_text()

                if rule_out_mayor_page(text):
                    return None

                if 'ESTIMULADA' in text:
                    e = True

                y = round(element.bbox[1], 4)
                if texts.get(y) is None:
                    texts[y] = []
                
                texts[y].append({
                    'text': text.strip(),
                    'x': element.bbox[0]
                })
                
        texts = {k: sorted(v, key=lambda l: l['x']) for k, v in texts.items()}
        texts = {k: [x['text'] for x in v] for k, v in texts.items()}
        
        return (e, 'p', generate_pairs(texts))

class ParanaParser2018(PollParser):
    @classmethod
    def is_relevant_page(cls, text):
        text = unidecode(text)
        return (('Situacao Eleitoral -' in text or
                'Segundo Turno -' in text) and
                'VOTOS VALIDOS' not in text and
                'Comparativo' not in text and
                'Governador/' not in text and
                'Governador /' not in text)
    
    @classmethod
    def handle_relevant_page(cls, page, _):
        position = None

        texts = {}
        for element in page:
            if isinstance(element, LTTextBoxHorizontal):
                text = element.get_text().strip()

                if position is None:
                    if 'Governador' in text:
                        position = 'g'
                    elif 'Senador' in text:
                        position = 's'
                    elif 'Presidente' in text:
                        position = 'pr'

                x = element.bbox[0]
                if x >= 250:
                    continue

                y = round(element.bbox[1], 4)
                if texts.get(y) is None:
                    texts[y] = []
                
                texts[y].append(text)

        c = combinations(texts.keys(), 2)
        c_tracker = [(a[0], a[1], abs(a[0] - a[1])) for a in c]
        c_tracker = [a for a in c_tracker if a[2] < 5]
        
        for a in c_tracker:
            texts[a[0]].extend(texts[a[1]])
            del texts[a[1]]

        return (True, position, generate_pairs(texts))
