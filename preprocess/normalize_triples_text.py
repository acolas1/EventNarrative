# -*- coding: utf-8 -*-

import os
import wikipedia
from bs4 import BeautifulSoup
from collections import defaultdict
from urllib.parse import unquote
import requests
import re
import json
import time
from tqdm import tqdm
import traceback
from mapper import WikiMapper
import argparse
import bs4
import nltk
from dateutil.parser import parse
import calendar
from datetime import datetime, date
import unicodedata
import unicodedata

parser = argparse.ArgumentParser()
# default_date = datetime.combine(date.today(), datetime.min.time()).replace(day=1)

parser.add_argument("-input", "--input", help="Input name")
parser.add_argument("-output_dir", "--output_dir", help="Output name")

latest_mapper = WikiMapper(
    "wikimapper/data/lower_enwiki-latest.db")
mapper_0101 = WikiMapper(
    "wikimapper/data/lower_enwiki-20210101.db")


def is_date(string):
    try:
        parse(string, default=default_date)
        return True
    except:
        return False


def is_number(s):
    try:
        float(s)
        return True
    except:
        return False


def find_dates_in_text(event_name, text):
    pattern_1 = fr"(?i)(?<!\w)(\d{{1,2}}\s(?:{months})\s\d{{4}}) *(?:-|–|and|&|to|or) *(\d{{1,2}}\s(?:{months})\s\d{{4}}\b)"
    pattern_2 = fr"(?i)(?<!\w)(\d{{1,2}}\s(?:{months})) *(?:-|–|and|&) *(\d{{1,2}}\s(?:{months})\s\d{{4}}\b)"
    pattern_3 = fr"(?i)(?<!\w)(\d{{1,2}}) *(?:-|–|and|&) *(\d{{1,2}}\s(?:{months})\s\d{{4}}\b)"
    pattern_4 = fr"(?i)(?<!\w)(\d{{1,2}}\s(?:{months})) *(?:-|–|and|&) *(\d{{1,2}}\s(?:{months})\b)"
    pattern_5 = fr"(?i)(?<!\w)(\d{{1,2}}) *(?:-|–|and|&) *(\d{{1,2}}\s(?:{months})\b)"
    pattern_6 = fr"(?i)(?<!\w)(\d{{1,2}}\s(?:{months})\s\d{{4}}\b)"
    pattern_7 = fr"(?i)(?<!\w)(\d{{1,2}}\s(?:{months})\b)"
    pattern_8 = fr"(?i)((?<!\w)(?:{months})\s\d{{4}}\b)"
    pattern_9 = fr"(?i)((?<!\w)(?:{months})\s\d{{1,2}},\s\d{{4}}\b)"
    pattern_10 = fr"(?i)((?<!\w)(?:{months})\s\d{{1,2}}\b)"
    patterns = [pattern_1, pattern_2, pattern_3, pattern_4, pattern_5,
                pattern_6, pattern_7, pattern_8, pattern_9, pattern_10]

    temp_text = text
    dates_dict = defaultdict(list)
    for pattern in patterns:
        found = re.findall(pattern, temp_text)
        spans = [x.span() for x in re.finditer(pattern, temp_text)]
        if len(found) > 0:
            if isinstance(found[0], tuple):
                for idx, i in enumerate(found):
                    first = i[0]
                    second = i[1]

                    match_indices = spans[idx]
                    first_indeces = (
                        match_indices[0], match_indices[0]+len(first))
                    second_indeces = (
                        match_indices[1]-len(second), match_indices[1])

                    split_second = second.split(' ')
                    if len(split_second) == 3:
                        if len(first.split(' ')) == 1:
                            new_first = first+' '+' '.join(split_second[1:])
                        elif len(first.split(' ')) == 2:
                            new_first = first+' '+' '.join(split_second[2:])
                        else:
                            new_first = first
                        dates_dict[new_first].append(first_indeces)
                        # dates.append(new_first)
                        dates_dict[second].append(second_indeces)
                        # dates.append(second)
                        # replace second indices first
                        temp_text = temp_text[:second_indeces[0]] + \
                            second + temp_text[second_indeces[1]:]
                        # replace first indices next
                        temp_text = temp_text[:first_indeces[0]] + \
                            new_first + temp_text[first_indeces[1]:]
                    elif len(split_second) == 2:
                        if len(first.split(' ')) == 1:
                            new_first = first+' '+' '.join(split_second[1:])
                        else:
                            new_first = first
                        dates_dict[new_first].append(first_indeces)
                        dates_dict[second].append(second_indeces)
                        # replace second
                        temp_text = temp_text[:second_indeces[0]] + \
                            second + temp_text[second_indeces[1]:]
                        # replace first
                        temp_text = temp_text[:first_indeces[0]] + \
                            new_first + temp_text[first_indeces[1]:]
            else:
                for idx, i in enumerate(found):
                    match_indices = spans[idx]
                    first_index = match_indices[0]
                    second_indeces = match_indices[1]
                    dates_dict[i].append(match_indices)
                    # replace
                    temp_text = temp_text[:first_index] + \
                        i + temp_text[second_indeces:]
    return dates_dict, temp_text

