import os
import random
import json
import re

def tokenize_entities(entities):
    entities_list = []
    for entity in entities:
        entity = entity.replace('–', ' - ')
        entity = re.sub('([,!?():;&\"\'/])', r' \1 ', entity)
        entity = re.sub('\s{2,}', ' ', entity).strip()
        entity_list = entity.split(' ')
        entities_list.append(entity_list)
    return entities_list

def tokenize_triples(triples):
    triples_list = []
    for triple in triples:
        subject = triple[0]
        object_ = triple[2]
        subject = subject.replace('–', ' - ')
       
        subject = re.sub('([,!?():;&\"\'/])', r' \1 ', subject)
        subject = re.sub('\s{2,}', ' ', subject).strip()
        subject_list = subject.split(' ')

        object_ = object_.replace('–', ' - ')
        object_ = re.sub('([,!?():;&\"\'/])', r' \1 ', object_)
        object_ = re.sub('\s{2,}', ' ', object_).strip()
        object_list = object_.split(' ')

        triples_list.append([subject_list, triple[1], object_list])
    return triples_list

def tokenize_text(text):
    text = text.replace('–', ' - ')
    text = text.replace('—', ' - ')
    text = text.replace(u'\u2212', ' - ')
    text = text.replace(u'\u2044', ' - ')
    text = text.replace(u'\xd7', ' x ')
    text = text.replace(u'>\u200b<', u'> <')
    text = text.replace(u'\xa0', u' ')
    # text = text.replace('><ent', '> <ent')
    # text = re.sub(">+(\S)+<ent", r'> \1 <', text)
    text = re.sub('([|.,!?():;&\+\"\'/-])', r' \1 ', text)
    text = text.replace('><e', '> <e')
    text = re.sub('\s{2,}', ' ', text)
    text = text.replace('<entity_','<ENT_')
    return text

        
def convert_to_graphwriter(dataset, split):
    out_data = []

    for data in dataset:
        instance_dict = dict()
        triples = data['keep_triples']
        entities = data['entity_ref_dict'].values()
        text = data['narration']
        relations = tokenize_triples(triples)
        entities = tokenize_entities(entities)
        text = tokenize_text(text)
        instance_dict['relations'] = relations
        instance_dict['text'] = text
        instance_dict['entities'] = entities
        out_data.append(instance_dict)

   
    with open('../data/split_data/graphwriter/' + split, "w", encoding='utf-8') as data1:
        data1.write(json.dumps(out_data, ensure_ascii=False))

path = "../data/split_data/"
filelist = [dir_file for dir_file in os.listdir(path) if dir_file.endswith('.json')]

for file_ in filelist:
    data_list = []
    print(path+file_)
    with open(path+file_, 'r', encoding='utf-8') as files:
        data_list = json.load(files)
    convert_to_graphwriter(data_list,file_)