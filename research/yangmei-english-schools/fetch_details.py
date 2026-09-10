"""Fetch 立案 detail pages and extract email + scale fields.

usage: python3 fetch_details.py <index.json> <out.json> [workers]

The mirror hides e-mail behind Cloudflare's email-protection: the address is hex in
data-cfemail, first byte is the XOR key for the rest.
"""
import json, os, re, sys, html, threading, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

SP = os.path.dirname(os.path.abspath(__file__))
BASE = "https://afterschools.olc.tw/afterschools/view/"
IDX = sys.argv[1] if len(sys.argv) > 1 else f"{SP}/registry-tw-index.json"
OUT = sys.argv[2] if len(sys.argv) > 2 else f"{SP}/registry-tw-detail.json"
WORKERS = int(sys.argv[3]) if len(sys.argv) > 3 else 12

index = json.load(open(IDX))
ids = [r["id"] for r in index] if isinstance(index[0], dict) else list(index)
print(f"fetching {len(ids)} detail pages with {WORKERS} workers", flush=True)

lock = threading.Lock()
out, stats = {}, {"ok": 0, "err": 0, "mail": 0}


def cfdecode(hexstr):
    b = bytes.fromhex(hexstr)
    key = b[0]
    try:
        return "".join(chr(c ^ key) for c in b[1:])
    except Exception:
        return ""


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
            time.sleep(1.0 * (a + 1))
    return ""


DL = re.compile(r"<dt[^>]*>(.*?)</dt>\s*<dd[^>]*>(.*?)</dd>", re.S)
ROW = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)
CELL = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", re.S)
CFMAIL = re.compile(r'data-cfemail="([0-9a-f]+)"')
PLAINMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


def num(s):
    m = re.search(r"(\d+(?:\.\d+)?)", s or "")
    return float(m.group(1)) if m else None


def job(sid):
    s = get(BASE + sid)
    if not s:
        with lock:
            stats["err"] += 1
        return
    raw = {k: v for k, v in DL.findall(s)}
    fields = {txt(k): txt(v) for k, v in raw.items()}

    # e-mail: decode the cfemail inside the 電子郵件 <dd>, else any plain address
    email = ""
    for k, v in raw.items():
        if "電子郵件" in txt(k):
            m = CFMAIL.search(v)
            if m:
                email = cfdecode(m.group(1))
            else:
                pm = PLAINMAIL.search(txt(v))
                email = pm.group(0) if pm else ""
            break
    email = email if "@" in email else ""

    subjects, staff = [], []
    for t in re.findall(r"<table.*?</table>", s, re.S):
        for r in ROW.findall(t):
            c = [txt(x) for x in CELL.findall(r)]
            if len(c) >= 6 and re.search(r"\d+\s*班", c[1]) and re.search(r"\d+\s*人", c[2]):
                subjects.append({"subject": c[0], "classes": int(num(c[1]) or 0),
                                 "per_class": int(num(c[2]) or 0), "target": c[5]})
            elif (len(c) >= 5 and c[0] and "姓名" not in c[0]
                  and re.search(r"(大學|碩士|學士|專科|研究所|博士|高中)", " ".join(c[1:3]))):
                staff.append(c[0])

    cap = sum(x["classes"] * x["per_class"] for x in subjects)
    cap_en = sum(x["classes"] * x["per_class"] for x in subjects
                 if re.search(r"(英|美語)", x["subject"]))
    rec = {
        "id": sid,
        "reg_name": fields.get("補習班名稱", ""),
        "reg_address": fields.get("地址", ""),
        "reg_phone": fields.get("電話", ""),
        "email": email,
        "category": fields.get("補習班類別/科目", ""),
        "reg_status": fields.get("立案情形", ""),
        "licensed_on": fields.get("立案日期", ""),
        "revoked_on": fields.get("廢止、註銷日期", ""),
        "principal": fields.get("負責人", "") or fields.get("負責人姓名", ""),
        "director": fields.get("班主任", ""),
        "classrooms": int(num(fields.get("教室數", "")) or 0) or None,
        "classroom_m2": num(fields.get("教室面積", "")),
        "building_m2": num(fields.get("班舍總面積", "")),
        "approved_capacity": cap or None,
        "approved_capacity_en": cap_en or None,
        "n_classes": sum(x["classes"] for x in subjects) or None,
        "n_teachers": len(staff) or None,
        "subjects": subjects,
    }
    with lock:
        out[sid] = rec
        stats["ok"] += 1
        if email:
            stats["mail"] += 1
        if stats["ok"] % 250 == 0:
            json.dump(out, open(OUT + ".part", "w"), ensure_ascii=False)
            print(f"{stats['ok']}/{len(ids)}  email={stats['mail']}  err={stats['err']}", flush=True)


t0 = time.time()
with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    list(ex.map(job, ids))
json.dump(out, open(OUT, "w"), ensure_ascii=False, indent=1)
if os.path.exists(OUT + ".part"):
    os.remove(OUT + ".part")

have = lambda k: sum(1 for r in out.values() if r.get(k))
gmail = sum(1 for r in out.values() if r["email"].lower().endswith("@gmail.com"))
print(f"\nDONE {len(out)} 筆，{stats['err']} 失敗，{time.time()-t0:.0f}s")
print(f"email {have('email')} 筆（其中 Gmail {gmail} 筆）｜教室數 {have('classrooms')}｜"
      f"班舍面積 {have('building_m2')}｜師資 {have('n_teachers')}")