# This code block will replace the bold best match to the wikipediaLabel entity with the wikipediaLabel


def get_bold_match(soup, title):
    tags = soup.find_all()
    bold_list = []
    for tag in tags:
        if isinstance(tag, bs4.element.Tag):
            if tag.name == 'h2':
                break
            elif tag.previousSibling and tag.previousSibling.name == 'h2':
                break
            elif tag.name == 'p':
                if '<b>' in str(tag):
                    bold_list.extend(re.findall(r'<b>(.+?)</b>', str(tag)))
                tag = tag.nextSibling
                if not tag:
                    break
            else:
                tag = tag.nextSibling
        else:
            tag = tag.nextSibling
    clean_list = []
    for bold in bold_list:
        bold = BeautifulSoup(bold, "lxml").text
        if bold and bold.strip() and '<a href=' not in bold and bold != '.':
            clean_list.append(bold)
    if clean_list:
        distance_list = [nltk.edit_distance(
            title, bold) for bold in clean_list]
        min_pos = distance_list.index(min(distance_list))
        return str(clean_list[min_pos])
    else:
        return None


# Execute below functions before executing code for TEXT Normalization
def get_blue_links_wikidata_ID(event):
    entity_dict = defaultdict(list)
    event_title = event["wikipediaLabel"]
    event_title = event_title.replace('?', '%3F')

    # flag/switch used to get entities from the correct mapper.
    # True if found in wikipedia call
    # False if found in local wikipedia (from 01-01-2021)
    wikipedia_api_flag = False
    try:
        result = requests.get(
            f'http://localhost:8080/wikipedia_en_all_nopic_2021-01/A/{event_title}', allow_redirects=True)
        if result.status_code == 302:
            result = requests.get(f'https://en.wikipedia.org/wiki/{event_title}', headers={
                                  'User-agent': 'wikipedia_302'+str(event_title.encode('utf-8'))})
            wikipedia_api_flag = True
        if result.status_code == 429:
            time.sleep(1)
            result = requests.get(
                f'http://localhost:8080/wikipedia_en_all_nopic_2021-01/A/{event_title}')
        if result.status_code == 404:
            time.sleep(1)
            result = requests.get(f'https://en.wikipedia.org/wiki/{event_title}', headers={
                                  'User-agent': 'wikipedia_404'+str(event_title.encode('utf-8'))})
            wikipedia_api_flag = True
    except requests.exceptions.TooManyRedirects as exc:
        result = requests.get(f'https://en.wikipedia.org/wiki/{event_title}', headers={
                              'User-agent': 'wikipedia_TooManyRedirects'+str(event_title.encode('utf-8'))})
        wikipedia_api_flag = True
    result.encoding = 'utf-8'
    invalid_strings = ['http://', 'https://', 'redlink=1', '#cite_note', 'action=edit',
                       '#ref_', '#cnote_', '.php?', 'geo:', '#CITEREF', 'endnote', 'Special:']
    if result.text:
        soup = BeautifulSoup(result.text, 'html.parser')
        all_div = soup.find_all("div")
        for div in all_div:
            if "class" in div and "redirectMsg" in str(div["class"]):
                redirect = div.find('ul').find('a')['href'].split("/")[2][:-2]
                result = requests.get(
                    f'http://localhost:8080/wikipedia_en_all_nopic_2021-01/A/{redirect}', allow_redirects=False)
                if result.text:
                    soup = BeautifulSoup(result.text, 'html.parser')
        for item in soup.find_all("p"):
            for a in item.find_all('a', href=True):
                a_str = str(a['href'])
                
                if not any(ele in a_str for ele in invalid_strings) and len(a.contents) > 0 and 'upload.wikimedia.org' not in str(a.contents[0]):

                    # first get the page id
                    if '/wiki/' in a_str:
                        wikipedia_title = a_str.split("/wiki/")[-1]
                    elif '/A/' in a_str:
                        wikipedia_title = a_str.split("/A/")[-1]
                    else:
                        wikipedia_title = unquote(a_str)

                    # check if # in string, if so split
                    if "#" in wikipedia_title:
                        if wikipedia_title[0] == '#':
                            if '#' in wikipedia_title[1:]:
                                wikipedia_title = wikipedia_title.split(
                                    "#")[-1]
                            else:
                                wikipedia_title = wikipedia_title[1:]
                        else:
                            wikipedia_title = wikipedia_title.split("#")[0]
                    entity_in_article_name = str(a.text)
                    # entity_in_article_name = re.sub(
                    #     r'\<[^>]*\>', '', str(a.contents[0]))
                    entity_dict[wikipedia_title].append(entity_in_article_name)

        # get best match for the wikipediaLabel
        label = event['Event_Name'].replace('_', ' ')
        event_name_in_article = get_bold_match(soup, label)
        if event_name_in_article:
            entity_dict[event['Event_Name']].append(event_name_in_article)

    # get wikidata ids for blue links
    wikidata_id_name_dict = {}
    for wikipedia_title in entity_dict:
        # if wikipedia_title is the name of the main article (wikipediaLabel)
        # then use the first QID
        if wikipedia_title == event['Event_Name']:
            QID = get_triple_wiki_ID(event["wikipediaLabel"])
            wikidata_id_name_dict[str(QID)] = entity_dict[wikipedia_title]
        else:
            try:
                if wikipedia_api_flag:
                    wikidata_id = latest_mapper.title_to_id(
                        wikipedia_title.lower())
                else:
                    wikidata_id = mapper_0101.title_to_id(
                        wikipedia_title.lower())
                if wikidata_id is None:
                    request_result = requests.get(f'https://www.wikidata.org/w/api.php?action=wbgetentities&sites=enwiki&titles={wikipedia_title}&normalize=1&format=json', headers={
                                                  'User-agent': 'wikidata_get_blue_links_wikidata_ID'+str(wikipedia_title.encode('utf-8'))})
                    result = request_result.json()
                    for key in result['entities'].keys():
                        wikidata_id = key
                if wikidata_id is None or wikidata_id == '-1':
                    pass
                wikidata_id_name_dict[str(
                    wikidata_id)] = entity_dict[wikipedia_title]
            except Exception:
                f.write("EXCEPTION")
                f.write("\n")
                f.write(str(event_title))
                f.write('\n')
                f.write(str(entity_dict))
                f.write('\n')
                f.write("article title " + str(wikipedia_title))
                f.write('\n')
                f.write(str(request_result.text))
                f.write(traceback.format_exc())
                f.write('\n\n\n\n')
    return(wikidata_id_name_dict)


