import json, math, os, time, threading, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

KEY = os.environ["GKEY"]
SP = os.path.dirname(os.path.abspath(__file__))
OUT = f"{SP}/raw-places.json"
CLAT, CLON = 24.920261, 121.1781411
RADIUS_M = 20000
CELL_R_M = 2800.0          # coverage radius per call
SPACING_M = CELL_R_M * 1.72  # hex packing (<= r*sqrt(3))
BUDGET = 92                 # stay under the 100/day cap

FIELDS = ("places.id,places.displayName,places.formattedAddress,places.shortFormattedAddress,"
          "places.location,places.nationalPhoneNumber,places.internationalPhoneNumber,"
          "places.websiteUri,places.rating,places.userRatingCount,places.businessStatus,"
          "places.primaryTypeDisplayName,places.types,places.googleMapsUri")


def hav(a1, o1, a2, o2):
    R = 6371000.0
    p1, p2 = math.radians(a1), math.radians(a2)
    dp, dl = math.radians(a2 - a1), math.radians(o2 - o1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


lock = threading.Lock()
found = {}
stats = {"calls": 0, "err": 0, "done": 0, "saturated": []}


def save():
    tmp = OUT + ".tmp"
    with open(tmp, "w") as f:
        json.dump(list(found.values()), f, ensure_ascii=False, indent=1)
    os.replace(tmp, OUT)


def post(la, lo):
    body = {
        "includedTypes": ["school", "child_care_agency"],
        "excludedPrimaryTypes": ["primary_school", "secondary_school", "university"],
        "maxResultCount": 20,
        "rankPreference": "DISTANCE",
        "languageCode": "zh-TW",
        "regionCode": "TW",
        "locationRestriction": {"circle": {"center": {"latitude": la, "longitude": lo},
                                           "radius": CELL_R_M}},
    }
    req = urllib.request.Request(
        "https://places.googleapis.com/v1/places:searchNearby",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "X-Goog-Api-Key": KEY,
                 "X-Goog-FieldMask": FIELDS})
    for a in range(2):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                with lock:
                    stats["calls"] += 1
                return json.load(r)
        except urllib.error.HTTPError as e:
            txt = e.read().decode()[:220]
            with lock:
                stats["calls"] += 1
                stats["err"] += 1
                if stats["err"] <= 4:
                    print("HTTP", e.code, txt, flush=True)
            if e.code in (500, 503) and a < 1:
                time.sleep(2)
                continue
            return {}
        except Exception as ex:
            with lock:
                stats["err"] += 1
            if a < 1:
                time.sleep(2)
                continue
            print("ERR", ex, flush=True)
            return {}
    return {}


def job(pt):
    la, lo = pt
    res = post(la, lo)
    pl = res.get("places", [])
    with lock:
        for p in pl:
            found[p["id"]] = p
        stats["done"] += 1
        if len(pl) >= 20:
            stats["saturated"].append([round(la, 5), round(lo, 5)])
        if stats["done"] % 10 == 0:
            save()
            print(f"{stats['done']}/{TOTAL} unique={len(found)} calls={stats['calls']} "
                  f"err={stats['err']} saturated={len(stats['saturated'])}", flush=True)


# hexagonal lattice covering the disc
dlat = SPACING_M / 111320.0
dlon = SPACING_M / (111320.0 * math.cos(math.radians(CLAT)))
row_h = dlat * math.sqrt(3) / 2
pts = []
rows = int(RADIUS_M / (SPACING_M * math.sqrt(3) / 2)) + 2
cols = int(RADIUS_M / SPACING_M) + 2
for i in range(-rows, rows + 1):
    for j in range(-cols, cols + 1):
        la = CLAT + i * row_h
        lo = CLON + (j + (0.5 if i % 2 else 0)) * dlon
        if hav(CLAT, CLON, la, lo) <= RADIUS_M + CELL_R_M * 0.8:
            pts.append((la, lo))

pts.sort(key=lambda p: hav(CLAT, CLON, p[0], p[1]))
if len(pts) > BUDGET:
    print(f"WARNING: {len(pts)} cells > budget {BUDGET}; truncating to nearest {BUDGET}", flush=True)
    pts = pts[:BUDGET]
TOTAL = len(pts)
print(f"cells={TOTAL} cell_r={CELL_R_M}m spacing={SPACING_M:.0f}m", flush=True)

t0 = time.time()
with ThreadPoolExecutor(max_workers=6) as ex:
    list(ex.map(job, pts))
save()
json.dump(stats["saturated"], open(f"{SP}/saturated-cells.json", "w"))
print(f"SAVED {len(found)} places calls={stats['calls']} err={stats['err']} "
      f"saturated_cells={len(stats['saturated'])} {time.time()-t0:.0f}s", flush=True)
