"""Add `name_ur` to the FTS5 search DB and index both scripts."""
import json
import os
import re
import sqlite3
import time

OUT = r'G:\sketcyshitx2\data\urdu'
DB = r'G:\sketcyshitx2\data\places_search.db'
TOKEN = re.compile(r"[A-Za-z][A-Za-z'\-]*")
LATIN = re.compile(r'[A-Za-z]')
URDU = re.compile('[\u0600-\u06FF]')

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
W = json.load(open(os.path.join(OUT, 'dict.json'), encoding='utf-8'))


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
    if not name:
        return name
    name = name.replace('\ufffd', "'")
    if URDU.search(name) or not LATIN.search(name):
        return name
    out, last = [], 0
    for m in TOKEN.finditer(name):
        out.append(name[last:m.start()])
        key = m.group(0).lower().strip("'-")
        out.append(W.get(key) or rule_xlit(key))
        last = m.end()
    out.append(name[last:])
    return ''.join(out).strip()


def main():
    t = time.time()
    con = sqlite3.connect(DB)
    con.execute('PRAGMA journal_mode=OFF')
    con.execute('PRAGMA synchronous=OFF')
    cols = [r[1] for r in con.execute('PRAGMA table_info(places)')]
    if 'name_ur' not in cols:
        con.execute('ALTER TABLE places ADD COLUMN name_ur TEXT')
    rows = con.execute('SELECT id, name FROM places').fetchall()
    print('rows', len(rows), flush=True)
    upd = []
    for i, name in rows:
        ur = xlit(name)
        upd.append((ur or name, i))
    con.executemany('UPDATE places SET name_ur = ? WHERE id = ?', upd)
    con.commit()
    print('updated', len(upd), f'{time.time()-t:.0f}s', flush=True)

    con.execute('DROP TABLE IF EXISTS places_fts')
    con.execute("""CREATE VIRTUAL TABLE places_fts USING fts5(
                     name, name_ur, content='places', content_rowid='id',
                     tokenize='unicode61 remove_diacritics 2')""")
    con.execute("INSERT INTO places_fts(places_fts) VALUES('rebuild')")
    con.commit()
    print('fts rebuilt', f'{time.time()-t:.0f}s', flush=True)
    con.execute('VACUUM')
    con.close()
    print('MB', round(os.path.getsize(DB) / 1e6, 1), flush=True)


if __name__ == '__main__':
    main()
