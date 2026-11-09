"""Build an offline Latin->Urdu transliteration dictionary for map labels.

Uses Google Input Tools at build time (cached), with a curated override table and
a deterministic rule-based fallback for long-tail words. The output dict is bundled
into the tile patch step; no network is needed at runtime.
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

OUT = r'G:\sketcyshitx2\data\urdu'
DICT_PATH = os.path.join(OUT, 'dict.json')
TOKEN = re.compile(r"[A-Za-z][A-Za-z'\-]*")

MANUAL = {
    'road': 'روڈ', 'street': 'سٹریٹ', 'avenue': 'ایونیو', 'boulevard': 'بلیوارڈ',
    'highway': 'ہائی وے', 'bypass': 'بائی پاس', 'service': 'سروس', 'link': 'لنک',
    'main': 'مین', 'minor': 'مائنر', 'provincial': 'صوبائی', 'canal': 'نہر',
    'distributary': 'ڈسٹری بیوٹری', 'river': 'دریا', 'colony': 'کالونی',
    'town': 'ٹاؤن', 'society': 'سوسائٹی', 'chowk': 'چوک', 'bazaar': 'بازار',
    'masjid': 'مسجد', 'mosque': 'مسجد', 'hospital': 'ہسپتال', 'school': 'سکول',
    'college': 'کالج', 'university': 'یونیورسٹی', 'bank': 'بینک', 'hotel': 'ہوٹل',
    'market': 'مارکیٹ', 'park': 'پارک', 'garden': 'گارڈن', 'station': 'اسٹیشن',
    'block': 'بلاک', 'sector': 'سیکٹر', 'phase': 'فیز', 'lane': 'لین',
    'centre': 'سینٹر', 'center': 'سینٹر', 'clinic': 'کلینک', 'pharmacy': 'فارمیسی',
    'police': 'پولیس', 'airport': 'ایئرپورٹ', 'railway': 'ریلوے', 'bridge': 'پل',
    'flyover': 'فلائی اوور', 'underpass': 'انڈر پاس', 'square': 'اسکوائر',
    'plaza': 'پلازہ', 'tower': 'ٹاور', 'complex': 'کمپلیکس', 'house': 'ہاؤس',
    'village': 'گاؤں', 'city': 'شہر', 'district': 'ضلع', 'tehsil': 'تحصیل',
    'union': 'یونین', 'council': 'کونسل', 'committee': 'کمیٹی', 'office': 'دفتر',
    'court': 'عدالت', 'prison': 'جیل', 'fire': 'فائر', 'post': 'پوسٹ',
    'telephone': 'ٹیلی فون', 'electric': 'الیکٹرک', 'water': 'واٹر', 'works': 'ورکس',
    'mill': 'مل', 'factory': 'فیکٹری', 'industrial': 'صنعتی', 'estate': 'اسٹیٹ',
    'housing': 'ہاؤسنگ', 'scheme': 'سکیم', 'authority': 'اتھارٹی', 'board': 'بورڈ',
    'department': 'محکمہ', 'government': 'حکومت', 'national': 'قومی', 'public': 'پبلک',
    'general': 'جنرل', 'military': 'ملٹری', 'cantonment': 'چھاؤنی', 'camp': 'کیمپ',
    'fort': 'قلعہ', 'tomb': 'مقبرہ', 'shrine': 'مزار', 'church': 'چرچ',
    'temple': 'مندرج', 'gurdwara': 'گردوارہ', 'academy': 'اکیڈمی',
    'institute': 'انسٹیٹیوٹ', 'library': 'لائبریری', 'museum': 'میوزیم',
    'stadium': 'اسٹیڈیم', 'ground': 'گراؤنڈ', 'playground': 'پلے گراؤنڈ',
    'nagar': 'نگر', 'abad': 'آباد', 'pur': 'پور', 'wala': 'والا', 'wali': 'والی',
    'kot': 'کوٹ', 'goth': 'گاؤٹھ', 'basti': 'بستی', 'dhoke': 'ڈھوک', 'dera': 'ڈیرہ',
    'khel': 'خیل', 'kalay': 'کلے', 'nala': 'نالہ', 'nullah': 'نالہ', 'pir': 'پیر',
    'haji': 'حاجی', 'shaheed': 'شہید', 'muhammad': 'محمد', 'mohammad': 'محمد',
    'khan': 'خان', 'shah': 'شاہ', 'ali': 'علی', 'faisal': 'فیصل', 'iqbal': 'اقبال',
    'jinnah': 'جناح', 'quaid': 'قائد', 'liaquat': 'لیاقت', 'bhutto': 'بھٹو',
    'road': 'روڈ', 'street': 'سٹریٹ', 'sector': 'سیکٹر', 'block': 'بلاک',
    'rd': 'روڈ', 'st': 'سٹریٹ', 'ave': 'ایونیو', 'blvd': 'بلیوارڈ', 'hwy': 'ہائی وے',
    'sq': 'اسکوائر', 'ctr': 'سینٹر', 'univ': 'یونیورسٹی', 'govt': 'حکومتی',
    'north': 'شمال', 'south': 'جنوب', 'east': 'مشرق', 'west': 'مغرب',
    'upper': 'بالائی', 'lower': 'زیریں', 'central': 'مرکزی', 'model': 'ماڈل',
    'extension': 'ایکسٹینشن', 'pull': 'پل', 'pul': 'پل', 'mor': 'موڑ', 'morh': 'موڑ',
    'near': 'قریب', 'old': 'پرانا', 'new': 'نیا', 'no': 'نمبر',
}

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


def has_latin(s):
    return any('a' <= c.lower() <= 'z' for c in s)


def google(word, timeout=15):
    url = ('https://inputtools.google.com/request?text=' +
           urllib.parse.quote(word) + '&itc=ur-t-i0-und&num=1')
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = json.loads(r.read().decode('utf-8'))
            if data and data[0] == 'SUCCESS':
                cands = data[1][0][1]
                if cands:
                    cand = cands[0]
                    if not has_latin(cand):
                        return cand
            return None
        except Exception:
            time.sleep(0.8 * (attempt + 1))
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--osm', type=int, default=15600)
    ap.add_argument('--poi', type=int, default=5000)
    ap.add_argument('--workers', type=int, default=6)
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--save-every', type=int, default=100)
    args = ap.parse_args()

    words = []
    seen = set()
    for fname, n in (('osm_words.json', args.osm), ('poi_words.json', args.poi)):
        rows = json.load(open(os.path.join(OUT, fname), encoding='utf-8'))
        for w, _ in rows[:n]:
            if w not in seen:
                seen.add(w)
                words.append(w)
    if args.limit:
        words = words[:args.limit]

    d = {}
    if os.path.exists(DICT_PATH):
        d = json.load(open(DICT_PATH, encoding='utf-8'))
    for w in words:
        if w in MANUAL:
            d[w] = MANUAL[w]
    todo = [w for w in words if w not in d and w not in MANUAL]
    print(f'words={len(words)} cached={len(words)-len(todo)} todo={len(todo)}', flush=True)

    t0 = time.time()
    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(google, w): w for w in todo}
        for fut in as_completed(futs):
            w = futs[fut]
            try:
                r = fut.result()
            except Exception:
                r = None
            if r:
                d[w] = r
            done += 1
            if done % args.save_every == 0:
                json.dump(d, open(DICT_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
                rate = done / max(time.time() - t0, 0.01)
                print(f'{done}/{len(todo)}  {rate:.1f}/s  dict={len(d)}', flush=True)
    json.dump(d, open(DICT_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print(f'done: dict={len(d)}  elapsed={time.time()-t0:.0f}s', flush=True)


if __name__ == '__main__':
    main()
