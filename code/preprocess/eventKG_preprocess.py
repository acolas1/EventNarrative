# -*- coding: utf-8 -*-
###---Script to preprocess EventKG ###
import re
import nltk
import json
from nltk.tokenize import word_tokenize
from dateutil.parser import parse
import traceback
from collections import defaultdict


def is_date(string):
    try: 
        parse(string)
        return True
    except:
        return False

def is_number(s):
    try:
        float(s)
        return True
    except:
        return False


def filter_lowercase(orig, wikidata):
    Q_pattern = '\([Q]+[0-9]+\)'
    for idx, orig_triple in enumerate(orig):
        for wikidata_triple in wikidata:
            subject= wikidata_triple[0]
            object_ = wikidata_triple[2]
            if re.search(Q_pattern, subject):
                split_subject = subject.rsplit(' ', 1)
                subject = split_subject[0]
            if re.search(Q_pattern, object_):
                split_object =object_.rsplit(' ', 1)
                object_ = split_object[0]
                # print(object_)
            if orig_triple[0].lower() == subject.lower() and orig_triple[1].lower() == wikidata_triple[1].lower() and orig_triple[2].lower() == object_.lower():
                orig[idx] = None
    new_orig = [triple for triple in orig if triple is not None]
    return new_orig


def fix_timestamps(triples):
    new_event_triples = []
    for triple in triples:
        if triple[1] not in useless_types:
            subject = triple[0]
            predicate=triple[1]
            object_ = triple[2]
            if ('start time' in predicate or 'end time' in predicate) and object_.startswith('t'):
                continue
            if predicate=='hasEndTimeStamp' or predicate=='hasBeginTimeStamp' or predicate=='start time' or predicate=='end time' or predicate=='point in time' or predicate=='date of official opening':
                # mainsnak={}
                if data[i]['wikidataLabel'] == "Morgan's Raid":
                    if predicate == 'hasEndTimeStamp':
                        object_ = "1863-07-26"
                    else:
                        object_ = "1863-07-11"
                if data[i]['wikidataLabel'] == "1983 Tolly Cobbold Classic":
                    if predicate == 'hasEndTimeStamp':
                        object_ = "1983-02-23"
                d=parse(object_).strftime('%d %B %Y')
                object_ = d
            new_tr = [subject,predicate,object_]
            if new_tr is None:
                print(new_tr)
            new_event_triples.append(new_tr)
    return new_event_triples

def remove_non_QID_duplicates(triples):
    #remove any triples which are duplicates (relation is the same)
    #the only difference is QID in subject or object
    Q_pattern = '\([Q]+[0-9]+\)'
    qid_triples = []
    for triple in triples:
        subject = triple[0]
        object_ = triple[2]
        if triple not in qid_triples:
            subject = triple[0]
            object_ = triple[2]
           
            if re.search(Q_pattern, subject) and re.search(Q_pattern, object_):
                split_subject = subject.rsplit(' ', 1)
                subject_name = split_subject[0]
                
                split_object = object_.rsplit(' ', 1)
                object_name = split_object[0]
                qid_triples.append([subject_name,triple[1],object_name])
            elif re.search(Q_pattern, subject):
                split_entity = subject.rsplit(' ', 1)
                entity_name = split_entity[0]
                qid_triples.append([entity_name,triple[1],triple[2]])                
            elif re.search(Q_pattern, object_):
                split_entity = object_.rsplit(' ', 1)
                entity_name = split_entity[0]
                qid_triples.append([triple[0],triple[1],entity_name])
            else:
                continue
    for triple in qid_triples:
        if triple in triples[:]:
            triples.remove(triple)
    return triples
    
