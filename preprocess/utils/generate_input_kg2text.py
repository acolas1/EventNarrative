"""
Leonardo Ribeiro
ribeiro@aiphes.tu-darmstadt.de
"""
from collections import Counter
import sys
import getopt
import json
import os
from collections import Counter

if sys.version_info[0] < 3:
    raise Exception("Python 3 or a more recent version is required.")

def split_data(d,relations_num_dict):
    d_ = []
    d_.append(d[0])
    d_.append(d[2])
    
    relation = d[1]
    relation_num = relations_num_dict[relation]
    relation_inv = d[1]+'-inv'
    relation_num_inv = relations_num_dict[relation]+len(relations_num_dict)
    return d_, (relation,relation_num,relation_inv,relation_num_inv)
    # d_ = d.split('-- CONJUNCTION --')
    # if len(d_) == 2:
    #     return d_, ('CONJUNCTION', 1)

    # d_ = d.split('-- USED-FOR --')
    # if len(d_) == 2:
    #     return d_, ('USED-FOR', 2, 'USED-FOR-inv', 3)

    # d_ = d.split('-- COMPARE --')
    # if len(d_) == 2:
    #     return d_, ('COMPARE', 4)

    # d_ = d.split('-- EVALUATE-FOR --')
    # if len(d_) == 2:
    #     return d_, ('EVALUATE-FOR', 5, 'EVALUATE-FOR-inv', 6)

    # d_ = d.split('-- HYPONYM-OF --')
    # if len(d_) == 2:
    #     return d_, ('HYPONYM-OF', 7, 'HYPONYM-OF-inv', 8)

    # d_ = d.split('-- FEATURE-OF --')
    # if len(d_) == 2:
    #     return d_, ('FEATURE-OF', 9, 'FEATURE-OF-inv', 10)

    # d_ = d.split('-- PART-OF --')
    # if len(d_) == 2:
    #     return d_, ('PART-OF', 11, 'PART-OF-inv', 12)

    # print('error')
    # exit()

def fill_text(text, entity_ref_dict):
    filled_text = text
    for ref in entity_ref_dict:
        filled_text = filled_text.replace(ref, entity_ref_dict[ref])
    return filled_text

def process_data(relations,relations_num_dict):
    edges = []
    for r in relations:
        n, rel = split_data(r,relations_num_dict)
        edges.append([n, rel])
    return edges


def read_dataset(file_, part,relations_num_dict_curr):
    print(file_)
    with open(file_, 'r', encoding="utf-8") as dataset_file:
        data = json.load(dataset_file)

    all_instances = []
    number_nodes = []
    for idx, point in enumerate(data):

        map = {}

        src = []
        # title = point['title'].lower().strip().split()

        # src.append('<title>')
        # for t in title:
        #     src.append(t)
        # src.append('</title>')
        filled_text = fill_text(point['narration'],point['entity_ref_dict'])

        surfaces = filled_text.lower().strip().split()
        entities = list(point['entity_ref_dict'].values())
        triples = point['keep_triples']
        for triple in triples:
            relation = triple[1]
            if relation not in relations_num_dict_curr:
                relations_num_dict_curr[relation] = len(relations_num_dict_curr)+1
        for idx_e, e in enumerate(entities):
            map[e] = []
            src.append('<entity>')
            for ee in e.lower().strip().split():
                src.append(ee)
                map[e].append([len(src) - 1, ee])
            src.append('</entity>')

        number_nodes.append(len(map))

        all_instances.append((src, surfaces))
        
    print("Number of nodes")
    c = Counter(number_nodes)
    print(c)
    print("Number of relations")
    print(len(relations_num_dict_curr))


    print('Total of {} instances processed in {} dataset'.format(len(data), part))
    return all_instances, relations_num_dict_curr


def read_dataset_bpe(file_, path, part, relations_num_dict):
    print(file_)
    with open(file_, 'r', encoding="utf-8") as dataset_file:
        data = json.load(dataset_file)

    all_instances = []

    number_nodes = []
    number_relations = []

    file_src = open(path + '/' + str(part) + '-src-bpe.txt', 'r')
    file_tgt = open(path + '/' + str(part) + '-tgt-bpe.txt', 'r')

    ents = []

    for l in file_src.readlines():
        ent = l.split('</entity> <entity>')
        ee = []
        for e in ent:
            e = e.strip().replace('<entity>', '')
            e = e.strip().replace('</entity>', '')
            ee.append(e.strip().split())
        ents.append(ee)

    abstrs = []
    for l in file_tgt.readlines():
        l = l.strip().split()
        abstrs.append(l)

    print(len(ents), len(abstrs), len(data))
    assert len(ents) == len(abstrs) == len(data)

    for idx, point in enumerate(data):

        map = {}

        edges1 = []
        edges2 = []
        label_edges = []
        label_edges_num = []

        src = []

        surfaces = abstrs[idx]
        entities = list(point['entity_ref_dict'].values())
        assert len(ents[idx]) == len(entities)

        for idx_e, e in enumerate(entities):
            e = e.strip()
            map[e] = []
            for ee in ents[idx][idx_e]:
                src.append(ee)
                map[e].append([len(src) - 1, ee])

        number_nodes.append(len(map))

        edges = process_data(point['keep_triples'],relations_num_dict)
        number_relations.append(len(edges))
        for e in edges:
            e1 = e[0][0].strip()
            e2 = e[0][1].strip()
            label = e[1]
            for r_e1 in map[e1]:
                for r_e2 in map[e2]:
                    edges2.append(r_e1[0])
                    edges1.append(r_e2[0])
                    label_edges.append(label[0])
                    label_edges_num.append(label[1])

                    if label[0] == 'CONJUNCTION' or label[0] == 'COMPARE':
                        edges2.append(r_e2[0])
                        edges1.append(r_e1[0])
                        label_edges.append(label[0])
                        label_edges_num.append(label[1])
                    else:
                        edges2.append(r_e2[0])
                        edges1.append(r_e1[0])
                        label_edges.append(label[2])
                        label_edges_num.append(label[3])

        assert len(edges1) == len(edges2) == len(label_edges) == len(label_edges_num)
        all_instances.append((src, edges1, edges2, label_edges, label_edges_num, surfaces))

    print("Number of nodes")
    c = Counter(number_nodes)
    print(c)

    print("Number of relations")
    c = Counter(number_relations)
    print(c)

    f = open(part + '-triples.txt', 'w')
    for d in number_relations:
        f.write(str(d)+'\n')
    f.close()

    print('Total of {} instances processed in {} dataset'.format(len(data), part))
    return all_instances


