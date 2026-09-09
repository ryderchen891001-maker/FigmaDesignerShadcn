"""Match Google Places records to 短期補習班 registry entries.

Three passes, most reliable first:
  1. address  — district + road + 巷/弄/號 (registry writes floors many ways, so
                only the 號 numbers are trusted; a record may list several 號)
  2. phone    — last 8 digits
  3. name     — a distinctive 3+ char run of the Google name inside a registry
                name in the same district, and unique there
"""
import json, os, re
from collections import Counter

SP = os.path.dirname(os.path.abspath(__file__))
places = json.load(open(f"{SP}/english-schools.json"))
reg = json.load(open(f"{SP}/registry-index.json"))

FULL, DIG = "０１２３４５６７８９", "0123456789"
CN = {"一": "1", "二": "2", "三": "3", "四": "4", "五": "5",
      "六": "6", "七": "7", "八": "8", "九": "9", "十": "10"}


def prep(a):
    for f, d in zip(FULL, DIG):
        a = a.replace(f, d)
    a = re.sub(r"^(臺灣省|台灣省|臺灣|台灣)\s*", "", a.strip())
    a = re.sub(r"^\d{3,6}\s*", "", a)
    a = re.sub(r"(新北市|桃園市|新竹縣|新竹市)", "", a)
    a = re.sub(r"^([一-鿿]{1,3}[區鄉鎮市])[一-鿿]{1,4}里(?=[一-鿿])", r"\1", a)
    a = re.sub(r"\d+鄰", "", a)
    a = re.sub(r"([一二三四五六七八九十])段", lambda m: CN[m.group(1)] + "段", a)
    return re.sub(r"\s+", "", a)


def addr_keys(a):
    """Every (district, road, lane, alley, number) key this address can stand for."""
    a = prep(a)
    m = re.match(r"([一-鿿]{1,3}[區鄉鎮市])(.+)", a)
    if not m:
        return []
    dist, rest = m.group(1), m.group(2)
    rm = re.match(r"([^\d]+(?:\d+段)?)", rest)
    if not rm:
        return []
    road = rm.group(1).rstrip("之-")
    lane = (re.search(r"(\d+)巷", rest) or [None, ""])[1] if re.search(r"(\d+)巷", rest) else ""
    alley = (re.search(r"(\d+)[弄衖]", rest).group(1)) if re.search(r"(\d+)[弄衖]", rest) else ""
    haos = re.findall(r"(\d+(?:-\d+)?)號", rest)
    if not haos:  # some records omit 號 entirely
        tail = re.findall(r"\d+", rest)
        haos = [tail[-1]] if tail else []
    keys = []
    for h in haos:
        keys.append(f"{dist}|{road}|{lane}|{alley}|{h}")
        if "-" in h:
            keys.append(f"{dist}|{road}|{lane}|{alley}|{h.split('-')[0]}")
    return keys


def tel8(s):
    d = re.sub(r"\D", "", s or "")
    return d[-8:] if len(d) >= 8 else ""


idx_addr, idx_tel, by_dist = {}, {}, {}
for r in reg:
    for k in addr_keys(r["address"]):
        idx_addr.setdefault(k, []).append(r)
    t = tel8(r["phone"])
    if t:
        idx_tel.setdefault(t, []).append(r)
    by_dist.setdefault(r["district"], []).append(r)

STOP = re.compile(r"(短期補習班|補習班|語文|美語|英語|英文|文理|分校|分班|校區|國小|國中|"
                  r"高中|安親|才藝|兒童|學校|教室|私立|桃園|楊梅|平鎮|中壢|龍潭|推薦|課輔)")


def name_tokens(n):
    n = re.split(r"[|｜/（(]", n)[0]
    n = STOP.sub(" ", n)
    return [t for t in re.findall(r"[一-鿿]{3,6}", n) if len(t) >= 3]


matched, unmatched = [], []
for p in places:
    hits, how = [], ""
    for k in addr_keys(p["address"]):
        if k in idx_addr:
            hits = idx_addr[k]
            how = "address"
            break
    if not hits and tel8(p["phone"]):
        hits = idx_tel.get(tel8(p["phone"]), [])
        how = "phone" if hits else ""
    if not hits:
        pool = by_dist.get(p["district"], [])
        for tok in name_tokens(p["name"]):
            c = [r for r in pool if tok in r["name"]]
            if len(c) == 1:
                hits, how = c, "name"
                break
    if hits:
        matched.append({**p, "reg_ids": [h["id"] for h in hits],
                        "reg_names": [h["name"] for h in hits],
                        "reg_types": [h["type"] for h in hits], "match": how})
    else:
        unmatched.append(p)

json.dump(matched, open(f"{SP}/matched.json", "w"), ensure_ascii=False, indent=1)
json.dump(unmatched, open(f"{SP}/unmatched.json", "w"), ensure_ascii=False, indent=1)
print(f"places {len(places)}  matched {len(matched)} ({len(matched)*100//len(places)}%)  "
      f"unmatched {len(unmatched)}")
print("method:", dict(Counter(m["match"] for m in matched)))
print("registry ids to fetch:", len({i for m in matched for i in m["reg_ids"]}))
print("\nstill unmatched:")
for u in unmatched[:14]:
    print(f'  {u["name"][:34]:<34} | {u["address"]}')
