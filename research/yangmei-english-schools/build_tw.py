"""Merge the nationwide 外語類 index with its detail pages, keep the ones that actually
teach English, and write 全台英文補習班 CSV/JSON."""
import json, os, csv, re, statistics as st
from collections import Counter

SP = os.path.dirname(os.path.abspath(__file__))
idx = {r["id"]: r for r in json.load(open(f"{SP}/registry-tw-index.json"))}
det = json.load(open(f"{SP}/registry-tw-detail.json"))

EN_SUBJ = re.compile(r"(英|美語)")
EN_NAME = re.compile(r"(美語|英語|英文|English|ENGLISH|ESL|英檢|多益|TOEIC|托福|TOEFL|雅思|IELTS)")


def tier(rooms, area):
    if not rooms and not area:
        return ""
    if (area or 0) >= 400 or (rooms or 0) >= 8:
        return "大型"
    if (area or 0) >= 200 or (rooms or 0) >= 5:
        return "中型"
    return "小型"


rows, skipped = [], 0
for sid, d in det.items():
    i = idx.get(sid, {})
    subj_en = [s for s in d["subjects"] if EN_SUBJ.search(s["subject"])]
    name = d["reg_name"] or i.get("name", "")
    # actually teaches English: an approved 英文/美語 subject, or the name says so
    if not subj_en and not EN_NAME.search(name):
        skipped += 1
        continue
    if d.get("revoked_on"):          # 已廢止/註銷
        skipped += 1
        continue
    rows.append({
        "city": i.get("city", ""), "district": i.get("district", ""),
        "reg_name": name,
        "address": d["reg_address"] or i.get("address", ""),
        "phone": d["reg_phone"] or i.get("phone", ""),
        "email": d["email"],
        "size_tier": tier(d["classrooms"], d["building_m2"]),
        "classrooms": d["classrooms"] or "",
        "classroom_m2": d["classroom_m2"] or "",
        "building_m2": d["building_m2"] or "",
        "n_classes": d["n_classes"] or "",
        "n_teachers": d["n_teachers"] or "",
        "approved_capacity": d["approved_capacity"] or "",
        "approved_capacity_en": d["approved_capacity_en"] or "",
        "en_subjects": "、".join(dict.fromkeys(s["subject"] for s in subj_en)),
        "category": d["category"],
        "reg_status": d["reg_status"],
        "licensed_on": d["licensed_on"],
        "principal": d["principal"],
        "director": d.get("director", ""),
        "reg_id": sid,
        "reg_url": f"https://afterschools.olc.tw/afterschools/view/{sid}",
    })

ORDER = ["臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市", "基隆市", "新竹市",
         "新竹縣", "苗栗縣", "彰化縣", "南投縣", "雲林縣", "嘉義市", "嘉義縣", "屏東縣",
         "宜蘭縣", "花蓮縣", "臺東縣", "澎湖縣", "金門縣", "連江縣"]
rows.sort(key=lambda r: (ORDER.index(r["city"]) if r["city"] in ORDER else 99,
                         r["district"], r["reg_name"]))

cols = ["city", "district", "reg_name", "address", "phone", "email", "size_tier",
        "classrooms", "classroom_m2", "building_m2", "n_classes", "n_teachers",
        "approved_capacity", "approved_capacity_en", "en_subjects", "category",
        "reg_status", "licensed_on", "principal", "director", "reg_id", "reg_url"]
with open(f"{SP}/tw-english-schools.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow(r)
json.dump(rows, open(f"{SP}/tw-english-schools.json", "w"), ensure_ascii=False, indent=1)

mail = [r for r in rows if r["email"]]
gmail = [r for r in mail if "gmail.com" in r["email"].lower()]
areas = [r["building_m2"] for r in rows if r["building_m2"]]
rooms = [r["classrooms"] for r in rows if r["classrooms"]]
tch = [r["n_teachers"] for r in rows if r["n_teachers"]]
print(f"外語類 {len(det)} → 教英文且未廢止 {len(rows)} 家（剔除 {skipped}）")
print(f"email {len(mail)} 家（{len(mail)*100//len(rows)}%），其中 Gmail {len(gmail)} 家")
print(f"教室數中位數 {st.median(rooms):.0f}｜班舍面積中位數 {st.median(areas):.0f} ㎡｜"
      f"師資中位數 {st.median(tch):.0f} 人")
print("規模:", dict(Counter(r["size_tier"] for r in rows if r["size_tier"]).most_common()))
print("縣市:", dict(Counter(r["city"] or "?" for r in rows).most_common()))
