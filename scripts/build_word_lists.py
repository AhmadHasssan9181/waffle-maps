import json
import os
import re
from collections import Counter

import duckdb
import osmium

OUT = r'G:\sketcyshitx2\data\urdu'
os.makedirs(OUT, exist_ok=True)
PBF = r'G:\sketcyshitx2\data\pakistan-latest.osm.pbf'
MAJOR = {'motorway', 'trunk', 'primary', 'secondary', 'tertiary'}
PLACE = {'city', 'town', 'village', 'suburb', 'neighbourhood', 'hamlet', 'quarter'}
TOKEN = re.compile(r"[A-Za-z][A-Za-z'\-]*")

osm_names = set()
osm_words = Counter()


class H(osmium.SimpleHandler):
    def _add(self, tags):
        if 'name' not in tags or 'name:ur' in tags:
            return
        n = tags['name'].strip()
        if not n:
            return
        osm_names.add(n)
        for w in TOKEN.findall(n.lower()):
            osm_words[w] += 1

    def way(self, w):
        if 'highway' in w.tags and w.tags['highway'] in MAJOR:
            self._add(w.tags)
        if 'waterway' in w.tags:
            self._add(w.tags)
        if 'natural' in w.tags and w.tags['natural'] == 'water':
            self._add(w.tags)

    def node(self, n):
        if 'place' in n.tags and n.tags['place'] in PLACE:
            self._add(n.tags)


H().apply_file(PBF)
print('osm names', len(osm_names), 'words', len(osm_words), flush=True)

con = duckdb.connect(r'G:\sketcyshitx2\data\overture\overture.duckdb', read_only=True)
poi_names = []
poi_words = Counter()
for (n,) in con.execute('SELECT name FROM places').fetchall():
    if not n:
        continue
    n = n.strip()
    if not n:
        continue
    poi_names.append(n)
    for w in TOKEN.findall(n.lower()):
        poi_words[w] += 1
print('poi names', len(poi_names), 'words', len(poi_words), flush=True)

json.dump(sorted(osm_names), open(os.path.join(OUT, 'osm_names.json'), 'w', encoding='utf-8'),
          ensure_ascii=False)
json.dump(osm_words.most_common(), open(os.path.join(OUT, 'osm_words.json'), 'w', encoding='utf-8'),
          ensure_ascii=False)
json.dump(poi_names, open(os.path.join(OUT, 'poi_names.json'), 'w', encoding='utf-8'),
          ensure_ascii=False)
json.dump(poi_words.most_common(), open(os.path.join(OUT, 'poi_words.json'), 'w', encoding='utf-8'),
          ensure_ascii=False)


def coverage(counter, label):
    total = sum(counter.values())
    print(label, 'total tokens', total)
    for n in (1000, 3000, 5000, 10000, 15000, 20000):
        s = sum(c for _, c in counter.most_common(n))
        print(f'  top {n:6d}: {100.0*s/total:5.1f}%')


coverage(osm_words, 'OSM')
coverage(poi_words, 'POI')
