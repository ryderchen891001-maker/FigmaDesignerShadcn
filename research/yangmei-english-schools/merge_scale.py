import json, os, csv, statistics as st
from collections import Counter

SP = os.path.dirname(os.path.abspath(__file__))
places = json.load(open(f"{SP}/english-schools.json"))
matched = {m["place_id"]: m for m in json.load(open(f"{SP}/matched.json"))}
scale = json.load(open(f"{SP}/registry-scale.json"))

rows = []
for p in places:
    m = matched.get(p["place_id"])
    r = dict(p)
    r.update({k: "" for k in ("reg_name", "reg_id", "match", "email", "category",
                              "licensed_on", "principal", "director", "classrooms",
                              "classroom_m2", "building_m2", "approved_capacity",
                              "approved_capacity_en", "n_classes", "n_teachers",
                              "size_tier")})
    if m:
        # a Google pin can cover several licences at one address; sum them
        recs = [scale[i] for i in m["reg_ids"] if i in scale]
        if recs:
            r["reg_name"] = " + ".join(x["reg_name"] for x in recs)
            r["reg_id"] = " ".join(x["id"] for x in recs)
            r["match"] = m["match"]
            r["category"] = " / ".join(sorted({x["category"] for x in recs}))
            r["licensed_on"] = min(x["licensed_on"] for x in recs if x["licensed_on"]) \
                if any(x["licensed_on"] for x in recs) else ""
            r["principal"] = recs[0]["principal"]
            r["director"] = recs[0].get("director", "")
            r["email"] = "; ".join(dict.fromkeys(
                x["email"] for x in recs if x.get("email")))
            for k, f in (("classrooms", int), ("classroom_m2", float), ("building_m2", float),
                         ("approved_capacity", int), ("approved_capacity_en", int),
                         ("n_classes", int), ("n_teachers", int)):
                v = sum(x[k] or 0 for x in recs)
                r[k] = f(round(v, 2)) if v else ""
    rows.append(r)


def concurrent_seats(recs):
    """Rooms x the median approved per-class size = how many students can sit at once.
    Far more defensible than summing every approved subject-class."""
    per = [x["per_class"] for rec in recs for x in rec["subjects"] if x["per_class"]]
    rooms = sum(rec["classrooms"] or 0 for rec in recs)
    if not rooms or not per:
        return ""
    return int(rooms * st.median(per))


def tier(r):
    """Physical scale: rooms and floor area, not the summed approval ceiling."""
    area, rooms = r["building_m2"] or 0, r["classrooms"] or 0
    if not area and not rooms:
        return ""
    if area >= 400 or rooms >= 8:
        return "大型"
    if area >= 200 or rooms >= 5:
        return "中型"
    return "小型"


for r in rows:
    m = matched.get(r["place_id"])
    recs = [scale[i] for i in m["reg_ids"] if i in scale] if m else []
    r["seats_at_once"] = concurrent_seats(recs) if recs else ""
    r["size_tier"] = tier(r)

cols = ["band", "distance_km", "name", "reg_name", "city", "district", "address", "phone",
        "email", "website", "rating", "reviews", "size_tier", "seats_at_once",
        "approved_capacity",
        "approved_capacity_en", "n_classes", "classrooms", "classroom_m2", "building_m2",
        "n_teachers", "category", "licensed_on", "principal", "director", "match", "reg_id",
        "type", "status", "maps", "lat", "lng", "place_id"]
with open(f"{SP}/english-schools-scale.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow(r)
json.dump(rows, open(f"{SP}/english-schools-scale.json", "w"), ensure_ascii=False, indent=1)

got = [r for r in rows if r["approved_capacity"]]
caps = sorted(r["approved_capacity"] for r in got)
areas = sorted(r["building_m2"] for r in rows if r["building_m2"])
tch = sorted(r["n_teachers"] for r in rows if r["n_teachers"])
cls = sorted(r["classrooms"] for r in rows if r["classrooms"])

print(f"總數 {len(rows)}｜對上立案 {sum(1 for r in rows if r['reg_name'])}｜有規模數據 {len(got)}")
print(f"\n核定總容量  中位數 {st.median(caps):.0f} 人  平均 {st.mean(caps):.0f} 人  "
      f"範圍 {caps[0]}–{caps[-1]}  總計 {sum(caps):,} 人")
print(f"英文科容量  中位數 {st.median([r['approved_capacity_en'] for r in rows if r['approved_capacity_en']]):.0f} 人  "
      f"總計 {sum(r['approved_capacity_en'] or 0 for r in rows):,} 人")
print(f"班舍總面積  中位數 {st.median(areas):.0f} ㎡  範圍 {areas[0]:.0f}–{areas[-1]:.0f} ㎡")
print(f"教室數      中位數 {st.median(cls):.0f} 間  範圍 {cls[0]}–{cls[-1]}")
print(f"登記師資    中位數 {st.median(tch):.0f} 人  範圍 {tch[0]}–{tch[-1]}  總計 {sum(tch)} 人")
print("\n規模分級:", dict(Counter(r["size_tier"] for r in rows if r["size_tier"]).most_common()))
print("距離帶 × 有數據:", dict(Counter(r["band"] for r in got).most_common()))

seats = sorted((r["seats_at_once"] for r in rows if r["seats_at_once"]))
print(f"同時段可容納  中位數 {st.median(seats):.0f} 人  範圍 {seats[0]}–{seats[-1]}  總計 {sum(seats):,} 人")

print("\n── 規模前 12 大（依同時段可容納人數）──")
for r in sorted([x for x in rows if x["seats_at_once"]], key=lambda x: -x["seats_at_once"])[:12]:
    print(f'{r["seats_at_once"]:>4}人 {r["classrooms"] or 0:>2}室 {r["building_m2"] or 0:>6.0f}㎡ '
          f'{r["n_teachers"] or 0:>2}師 | {r["distance_km"]:>5}km | {r["size_tier"]} | '
          f'{(r["reg_name"] or r["name"])[:36]}')
print("\n── 20 公里內、有規模數據者的合計 ──")
print(f'核定總容量 {sum(caps):,} 人｜英文科 {sum(r["approved_capacity_en"] or 0 for r in rows):,} 人｜'
      f'班級 {sum(r["n_classes"] or 0 for r in rows):,} 班｜教室 {sum(r["classrooms"] or 0 for r in rows):,} 間｜'
      f'登記師資 {sum(tch):,} 人')
