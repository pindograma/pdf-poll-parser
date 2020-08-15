# interface.py
# (c) 2020 CincoNoveSeis Jornalismo Ltda.
#
# This program is licensed under the GNU General Public License, version 3.
# See the LICENSE file for details.

import re
from unidecode import unidecode
from pprint import pprint

import json
import csv

from pdfminer.layout import LTTextBox, LTTextBoxHorizontal, LAParams
from pdfminer.converter import PDFPageAggregator
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage

from util import normalize_ids

def extract_pages(pdf_file, page_numbers=None,
                    maxpages=0, password='',
                    check_extractable=False, caching=True):
    with open(pdf_file, 'rb') as fp:
        laparams = LAParams()
        resource_manager = PDFResourceManager()
        device = PDFPageAggregator(resource_manager, laparams=laparams)
        interpreter = PDFPageInterpreter(resource_manager, device)
        for page in PDFPage.get_pages(fp, page_numbers, maxpages=maxpages,
                                      password=password, caching=caching,
                                      check_extractable = check_extractable):
            interpreter.process_page(page)
            layout = device.get_result()
            yield layout

class PollParser:
    tse_id_rgx = r'[A-Z][A-Z][\s\-]*\d{5}[\s\/]*\d+'
    
    @classmethod
    def generate_already_have(cls):
        return {
            'v': [[False, False], [False, False]],
            'p': [[False, False], [False, False]],
            's': [[False, False], [False, False]],
            'g': [[False, False], [False, False]],
            'pr': [[False, False], [False, False]]
        }
    
    @classmethod
    def select_tse_id(cls, tse_ids, p):
        if p == 'p' or p == 'v':
            return tse_ids[0]

        for x in tse_ids:
            if x.startswith('BR') and p == 'pr':
                return x
            if not x.startswith('BR') and (p == 'g' or p == 's'):
                return x
        
        return None
    
    @classmethod
    def find_ids(cls, page):
        for element in page:
            if isinstance(element, LTTextBox):
                text = unidecode(element.get_text())

                tse_ids = re.findall(cls.tse_id_rgx, text)
                if len(tse_ids) == 0:
                    continue
                
                return normalize_ids(tse_ids)

        return None

    @classmethod
    def handle_page(cls, tse_ids, page, ah):
        for element in page:
            if isinstance(element, LTTextBoxHorizontal):
                text = unidecode(element.get_text())

                if cls.is_stop_marker(text):
                    return (None, True)
                
                if cls.is_relevant_page(text):
                    ret = cls.handle_relevant_page(page, ah)
                    if ret is not None:
                        (e, p, d) = ret
                        return ({
                            'tse_id': cls.select_tse_id(tse_ids, p),
                            'estimulada': e,
                            'position': p,
                            'poll_data': d
                        } if d is not None else None, False)
        
        return (None, False)

    @classmethod
    def parseids(cls, pathlist, name='default'):
        for path in pathlist:
            tse_ids = None
            for page in extract_pages(str(path), page_numbers = cls.page_numbers_for_id_search()):
                if tse_ids is not None:
                    break

                tse_ids = cls.find_ids(page)
                print(tse_ids)

    @classmethod
    def parse(cls, pathlist, name='default'):
        output = []

        for path in pathlist:
            print('==== {} ===='.format(str(path)))

            tse_ids = None
            for page in extract_pages(str(path), page_numbers = cls.page_numbers_for_id_search()):
                if tse_ids is not None:
                    break

                tse_ids = cls.find_ids(page)

            if tse_ids is None:
                print('WARNING: Could not find tse_id.')
                continue
            
            ah = cls.generate_already_have()
            for page in extract_pages(str(path), page_numbers = cls.page_numbers_for_content_search()):
                try:
                    ret, stop = cls.handle_page(tse_ids, page, ah)
                    if stop:
                        break

                    if ret is not None:
                        output.append(ret)
                        pprint(ret)

                        if cls.should_stop(ah, tse_ids):
                            break

                except ValueError:
                    print('WARNING: Value Error.')
                    break
        
        with open(name + '.json', 'w') as f:
            json.dump(output, f)

        pp = cls.postprocess(output)

        with open(name + '_pp.json', 'w') as f:
            json.dump(pp, f)

        output2 = []
        for idx, item in enumerate(pp):
            for k, v in item['poll_data'].items():
                output2.append({
                    'tse_id': item['tse_id'],
                    'estimulada': item['estimulada'],
                    'position': item['position'],
                    'scenario': idx,
                    'candidate': k,
                    'value': v
                })
            
        with open(name + '.csv', 'w') as f:
            dict_writer = csv.DictWriter(f, output2[0].keys(), lineterminator='\n')
            dict_writer.writeheader()
            dict_writer.writerows(output2)

    @classmethod
    def get_output(cls):
        return cls.output

    @classmethod
    def page_numbers_for_id_search(cls):
        return None

    @classmethod
    def page_numbers_for_content_search(cls):
        return None

    @classmethod
    def should_stop(cls, ah, tse_ids):
        return False

    @classmethod
    def is_stop_marker(cls, text):
        return False

    @classmethod
    def is_relevant_page(cls, text):
        return False

    @classmethod
    def handle_relevant_page(cls, page, ah):
        return None

    @classmethod
    def postprocess(cls, oup):
        return oup
