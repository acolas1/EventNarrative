import os
import json
import re
from dateutil.parser import parse
import calendar
from tqdm import tqdm
import nltk
from nltk.tokenize import sent_tokenize
import networkx as nx
import matplotlib.pyplot as plt

def fill_text(text, entity_ref_dict):
    filled_text = text
    for ref in entity_ref_dict:
        filled_text = filled_text.replace(ref, entity_ref_dict[ref])
    return filled_text

def tokenize_text(text, entity_ref_dict):
    filled_text = fill_text(text, entity_ref_dict)
    tokenized_text = nltk.word_tokenize(filled_text)
    return tokenized_text
    
def sorted_nicely(list_): 
    convert = lambda text: int(text) if text.isdigit() else text 
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key[0]) ] 
    return sorted(list_, key = alphanum_key)


def connect_neighbors(from_graph, modify_graph, entities_set):
    for entity in entities_set:
        triple_graph_neighbors = [n for n in from_graph.neighbors(entity)]
        for neighbor in triple_graph_neighbors:
            if neighbor in entities_set:
                modify_graph.add_edge(entity,neighbor)
    return modify_graph

def create_text_graph(triples, text, entity_dict):
    #first build triples graph (all triples)
    triples_graph = nx.Graph()
    for triple in triples:
        subject = triple[0]
        object_ = triple[2]
        triples_graph.add_edge(triple[0], triple[2])
    
    entities_set = set()

    #build graph from paragraph 
    text_graph = nx.Graph()
    for text_entity in entity_dict:
        text_graph.add_node(entity_dict[text_entity])
        entities_set.add(entity_dict[text_entity])

    #connecting the neighbors based on the triples graph
    text_graph = connect_neighbors(triples_graph, text_graph, entities_set)
   

    return text_graph

def filter_text_init(text_graph, text_string, entity_in_text_dict):
    entity_count = 0
    found_dict = dict()
    entity_set = set()
    entity_dict = dict()
    #for the nodes in_text find those that have neighbors
    for in_text in entity_in_text_dict:
        entity = entity_in_text_dict[in_text]
        neighbors = [n for n in text_graph.neighbors(entity)]
        #if neighbors are found then replace in text
        if neighbors:
            #if new entity, then make new placeholder
            if entity not in found_dict:
                
                placeholder = '<entity_'+str(entity_count)+'>'
                entity_count += 1
                found_dict[entity] = placeholder
                entity_dict[placeholder] = entity
                entity_set.add(entity)
            #else use old placeholder
            else:
                placeholder = found_dict[entity]
            text_string = re.sub(r'(?<!\w){}(?!\w)'.format(re.escape(in_text)),placeholder,text_string)
    
    #split into sentences
    sentences = sent_tokenize(text_string)
    for idx, sentence in enumerate(sentences):
        #for each sentence find the entities in the paragraph graph (that have neighbors)
        found_entities = re.findall(r'\<entity[^>]*\>', sentence)
        found_entities = set(found_entities)
        #if less than 2 entities in a sentence, delete that sentence
        if len(found_entities) <= 1:
            sentences[idx] = None
    new_sentences = list()
    for sentence in sentences:
        if sentence:
            new_sentences.append(sentence)
    new_text = ' '.join(new_sentences)
    
    new_found_dict = dict()
    found_entities = re.findall(r'\<entity[^>]*\>', new_text)
    for entity_ref in found_entities:
        if entity_ref in entity_dict:
            new_found_dict[entity_dict[entity_ref]] = entity_ref
    return new_text, new_found_dict

