"""Build the Excel deliverable from english-schools-scale.json."""
import json, os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

SP = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(f"{SP}/english-schools-scale.json"))
rows.sort(key=lambda r: r["distance_km"])
OUT = f"{SP}/楊梅英語補習班名錄.xlsx"
VIEW = "https://afterschools.olc.tw/afterschools/view/"

F = "Arial"
INK = "1F2A28"
HDR_FILL = PatternFill("solid", fgColor="0B5C50")
BAND_FILL = {"0–5 km": "D6E7E0", "5–10 km": "E4EFE9", "10–15 km": "EFF3EE", "15–20 km": "F7F8F6"}
TIER_FONT = {"大型": "8A4B12", "中型": "1F5F7A", "小型": "6B736E"}
LINK = Font(name=F, size=10, color="0B5C50", underline="single")
THIN = Side(style="thin", color="D7DCD4")
BORDER = Border(bottom=THIN)

COLS = [
    ("距離級距", "band", 11), ("距離(km)", "distance_km", 10),
    ("名稱（Google 招牌）", "name", 42), ("立案名稱", "reg_name", 40),
    ("縣市", "city", 9), ("行政區", "district", 9), ("地址", "address", 34),
    ("電話", "phone", 15), ("官網", "website", 26),
    ("評分", "rating", 7), ("評論數", "reviews", 8),
    ("規模", "size_tier", 7), ("教室數", "classrooms", 8),
    ("教室面積(㎡)", "classroom_m2", 12), ("班舍總面積(㎡)", "building_m2", 14),
    ("核准班級數", "n_classes", 11), ("登記師資(人)", "n_teachers", 12),
    ("核定容量(人)", "approved_capacity", 12), ("英文科核定(人)", "approved_capacity_en", 14),
    ("立案類別", "category", 22), ("立案日期", "licensed_on", 11), ("負責人", "principal", 12),
    ("比對方式", "match", 9), ("立案頁", "_reg_url", 12), ("Google Maps", "maps", 12),
    ("緯度", "lat", 11), ("經度", "lng", 11),
]
NUMFMT = {"distance_km": "0.00", "rating": "0.0", "reviews": "#,##0",
          "classrooms": "#,##0", "classroom_m2": "#,##0.0", "building_m2": "#,##0.0",
          "n_classes": "#,##0", "n_teachers": "#,##0", "approved_capacity": "#,##0",
          "approved_capacity_en": "#,##0", "lat": "0.000000", "lng": "0.000000"}

wb = Workbook()

# ── 說明 ──────────────────────────────────────────────────────────────────
ws = wb.active
ws.title = "說明"
ws.sheet_view.showGridLines = False
ws.column_dimensions["A"].width = 20
ws.column_dimensions["B"].width = 96


def line(r, k, v, bold=False, size=10, gap=0):
    ws.cell(r, 1, k).font = Font(name=F, size=size, bold=True, color=INK)
    c = ws.cell(r, 2, v)
    c.font = Font(name=F, size=size, bold=bold, color=INK)
    c.alignment = Alignment(wrap_text=True, vertical="top")
    return r + 1 + gap


ws["A1"] = "楊梅英語補習班名錄"
ws["A1"].font = Font(name=F, size=18, bold=True, color="0B5C50")
ws["A2"] = "以桃園市楊梅區永平路為圓心，半徑 20 公里內的英文／美語補習班"
ws["A2"].font = Font(name=F, size=11, color="55625D")

r = 4
r = line(r, "圓心", "桃園市楊梅區永平路（24.920261, 121.178141，座標由 Google Places 回傳）")
r = line(r, "半徑", "20 公里，haversine 直線距離（非行車距離）")
r = line(r, "擷取日期", "2026-09-09")
r = line(r, "筆數", f"{len(rows)} 家；其中 {sum(1 for x in rows if x['reg_name'])} 家已對上教育部立案資料", gap=1)

r += 1
ws.cell(r, 1, "資料來源").font = Font(name=F, size=12, bold=True, color="0B5C50")
r += 1
r = line(r, "名單／聯絡方式", "Google Maps Places API (New) places:searchNearby。六角網格覆蓋 20 公里圓域，"
                       "每格搜尋半徑 2,800 公尺、共 85 格；類型限定 school 與 child_care_agency，"
                       "排除主類型為公立中小學與大學者。名稱、地址、電話、官網、評分、評論數皆來自此。")
r = line(r, "規模欄位", "教育部「直轄市及各縣市短期補習班資訊管理系統」立案資料，"
                    "經 https://afterschools.olc.tw/ 取得。教室數、教室面積、班舍總面積、"
                    "核准班級數、每班核准人數、登記教學人員數、立案日期、負責人皆來自此。")
