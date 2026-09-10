# 英文補習班名錄：楊梅 20 公里圈 ＋ 全台立案

**主要成品**：`楊梅英語補習班名錄.xlsx`（說明／楊梅20km名錄／全台英文補習班／規模統計／未對上立案）

| 資料集 | 家數 | 來源 | 有 Email |
|---|---|---|---|
| 楊梅永平路 20 km 圈 | 159 | Google Places ＋ 立案資料 | 113 |
| 全台英文補習班 | 4,685 | 純立案資料，22 縣市 | 3,790（Gmail 2,140）|

---

## 楊梅永平路 20 公里普查

以 **桃園市楊梅區永平路**（`24.920261, 121.178141`，座標由 Google Places 回傳）為圓心，
半徑 20 公里內的英文／美語補習班清單，依直線距離分為 0–5 / 5–10 / 10–15 / 15–20 km 四級。

**擷取日期**：2026-09-09 ／ **筆數**：159 家（148 家有電話、71 家有官網）
其中 **120 家**已對上教育部立案資料，補上教室數、班舍面積、核准班級數與登記師資人數。

> **沒有「實際學生人數」。** 在學人數不屬於公開資訊，Google Maps 與教育部立案系統都沒有
> 這個欄位。本資料集提供的是立案登記的硬體規模與法定招生上限。

## 檔案

| 檔案 | 內容 |
|---|---|
| `sweep.py` | 呼叫 Google Places API (New) `places:searchNearby`，六角網格覆蓋 20 公里圓域 |
| `build.py` | 過濾英文相關機構、計算 haversine 距離、分級、輸出 CSV/JSON |
| `crawl_registry.py` | 爬立案清單，篩出研究範圍內 20 個行政區（1,946 家，外語類 1,064 家） |
| `crawl_all_tw.py` | 爬全國 357 頁清單（17,836 家），篩出外語類 4,819 家 → `registry-tw-index.json` |
| `fetch_details.py` | 抓立案詳細頁，取 email（解 Cloudflare `data-cfemail` 混淆）＋ 規模欄位 |
| `build_tw.py` | 篩出實際教英文且未廢止者 4,685 家 → `tw-english-schools.csv` |
| `make_xlsx.py` | 產生 5 分頁 Excel 成品 |
| `match.py` | 以地址（行政區＋路名＋巷弄號）為主、電話與名稱為輔，把 Google 記錄對上立案記錄 |
| `fetch_scale.py` | 抓立案詳細頁，取出教室數／教室面積／班舍總面積／核准科目班級數與人數／教學人員 |
| `merge_scale.py` | 合併規模欄位、規模分級、輸出 `english-schools-scale.csv` |
| `gen_page.py` | 由 JSON 產生可篩選的 HTML 名錄頁 |
| `raw-places.json` | API 原始回應（930 個 POI，未過濾） |
| `english-schools.csv` / `.json` | 成品清單（Google 欄位） |
| `english-schools-scale.csv` / `.json` | 成品清單＋立案規模欄位（**主要成品**） |
| `registry-index.json` | 研究範圍內的立案補習班索引（1,946 家） |
| `registry-scale.json` | 117 筆立案詳細頁的規模資料 |
| `matched.json` / `unmatched.json` | 比對結果 |
| `saturated-cells.json` | 回傳達 20 筆上限的網格中心座標（代表該格未取盡） |

## 重跑

```bash
export GKEY="<你的 Google Maps API key>"   # 不要寫進版控
python3 sweep.py        # 85 次 API 呼叫，約 5 秒
python3 build.py        # 過濾 + 輸出 CSV
python3 gen_page.py     # 產生 HTML

# 規模資料（不需要 API key，來源是教育部立案資料鏡站）
python3 crawl_registry.py   # 爬 357 頁清單，約 20 秒
python3 match.py            # 對上 120/159 家
python3 fetch_scale.py      # 抓 117 筆詳細頁，約 8 秒
python3 merge_scale.py      # 合併並輸出 english-schools-scale.csv
python3 gen_page.py         # 重新產生 HTML

# 全台資料集（約 9 分鐘，4,819 次 HTTP 請求）
python3 crawl_all_tw.py                                              # 30 秒
python3 fetch_details.py registry-tw-index.json registry-tw-detail.json 12   # 8 分鐘
python3 build_tw.py                                                  # 篩英文
python3 make_xlsx.py                                                 # 產 Excel
```

