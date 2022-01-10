import json
import requests
from tqdm import tqdm
import os
from pathlib import Path
from dateutil.parser import parse
import re
from collections import defaultdict

import time

def is_number(s):
    try:
      float(s)
      return True
    except ValueError:
      pass

    try:
      import unicodedata
      unicodedata.numeric(s)
      return True
    except (TypeError, ValueError):
      pass
    return False

def is_date_str(string, fuzzy=False):
    try:
      parse(string, fuzzy=fuzzy)
      return True
    except:
      return False

def get_wikidata_triples(QIDs_dict):
    Q_pattern = '[Q]+[0-9]+$'
    url = 'https://query.wikidata.org/sparql'
    query="""
          SELECT DISTINCT * WHERE {{
          {{ SELECT (?eventOrig as ?QID) ?eventTgtLabel ?wdLabel ?ps_ ?ps_Label ?wdpqLabel ?pq ?pq_ ?pq_Label WHERE {{
            VALUES (?eventOrig) {{
              {}
              }}
            ?eventOrig owl:sameAs ?eventTgt .
            ?eventTgt ?p ?statement .
            ?statement ?ps ?ps_ .
            ?wd wikibase:claim ?p.
            ?wd wikibase:statementProperty ?ps.

            OPTIONAL {{
              ?statement ?pq ?pq_ .
              ?wdpq wikibase:qualifier ?pq .
            }}
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en" }}
        }} }}
        UNION
        {{ SELECT (?eventTgt as ?QID) ?eventTgtLabel ?wdLabel ?ps_ ?ps_Label ?wdpqLabel ?pq_ ?pq_Label WHERE {{
          VALUES (?eventTgt) {{
            {}
          }}
          MINUS {{?eventTgt owl:sameAs ?tgt .}}
          ?eventTgt ?p ?statement .
          ?statement ?ps ?ps_ .
          ?wd wikibase:claim ?p.
          ?wd wikibase:statementProperty ?ps.

          OPTIONAL {{
          ?statement ?pq ?pq_ .
          ?wdpq wikibase:qualifier ?pq .
          }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en" }}
          }} }}
          }}
        """.format(' '.join(QIDs_dict), ' '.join(QIDs_dict))
    r = requests.get(url, params = {'format': 'json', 'query': query},headers = {'User-agent': 'prop: '+str(list(QIDs_dict.keys())[0])})
    
    if r.status_code == 409:
        r = requests.get(url, params = {'format': 'json', 'query': query},headers = {'User-agent': 'prop 2: '+str(list(QIDs_dict.keys())[0])})
    data = r.json()
    
    if r is None:
      print(r.status_code)
      print(qid)
    
   
    bindings = data['results']['bindings']
    properties_dict = defaultdict(list)
    for answer in bindings:
        eventQID = answer['QID']['value'].split('/')[-1]
        eventLabel = answer['eventTgtLabel']['value'] + str(' (') + "EVENT_NAME" + str(')')
        propLabel = answer['wdLabel']['value']
        itemID = answer['ps_']['value'].split('/')[-1]
        if re.search(Q_pattern, itemID):
          itemLabel = answer['ps_Label']['value'] + str(' (') + itemID + str(')')
        else:
          itemLabel = answer['ps_Label']['value']
        
    
      

        if 'wdpqLabel' in answer and 'pq_Label' in answer:
          wdpqLabel = answer['wdpqLabel']['value']
          if 'pq_' in answer:
            pq_ = answer['pq_']['value'].split('/')[-1]
          else: 
            pq_ = None
          if pq_ is not None and re.search(Q_pattern, pq_):
            pq_Label = answer['pq_Label']['value'] + str(' (') + pq_ + str(')')
          else:
            pq_Label = answer['pq_Label']['value']

        
        if re.search(Q_pattern, itemID) or is_date_str(itemID) or is_number(itemLabel):
          properties_dict[QIDs_dict['(wd:'+eventQID+')']].append((eventLabel,propLabel,itemLabel))
        if re.search(Q_pattern, itemID) and 'wdpqLabel' in answer and 'pq_Label' in answer:
          properties_dict[QIDs_dict['(wd:'+eventQID+')']].append((itemLabel,wdpqLabel,pq_Label))
      
    return properties_dict





with open('data/eventkg_qa_wikidata_augmented_events_with_types.json') as f:
  data = json.load(f)
print(len(data))



with open('data/wikidata_properties/wikidata_properties.json') as f:
  wikidata_props = json.load(f)
print(len(wikidata_props))

all_triples_dict = dict()
for event in wikidata_props:
  all_triples_dict[event] = []

output = 'data/all_triples/triples_2.json'
# output_triples = dict()

    # with open(output,'r', encoding='utf-8') as f:
    #         output_triples = json.load(f)
    #         print(len(output_triples))

no_triples_list = []
num_chunks = 24
chunks = []
for i in range(-(-len(wikidata_props)//24)):
    chunks.append([])

for index, key in enumerate(wikidata_props):
  chunks[index//num_chunks].append(key)

for chunk in tqdm(chunks):
  # in_data_QIDs = list()
  QIDs_dict = dict()
  for event in chunk:
    if event in data:
      QID = data[event]['wikidataLink'].split('/')[-1]
      # in_data_QIDs.append("(wd:"+QID+")")
      QIDs_dict["(wd:"+QID+")"] = event
  triples_dict = get_wikidata_triples(QIDs_dict)
  all_triples_dict.update(triples_dict)
 
  # if  key in data:
  #   label = data[event]['wikipediaLabel']
  #   QID = data[event]['wikidataLink'].split('/')[-1]
  #   triples = get_wikidata_triples(QID,key)
  if len(triples_dict) == 0:
    print(QIDs_dict.keys())
    no_triples_list.extend(list(QIDs_dict.keys()))
    with open('logs/no_triples_list.log', "w", encoding='utf-8') as log:
      log.write(str(no_triples_list))

with open(output, "w", encoding='utf-8') as out_file:
  out_file.write(json.dumps(all_triples_dict,ensure_ascii=False, indent=4))

    # if not os.path.isfile(output):
    #   with open(output, "w", encoding='utf-8') as new_file:
    #     new_file.write(json.dumps(triples_dict,ensure_ascii=False, indent=4))
    # else:
    #   with open(output, "r+", encoding='utf-8') as old_file:
    #     curr_out_data = json.load(old_file)
    #     curr_out_data.update(triples_dict)
    #     old_file.seek(0)
    #     json.dump(curr_out_data, old_file, ensure_ascii=False, indent=4)
  # else:
    # print(QIDs_dict.keys())
    # no_triples_list.extend(list(QIDs_dict.keys()))
    # with open('logs/no_triples_list.log', "w", encoding='utf-8') as log:
    #   log.write(str(no_triples_list))