r = line(r, "官方原始站", "https://bsb.kh.edu.tw/ （立案資料權威版本，鏡站為二手；有出入以官方為準）", gap=1)

r += 1
ws.cell(r, 1, "重要限制").font = Font(name=F, size=12, bold=True, color="8A4B12")
r += 1
for k, v in [
    ("沒有學生人數", "各補習班的實際在學人數不屬於公開資訊。Google Maps 與教育部立案系統都沒有這個欄位，"
                "本表無法提供。「核定容量」是法定上限，不是招生人數。"),
    ("核定容量的算法", "各核准科目的「班級數 × 每班核准人數」加總。同一批學生修多科會重複計算，"
                 "會出現「4 間教室卻核定 1,773 人」這種數字。判斷規模請優先看教室數與班舍總面積。"),
    ("名單不完整", "Places API 單次呼叫最多回傳 20 筆，85 個網格中有 36 格觸頂，"
               "中壢、桃園、八德等密集區必有遺漏。同樣這 20 個行政區的立案外語類補習班共 1,064 家。"),
    ("立案比對率 75%", f"{len(rows)} 家中 {sum(1 for x in rows if not x['reg_name'])} 家對不上，"
                  "多為登記在「兒童課後照顧服務中心」名下（另一套系統），或 Google 地址與立案地址不一致。"),
    ("篩選偏保守", "名稱與 Google 類型皆不含美語／英語／英文／語文等字樣的純升學文理班未納入，"
               "但這類補習班多半也教英文。"),
]:
    r = line(r, k, v)

r += 1
ws.cell(r, 1, "規模分級標準").font = Font(name=F, size=12, bold=True, color="0B5C50")
r += 1
for k, v in [("大型", "班舍總面積 ≥ 400 ㎡ 或教室數 ≥ 8 間"),
             ("中型", "班舍總面積 ≥ 200 ㎡ 或教室數 ≥ 5 間"),
             ("小型", "其餘"),
             ("空白", "未對上立案資料，無規模數據")]:
    r = line(r, k, v)

r += 1
ws.cell(r, 1, "比對方式欄").font = Font(name=F, size=12, bold=True, color="0B5C50")
r += 1
for k, v in [("address", "以行政區＋路名＋巷弄號比對（最可靠）"),
             ("phone", "以電話後 8 碼比對"),
             ("name", "以名稱中的特徵字串在同行政區內唯一命中"),
             ("（空白）", "未對上立案資料")]:
    r = line(r, k, v)

# ── 名錄 ──────────────────────────────────────────────────────────────────
ws = wb.create_sheet("名錄")
ws.sheet_view.showGridLines = False
for i, (title, _, w) in enumerate(COLS, 1):
    c = ws.cell(1, i, title)
    c.font = Font(name=F, size=10, bold=True, color="FFFFFF")
    c.fill = HDR_FILL
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.column_dimensions[get_column_letter(i)].width = w
ws.row_dimensions[1].height = 30

for ri, rec in enumerate(rows, 2):
    fill = PatternFill("solid", fgColor=BAND_FILL[rec["band"]])
    for ci, (title, key, _) in enumerate(COLS, 1):
        if key == "_reg_url":
            ids = (rec["reg_id"] or "").split()
            c = ws.cell(ri, ci, "立案頁" if ids else "")
            if ids:
                c.hyperlink = VIEW + ids[0]
                c.font = LINK
        else:
            v = rec.get(key, "")
            c = ws.cell(ri, ci, v if v != "" else None)
            if key in ("website", "maps") and v:
                c.hyperlink = v
                c.value = {"website": "官網", "maps": "地圖"}[key]
                c.font = LINK
            elif key == "size_tier" and v:
                c.font = Font(name=F, size=10, bold=True, color=TIER_FONT[v])
                c.alignment = Alignment(horizontal="center")
            else:
                c.font = Font(name=F, size=10, color=INK)
        if key in NUMFMT:
            c.number_format = NUMFMT[key]
        if key == "band":
            c.fill = fill
            c.alignment = Alignment(horizontal="center")
        if key in ("name", "reg_name", "address", "category"):
            c.alignment = Alignment(wrap_text=True, vertical="top")
        c.border = BORDER

last = get_column_letter(len(COLS))
tbl = Table(displayName="名錄", ref=f"A1:{last}{len(rows)+1}")
tbl.tableStyleInfo = TableStyleInfo(name="TableStyleLight1", showRowStripes=False)
ws.add_table(tbl)
ws.freeze_panes = "D2"

