# SA-3 Diff 掃描模式指令（Diff-only Test Mode）

> 此模板用於 SA-3 在疊代版本時，只掃描有變動的區塊，不掃描整個檔案。
> 可節省約 60–80% 的靜態分析 token（取決於改動範圍）。

---

## 前置條件

SA-2 疊代後，下列檔案必須存在：

- `.claude/workspace/{ProjectName}/{ComponentName}/changed-zones.json`
- `projects/{ProjectName}/components/pending/{ComponentName}/{ComponentName}.tsx`（新版）
- `.claude/workspace/{ProjectName}/{ComponentName}/design-spec.json`

如果 `changed-zones.json` 不存在 → **切換回全檔掃描模式**（見下方說明）。

---

## 執行流程

### Step 1 — 讀取 changed-zones.json

```bash
Read .claude/workspace/{ProjectName}/{ComponentName}/changed-zones.json
```

取出：
- `changedZones` — 要測試的 ReviewZone id 列表
- `changedFunctions` — 要測試的函式名稱列表
- `addedLines` / `removedLines` — 變動規模評估

**規模判斷**：
- `addedLines + removedLines < 50`：只測 changedZones（層一 + 層四）
- `addedLines + removedLines 50–200`：測 changedZones（四層）
- `addedLines + removedLines > 200`：切換回全檔模式

### Step 2 — 定位測試目標

用 Grep 找到 changedZones 和 changedFunctions 的行號範圍：

```bash
# 找 zone
Grep "id=\"{zone}\"" {ComponentName}.tsx

# 找 function
Grep "function {FunctionName}\|const {FunctionName}" {ComponentName}.tsx
```

用 Read with offset + limit 只讀目標區塊（不讀整個檔案）。

### Step 3 — 四層測試（只對 changedZones）

**層一：視覺 token 吻合**
- 對照 design-spec.json 的 colors / typography / spacing
- 只檢查 changedZones 內的 Tailwind class
- 允許誤差：Tailwind 等效換算，尺寸 < 2px

**層二：互動行為**
- 只確認 changedFunctions 內有沒有：handler 缺失、hover state 缺失
- 不掃沒有改動的函式

**層三：RWD 響應式**
- 只確認 changedZones 內有沒有硬寫 px 寬高
- 如果 changedZones 不含 layout 區塊，可跳過

**層四：Accessibility**
- 確認 changedZones 內新增的 button/input 有 aria-label / label

### Step 4 — 自動修正（只修改問題區塊）

如果發現問題，用 Edit tool 精準修改（不用 Write 覆蓋整個檔案）。

允許自動修的清單（同全檔模式）：
| 類型 | 說明 |
|---|---|
| 缺少 `aria-label` | button/a 無文字時補上 |
| 缺少 `<label>` 或 `aria-labelledby` | input 孤立時補對應 label |
| Tailwind 顏色 class 誤差 | 換算對應 design-spec 指定的色階 |
| 字體大小 class 誤差 ≤ 2px | `text-sm` / `text-base` 等換算 |
| 間距 class 誤差 ≤ 2px | `p-3` / `p-4` 等換算 |
| 缺少 `hover:` state class | 有 onClick 但無 hover 視覺回饋 |
| 硬寫固定 px 寬高 | 替換成等效 Tailwind class |

自動修後：重新掃描一次（同樣只掃 changedZones，不重掃全檔）。

不允許自動修 → 輸出 `needs-human` 報告（同全檔模式規則）。

---

## 全檔模式 fallback 條件

遇到以下任一情況，切換回全檔模式：

1. `changed-zones.json` 不存在
2. `changedZones` 為空陣列（全面重構）
3. `addedLines + removedLines > 200`
4. changedFunctions 包含 `default export` 或頂層 component 名稱（整個 component 重寫）

切換後，按照原有的四層全檔測試流程執行。

---

## 寫入 test-report.json

```json
{
  "componentName": "{ComponentName}",
  "version": {N},
  "mode": "diff",
  "testedZones": ["{zone1}", "{zone2}"],
  "testedFunctions": ["{fn1}"],
  "layers": {
    "visual": { "passed": true, "issues": [] },
    "interaction": { "passed": true, "issues": [] },
    "rwd": { "passed": true, "issues": [], "skipped": true },
    "a11y": { "passed": true, "issues": [] }
  },
  "autoFixed": false,
  "autoFixedItems": [],
  "overallPassed": true,
  "testedAt": "{ISO timestamp}"
}
```

### 備份到 reports/

```bash
# 複製到歷史報告目錄
Write projects/{ProjectName}/reports/{ComponentName}-v{N}-{YYYYMMDD-HHmm}.json
```

---

## 更新 queue-entry

```bash
node .claude/scripts/queue-update.js {ComponentName} --set \
  '{"status":"test-passed","testPassed":true,"autoFixApplied":false}'
```

---

## 回傳給 Orchestrator（< 100 字）

```
✅ {ComponentName} v{N} 測試通過（diff 模式）
- 測試區塊：{testedZones}
- 自動修正：{是/否}（{修正項目}）
- 掃描行數：~{N} 行（全檔 {total} 行的 {%}%）
- 下一步：SA-4 部署
```

失敗時：
```
❌ {ComponentName} v{N} 測試未通過（diff 模式）
- 問題區塊：{zone}
- 問題類型：{不允許自動修的類型}
- 需要人工決定：{具體描述}
- queue: needs-human
```