#normalize all timestamps in triples
def normalize_wikidata_times(triples):
    new_triples = []
    for idx, triple in enumerate(triples):
            object_ = triple[2]
            if re.match("-0\d{3}-01-01T00:00:00Z",object_):
                triples[idx][2] = object_[2:5] + " " + "BC"
            elif re.match("-0\d{3}-\d{2}-\d{2}T00:00:00Z",object_):
                date_list = parse(object_).strftime('%d %B %Y').split(' ')
                date_list[-1] = date_list[-1].lstrip('0')
                triples[idx][2] = ' '.join(date_list) + " " + "BC"
            elif re.match("-\d{4}-01-01T00:00:00Z",object_):
                triples[idx][2] = object_[1:5] + " " + "BC"
            elif re.match("-\d{4}-\d{2}-\d{2}T00:00:00Z",object_):
                triples[idx][2]= parse(object_).strftime('%d %B %Y') + " " + "BC"
            elif re.match("0\d{3}-01-01T00:00:00Z",object_):
                triples[idx][2] = object_[1:4]
            elif re.match("0\d{3}-\d{2}-\d{2}T00:00:00Z",object_):
                date_list = parse(object_).strftime('%d %B %Y').split(' ')
                date_list[-1] = date_list[-1].lstrip('0')
                triples[idx][2] = ' '.join(date_list)
            elif re.match("\d{4}-01-01T00:00:00Z",object_):
                triples[idx][2] = object_[0:4]
            elif re.match("\d{4}-\d{2}-\d{2}T00:00:00Z",object_):
                triples[idx][2]= parse(object_).strftime('%d %B %Y')
            else:
                continue
    return triples

#fix eventkg relations
def fix_relations(triples):
    for idx, triple in enumerate(triples):
        if 'hasBeginTimeStamp' in triple[1]:
           triples[idx][1] = 'start time'
        elif 'hasEndTimeStamp' in triple[1]:
            triples[idx][1] = 'end time'
        if 'hasPlace' in triple[1]:
            triples[idx][1] = 'location'
        if 'type' == triple[1] and 'Event' == triple[2]:
            triples[idx] = None

    triples_unique = []
    for triple in triples:
        if triple not in triples_unique and triple is not None:
            triples_unique.append(triple)
    triples = triples_unique
    return triples

#normalize temporal relations
def normalize_temporal(triples):
    for idx, triple in enumerate(triples):
        if 'start time' in triple[1] or 'end time' in triple[1]:
            # triples.remove(triple)
            triples[idx] = None
    new_triples = [triple for triple in triples if triple is not None]
    year_dict = defaultdict(dict)
    for triple_idx, triple in enumerate(new_triples):
        if 'hasBeginTimeStamp' in triple[1] and '01 January' in triple[2]: 
                year_dict[triple[2].rpartition(' ')[-1]]['has_begin'] = True
                year_dict[triple[2].rpartition(' ')[-1]]['begin_same'] = True
                year_dict[triple[2].rpartition(' ')[-1]]['begin_idx'] = triple_idx
                year_dict[triple[2].rpartition(' ')[-1]]['begin_year'] = triple[2].rpartition(' ')[-1]
                year_dict[triple[2].rpartition(' ')[-1]]['begin_subject'] = triple[0]
        if 'hasEndTimeStamp' in triple[1] and '31 December' in triple[2]: 
                year_dict[triple[2].rpartition(' ')[-1]]['has_end'] = True
                year_dict[triple[2].rpartition(' ')[-1]]['end_same'] = True
                year_dict[triple[2].rpartition(' ')[-1]]['end_idx'] = triple_idx
                year_dict[triple[2].rpartition(' ')[-1]]['end_year'] = triple[2].rpartition(' ')[-1]
                year_dict[triple[2].rpartition(' ')[-1]]['end_subject'] = triple[0]
    
    for year in year_dict:
        if 'has_begin' in year_dict[year] and 'has_end' not in year_dict[year]:
            new_triples[year_dict[year]['begin_idx']][-1] = year
        elif 'has end' in year_dict[year] and 'has_begin' not in year_dict[year]:
            new_triples[year_dict[year]['end_idx']][-1] = year
        elif 'has_begin' in year_dict[year] and 'has_end' in year_dict[year] and 'begin_same' in year_dict[year] and 'end_same' in year_dict[year]:
            new_triples[year_dict[year]['begin_idx']] = None
            new_triples[year_dict[year]['end_idx']] = None
            new_triples.append([year_dict[year]['begin_subject'], 'point in time', year])
    normalized_triples = [triple for triple in new_triples if triple is not None]
    return normalized_triples