# ── 規模統計 ──────────────────────────────────────────────────────────────
st = wb.create_sheet("規模統計")
st.sheet_view.showGridLines = False
for col, w in zip("ABCDEFGH", (16, 11, 11, 13, 15, 13, 13, 13)):
    st.column_dimensions[col].width = w
N = len(rows) + 1
BAND_C, TIER_C = "名錄!$A$2:$A$%d" % N, "名錄!$L$2:$L$%d" % N
ROOM_C, AREA_C = "名錄!$M$2:$M$%d" % N, "名錄!$O$2:$O$%d" % N
TCH_C, REG_C = "名錄!$Q$2:$Q$%d" % N, "名錄!$D$2:$D$%d" % N
DIST_C, RATE_C = "名錄!$F$2:$F$%d" % N, "名錄!$J$2:$J$%d" % N


def head(row, text, span=8):
    c = st.cell(row, 1, text)
    c.font = Font(name=F, size=12, bold=True, color="0B5C50")
    return row + 1


def hrow(row, labels):
    for i, t in enumerate(labels, 1):
        c = st.cell(row, i, t)
        c.font = Font(name=F, size=10, bold=True, color="FFFFFF")
        c.fill = HDR_FILL
        c.alignment = Alignment(horizontal="center", wrap_text=True)
    return row + 1


st["A1"] = "規模統計"
st["A1"].font = Font(name=F, size=16, bold=True, color="0B5C50")
st["A2"] = "所有數字皆為公式，改動「名錄」分頁會自動重算。"
st["A2"].font = Font(name=F, size=10, color="55625D")

r = head(4, "整體")
r = hrow(r, ["", "家數", "有立案資料", "教室數中位數", "班舍面積中位數(㎡)",
             "師資中位數(人)", "平均教室數", "平均班舍面積(㎡)"])
st.cell(r, 1, "全部").font = Font(name=F, size=10, bold=True, color=INK)
for col, f in zip("BCDEFGH", [
        f'=COUNTA({BAND_C})', f'=COUNTA({REG_C})', f'=MEDIAN({ROOM_C})', f'=MEDIAN({AREA_C})',
        f'=MEDIAN({TCH_C})', f'=AVERAGE({ROOM_C})', f'=AVERAGE({AREA_C})']):
    c = st[f"{col}{r}"]
    c.value = f
    c.font = Font(name=F, size=10, color=INK)
    c.number_format = "#,##0.0" if col in "EH" else "#,##0.#"
r += 2

r = head(r, "依距離級距")
r = hrow(r, ["距離級距", "家數", "有立案資料", "平均教室數", "平均班舍面積(㎡)",
             "平均師資(人)", "大型", "平均評分"])
for band in ["0–5 km", "5–10 km", "10–15 km", "15–20 km"]:
    st.cell(r, 1, band).font = Font(name=F, size=10, color=INK)
    st.cell(r, 1).fill = PatternFill("solid", fgColor=BAND_FILL[band])
    for col, f in zip("BCDEFGH", [
            f'=COUNTIF({BAND_C},$A{r})',
            f'=COUNTIFS({BAND_C},$A{r},{REG_C},"<>")',
            f'=IFERROR(AVERAGEIFS({ROOM_C},{BAND_C},$A{r},{ROOM_C},">0"),"")',
            f'=IFERROR(AVERAGEIFS({AREA_C},{BAND_C},$A{r},{AREA_C},">0"),"")',
            f'=IFERROR(AVERAGEIFS({TCH_C},{BAND_C},$A{r},{TCH_C},">0"),"")',
            f'=COUNTIFS({BAND_C},$A{r},{TIER_C},"大型")',
            f'=IFERROR(AVERAGEIFS({RATE_C},{BAND_C},$A{r},{RATE_C},">0"),"")']):
        c = st[f"{col}{r}"]
        c.value = f
        c.font = Font(name=F, size=10, color=INK)
        c.number_format = "0.0" if col in "DEFH" else "#,##0"
    r += 1
r += 1

r = head(r, "依規模分級")
r = hrow(r, ["規模", "家數", "平均教室數", "平均班舍面積(㎡)", "平均師資(人)",
             "平均核准班級數", "平均評分", "占比"])
