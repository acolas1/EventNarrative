import random
import json
import os

path = "../data/full_normalized/"
filelist = os.listdir(path)
data_list = []

def split_data(data):
    len_data = len(data)
    len_test_val = int(len_data*.1)
    random.shuffle(data)

    val = data[:len_test_val]
    test = data[len_test_val:len_test_val*2]
    train = data[len_test_val*2:]

    print("train_size: ", len(train))
    print("val_size: ", len(val))
    print("test_size: ", len(test))
    return train, val, test


for file_ in filelist:
    with open(path+file_, 'r', encoding='utf-8') as files:
        for line in files:
            event = json.loads(line.strip('\n'))
            data_list.append(event)
print(len(data_list))
train, val, test = split_data(data_list)

for event in train:
    with open('../data/split_data/train.json', "a", encoding='utf-8') as data1:
        data1.write(json.dumps(event, ensure_ascii=False))
        data1.write("\n")

for event in val:
    with open('../data/split_data/val.json', "a", encoding='utf-8') as data1:
        data1.write(json.dumps(event, ensure_ascii=False))
        data1.write("\n")

for event in test:
    with open('../data/split_data/test.json', "a", encoding='utf-8') as data1:
        data1.write(json.dumps(event, ensure_ascii=False))
        data1.write("\n")