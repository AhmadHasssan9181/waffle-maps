import json, os, re, time, urllib.request

PREFIX = "release/2026-10-21.0/theme=places/type/place/"
url = f"https://overturemaps-us-west-2.s3.amazonaws.com/?list-type=2&prefix={PREFIX}"
out = r"G:\sketcyshitx2\data\overture\places_files.json"
os.makedirs(os.path.dirname(out), exist_ok=True)

for i in range(10):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        xml = urllib.request.urlopen(req, timeout=40).read().decode()
        keys = re.findall(r"<Key>(.*?)</Key>", xml)
        print(f"attempt {i}: {len(keys)} keys")
        if keys:
            json.dump(keys, open(out, "w"))
            print("saved ->", out)
            break
    except Exception as e:
        print(f"attempt {i}: ERR {str(e)[:120]}")
    time.sleep(3 * (i + 1))
else:
    print("FAILED to list")
