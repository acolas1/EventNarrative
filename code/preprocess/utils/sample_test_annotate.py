import os
import json
import random

data_list = []
with open('../data/split_data/train.json', 'r', encoding='utf-8') as files:
    for line in files:
        event = json.loads(line.strip('\n'))
        data_list.append(event)
annotate_samples = random.sample(data_list, 500)

# with open('../data/split_data/annotate_test_sample.json', 'w', encoding='utf-8') as files:
#      files.write(json.dumps((annotate_samples)))


# with open('../data/split_data/test.json', 'r', encoding='utf-8') as file_:
#      events = json.load(file_)
# print(len(annotate_samples))
# events1 = annotate_samples[:len(annotate_samples)//2]
# print(len(events1))
# events2 = annotate_samples[len(annotate_samples)//2:]
# print(len(events2))

with open('../data/check.json', 'w', encoding='utf-8') as files:
     files.write(json.dumps((annotate_samples)))
# with open('../data/split_data/jabir_annotate_test_sample.json', 'w', encoding='utf-8') as files:
#      files.write(json.dumps((events2)))