tier_first = r
for tier in ["大型", "中型", "小型"]:
    c0 = st.cell(r, 1, tier)
    c0.font = Font(name=F, size=10, bold=True, color=TIER_FONT[tier])
    for col, f in zip("BCDEFG", [
            f'=COUNTIF({TIER_C},$A{r})',
            f'=IFERROR(AVERAGEIFS({ROOM_C},{TIER_C},$A{r}),"")',
            f'=IFERROR(AVERAGEIFS({AREA_C},{TIER_C},$A{r}),"")',
            f'=IFERROR(AVERAGEIFS({TCH_C},{TIER_C},$A{r}),"")',
            f'=IFERROR(AVERAGEIFS(名錄!$P$2:$P${N},{TIER_C},$A{r}),"")',
            f'=IFERROR(AVERAGEIFS({RATE_C},{TIER_C},$A{r},{RATE_C},">0"),"")']):
        c = st[f"{col}{r}"]
        c.value = f
        c.font = Font(name=F, size=10, color=INK)
        c.number_format = "0.0" if col != "B" else "#,##0"
    c = st[f"H{r}"]
    c.value = f'=IFERROR(B{r}/SUM($B${tier_first}:$B${tier_first+2}),"")'
    c.number_format = "0.0%"
    c.font = Font(name=F, size=10, color=INK)
    r += 1
r += 1

r = head(r, "依行政區")
r = hrow(r, ["行政區", "家數", "有立案資料", "平均教室數", "平均班舍面積(㎡)",
             "平均師資(人)", "大型", "平均評分"])
from collections import Counter
for d, _ in Counter(x["district"] for x in rows).most_common():
    st.cell(r, 1, d).font = Font(name=F, size=10, color=INK)
    for col, f in zip("BCDEFGH", [
            f'=COUNTIF({DIST_C},$A{r})',
            f'=COUNTIFS({DIST_C},$A{r},{REG_C},"<>")',
            f'=IFERROR(AVERAGEIFS({ROOM_C},{DIST_C},$A{r},{ROOM_C},">0"),"")',
            f'=IFERROR(AVERAGEIFS({AREA_C},{DIST_C},$A{r},{AREA_C},">0"),"")',
            f'=IFERROR(AVERAGEIFS({TCH_C},{DIST_C},$A{r},{TCH_C},">0"),"")',
            f'=COUNTIFS({DIST_C},$A{r},{TIER_C},"大型")',
            f'=IFERROR(AVERAGEIFS({RATE_C},{DIST_C},$A{r},{RATE_C},">0"),"")']):
        c = st[f"{col}{r}"]
        c.value = f
        c.font = Font(name=F, size=10, color=INK)
        c.number_format = "0.0" if col in "DEFH" else "#,##0"
    r += 1

st.cell(r + 1, 1, "註：平均值只計有數據者；未對上立案資料的補習班不列入教室／面積／師資的平均。") \
  .font = Font(name=F, size=9, italic=True, color="7D8A84")

# ── 未對上立案 ────────────────────────────────────────────────────────────
un = wb.create_sheet("未對上立案")
un.sheet_view.showGridLines = False
UC = [("距離(km)", "distance_km", 10), ("名稱", "name", 46), ("行政區", "district", 10),
      ("地址", "address", 36), ("電話", "phone", 15), ("評分", "rating", 7),
      ("評論數", "reviews", 8), ("Google Maps", "maps", 12)]
for i, (t, _, w) in enumerate(UC, 1):
    c = un.cell(1, i, t)
    c.font = Font(name=F, size=10, bold=True, color="FFFFFF")
    c.fill = PatternFill("solid", fgColor="8A5A12")
    c.alignment = Alignment(horizontal="center")
    un.column_dimensions[get_column_letter(i)].width = w
miss = [x for x in rows if not x["reg_name"]]
for ri, rec in enumerate(miss, 2):
    for ci, (t, k, _) in enumerate(UC, 1):
        v = rec.get(k, "")
        c = un.cell(ri, ci, v if v != "" else None)
        c.font = Font(name=F, size=10, color=INK)
        if k == "maps" and v:
            c.hyperlink, c.value, c.font = v, "地圖", LINK
        if k in NUMFMT:
            c.number_format = NUMFMT[k]
        if k in ("name", "address"):
            c.alignment = Alignment(wrap_text=True, vertical="top")
        c.border = BORDER
un.freeze_panes = "A2"
un.cell(len(miss) + 3, 1,
        "這些是 Google 找得到、但對不上教育部立案資料的補習班。"
        "多為登記在「兒童課後照顧服務中心」名下，或 Google 地址與立案地址不一致；"
        "要確認立案狀態請到 https://bsb.kh.edu.tw/ 以名稱或地址查詢。") \
  .font = Font(name=F, size=9, italic=True, color="7D8A84")

wb.save(OUT)
print(f"saved {OUT}  |  名錄 {len(rows)} 列  |  未對上 {len(miss)} 列")
