# datafolha.py
# (c) 2020 CincoNoveSeis Jornalismo Ltda.
#
# This program is licensed under the GNU General Public License, version 3.
# See the LICENSE file for details.

# NOTE: This parser is unable to parse poll PDFs with multiple scenarios for a
# first round. Trying it WILL GENERATE UNRELIABLE DATA. At Pindograma, we
# separate these PDFs from the others.

from util import as_dec, is_number
from table import TableParser

from itertools import tee, groupby
from functools import reduce
from operator import itemgetter
import re

class DatafolhaParser(TableParser):
    @classmethod
    def page_numbers_for_id_search(cls):
        return [2, 3, 4, 5, 6]

    @classmethod
    def page_numbers_for_content_search(cls):
        return range(6, 100)
    
    @classmethod
    def is_proper_field(cls, text):
        return ('Projeto:' not in text and
                'Base:' not in text and
                'Data do campo:' not in text and
                'INTENCAO' not in text and
                'PRETENDE' not in text and
                not text.startswith('***') and
                'SENADORES' not in text and
                re.search(r'[pP]\d+', text) is None and
                not text.startswith('No dia'))
    
    @classmethod
    def field_has_newlines(cls, element):
        return len(element.get_text().strip().split('\n')) > 1

    @classmethod
    def postprocess(cls, oup):
        pp = []

        grouper = itemgetter('estimulada', 'tse_id', 'position')
        for k, grp in groupby(sorted(oup, key = grouper), grouper):
            polls = [x['poll_data'] for x in grp]

            pp.extend([{
                'estimulada': k[0],
                'tse_id': k[1],
                'position': k[2],
                'poll_data': p
            } for p in polls])
        
        return [i for n, i in enumerate(pp) if i not in pp[n + 1:]]

class DatafolhaMayorParser(DatafolhaParser):
    @classmethod
    def is_relevant_page(cls, text):
        text = text.lower()
        
        if 'segundo turno' in text:
            return 'p.1 ' in text

        return (('p.1 ' in text or
                 'p.2 ' in text or
                 'p.2a' in text or
                 'p.3 ' in text or
                 'p.4 ' in text) and
                'votar' in text and
                'numero' not in text and
                'nao votaria' not in text and
                'ficasse apenas' not in text and
                'fonte' not in text and
                'interesse' not in text and
                'mudar seu voto' not in text)

    @classmethod
    def rule_out_page(cls, text):
        text = text.lower()
        return ('votos validos' in text or
                'voto validos' in text or
                'rejeicao' in text)

    @classmethod
    def get_pste(cls, text, ah):
        text = text.lower()

        if text.startswith('p.'):
            e = 'estimulada' in text
            st = 'segundo turno' in text

            return ('p', st, e)

        return None

    
    @classmethod
    def allow_mixed_mode(cls):
        return False
    
class DatafolhaGeneralParser(DatafolhaParser):
    @classmethod
    def is_proper_field(cls, text):
        return (super().is_proper_field(text) and
            not 'TOTAL' in text)

    @classmethod
    def is_relevant_page(cls, text):
        text = text.lower()
        return (('eleicao para governador' in text or
                'eleicao para senador' in text or
                'eleicao para presidente' in text or
                'eleicoes para governador' in text or
                'eleicoes para senador' in text or
                'eleicoes para presidente' in text) and
                'nao votaria' not in text and
                'ficasse apenas' not in text and
                'fonte' not in text and
                'interesse' not in text)
    
    @classmethod
    def get_pste(cls, text, ah):
        text = text.lower()

        if text.startswith('p.'):
            e = 'estimulada' in text
            st = 'segundo turno' in text

            p = None
            if 'senador' in text:
                p = 's'
            elif 'governador' in text:
                p = 'g'
            elif 'presidente' in text:
                p = 'pr'

            if p is not None:
                return (p, st, e)

        return None
