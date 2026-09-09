"""Crawl afterschools.olc.tw (mirror of 教育部短期補習班資訊管理系統) listing pages,
keeping only records in the districts that fall inside the 20 km study area."""
import json, os, re, html, threading, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

SP = os.path.dirname(os.path.abspath(__file__))
BASE = "https://afterschools.olc.tw"
PAGES = 357
DISTRICTS = ["楊梅區", "平鎮區", "中壢區", "龍潭區", "新屋區", "觀音區", "大園區", "大溪區",
             "八德區", "桃園區", "蘆竹區", "龜山區",
             "湖口鄉", "新豐鄉", "新埔鎮", "關西鎮", "芎林鄉", "竹北市",
             "鶯歌區", "三峽區"]
# same names appear in other counties; city code prefix disambiguates
CITY_PREFIX = {"33": "桃園市", "36": "新竹縣", "35": "新竹市", "21": "新北市"}

CARD = re.compile(
    r'/afterschools/view/(\d+)">\s*<h2[^>]*>\s*(.*?)\s*</h2>.*?'
    r'類型</dt>\s*<dd[^>]*>\s*(.*?)\s*(?:&nbsp;)?</dd>.*?'
    r'住址\s*</dt>\s*<dd[^>]*>\s*(.*?)\s*(?:&nbsp;)?</dd>.*?'
    r'電話\s*</dt>\s*<dd[^>]*>\s*(.*?)\s*(?:&nbsp;)?</dd>',
    re.S)

lock = threading.Lock()
recs, stats = {}, {"ok": 0, "err": 0}


def get(url, tries=3):
    for a in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (research)"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except Exception:
            if a == tries - 1:
                return ""
            time.sleep(1.2 * (a + 1))
    return ""


def clean(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s))).strip()


def page_job(n):
    url = f"{BASE}/afterschools" if n == 1 else f"{BASE}/afterschools/page/{n}"
    s = get(url)
    if not s:
        with lock:
            stats["err"] += 1
        return
    hit = 0
    for sid, name, typ, addr, tel in CARD.findall(s):
        city = CITY_PREFIX.get(sid[:2])
        if not city:
            continue
        addr = clean(addr)
        d = next((x for x in DISTRICTS if addr.startswith(x)), None)
        if not d:
            continue
        with lock:
            recs[sid] = {"id": sid, "name": clean(name), "type": clean(typ),
                         "city": city, "district": d, "address": addr, "phone": clean(tel)}
        hit += 1
    with lock:
        stats["ok"] += 1
        if stats["ok"] % 40 == 0:
            print(f"pages {stats['ok']}/{PAGES}  matched={len(recs)}  err={stats['err']}", flush=True)


t0 = time.time()
with ThreadPoolExecutor(max_workers=12) as ex:
    list(ex.map(page_job, range(1, PAGES + 1)))
json.dump(list(recs.values()), open(f"{SP}/registry-index.json", "w"), ensure_ascii=False, indent=1)
from collections import Counter
print(f"DONE {len(recs)} records in study districts, {stats['err']} page errors, {time.time()-t0:.0f}s")
print(dict(Counter(f'{r["city"]}{r["district"]}' for r in recs.values()).most_common()))
print("外語類:", sum(1 for r in recs.values() if "外語" in r["type"]))
