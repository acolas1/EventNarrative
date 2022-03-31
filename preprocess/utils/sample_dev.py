import os
import json
import random

sources_bart = open('../data/split_data/huggingface_bart/val.source', 'r', encoding='utf-8').readlines()
targets_bart = open('../data/split_data/huggingface_bart/val.target', 'r', encoding='utf-8').readlines()
targets_tok_bart = open('../data/split_data/huggingface_bart/val.target.tok', 'r', encoding='utf-8').readlines()

sources_t5 = open('../data/split_data/huggingface_t5/val.source', 'r', encoding='utf-8').readlines()
targets_t5 = open('../data/split_data/huggingface_t5/val.target', 'r', encoding='utf-8').readlines()
targets_tok_t5 = open('../data/split_data/huggingface_t5/val.target.tok', 'r', encoding='utf-8').readlines()



zipped = list(zip(sources_bart,targets_bart,targets_tok_bart,sources_t5,targets_t5,targets_tok_t5))
_1000_sample = random.sample(zipped, 1000)
unzipped = list(zip(*_1000_sample))

with open('../data/split_data/huggingface_bart/val1000.source', 'w', encoding='utf8') as f:
    f.write(''.join(unzipped[0]))

with open('../data/split_data/huggingface_bart/val1000.target', 'w', encoding='utf8') as f:
    f.write(''.join(unzipped[1]))

with open('../data/split_data/huggingface_bart/val1000.target.tok', 'w', encoding='utf8') as f:
    f.write(''.join(unzipped[2]))

with open('../data/split_data/huggingface_t5/val1000.source', 'w', encoding='utf8') as f:
    f.write(''.join(unzipped[3]))

with open('../data/split_data/huggingface_t5/val1000.target', 'w', encoding='utf8') as f:
    f.write(''.join(unzipped[4]))

with open('../data/split_data/huggingface_t5/val1000.target.tok', 'w', encoding='utf8') as f:
    f.write(''.join(unzipped[5]))



