import os
import json
import random

####training data
train_sources = open('../data/split_final_data/huggingface/invest/train.source', 'r', encoding='utf-8').readlines()

train_targets = open('../data/split_final_data/huggingface/invest/train.target', 'r', encoding='utf-8').readlines()
zipped = list(zip(train_sources,train_targets))
unzipped = list(zip(*zipped))
print(len(unzipped))

for graph, text in zipped:
    graph = graph.rstrip('\n')
    text = text.rstrip('\n')

    graph = 'translate from Graph to Text: ' + graph 
    graph = graph.rstrip()
    print(graph)
    print(text)
    print(daadfadf)
    with open('../data/split_final_data/huggingface/invest/t5_lower/train.source', 'w', encoding='utf8') as f:
        f.write(''.join(unzipped[0]))
    with open('../data/split_final_data/huggingface/invest/t5/train.target', 'w', encoding='utf8') as f:
        f.write(''.join(unzipped[1]))

 
# with open('../data/split_final_data/huggingface/invest/t5_lower/train.source', 'w', encoding='utf8') as f:
#     f.write(''.join(unzipped[0]))

# with open('../data/split_final_data/huggingface/invest/t5/train.target', 'w', encoding='utf8') as f:
#     f.write(''.join(unzipped[1]))


####val data
# train_sources = open('../data/split_final_data/huggingface/invest/t5/val.source', 'r', encoding='utf-8').readlines()

# train_targets = open('../data/split_final_data/huggingface/invest/t5/val.target', 'r', encoding='utf-8').readlines()
# zipped = list(zip(train_sources,train_targets))
# unzipped = list(zip(*zipped))
# print(len(unzipped))

# with open('../data/split_final_data/huggingface/invest/t5/val1000.source', 'w', encoding='utf8') as f:
#     f.write(''.join(unzipped[0]))

# with open('../data/split_final_data/huggingface/invest/t5/val1000.target', 'w', encoding='utf8') as f:
#     f.write(''.join(unzipped[1]))

# ####val sample data
# train_sources = open('../data/split_final_data/huggingface/invest/t5/val.source', 'r', encoding='utf-8').readlines()

# train_targets = open('../data/split_final_data/huggingface/invest/t5/val.target', 'r', encoding='utf-8').readlines()
# zipped = list(zip(train_sources,train_targets))
# unzipped = list(zip(*zipped))
# print(len(unzipped))

# with open('../data/split_final_data/huggingface/invest/t5/val1000.source', 'w', encoding='utf8') as f:
#     f.write(''.join(unzipped[0]))

# with open('../data/split_final_data/huggingface/invest/t5/val1000.target', 'w', encoding='utf8') as f:
#     f.write(''.join(unzipped[1]))


# ####test data
# train_sources = open('../data/split_final_data/huggingface/invest/t5/val.source', 'r', encoding='utf-8').readlines()

# train_targets = open('../data/split_final_data/huggingface/invest/t5/val.target', 'r', encoding='utf-8').readlines()
# zipped = list(zip(train_sources,train_targets))
# unzipped = list(zip(*zipped))
# print(len(unzipped))

# with open('../data/split_final_data/huggingface/invest/t5/val1000.source', 'w', encoding='utf8') as f:
#     f.write(''.join(unzipped[0]))

# with open('../data/split_final_data/huggingface/invest/t5/val1000.target', 'w', encoding='utf8') as f:
#     f.write(''.join(unzipped[1]))

