# 楊梅永平路 20 公里英文補習班普查

以 **桃園市楊梅區永平路**（`24.920261, 121.178141`，座標由 Google Places 回傳）為圓心，
半徑 20 公里內的英文／美語補習班清單，依直線距離分為 0–5 / 5–10 / 10–15 / 15–20 km 四級。

**擷取日期**：2026-09-09 ／ **筆數**：159 家（148 家有電話、71 家有官網）

## 檔案

| 檔案 | 內容 |
|---|---|
| `sweep.py` | 呼叫 Google Places API (New) `places:searchNearby`，六角網格覆蓋 20 公里圓域 |
| `build.py` | 過濾英文相關機構、計算 haversine 距離、分級、輸出 CSV/JSON |
| `gen_page.py` | 由 JSON 產生可篩選的 HTML 名錄頁 |
| `raw-places.json` | API 原始回應（930 個 POI，未過濾） |
| `english-schools.csv` / `.json` | 成品清單 |
| `saturated-cells.json` | 回傳達 20 筆上限的網格中心座標（代表該格未取盡） |

## 重跑

```bash
export GKEY="<你的 Google Maps API key>"   # 不要寫進版控
python3 sweep.py        # 85 次 API 呼叫，約 5 秒
python3 build.py        # 過濾 + 輸出 CSV
python3 gen_page.py     # 產生 HTML
```

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
