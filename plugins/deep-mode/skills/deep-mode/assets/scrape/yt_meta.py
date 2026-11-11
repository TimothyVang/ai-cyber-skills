"""Anonymous YouTube watch-page metadata scraper (title, date, views, likes, description, chapters).

Usage: python yt_meta.py IDS_JSON OUT_JSONL [--workers N]

IDS_JSON is a JSON list of video ids. OUT_JSONL is appended to and resumable: ids already
present without an "error" field are skipped, so rerun until the error count reaches zero.
Works while YouTube's player API is bot-walled, because the watch page still ships ytInitialData.
"""
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import requests

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"


def extract_json(html, var):
    m = re.search(r'(?:var |window\[")' + re.escape(var) + r'(?:"\])?\s*=\s*', html)
    if not m:
        return None
    return json.JSONDecoder().raw_decode(html, m.end())[0]


def text(x):
    if not x:
        return None
    if "simpleText" in x:
        return x["simpleText"]
    return "".join(r.get("text", "") for r in x.get("runs", []))


def walk(o, key):
    if isinstance(o, dict):
        for k, v in o.items():
            if k == key:
                yield v
            yield from walk(v, key)
    elif isinstance(o, list):
        for v in o:
            yield from walk(v, key)


def parse(vid, html):
    d = extract_json(html, "ytInitialData")
    if not d:
        raise ValueError("no ytInitialData")
    cs = d["contents"]["twoColumnWatchNextResults"]["results"]["results"]["contents"]
    prim = next((c["videoPrimaryInfoRenderer"] for c in cs if "videoPrimaryInfoRenderer" in c), {})
    sec = next((c["videoSecondaryInfoRenderer"] for c in cs if "videoSecondaryInfoRenderer" in c), {})
    chapters, seen = [], set()
    for mm in walk(d, "macroMarkersListItemRenderer"):
        c = (text(mm.get("timeDescription")), text(mm.get("title")))
        if c not in seen:
            seen.add(c)
            chapters.append({"time": c[0], "title": c[1]})
    return {
        "id": vid,
        "title": text(prim.get("title")),
        "date": text(prim.get("dateText")),
        "views_text": text(prim.get("viewCount", {}).get("videoViewCountRenderer", {}).get("viewCount")),
        "likes": next(walk(prim, "likeCountIfLikedNumber"), None),
        "description": sec.get("attributedDescription", {}).get("content"),
        "chapters": chapters,
    }


def fetch(vid):
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
    s.cookies.set("SOCS", "CAI", domain=".youtube.com")  # skips the EU consent interstitial
    err = None
    for attempt in range(4):
        try:
            html = s.get(f"https://www.youtube.com/watch?v={vid}&hl=en", timeout=30).text
            r = parse(vid, html)
            time.sleep(1.5)
            return r
        except Exception as e:
            err = repr(e)
            time.sleep(15 * (attempt + 1))
    return {"id": vid, "error": err}


def main():
    args = sys.argv[1:]
    workers = 2
    if "--workers" in args:
        i = args.index("--workers")
        workers = int(args[i + 1])
        del args[i : i + 2]
    ids_path, out = args
    ids = json.load(open(ids_path, encoding="utf-8"))
    done = set()
    if os.path.exists(out):
        for line in open(out, encoding="utf-8"):
            r = json.loads(line)
            if not r.get("error"):
                done.add(r["id"])
    todo = [i for i in ids if i not in done]
    print(f"{len(done)} done, {len(todo)} to fetch", flush=True)
    errors = 0
    with open(out, "a", encoding="utf-8") as f, ThreadPoolExecutor(workers) as ex:
        for n, r in enumerate(ex.map(fetch, todo), 1):
            errors += bool(r.get("error"))
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            f.flush()
            if n % 100 == 0:
                print(n, f"errors={errors}", flush=True)
    print(f"finished errors={errors}", flush=True)


if __name__ == "__main__":
    main()
