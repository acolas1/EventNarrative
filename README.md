# EventNarrative: A large-scale Event-centric Dataset for Knowledge Graph-to-Text Generation

**Abstract**: We introduce EventNarrative, a knowledge graph-to-text dataset from publicly available open-world knowledge graphs. Given the recent advances in event-driven Information Extraction (IE), and that prior research on graph-to-text only focused on entity-driven KGs, this paper focuses on event-centric data. However, our data generation system can still be adapted to other other types of KG data. Existing large-scale datasets in the graph-to-text area are non-parallel, meaning there is a large disconnect between the KGs and text. The datasets that have a paired KG and text, are small scale and manually generated or generated without a rich ontology, making the corresponding graphs sparse. Furthermore, these datasets contain many unlinked entities between their KG and text pairs. EventNarrative consists of approximately 230,000 graphs and their corresponding natural language text, 6 times larger than the current largest parallel dataset. It makes use of a rich ontology, all of the KGs entities are linked to the text, and our manual annotations confirm a high data quality. Our aim is two-fold: help break new ground in event-centric research where data is lacking, and to give researchers a well-defined, large-scale dataset in order to better evaluate existing and future knowledge graph-to-text models. We also evaluate two types of baseline on EventNarrative: a graph-to-text specific model and two state-of-the-art language models, which previous work has shown to be adaptable to the knowledge graph-to-text domain. 

Anthony Colas, Ali Sadeghian, Yue Wang, Daisy Wang<br>
University of Florida <br>

## Dataset Link
https://www.kaggle.com/datasets/acolas1/eventnarration

## Paper
Accepted at the *Thirty-fifth Conference on Neural Information Processing Systems Datasets and Benchmarks Track (Round 1). 2021.*<br>
Paper can be found [here](https://openreview.net/pdf?id=3ZQqjt_Q6b).

Please cite:
```
@inproceedings{colas2021eventnarrative,
  title={EventNarrative: A Large-scale Event-centric Dataset for Knowledge Graph-to-Text Generation},
  author={Colas, Anthony and Sadeghian, Ali and Wang, Yue and Wang, Daisy Zhe},
  booktitle={Thirty-fifth Conference on Neural Information Processing Systems Datasets and Benchmarks Track (Round 1)},
  year={2021}
}
```

## Getting Started
We describe here how to pre-process the data. We start by first having a copy of events in EventKG that have a Wikidata and Wikipedia source and Wikidata triples for those events. For further information on EventKG please see the links below.

To train the baseline models please see "Preprocessing for Models".

### Data Sources
[EventKG](http://eventkg.l3s.uni-hannover.de/),
[WikiData](https://www.wikidata.org/wiki/Wikidata:Database_download),
[Wikipedia Local](https://github.com/ipfs/distributed-wikipedia-mirror)<br>
We use wikipedia_en_all_nopic_2021-01.zim and the [WikiMapper](https://github.com/jcklie/wikimapper)

### Initial data files
eventkg_wikidata_augmented_events_with_types.json, triples.json can be found [here](https://drive.google.com/file/d/1jNiZqIsvD0vXY001zkH5SoqTR2kc-1cq/view?usp=sharing).
- move files to data folder
```bash
mv <file> preprocess/data/
```

### Data Preprocessing
- cd into preprocess/
- merge the eventkg and wikidata events 
```bash
python eventKG_preprocess.py
```

- get the full text of wikipedia
```bash
python modify_full_TEXT.py -input <input_path> -output_dir <output_dir>
```
Note: We use the wikipedia_en_all_nopic_2021-01 version of Wikipedia and host it on localhost:8080. Please change accordingly.

- get entities which match KGs and text (normalization)
```bash
python normalize_triples_text.py -input <input_dir> -output_dir <output_file>
```
Note: change line 30 and 32 accordingly as this was the path to our WikiMapper DBs. For more information on setting up WikiMappper please see the WikiMapper link above.

- postprocess KGs/text: replace entities in text with entities in KG and match KG to text
```bash
python postprocess.py
```
Note: We place the data from the last step into data/full_entities_in_text/. Change the path to the data if need on line 176.

**The workload for pre-processing fetching the data was distributed through multiple machines.**

### Preprocessing for Models
We provide the training/val/teting data split [here](https://www.kaggle.com/datasets/acolas1/eventnarration).

- insert data into data/split_data/

#### GraphWriter 
- preprocess graphwriter data
```bash
mkdir data/split_data/graphwriter/
```
```bash
python preprocess_baselines/graphwriter.py
```

#### BART/T5
- preprocess BART and T5 data
```bash
mkdir data/split_data/huggingface_bart/
mkdir data/split_data/huggingface_t5/
```
```bash
python preprocess_baselines/invest_huggingface.py
cp data/split_data/huggingface_t5/dev.source
```
### Training and Evaluation
- GraphWriter<br>
We use the version of GraphWriter found [here](https://github.com/QipengGuo/CycleGT). Please see their requirements.txt file.
- BART/T5<br>
We train BART/T5 following the repo [here](https://github.com/UKPLab/plms-graph2text). Please see their requirements.txt file.

train a model on GraphWriter:
```bash
cd models/CycleGT/
```
Make sure to have dev.json, train.json, and test.json
```bash
python main.py
```

Move to folder for BART/T5:
```bash
cd models/plms-graph2text/
```
- move all BART data to models/plms-graph2text/event/data/huggingface_bart/
```bash
./finetune_EVENT_bart.sh facebook/bart-base <gpu_id>
```

Train a model on T5:
-  move all T5 data to plms-graph2text/event/data/huggingface_t5/
```bash
./finetune_EVENT_t5.sh t5-base <gpu_id>
```

- All outputs can be found in the plms-graph2text/outputs/ folder, for their respective model. 
- Test results are found in val_outputs, with the last epoch contained in the file name (10 in our case). Please use the '.tok' file.


### Metrics
- Although the models above evaluate the test set, we decided to evaluate each test set ourselves using the same uniform libraries for every model.
- Use tokenized files for evaluating metrics.
We used [pycocoevalcap](https://github.com/salaniz/pycocoevalcap) for ROUGE, CIDER, and METEOR.
We used Hugginface datasets for [BLEUscore](https://github.com/huggingface/datasets).
We used the [chrF++](https://github.com/m-popovic/chrF) package for chrf++.

## Acknowledgments
- [WikiMapper library]((https://github.com/m-popovic/chrF)) for efficient Wikidata QID to Wikipedia ID matching.<br>
- Our GraphWriter code is borrowed from [CycleGT](https://github.com/QipengGuo/CycleGT).<br>
- Our BART/T5 code on KG to text is borrowed from the [UKPLab](https://github.com/UKPLab/plms-graph2text).<br>
- Metrics were caluclated with [pycocoevalcap](https://github.com/salaniz/pycocoevalcap), [BLEUscore](https://github.com/huggingface/datasets), and [chrF++](https://github.com/m-popovic/chrF).

We thank all the authors for their useful code.
