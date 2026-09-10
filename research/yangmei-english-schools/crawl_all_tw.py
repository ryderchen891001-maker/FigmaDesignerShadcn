"""Crawl every 立案短期補習班 listing page nationwide, keep the 外語類 (foreign-language)
records. Output: registry-tw-index.json"""
import json, os, re, html, threading, time, urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

SP = os.path.dirname(os.path.abspath(__file__))
BASE = "https://afterschools.olc.tw"
PAGES = 357

CITY = {"63": "臺北市", "65": "新北市", "68": "桃園市", "66": "臺中市", "67": "臺南市",
        "64": "高雄市", "10002": "宜蘭縣", "10004": "新竹縣", "10005": "苗栗縣",
        "10007": "彰化縣", "10008": "南投縣", "10009": "雲林縣", "10010": "嘉義縣",
        "10013": "屏東縣", "10014": "臺東縣", "10015": "花蓮縣", "10016": "澎湖縣",
        "10017": "基隆市", "10018": "新竹市", "10020": "嘉義市", "09020": "金門縣",
        "09007": "連江縣",
        # the view-id prefixes actually used by this dataset (city codes from bsb)
        "20": "臺北市", "21": "新北市", "33": "桃園市", "42": "臺中市", "62": "臺南市",
        "70": "高雄市", "24": "基隆市", "35": "新竹市", "36": "新竹縣", "37": "苗栗縣",
        "47": "彰化縣", "49": "南投縣", "55": "雲林縣", "52": "嘉義市", "53": "嘉義縣",
        "87": "屏東縣", "39": "宜蘭縣", "38": "花蓮縣", "89": "臺東縣", "69": "澎湖縣",
        "82": "金門縣", "83": "連江縣"}

CARD = re.compile(
    r'/afterschools/view/(\d+)">\s*<h2[^>]*>\s*(.*?)\s*</h2>.*?'
    r'類型</dt>\s*<dd[^>]*>\s*(.*?)\s*(?:&nbsp;)?</dd>.*?'
    r'住址\s*</dt>\s*<dd[^>]*>\s*(.*?)\s*(?:&nbsp;)?</dd>.*?'
    r'電話\s*</dt>\s*<dd[^>]*>\s*(.*?)\s*(?:&nbsp;)?</dd>',
    re.S)

lock = threading.Lock()
recs, stats = {}, {"ok": 0, "err": 0, "seen": 0}


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


DISTRICT = re.compile(r"^([一-鿿]{1,4}[區鄉鎮市])")


def page_job(n):
    url = f"{BASE}/afterschools" if n == 1 else f"{BASE}/afterschools/page/{n}"
    s = get(url)
    if not s:
        with lock:
            stats["err"] += 1
        return
    out = []
    for sid, name, typ, addr, tel in CARD.findall(s):
        typ, addr = clean(typ), clean(addr)
        with lock:
            stats["seen"] += 1
        if "外語" not in typ:
            continue
        m = DISTRICT.match(addr)
        out.append({"id": sid, "name": clean(name), "type": typ,
                    "city": CITY.get(sid[:2], ""), "district": m.group(1) if m else "",
                    "address": addr, "phone": clean(tel)})
    with lock:
        for r in out:
            recs[r["id"]] = r
        stats["ok"] += 1
        if stats["ok"] % 50 == 0:
            print(f"pages {stats['ok']}/{PAGES}  seen={stats['seen']}  外語類={len(recs)}", flush=True)


t0 = time.time()
with ThreadPoolExecutor(max_workers=12) as ex:
    list(ex.map(page_job, range(1, PAGES + 1)))
json.dump(list(recs.values()), open(f"{SP}/registry-tw-index.json", "w"),
          ensure_ascii=False, indent=1)
print(f"\nDONE  掃過 {stats['seen']} 家，外語類 {len(recs)} 家，"
      f"{stats['err']} 頁失敗，{time.time()-t0:.0f}s")
print("縣市分布:", dict(Counter(r["city"] or "?" for r in recs.values()).most_common()))