def create_files(data, part, path, bpe=None):

    sources = []
    surfaces = []
    graphs = []
    id_sample = []

    for _id, instance in enumerate(data):
        if bpe:
            src, edge1, edge2, label_edge, label_edge_num, surface = instance
            graph_line = ''
            edges_ = []
            for e2, e1, label_num, label in zip(edge2, edge1, label_edge_num, label_edge):
                graph_line += '(' + str(e2) + ',' + str(e1) + ',' + str(label_num) + ',' + label + ') '
                edges_.append((e2, e1, label_num))

            graphs.append(graph_line)
            id_sample.append(str(_id))
        else:
            src, surface = instance

        sources.append(' '.join(src))
        surfaces.append(' '.join(surface))

    if bpe:
        with open(path + '/' + part + '-nodes.txt', 'w', encoding='utf8') as f:
            f.write('\n'.join(sources))
        with open(path + '/' + part + '-surface.txt', 'w', encoding='utf8') as f:
            f.write('\n'.join(surfaces))
        with open(path + '/' + part + '-graph.txt', 'w', encoding='utf8') as f:
            f.write('\n'.join(graphs))
        with open(path + '/' + part + '-ids.txt', 'w', encoding='utf8') as f:
            f.write('\n'.join(id_sample))
    else:
        with open(path + '/' + part + '-src.txt', 'w', encoding='utf8') as f:
            f.write('\n'.join(sources))
        with open(path + '/' + part + '-tgt.txt', 'w', encoding='utf8') as f:
            f.write('\n'.join(surfaces))


def input_files(path_dataset, processed_data_folder):
    """
    Read the corpus, write train and dev files.
    :param path: directory with the AMR json files
    :return:
    """

    parts = ['training', 'dev', 'test']
    relations_num_dict = dict()
    for part in parts:
        file_ = path_dataset + part + '.json'
    
        print('Processing files...')
        data,relations_num_curr = read_dataset(file_, part,relations_num_dict)
        relations_num_dict.update(relations_num_curr)
        print('Done')
        print('Creating opennmt files...')
        create_files(data, part, processed_data_folder)
        print('Done')
    num_operations = 20000
    os.system('cat ' + processed_data_folder + '/training-src.txt ' + processed_data_folder + '/training-tgt.txt > ' +
              processed_data_folder + '/training_source.txt')
    print('creating bpe codes...')
    os.system('subword-nmt learn-bpe -s ' + str(num_operations) + ' < ' +
                    processed_data_folder + '/training_source.txt > ' + processed_data_folder + '/codes-bpe.txt')
    print('done')
    print('converting files to bpe...')
    for part in parts:
        print(part)
        file_pre = processed_data_folder + '/' + part + '-src.txt'
        file_ = processed_data_folder + '/' + part + '-src-bpe.txt'
        os.system('subword-nmt apply-bpe -c ' + processed_data_folder +
                  '/codes-bpe.txt < ' + file_pre + ' > ' + file_)

        file_pre = processed_data_folder + '/' + part + '-tgt.txt'
        file_ = processed_data_folder + '/' + part + '-tgt-bpe.txt'
        os.system('subword-nmt apply-bpe -c ' + processed_data_folder +
                  '/codes-bpe.txt < ' + file_pre + ' > ' + file_)

    print('done')

    for part in parts:
        file_ = path_dataset + part + '.json'

        print('Processing files bpe...')
        data = read_dataset_bpe(file_, processed_data_folder, part, relations_num_dict)
        print('Done')

        print('Creating opennmt bpe files...')
        create_files(data, part, processed_data_folder, bpe=True)
        print('Done')

    print('Files necessary for training/evaluating/test are written on disc.')


def main(path_dataset, processed_data_folder):

    input_files(path_dataset, processed_data_folder)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])