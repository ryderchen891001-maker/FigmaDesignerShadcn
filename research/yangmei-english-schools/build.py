import json, math, csv, os, re

SP = os.path.dirname(os.path.abspath(__file__))
CLAT, CLON = 24.920261, 121.1781411


def hav(a1, o1, a2, o2):
    R = 6371000.0
    p1, p2 = math.radians(a1), math.radians(a2)
    dp, dl = math.radians(a2 - a1), math.radians(o2 - o1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


EN = ["美語", "英語", "英文", "English", "ENGLISH", "english", "ESL", "外語", "語文", "語言",
      "兒美", "全民英檢", "英檢", "多益", "TOEIC", "托福", "TOEFL", "雅思", "IELTS",
      "劍橋", "Cambridge", "phonics", "自然發音", "Language", "language"]

SIMP = {"桃园": "桃園", "复旦": "復旦", "龙凤": "龍鳳", "平镇": "平鎮", "区": "區", "县": "縣",
        "台湾": "臺灣", "国": "國", "学": "學", "语": "語", "补": "補", "习": "習"}


def clean_addr(a):
    a = a.strip()
    a = re.sub(r"^[A-Za-z0-9,.\s]*?(?=[一-鿿])", "", a)   # leading latin/No. fragments
    a = re.sub(r"^(台灣省|臺灣省|台灣|臺灣|台湾)\s*", "", a)
    a = re.sub(r"^\d{3,6}\s*", "", a)                    # leading postal code
    a = re.sub(r"^(台灣省|臺灣省|台灣|臺灣|台湾)\s*", "", a)
    a = re.sub(r"^\d{2,3}(?=[一-鿿])", "", a)  # stray postal fragment
    a = re.sub(r"^(台灣省|臺灣省)\s*", "", a)
    for k, v in SIMP.items():
        a = a.replace(k, v)
    a = re.sub(r"\s+", " ", a)
    return a.strip()


CITY_RE = re.compile(r"(新北市|桃園市|新竹縣|新竹市|苗栗縣|臺北市|台北市)?"
                     r"((?:楊梅|平鎮|中壢|龍潭|新屋|觀音|大園|大溪|八德|桃園|蘆竹|龜山|"
                     r"鶯歌|三峽|樹林|土城|湖口|新豐|新埔|關西|芎林|竹北|新竹)[區鄉鎮市])")


def split_area(addr):
    m = CITY_RE.search(addr)
    if not m:
        return "", ""
    city = m.group(1) or ""
    dist = m.group(2)
    if not city:
        if dist in ("鶯歌區", "三峽區", "樹林區", "土城區"):
            city = "新北市"
        elif dist in ("湖口鄉", "新豐鄉", "新埔鎮", "關西鎮", "芎林鄉", "竹北市", "新豐鄉"):
            city = "新竹縣"
        else:
            city = "桃園市"
    return city, dist


def short_name(n):
    n = re.sub(r"[（(].*", "", n)
    n = re.split(r"[|｜/]", n)[0]
    n = re.sub(r"\s*[-–—]\s*.*(分校|校區|補習班).*$", lambda m: m.group(0), n)
    return n.strip()[:40] or n[:40]


places = json.load(open(f"{SP}/raw-places.json"))
rows, dropped = [], 0
for p in places:
    loc = p.get("location") or {}
    if "latitude" not in loc:
        continue
    d = hav(CLAT, CLON, loc["latitude"], loc["longitude"])
    if d > 20000:
        continue
    name = p.get("displayName", {}).get("text", "")
    ptd = p.get("primaryTypeDisplayName", {}).get("text", "")
    if not any(k in f"{name} {ptd}" for k in EN):
        dropped += 1
        continue
    if re.search(r"(國民小學|國民中學|市立.*(國小|國中|高中)|高級中等學校|高級中學)", name):
        dropped += 1
        continue
    addr = clean_addr(p.get("formattedAddress", ""))
    city, dist = split_area(addr)
    band = ("0–5 km" if d <= 5000 else "5–10 km" if d <= 10000
            else "10–15 km" if d <= 15000 else "15–20 km")
    rows.append({
        "band": band,
        "distance_km": round(d / 1000, 2),
        "name": name,
        "short_name": short_name(name),
        "city": city, "district": dist,
        "address": addr,
        "phone": p.get("nationalPhoneNumber", ""),
        "website": p.get("websiteUri", ""),
        "rating": p.get("rating", ""),
        "reviews": p.get("userRatingCount", ""),
        "type": ptd,
        "status": p.get("businessStatus", ""),
        "maps": p.get("googleMapsUri", ""),
        "lat": loc["latitude"], "lng": loc["longitude"],
        "place_id": p.get("id", ""),
    })

rows.sort(key=lambda r: r["distance_km"])

cols = ["band", "distance_km", "name", "city", "district", "address", "phone", "website",
        "rating", "reviews", "type", "status", "maps", "lat", "lng", "place_id"]
with open(f"{SP}/english-schools.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow(r)
json.dump(rows, open(f"{SP}/english-schools.json", "w"), ensure_ascii=False, indent=1)

# saturation coverage report
sat = json.load(open(f"{SP}/saturated-cells.json"))
sat_d = sorted(round(hav(CLAT, CLON, a, b) / 1000, 1) for a, b in sat)
from collections import Counter
print("total kept:", len(rows), "| dropped(non-English):", dropped)
print("bands:", dict(Counter(r["band"] for r in rows)))
print("by district:", dict(Counter(f"{r['city']}{r['district']}" for r in rows).most_common()))
print("phone:", sum(1 for r in rows if r["phone"]), "website:", sum(1 for r in rows if r["website"]))
print("closed/temp:", sum(1 for r in rows if r["status"] != "OPERATIONAL"))
print(f"saturated cells: {len(sat)}/85, their distances(km): {sat_d}")
print("saturated within 5km:", sum(1 for d in sat_d if d <= 5))
