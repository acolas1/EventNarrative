import os
import json
import re

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

def normalize_relations(relation):
    relation = re.sub("([a-z])([A-Z])","\g<1> \g<2>",relation)
    relation = relation.replace('_', ' ')
    return relation

def convert_to_huggingface(dataset,split):
    narrative_file = open('narrative_tmp.txt', 'w')

    triples_data_bart = []
    triples_data_t5 = []
    tokenized_text_list = []
    for data in dataset:
        entity_ref_dict = data['entity_ref_dict']
        text = data['narration']
        triples = data['keep_triples']
        
        filled_text = text.strip()
        for ref in entity_ref_dict:
            filled_text = filled_text.replace(ref, entity_ref_dict[ref])
        filled_text = filled_text.lower().strip()
        
        triples_text = ''
        
        new_triple = []
        for triple in triples:
            subject = triple[0].lower()
            relation = normalize_relations(triple[1]).lower()
            object_ = triple[2].lower()
            new_triple.insert(0,'<S>')
            new_triple.insert(1,subject)
            new_triple.insert(2,'<P>')
            new_triple.insert(3,relation)
            new_triple.insert(4,'<O>')
            new_triple.insert(5,object_)
            new_triple_text = ' '.join(new_triple)
            triples_text = new_triple_text + ' '
        triples_text = triples_text.strip()
        triples_data_bart.append(triples_text)
        triples_text_t5 = 'translate from Graph to Text: ' + triples_text
        triples_text_t5 = triples_text_t5.strip()
        triples_data_t5.append(triples_text_t5)
        
        tokenized_text = tokenize_text(filled_text)
        tokenized_text_list.append(tokenized_text)
        narrative_file.write(tokenized_text + '\n')

    narrative_file.close()
    os.system("perl detokenize.perl -l en -q < /Users/anthonycolas/projects/qa_narration/EKG_DKB_Preprocessing/preprocess/narrative_tmp.txt > narrative_tmp.detok")

    detok_narratives = open('narrative_tmp.detok', 'r').readlines()

    with open('../data/split_data/huggingface_bart/' + split + '.source', 'w', encoding='utf8') as f:
        f.write('\n'.join(triples_data_bart))
    with open('../data/split_data/huggingface_bart/' + split + '.target.tok', 'w', encoding='utf8') as f:
        f.write('\n'.join(tokenized_text_list))
    with open('../data/split_data/huggingface_bart/' + split + '.target', 'w', encoding='utf8') as f:
        f.write(''.join(detok_narratives))

    with open('../data/split_data/huggingface_t5/' + split + '.source', 'w', encoding='utf8') as f:
        f.write('\n'.join(triples_data_t5))
    with open('../data/split_data/huggingface_t5/' + split + '.target.tok', 'w', encoding='utf8') as f:
        f.write('\n'.join(tokenized_text_list))
    with open('../data/split_data/huggingface_t5/' + split + '.target', 'w', encoding='utf8') as f:
        f.write(''.join(detok_narratives))

path = "../data/split_data/"
filelist = [dir_file for dir_file in os.listdir(path) if dir_file.endswith('.json')]

for file_ in filelist:
    data_list = []
    with open(path+file_, 'r', encoding='utf-8') as files:
        data_list = json.load(files)
    file_ = file_.split('.')[0]
    print(len(data_list))
    print(file_)
    convert_to_huggingface(data_list,file_)