with open ('data/triples.json',encoding='utf-8') as f:
    all_triples = json.load(f)
print(len(all_triples))
useless_types=['startUnitType','endUnitType']
with open('data/eventkg_wikidata_augmented_events_with_types.json',encoding='utf-8') as f:
  data = json.load(f)
print(len(data))

##Handle \u2013 in the code \u2013 is -
for i in data:
    # write_missing_event_flag = 0
    # write_invalid_date_event_flag = 0
    try:
        tok=data[i]['text']
        new_event={}
    

        ###FIX TRIPLES/NORMALIZE TRIPLES###
        #normalize event name as one
        Event_name_pattern = '\(EVENT_NAME\)'
        name = None
        for triple in all_triples[i]:
            if re.search(Event_name_pattern, triple[0]):
                    split_name = triple[0].rsplit(' ', 1)
                    name = split_name[0]
                    break
        for triple in all_triples[i]:
            if '(EVENT_NAME)' in triple[0]:
                if name is not None:
                    triple[0] = name
        if name is not None:
            data[i]['wikidataLabel'] = name
            new_event["Event_Name"] = data[i]['wikidataLabel']
        else:
            new_event["Event_Name"] = data[i]['wikidataLabel']

        for triple in data[i]['triples']:
            if name is not None:
                triple[0] = name
            else:
                triple[0] = data[i]['wikidataLabel']
       


        #fix begin and endtimestamp and fix times which are invalid
        fixed_time_stamp_triples_orig = fix_timestamps(data[i]['triples'])
        
        #normalize temporal of originla
        normalized_temporal_orig = normalize_temporal(fixed_time_stamp_triples_orig)
        #normalize relations of original triples
        fixed_relations_orig = fix_relations(normalized_temporal_orig)
        #Filter: keep unique triples only
        unique_orig_triples = []
        for triple in fixed_relations_orig:
            if triple not in unique_orig_triples:
                unique_orig_triples.append(triple)


        #normalize times from wikidata triples
        normalized_wikidata_times = normalize_wikidata_times(all_triples[i])
        #Filter: keep unique triples only
        unique_wikidata_triples = []
        for triple in normalized_wikidata_times:
            if triple not in unique_wikidata_triples:
                unique_wikidata_triples.append(triple)
        #remove lowercase duplicates
        filtered_lowercase_orig = filter_lowercase(unique_orig_triples, unique_wikidata_triples)
      
        
        combined_triples = unique_wikidata_triples + filtered_lowercase_orig
   
        # #remove non QID if QID instance exists
        non_duplicate_QIDs = remove_non_QID_duplicates(combined_triples)
       
        #Final Filter: keep unique triples only

       
        new_event['triples'] = non_duplicate_QIDs
        wiki_label=data[i]['wikipediaLabel']
        wiki_label=wiki_label.replace(" ","_")
        new_event['wikipediaLabel']=wiki_label
        if "\\" in wiki_label[-1] or wiki_label == 'At_the_1998_FIFA_World_Cup,_the_32_teams_were_divided_into_eight_groups_of_four,_labelled_A–H.':
            new_event['wikipediaLabel'] = new_event['Event_Name'].replace(' ','_')
        try:
            text=data[i]['text']
            remove_square_bracket = re.compile(r'\[[^>]*\]')
            remove_angle_bracket = re.compile(r'\<[^>]*\>')
            # remove_parentheses = re.compile(r'\([^>]*\)')
            text = re.sub(remove_square_bracket, '', text)
            text = re.sub(remove_angle_bracket, '', text)
            # text = re.sub(remove_parentheses, '', text)
            text=text.rstrip()
            if text and str(text[-1]) != '.':
                    text = text+'.'
         
            
            new_event["narration"]=text
            # if write_missing_event_flag:
            with open("data/eventkg_wikidata.json", "a",encoding='utf-8') as data1:
                data1.write(json.dumps(new_event,ensure_ascii=False))
                data1.write("\n")
        except:
            print("Exception thrown in text and write")
            pass
    except:
        print("Error while creating event")
        print(data[i]['wikidataLabel'])
        print(unique_orig_triples)
        print('\n')
        print(traceback.format_exc())
        print('\n\n')
        pass