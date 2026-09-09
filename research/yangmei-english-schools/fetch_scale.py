"""Fetch 立案 detail pages and extract the scale fields:
教室數 / 教室面積 / 班舍總面積 / 核准科目 (班級數 × 每班人數) / 教學人員數."""
import json, os, re, html, threading, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

SP = os.path.dirname(os.path.abspath(__file__))
BASE = "https://afterschools.olc.tw/afterschools/view/"

matched = json.load(open(f"{SP}/matched.json"))
ids = sorted({i for m in matched for i in m["reg_ids"]})
print(f"fetching {len(ids)} detail pages", flush=True)

lock = threading.Lock()
out, stats = {}, {"ok": 0, "err": 0}


def txt(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s))).strip()


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


DL = re.compile(r"<dt[^>]*>(.*?)</dt>\s*<dd[^>]*>(.*?)</dd>", re.S)
ROW = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)
CELL = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", re.S)


def num(s, pat=r"(\d+(?:\.\d+)?)"):
    m = re.search(pat, s or "")
    return float(m.group(1)) if m else None


def job(sid):
    s = get(BASE + sid)
    if not s:
        with lock:
            stats["err"] += 1
        return
    fields = {txt(k): txt(v) for k, v in DL.findall(s)}

    subjects, staff = [], []
    for rows in [ROW.findall(t) for t in re.findall(r"<table.*?</table>", s, re.S)]:
        for r in rows:
            c = [txt(x) for x in CELL.findall(r)]
            if len(c) >= 6 and re.search(r"\d+\s*班", c[1]) and re.search(r"\d+\s*人", c[2]):
                subjects.append({"subject": c[0], "classes": int(num(c[1]) or 0),
                                 "per_class": int(num(c[2]) or 0), "target": c[5]})
            elif len(c) >= 5 and c[0] and "姓名" not in c[0] and re.search(r"(大學|碩士|學士|專科|研究所|博士|高中)", " ".join(c[1:3])):
                staff.append({"name": c[0], "subjects": c[4] if len(c) > 4 else ""})

    cap = sum(x["classes"] * x["per_class"] for x in subjects)
    en = [x for x in subjects if re.search(r"(英|美語)", x["subject"])]
    cap_en = sum(x["classes"] * x["per_class"] for x in en)

    rec = {
        "id": sid,
        "reg_name": fields.get("補習班名稱", ""),
        "reg_address": fields.get("地址", ""),
        "reg_phone": fields.get("電話", ""),
        "category": fields.get("補習班類別/科目", ""),
        "status": fields.get("立案情形", ""),
        "licensed_on": fields.get("立案日期", ""),
        "revoked_on": fields.get("廢止、註銷日期", ""),
        "principal": fields.get("負責人", "") or fields.get("負責人姓名", ""),
        "director": fields.get("班主任", ""),
        "classrooms": int(num(fields.get("教室數", "")) or 0) or None,
        "classroom_m2": num(fields.get("教室面積", "")),
        "building_m2": num(fields.get("班舍總面積", "")),
        "approved_capacity": cap or None,
        "approved_capacity_en": cap_en or None,
        "n_subject_rows": len(subjects),
        "n_classes": sum(x["classes"] for x in subjects) or None,
        "n_teachers": len(staff) or None,
        "subjects": subjects,
    }
    with lock:
        out[sid] = rec
        stats["ok"] += 1
        if stats["ok"] % 25 == 0:
            print(f"{stats['ok']}/{len(ids)} err={stats['err']}", flush=True)


t0 = time.time()
with ThreadPoolExecutor(max_workers=10) as ex:
    list(ex.map(job, ids))
json.dump(out, open(f"{SP}/registry-scale.json", "w"), ensure_ascii=False, indent=1)

have = lambda k: sum(1 for r in out.values() if r.get(k))
print(f"\nDONE {len(out)} pages, {stats['err']} errors, {time.time()-t0:.0f}s")
print(f"教室數 {have('classrooms')} | 教室面積 {have('classroom_m2')} | "
      f"班舍總面積 {have('building_m2')} | 核定容量 {have('approved_capacity')} | "
      f"英文科容量 {have('approved_capacity_en')} | 師資 {have('n_teachers')}")