## Email 欄位

立案登記的聯絡信箱，**非 Google 資料**（Places API 沒有 email 欄位）。鏡站以 Cloudflare
email-protection 混淆，位址存在 `data-cfemail` 的十六進位字串中，首位元組是其餘位元組的
XOR key，`fetch_details.py` 的 `cfdecode()` 負責還原。

覆蓋率：楊梅名錄 113/159、全台 3,790/4,685（81%）。這是負責人或班務的登記信箱，
未必是招生窗口，也可能已停用；群發前請先小量測試退信率，並遵守個資法規範。

## 規模欄位

| 欄位 | 說明 |
|---|---|
| `size_tier` | 大型／中型／小型。班舍 ≥400㎡ 或教室 ≥8 間為大型；≥200㎡ 或 ≥5 間為中型 |
| `classrooms` / `classroom_m2` / `building_m2` | 教室數、教室面積、班舍總面積（立案登記值） |
| `n_classes` | 核准班級數合計 |
| `approved_capacity` | 各核准科目「班級數 × 每班核准人數」加總。**同一批學生修多科會重複計算**，僅為上限參考 |
| `approved_capacity_en` | 同上，只計英文／美語科目 |
| `seats_at_once` | 教室數 × 每班核准人數中位數，粗估同時段可容納人數 |
| `n_teachers` | 立案登記的教學人員數 |

統計（119 家有規模數據）：教室數中位數 4 間、班舍總面積中位數 172 ㎡、
登記師資中位數 3 人；規模分級為小型 66、中型 38、大型 16。

## 方法

- 端點 `places:searchNearby`，`rankPreference: DISTANCE`
- 類型限定 `school`、`child_care_agency`；排除主類型為 `primary_school`、`secondary_school`、`university`
- 網格：六角排列，每格搜尋半徑 2,800 m、間距 4,816 m，共 85 格
- 距離：haversine 直線距離，非行車距離
- 英文判定：名稱或 Google 類型含「美語／英語／英文／語文／語言／外語／英檢／多益／托福／雅思／ESL／English」等關鍵字

## 已知限制

1. **未取盡。** `searchNearby` 單次上限 20 筆，85 格中有 36 格觸頂（含楊梅市區 7 格），
   中壢、桃園、八德等密集區域必有遺漏。`saturated-cells.json` 記錄了這些座標，
   可用更小的網格半徑針對性補掃。
2. **配額。** 未啟用計費的 GCP 專案，`SearchTextRequest` 與 `SearchNearbyRequest`
   各為每日 100 次上限。啟用計費後即可用更密的網格取盡。
3. **名稱過濾偏保守。** 純升學型「文理補習班」若名稱不含英文相關字樣則未納入，
   但這類補習班多半也教英文。
4. Google 商家資料未必等同教育局立案資料；撥打前建議確認營業狀態。
5. **立案比對只到 75%。** 159 家中 39 家對不上，多為登記在「兒童課後照顧服務中心」
   名下（另一套登記系統）、或 Google 地址與立案地址不一致者。
6. **`approved_capacity` 不是招生人數。** 它是各科核准班級數乘上每班人數的加總，
   會出現 4 間教室卻「核定 1,773 人」這種數字；判斷規模請優先看教室數與班舍面積。
7. 立案名稱與招牌名稱常不同（加盟品牌多以在地登記名稱立案），兩者在成品中並列。
8. **全台分頁沒有距離、評分與官網。** 那些欄位需要 Google Places API，免費配額每日
   僅 100 次呼叫，不可能涵蓋 4,685 家。全台分頁是純立案資料。
9. **全台分頁的英文判定**：核准科目含「英」或「美語」為主、名稱關鍵字為輔；
   純日語／韓語補習班與已廢止／註銷者已剔除（4,819 → 4,685）。