def get_triples_and_text_to_keep(new_text, event_triples, entity_ref_dict):
    ignore = ['wikidata_type_label','label', 'sameAs']
    
    curr_entity_ref_dict = entity_ref_dict
    while True:
        entity_set = set()
        for entity in curr_entity_ref_dict:
            entity_set.add(entity)
        keep_triples = []
        keep_entities = set()
        for triple in event_triples:
            subject = triple[0]
            object_ = triple[2]
            if subject in entity_set and object_ in entity_set and triple[1] not in ignore:
                keep_triples.append(triple)
                keep_entities.add(subject)
                keep_entities.add(object_)
        if len(keep_triples) == 0:
            break
        if len(new_text) == 0:
            break
       
        if len(entity_set.difference(keep_entities)) != 0:
            difference_set = entity_set.difference(keep_entities)
            for diff in difference_set:
                new_text = re.sub(r'(?<!\w){}(?!\w)'.format(re.escape(entity_ref_dict[diff])),diff,new_text)
            # print(entity_set)

            entity_set.remove(diff)
            sentences = sent_tokenize(new_text)
            for idx, sentence in enumerate(sentences):
                #for each sentence find the entities in the paragraph graph (that have neighbors)
                found_entities = re.findall(r'\<entity[^>]*\>', sentence)
                found_entities = set(found_entities)
                #if less than 2 entities in a sentence, delete that sentence
                if len(found_entities) <= 1:
                    sentences[idx] = None
            new_sentences = list()
            for sentence in sentences:
                if sentence:
                    new_sentences.append(sentence)
            if len(new_sentences) != 0:
                rev_entity_ref_dict = {v: k for k, v in curr_entity_ref_dict.items()}
                new_text = ' '.join(new_sentences)
                found_text_entities = re.findall(r'\<entity[^>]*\>', new_text)
                new_curr_entity_ref_dict = dict()
                for placeholder in found_text_entities:
                    if placeholder in rev_entity_ref_dict:
                        value = rev_entity_ref_dict[placeholder]
                        new_curr_entity_ref_dict[value] = placeholder
                curr_entity_ref_dict = new_curr_entity_ref_dict
            else:
                new_text = ''
                break
        else:
            break
    return keep_triples, new_text
    
def reorder_entities(text, entity_ref_dict):
    new_text_entity_ref_dict = dict()
    for placeholder in entity_ref_dict:
        if placeholder in text:
            new_text_entity_ref_dict[placeholder] = entity_ref_dict[placeholder]
    new_text_entity_ref_dict = dict(sorted_nicely(new_text_entity_ref_dict.items()))
    new_placeholder_entity_ref_dict = dict()
    for idx, placeholder in enumerate(new_text_entity_ref_dict):
        new_placeholder = '<entity_'+str(idx)+'>'
        new_placeholder_entity_ref_dict[new_placeholder] = new_text_entity_ref_dict[placeholder]
        text = re.sub(r'(?<!\w){}(?!\w)'.format(re.escape(placeholder)),new_placeholder,text)
    return text, new_placeholder_entity_ref_dict

path = "data/full_entities_in_text/"
filelist = [file_ for file_ in os.listdir(path) if file_.endswith('.json')]
for file_ in filelist:
    num = file_.split('_')[2]
    with open(path+file_, 'r',encoding='utf-8') as f:
        for event in tqdm([json.loads(line.strip('\n')) for line in f]):
            if len(event['entities_in_text']) > 1 and event['narration']:
                event_name = event['Event_Name']
                event_triples = event['triples']
                for triple in event['triples']:
                    if triple[1] == 'follows' or triple[1] == 'followed by':
                        if triple[0] != event_name:
                            triple[0] = event_name
                entities_in_text = event['entities_in_text']
                sorted_entities_in_text = dict()
                # entity_ref_dict  = dict()
                text = event['narration']
                text = re.sub(r'([^\w\s])\:\d+', '', text)

                temp_text = text
                paragraph_graph = create_text_graph(event_triples, text, entities_in_text)

                for k in sorted(entities_in_text, key=len, reverse=True):
                    sorted_entities_in_text[k] = entities_in_text[k]
                


                new_text, ref_dict = filter_text_init(paragraph_graph, temp_text, sorted_entities_in_text)
                keep_triples, new_text = get_triples_and_text_to_keep(new_text, event_triples, ref_dict)
                event['keep_triples'] = keep_triples
                entity_ref_dict = {v: k for k, v in ref_dict.items()}
                new_text, entity_ref_dict = reorder_entities(new_text, entity_ref_dict)
           
                event['entity_ref_dict'] = entity_ref_dict
                event['narration'] = new_text

                del event['entities_in_text']

                tokenized_text = tokenize_text(event['narration'],event['entity_ref_dict'])
            
            
                    
