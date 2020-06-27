import csv
import json
import re
from sys import argv
from unidecode import unidecode

ret = []
pdflist = []

with open(argv[1]) as verita_file:
    data = json.load(verita_file)['pesquisas']
    for _, v in data.items():
        if v['categoria'] != 'eleicoes':
            continue

        for _, w in v['secoes'].items():
            if w['idsecaotipo'] == 'graf_barra' or w['idsecaotipo'] == 'graf_linha':
                obj = json.loads(w['conteudo'])
                
                poll_data = [{'cand': p[0], 'votes': p[1]} for p in obj]
                ret.append({
                    'state': v['estado'],
                    'desc': v['descr'],
                    'title': v['titulo'],
                    'poll_data': poll_data
                })

            elif w['idsecaotipo'] == 'pdf':
                pdflist.append(w['conteudo'])

with open('verita_pdflist.txt', 'w') as f:
    for item in pdflist:
        f.write('%s\n' % item)

output = []
scenario = 0

for poll in ret:
    tse_id = re.search(r'([A-Z]+?[\s\-]?)?[0-9]{5}\/[0-9]{4}', poll['desc'])
    
    if tse_id is None:
        continue

    tse_id = tse_id.group(0)

    if len(tse_id) == 10:
        if 'PRESIDENTE' in poll['title']:
            tse_id = 'BR-' + tse_id
        else:
            tse_id = poll['state'] + '-' + tse_id
    
    tse_id = re.sub(r'[\-\s\/]', '', tse_id)

    norm_desc = unidecode(poll['desc']).lower()
    norm_title = unidecode(poll['title']).lower()

    e = True
    if ('espontanea' in norm_desc or
        'espontanea' in norm_title):
        e = False

    position = None
    if 'prefeito' in norm_desc or 'prefeito' in norm_title:
        position = 'p'
    elif 'senador' in norm_desc or 'senador' in norm_title:
        position = 's'
    elif 'governador' in norm_desc or 'governador' in norm_title:
        position = 'g'
    elif 'presidente' in norm_desc or 'presidente' in norm_title:
        position = 'pr'
    
    for p in poll['poll_data']:
        output.append({
            'tse_id': tse_id,
            'estimulada': e,
            'position': position,
            'scenario': scenario,
            'candidate': p['cand'],
            'value': p['votes']
        })

    scenario += 1


with open('verita.csv', 'w') as f:
    dict_writer = csv.DictWriter(f, output[0].keys(), lineterminator='\n')
    dict_writer.writeheader()
    dict_writer.writerows(output)
