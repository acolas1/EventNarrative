from itertools import islice

def chunks(data, SIZE=10000):
    it = iter(data)
    for i in xrange(0, len(data), SIZE):
        yield {k:data[k] for k in islice(it, SIZE)}

with open('data/wikidata_properties.json') as f:
  wikidata_props = json.load(f)

# with open('data/all_event_triples_0.json') as f:
#   all_event_triples = json.load(f)


wikidata_props_not_processed = dict()

for i in wikidata_props:
    wikidata_props_not_processed[i] = wikidata_props[i]
i = 1
for item in chunks({i:i for i in wikidata_props_not_processed}, 6):
    output = 'data/all_event_triples_'+str(i)+'.json'
    with open(output, "w", encoding='utf-8') as data1:
        data1.write(json.dumps(item,ensure_ascii=False, indent=4))
        data1.write("\n")