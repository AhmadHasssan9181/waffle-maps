"""Fill `name:ur` in PMTiles by transliterating Latin names (offline dictionary).

Usage:
  python scripts/urdu_patch.py --src data/pakistan_vector.pmtiles \
      --dst data/pakistan_vector_ur.pmtiles --max-zoom 7 --workers 8
"""
import argparse
import gzip
import json
import os
import re
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import mapbox_vector_tile as mvt
from pmtiles.reader import Reader, MmapSource, all_tiles
from pmtiles.tile import zxy_to_tileid
from pmtiles.writer import Writer

OUT = r'G:\sketcyshitx2\data\urdu'
TOKEN = re.compile(r"[A-Za-z][A-Za-z'\-]*")
LATIN = re.compile(r'[A-Za-z]')
URDU = re.compile('[\u0600-\u06FF]')

DEFAULT_LAYERS = [
    'place', 'transportation_name', 'water_name', 'waterway',
    'park', 'aerodrome_label', 'mountain_peak', 'poi',
]

RULES = [
    ('kh', 'خ'), ('gh', 'غ'), ('ch', 'چ'), ('sh', 'ش'), ('th', 'تھ'), ('ph', 'ف'),
    ('bh', 'بھ'), ('dh', 'دھ'), ('jh', 'جھ'), ('rh', 'ڑھ'), ('lh', 'لھ'),
    ('aa', 'ا'), ('ee', 'ی'), ('ii', 'ی'), ('oo', 'و'), ('uu', 'و'), ('ai', 'ے'),
    ('au', 'و'), ('ay', 'ے'), ('ey', 'ے'), ('oa', 'و'), ('ck', 'ک'), ('qu', 'ق'),
    ('x', 'کس'), ('a', 'ا'), ('b', 'ب'), ('c', 'ک'), ('d', 'د'), ('e', 'ے'),
    ('f', 'ف'), ('g', 'گ'), ('h', 'ہ'), ('i', 'ی'), ('j', 'ج'), ('k', 'ک'),
    ('l', 'ل'), ('m', 'م'), ('n', 'ن'), ('o', 'و'), ('p', 'پ'), ('q', 'ق'),
    ('r', 'ر'), ('s', 'س'), ('t', 'ت'), ('u', 'و'), ('v', 'و'), ('w', 'و'),
    ('y', 'ی'), ('z', 'ز'),
]
RULES.sort(key=lambda kv: -len(kv[0]))

_W = {}
_TARGET = set()


def _init(d, layers):
    global _W, _TARGET
    _W = d
    _TARGET = set(layers)


def rule_xlit(word):
    out, i = [], 0
    while i < len(word):
        for src, dst in RULES:
            if word.startswith(src, i):
                out.append(dst)
                i += len(src)
                break
        else:
            out.append(word[i])
            i += 1
    return ''.join(out)


def xlit(name):
    # Already contains Urdu/Arabic script: keep it as-is instead of duplicating.
    if URDU.search(name):
        return name.strip()
    out = []
    last = 0
    for m in TOKEN.finditer(name):
        out.append(name[last:m.start()])
        key = m.group(0).lower().strip("'-")
        out.append(_W.get(key) or rule_xlit(key))
        last = m.end()
    out.append(name[last:])
    return ''.join(out).strip()


def _work(item):
    z, x, y, data = item
    if not data:
        return z, x, y, data
    try:
        raw = gzip.decompress(data) if data[:2] == b'\x1f\x8b' else data
    except Exception:
        return z, x, y, data
    try:
        layers = mvt.decode(raw)
    except Exception:
        return z, x, y, data

    changed = False
    for lname, layer in layers.items():
        if lname not in _TARGET:
            continue
        for ft in layer.get('features', []):
            p = ft.get('properties') or {}
            name = p.get('name')
            if not name or p.get('name:ur'):
                continue
            ur = xlit(name) if LATIN.search(name) else name
            if ur:
                p['name:ur'] = ur
                ft['properties'] = p
                changed = True
    if not changed:
        return z, x, y, data
    try:
        enc = mvt.encode([
            {'name': lname, 'features': layer.get('features', [])}
            for lname, layer in layers.items()
        ])
    except Exception:
        return z, x, y, data
    return z, x, y, gzip.compress(enc, mtime=0)


def patch(src, dst, layers, workers, max_zoom, chunk_size):
    dic = None
    for _ in range(20):
        try:
            dic = json.load(open(os.path.join(OUT, 'dict.json'), encoding='utf-8'))
            break
        except Exception:
            time.sleep(0.5)
    if dic is None:
        raise SystemExit('could not read dict.json (still being written?)')
    print('dict words:', len(dic), flush=True)
    with open(src, 'rb') as f:
        r = Reader(MmapSource(f))
        header = r.header()
        metadata = r.metadata()
        for vl in metadata.get('vector_layers', []):
            if vl.get('id') in layers:
                vl.setdefault('fields', {})['name:ur'] = 'String'
        from pmtiles.tile import Compression
        header['tile_compression'] = Compression.GZIP
        it = all_tiles(r.get_bytes)
        if max_zoom is not None:
            it = ((z, x, y, d) for (z, x, y), d in it if z <= max_zoom)
        else:
            it = ((z, x, y, d) for (z, x, y), d in it)

    t0 = time.time()
    n = 0
    with open(dst, 'wb') as out, ProcessPoolExecutor(
            max_workers=workers, initializer=_init, initargs=(dic, layers)) as ex:
        w = Writer(out)
        buf = []

        def flush(buf):
            nonlocal n
            for z, x, y, data in ex.map(_work, buf, chunksize=16):
                w.write_tile(zxy_to_tileid(z, x, y), data)
                n += 1
            if n and n % 5000 < len(buf):
                print(f'  {n} tiles  {time.time()-t0:.0f}s', flush=True)

        for item in it:
            buf.append(item)
            if len(buf) >= chunk_size:
                flush(buf)
                buf = []
        if buf:
            flush(buf)
        w.finalize(header, metadata)
    print(f'wrote {dst}  tiles={n}  {time.time()-t0:.0f}s  '
          f'MB={os.path.getsize(dst)/1e6:.1f}', flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', required=True)
    ap.add_argument('--dst', required=True)
    ap.add_argument('--layers', default=','.join(DEFAULT_LAYERS))
    ap.add_argument('--workers', type=int, default=8)
    ap.add_argument('--max-zoom', type=int, default=None)
    ap.add_argument('--chunk', type=int, default=2000)
    a = ap.parse_args()
    patch(a.src, a.dst, a.layers.split(','), a.workers, a.max_zoom, a.chunk)


if __name__ == '__main__':
    main()
