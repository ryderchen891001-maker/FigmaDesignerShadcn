# SA-2 疊代模式指令（Revision Mode）

> 此模板用於 SA-2 在已有現成版本的情況下進行疊代修改。
> **不讀整個 TSX**，只讀 diff + 評論，只改有變動的區塊。

---

## 輸入檢查清單

在開始之前，確認已取得：

- [ ] `comments.json` — 所有 pending 評論（只處理 `status: "pending"` 的）
- [ ] `changed-zones.json`（可選）— 前一版 diff 輸出的變更區塊清單
- [ ] `design-spec.json` — 只讀目標欄位（colors、typography、spacing）
- [ ] 當前版本號（從 queue-entry.json 讀）

**不需要讀**：
- 整個 `.tsx` 檔案（用 diff + zones 定位即可）
- 舊版 `versions/` 快照（已有 diff）

---

## 執行流程

### Step 1 — 讀取評論

```bash
# 讀 pending 評論
node .claude/scripts/queue-read.js {ComponentName}
# → 確認 version 號（假設為 N）

# 讀 comments
Read .claude/workspace/{ProjectName}/{ComponentName}/comments.json
# → 只處理 status: "pending" 的條目
```

### Step 2 — 取得 diff（如果有前一版）

```bash
node .claude/scripts/diff.js {ComponentName}
# 輸出：
# {
#   "diff": "--- v{N-1}\n+++ v{N}\n...",
#   "changedZones": ["edit-dialog", "header"],
#   "changedFunctions": ["EditClassDialog"],
#   "summary": "..."
# }
```

如果只有 v1（第一次疊代），直接跳到 Step 3，讀整個 TSX。

### Step 3 — 定位需要修改的區塊

根據評論的 `zone` 欄位，搜尋對應的函式或區塊：

```bash
# 搜尋特定 zone 或 function
Grep "zone-name\|FunctionName" {ComponentName}.tsx
# 只讀該區塊的行號範圍（用 Read with offset + limit）
```

### Step 4 — 套用修改

- **只修改**評論要求改的區塊
- **不動**沒有評論的區塊
- 用 Edit tool（不用 Write 覆蓋整個檔案）

### Step 5 — 更新版本資訊

1. 更新檔案頂部的版本註解：
   ```tsx
   // version: {N+1}
   // generatedAt: {ISO timestamp}
   ```

2. 把新版本快照寫到 versions/：
   ```bash
   # 複製當前 TSX 到 versions/v{N+1}.tsx
   ```

3. 把評論標為已解決：
   ```json
   // comments.json 中，每個處理的評論：
   { "status": "resolved", "resolvedInVersion": {N+1} }
   ```

4. **先快照，再更新 queue**（順序不能顛倒）：

   ```bash
   # Step A：把新版本快照寫入 versions/（必須在 queue version 更新前執行）
   node .claude/scripts/queue-update.js {ComponentName} version {N+1}
   node .claude/scripts/snapshot.js {ComponentName}
   # → 確認輸出 { "written": true, "version": {N+1} }

   # Step B：更新其他欄位
   node .claude/scripts/queue-update.js {ComponentName} --set \
     '{"status":"built","totalIterations":{N+1}}'
   ```

5. 執行 diff.js 生成本次的 changed-zones.json（供 SA-3 使用）：
   ```bash
   node .claude/scripts/diff.js {ComponentName}
   # → 自動寫入 .claude/workspace/{ProjectName}/{ComponentName}/changed-zones.json
   # → 確認輸出包含 changedZones 陣列（不能是空的）
   ```

   如果 diff.js 輸出 `"changedZones": []`，代表 ReviewZone id 沒有對上，
   需要確認 TSX 裡的 `<ReviewZone id="...">` 標記是否存在。

---

## 評論處理規則

| 評論內容 | 處理方式 |
|---|---|
| 文字標籤修改 | Edit 對應的 JSX 字串 |
| 顏色 / 間距調整 | Edit 對應的 Tailwind class |
| 新增欄位 / 功能 | 在對應 zone 內插入，不重寫整個 component |
| 刪除功能 | 只刪除指定區塊，不動周邊 |
| 互動邏輯（handler）| 只改 handler function，不動 JSX 結構 |

---

## 輸出規範

- 修改 `projects/{ProjectName}/components/pending/{ComponentName}/{ComponentName}.tsx`（用 Edit）
- 新增 `.claude/workspace/{ProjectName}/{ComponentName}/versions/v{N+1}.tsx`（用 Write）
- 更新 `.claude/workspace/{ProjectName}/{ComponentName}/comments.json`（resolved 評論）
- 更新 `.claude/workspace/{ProjectName}/{ComponentName}/queue-entry.json`
- 生成 `.claude/workspace/{ProjectName}/{ComponentName}/changed-zones.json`

---

## 回傳給 Orchestrator（< 150 字）

```
✅ {ComponentName} v{N+1} 疊代完成
- 處理評論：{已處理數}/{總數} 條
- 修改區塊：{changedZones}
- 修改函式：{changedFunctions}
- Changed-zones.json 已生成（供 SA-3 diff 掃描）
- 下一步：SA-3 測試
```
