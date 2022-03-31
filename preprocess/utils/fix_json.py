import os
import sys
import json

def fix_json(path_dataset):
    parts = ['train', 'dev', 'test']

    for part in parts:
        data_list = []
        file_ = path_dataset + part + '.json'
        with open(file_, 'r', encoding='utf-8') as files:
            for line in files:
                event = json.loads(line.strip('\n'))
                data_list.append(event)
        with open(path_dataset+part+'_data'+'.json', 'w') as fout:
            json.dump(data_list , fout)


def main(path_dataset):

    fix_json(path_dataset)

if __name__ == "__main__":
    main(sys.argv[1])