def get_triple_wiki_ID(entity_name):
    entity_name = entity_name.title().replace(' ', '_')
    ID = latest_mapper.title_to_id(entity_name.lower())
    return ID


f = open("logs/log_normalization.err", "a")

args = parser.parse_args()
# write into a new file
path = args.input
input_file = path.split('/')[-1]
output_dir = args.output_dir
output = (output_dir+input_file).replace('.json', '_blue_links.json')

get_triple_wiki_ID_searched = dict()

output_set = set()
print(output)
# if os.path.isfile(output):
#     with open(output, 'r', encoding='utf-8') as files:
#         for line in files:
#             temp_table = json.loads(line.strip('\n'))
#             output_set.add(temp_table["wikipediaLabel"])

with open(path, 'r', encoding='utf-8') as files:
    for event in tqdm([json.loads(line.strip('\n')) for line in files]):
        try:
            if event["wikipediaLabel"] not in output_set and event["narration"]:
                try:
                    if 'Event_Name' not in event:
                        event['Event_Name'] = event['triples'][0][0]
                    event_name = event['Event_Name']
                    wikidata_id_name_dict = get_blue_links_wikidata_ID(event)
                    wikidata_id_name = wikidata_id_name_dict

                    keep_dict = dict()
                    entity_name_qid_dict = dict()
                    wikipedia_article_QID = get_triple_wiki_ID(
                        event["wikipediaLabel"])
                    wikipediaLabel = str(event['Event_Name']).replace('_', ' ')
                    event['Event_Name'] = event['Event_Name'].replace('_',' ')
                    keep_dict[wikipedia_article_QID] = wikipediaLabel
                    get_triple_wiki_ID_searched[wikipediaLabel] = wikipedia_article_QID
                    entity_name_qid_dict[wikipedia_article_QID] = wikipediaLabel
                    entity_name_qid_dict['wikidataID'] = event['Event_Name']
                    keep_dict['wikidataID'] = event['Event_Name']
                    # not_delete=['Name_ID','TEXT','wikipediaLabel','wikidata_type_label','instance of', 'hasBeginTimeStamp', 'hasEndTimeStamp']
                    ignore = ['wikidata_type_label',
                              'label', 'alternative', 'sameAs']

                    # pattern to find QID in entity name
                    Q_pattern = '\([Q]+[0-9]+\)'
                    delete = []

                    # keep_triples = []
                    # first normalize relations from eventkg to wikidata
                    for triple in event['triples']:
                        if '_' in triple[0]:
                            triple[0] = triple[0].replace('_', ' ')
                        if (triple[1] not in ignore) and not is_date(triple[0]) and not is_date(triple[2]) and 'entity_' not in triple[0].lower() and 'event_' not in triple[0].lower() and 'category:' not in triple[0].lower() and triple[1] != 'alternative':
                            subject = triple[0]
                            object_ = triple[2]
                            # case where subject entity is the event name
                            if subject == event_name:
                                if re.search(Q_pattern, object_):
                                    split_entity = object_.rpartition(' ')
                                    entity_name = split_entity[0]
                                    ID = None
                                    triple[2] = entity_name
                                    if entity_name not in get_triple_wiki_ID_searched:
                                        if len(split_entity) > 1:
                                            ID = split_entity[-1][1:-1]
                                            if ID is not None:
                                                get_triple_wiki_ID_searched[entity_name] = ID
                                                if ID not in entity_name_qid_dict:
                                                    entity_name_qid_dict[ID] = entity_name
                                        else:
                                            entity_name = None
                                            ID = None
                                    else:
                                        try:
                                            ID = get_triple_wiki_ID_searched[entity_name]
                                            if ID is not None and ID not in entity_name_qid_dict:
                                                entity_name_qid_dict[ID] = entity_name
                                        except:
                                            ID = None
                                else:
                                    entity_name = object_
                                    ID = None
                                # if ID is not None and ID in get_triple_wiki_ID_searched and ID not in entity_name_qid_dict:
                                #     entity_name_qid_dict[ID] = entity_name

                            # case where subject and object have QID (subject is not event name)
                            else:
                                if re.search(Q_pattern, subject) and re.search(Q_pattern, object_):
                                    split_subject = subject.rpartition(' ')
                                    split_object = object_.rpartition(' ')

                                    subject_name = split_subject[0]
                                    object_name = split_object[0]

                                    if len(subject_name) > 1 and len(object_name) > 1:
                                        if subject_name in get_triple_wiki_ID_searched:
                                            subject_ID = get_triple_wiki_ID_searched[subject_name]
                                        else:
                                            subject_ID = split_subject[-1][1:-1]
                                            get_triple_wiki_ID_searched[subject_name] = subject_ID
                                        if subject_ID is not None and subject_ID not in entity_name_qid_dict:
                                            entity_name_qid_dict[subject_ID] = subject_name

                                        if object_name in get_triple_wiki_ID_searched:
                                            object_ID = get_triple_wiki_ID_searched[object_name]
                                        else:
                                            object_ID = split_object[-1][1:-1]
                                            get_triple_wiki_ID_searched[object_name] = object_ID
                                        if object_ID is not None and object_ID not in entity_name_qid_dict:
                                            entity_name_qid_dict[object_ID] = object_name

                                    else:
                                        subject_ID = None
                                        object_ID = None
                                else:
                                    subject_name = subject
                                    object_name = object_
                                    subject_ID = None
                                    object_ID = None

                                # if (subject_ID is not None and subject_ID in wikidata_id_name) and (object_ID is not None and object_ID in wikidata_id_name):
                                #     keep_dict[subject_ID] = subject_name
                                #     keep_dict[object_ID] = object_name

                                    # entity_name_qid_dict[subject_name] = subject_ID
                                    # entity_name_qid_dict[object_name] = object_ID
                    # for those that do not have wikidata id next to their entity names, find id and try to match
                    for triple in event['triples']:
                        if (triple[1] not in ignore) and not is_date(triple[0]) and not is_date(triple[2]) and 'entity_' not in triple[0].lower() and 'event_' not in triple[0].lower() and 'category:' not in triple[0].lower():
                            subject = triple[0]
                            object_ = triple[2]
                            if re.search(Q_pattern, subject):
                                split_entity = subject.rpartition(' ')
                                subject = split_entity[0]
                                triple[0] = subject
                            if re.search(Q_pattern, object_):
                                split_entity = object_.rpartition(' ')
                                object_ = split_entity[0]
                                triple[2] = object_
                            # case for both not in dict. both s & o need to find match
                            if subject in get_triple_wiki_ID_searched:
                                subject_ID = get_triple_wiki_ID_searched[subject]
                            else:
                                subject_ID = get_triple_wiki_ID(subject)
                                get_triple_wiki_ID_searched[subject] = subject_ID
                            if subject_ID is not None and subject_ID not in entity_name_qid_dict:
                                entity_name_qid_dict[subject_ID] = subject

                            if object_ in get_triple_wiki_ID_searched:
                                object_ID = get_triple_wiki_ID_searched[object_]
                            else:
                                object_ID = get_triple_wiki_ID(object_)
                                get_triple_wiki_ID_searched[object_] = object_ID
                            if object_ID is not None and object_ID not in entity_name_qid_dict:
                                entity_name_qid_dict[object_ID] = object_

                            # if subject_ID in keep_dict and subject != keep_dict[subject_ID]:
                            #     triple[0] = keep_dict[subject_ID]
                            #     subject = triple[0]
                            # if object_ID in keep_dict and object_ != keep_dict[object_ID]:
                            #     triple[2] = keep_dict[object_ID]
                            #     object_ = triple[2]
                            # if subject_ID not in keep_dict and object_ID not in keep_dict:

                            #     if subject_ID is not None and object_ID is not None and subject_ID in wikidata_id_name and object_ID in wikidata_id_name:

                            #         keep_dict[subject_ID] = subject
                            #         keep_dict[object_ID] = object_

                                # entity_name_qid_dict[subject] = subject_ID
                                # entity_name_qid_dict[object_] = object_ID
                                # triple = [subject, triple[1], object_]

                            # # case for only object_ not in dict.
                            # elif object_ID not in keep_dict:
                            #     if object_ID is not None and object_ID in wikidata_id_name:

                            #         keep_dict[object_ID] = object_
                            #         # entity_name_qid_dict[object_] = object_ID

                            #         triple = [subject, triple[1], object_]

                            # # case for only subject not in dict.
                            # elif subject_ID not in keep_dict:
                            #     # subject_ID = get_triple_wiki_ID(subject)
                            #     if subject_ID is not None and subject_ID in wikidata_id_name:
                            #         keep_dict[subject_ID] = subject
                            #         # entity_name_qid_dict[subject] = subject_ID

                            #         # get_triple_wiki_ID_searched[subject_ID] = subject
                            #         triple = [subject, triple[1], object_]
                                # if triple not in keep_triples:
                                #     keep_triples.append([subject,triple[1],object_])

                    replace_dict = dict()
                    # make dictionary with key as the entity in-text and value as entity in graph
                    for id in wikidata_id_name:
                        if id in entity_name_qid_dict:
                            replace_entity = entity_name_qid_dict[id]
                            for blue_link in wikidata_id_name[id]:
                                replace_dict[blue_link] = replace_entity
                        # for name, qid in entity_name_qid_dict.items():
                        #     if qid == id:
                                # replace_entity = name
                                # for blue_link in wikidata_id_name[id]:
                                #     replace_dict[blue_link] = replace_entity
                    # sort dict by length (some entities have overlap)
                    sorted_replace_dict = dict()
                    for k in sorted(replace_dict, key=len, reverse=True):
                        sorted_replace_dict[k] = replace_dict[k]
                    ###########dates after blue link###############
                    ignore_exact = ['wikidata_type_label', 'label', 'sameAs']
                    months = "|".join(
                        calendar.month_name[1:]+calendar.month_abbr[1:])
                    month_names = calendar.month_name[1:] + \
                        calendar.month_abbr[1:]
                    abbr_to_num = {name: num for num, name in enumerate(calendar.month_abbr) if num}
                    month_to_num = {name: num for num, name in enumerate(calendar.month_name) if num}
                    month_to_num.update(abbr_to_num)
                    dates_dict, temp_text = find_dates_in_text(
                        event['Event_Name'], event['narration'])
                    event['narration'] = temp_text
                    sorted_dates_dict = dict()
                    for k in sorted(dates_dict, key=len, reverse=True):
                        sorted_dates_dict[k] = dates_dict[k]
                    dates_in_text = sorted(dates_dict, key=len, reverse=True)

                    text_normalized_dict = dict()
                    for idx, date in enumerate(dates_in_text):
                        date = unicodedata.normalize("NFKD", date)
                        split_date = date.split(' ')
                        if len(split_date) > 2:
                            try:
                                text_normalized_dict[date] = parse(date).strftime('%d %B %Y')
                            except:
                                print(date)
                        elif len(date.split(' ')) > 1:
                            if split_date[0] in month_names:
                                month_num = month_to_num[split_date[0]]
                                try:
                                    newDate = datetime(1904,month_num,int(split_date[1]))
                                    text_normalized_dict[date] = parse(date + ' 1904').strftime('%d %B')
                                except ValueError:
                                    if len(split_date[1]) >= 3:
                                        text_normalized_dict[date] = parse(date).strftime('%B %Y')
                                    else:
                                        # split_date.reverse()
                                        new_date = ' '.join(split_date)
                                        text_normalized_dict[date] = new_date
                            elif split_date[1] in month_names:
                                month_num = month_to_num[split_date[1]]
                                try:
                                    newDate = datetime(1904,month_num,int(split_date[0]))
                                    text_normalized_dict[date] = parse(date + ' 1904').strftime('%d %B')
                                except ValueError:
                                    if len(split_date[0]) >= 3:
                                        text_normalized_dict[date] = parse(date).strftime('%B %Y')
                                    else:
                                        split_date.reverse()
                                        new_date = ' '.join(split_date)
                                        text_normalized_dict[date] = new_date
                        else:
                            text_normalized_dict[date] = parse(date).strftime('%d')
                    
                    sorted_text_normalized_dict = dict()
                    for k in sorted(text_normalized_dict, key=len, reverse=True):
                        sorted_text_normalized_dict[k] = text_normalized_dict[k]

                    for triple in event['triples']:
                        if triple[1] not in ignore_exact and is_date(triple[2]) and not is_number(triple[2]) and len(triple[2].split(' ')) > 1:
                            date = triple[2]
                            date = unicodedata.normalize("NFKD", date)
                            if any(month_name in date for month_name in month_names):
                                split_date = date.split(' ')
                                if ' BC' in date:
                                    triple[2] = triple[2]
                                if len(split_date) > 2:
                                    if len(split_date[-1]) >= 3:
                                        triple[2] = parse(
                                            date).strftime('%d %B %Y')
                                    else:
                                        triple[2] = triple[2]
                                elif len(split_date) > 1:
                                    if split_date[0] in month_names:
                                        month_num = month_to_num[split_date[0]]
                                        try:
                                            newDate = datetime(1904,month_num,int(split_date[1]))
                                            triple[2] = parse(date + ' 1904').strftime('%d %B')
                                        except ValueError:
                                            if len(split_date[1]) >= 3:
                                                triple[2] = parse(date).strftime('%B %Y')
                                            else:
                                                # split_date.reverse()
                                                new_date = ' '.join(split_date)
                                                triple[2] = new_date
                                    elif split_date[1] in month_names:
                                        month_num = month_to_num[split_date[1]]
                                        try:
                                            newDate = datetime(1904,month_num,int(split_date[0]))
                                            triple[2] = parse(date + ' 1904').strftime('%d %B')
                                        except ValueError:
                                            if len(split_date[0]) >= 3:
                                                triple[2] = parse(date).strftime('%B %Y')
                                            else:
                                                split_date.reverse()
                                                new_date = ' '.join(split_date)
                                                triple[2] = new_date
                                    elif len(split_date[-1]) >= 3 and is_number(split_date[-1]):
                                        triple[2] = parse(
                                            date).strftime('%B %Y')
                                    else:

                                        split_date = date.split(' ')
                                        triple[2] = parse(
                                            date + ' 1904').strftime('%d %B')

                    date_replace_dict = dict()

                    date_replace_dict = dict()
                    for date_in_text in sorted_text_normalized_dict:
                        found = False
                        for triple in event['triples']:
                            if triple[1] not in ignore_exact and sorted_text_normalized_dict[date_in_text] == triple[2]:
                                date_replace_dict[date_in_text] = triple[2]
                                found = True
                                break
                        if found == False:
                            for triple in event['triples']:
                                if triple[1] not in ignore_exact and re.search(r'(?<!\w){}(?!\w)'.format(re.escape(sorted_text_normalized_dict[date_in_text])), triple[2]):
                                    date_replace_dict[date_in_text] = triple[2]
                                    found = True
                                    break
                        if found == False:
                            for triple in event['triples']:
                                if triple[1] not in ignore_exact and re.search(r'(?<!\w){}(?!\w)'.format(re.escape(triple[2])), sorted_text_normalized_dict[date_in_text]):
                                    date_replace_dict[date_in_text] = triple[2]
                                    found = True
                                    break

                    merged__with_dates_dict = {
                        **sorted_replace_dict, **date_replace_dict}
                    sorted_merged__with_dates_dict = dict()
                    for k in sorted(merged__with_dates_dict, key=len, reverse=True):
                        sorted_merged__with_dates_dict[k] = merged__with_dates_dict[k]
                    ###########exact match case after dates###############
                    replace_exact_list = []
                    exact_replace_dict = dict()
                    replace_exact_dict = defaultdict(list)
                    for triple in event['triples']:
                        if triple[1] not in ignore_exact:
                            subject = triple[0]
                            object_ = triple[2]

                            if re.search(Q_pattern, subject):
                                split_entity = subject.rpartition(' ')
                                subject = split_entity[0]
                                triple[0] = subject
                            if re.search(Q_pattern, object_):
                                split_entity = object_.rpartition(' ')
                                object_ = split_entity[0]
                                triple[2] = object_
                            if subject not in sorted_merged__with_dates_dict.keys() and re.search(r'(?<!\w){}(?!\w)'.format(re.escape(subject)), event['narration']):
                                exact_replace_dict[subject] = subject
                            if object_ not in sorted_merged__with_dates_dict.keys() and re.search(r'(?<!\w){}(?!\w)'.format(re.escape(object_)), event['narration']):
                                exact_replace_dict[object_] = object_

                    merged_dictionary = {
                        **sorted_merged__with_dates_dict, **exact_replace_dict}

                    sorted_merged_dictionary = dict()
                    for k in sorted(merged_dictionary, key=len, reverse=True):
                        sorted_merged_dictionary[k] = merged_dictionary[k]
                    # entities_set = set()
                    # temp_text = None
                    # for i, in_text in enumerate(sorted_merged_dictionary):
                    #     if in_text in event['narration']:
                    #        temp_text = event['narration'].replace(in_text,'<entity_'+str(i)+'>')
                    #        event['entity_ref_dict']['<entity_'+str(i)+'>'] = sorted_merged_dictionary[in_text]
                    #        entities_set.add(sorted_merged_dictionary[in_text])

                    # keep_triples = []
                    # contained_entities = set()
                    # ignore = ['wikidata_type_label',
                    #           'label', 'sameAs']
                    # for triple in event['triples']:
                    #     if triple[1] not in ignore:
                    #         subject = triple[0]
                    #         object_ = triple[2]
                    #         if subject in entities_set and object_ in entities_set:
                    #             keep_triples.append(triple)
                    #             contained_entities.add(subject)
                    #             contained_entities.add(object_)

                    # event['keep_triples'] = unique_keep_triples
                    event['entities_in_text'] = sorted_merged_dictionary
                    with open(output, "a", encoding='utf-8') as data1:
                        data1.write(json.dumps(event, ensure_ascii=False))
                        data1.write("\n")
                    output_set.add(event["wikipediaLabel"])
                except Exception:
                    f.write(str(event['Event_Name']))
                    f.write('\n')
                    f.write(str(wikidata_id_name))
                    f.write('\n')
                    f.write(traceback.format_exc())
                    f.write('\n\n\n\n')
        except Exception:
            f.write(str(event['Event_Name']))
            f.write('\n')
            f.write(str(wikidata_id_name))
            f.write('\n')
            f.write(traceback.format_exc())
            f.write('\n\n\n\n')
f.close()
