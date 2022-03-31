# -*- coding: utf-8 -*-
import json
import numpy
from itertools import islice
from functools import partial

# with open('data/eventkg_qa_wikidata_augmented_events_with_types.json') as f:
#   data = json.load(f)
# print(len(data))

#https://stackoverflow.com/questions/22878743/how-to-split-dictionary-into-multiple-dictionaries-fast
def chunks(data, SIZE=10000):
    print(SIZE)
    it = iter(data)
    for i in range(0, len(data), SIZE):
        # for k in islice(it, SIZE):
        #     print(k)
        #     print(data[k])
        #     print(dafadfda)
        yield {k:data[k] for k in islice(it, SIZE)}

def split(data_list, num_splits):
     return numpy.array_split(data_list, num_splits)

path = '../data/eventkg_wikidata.json'
# data_list = []
# with open(path, 'r') as data_file:
#     for line in data_file:
#         temp_table = json.loads(line.strip('\n'))
#         data_list.append(temp_table)

# for idx, chunk in enumerate(chunks(large_file,int(numpy.ceil(len(large_file)/2)))):
#     with open ("data/simple_text/eventkg_wikidata_simple_"+str(idx)+".json", mode='wt',encoding='utf-8') as f:
#         json.dump(chunk, f,indent=4, ensure_ascii=False)
#         # f.write('\n'.join(map(json.dumps, chunk)))

data_list = []
with open(path, 'r') as data_file:
    for line in data_file:
        temp_table = json.loads(line.strip('\n'))
        data_list.append(temp_table)
print(len(data_list))

mapdumps = partial(json.dumps, ensure_ascii=False)
for i,chunk in enumerate(split(data_list,11)):
    with open ("../data/simple_text/simple_text_"+str(i)+".json", mode='wt',encoding='utf-8') as myfile:
        myfile.write('\n'.join(map(mapdumps, chunk)))
