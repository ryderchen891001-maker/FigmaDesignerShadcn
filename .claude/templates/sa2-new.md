# SA-2 新建模式指令（New Component Mode — shadcn-first）

> 此模板用於 SA-2 從 design-spec.json 全新生成一個 component。
> **shadcn-first 原則**：能用 shadcn 的一律 import，不重新造輪子。

---

## 輸入檢查清單

- [ ] `design-spec.json` — 完整設計規格
- [ ] `components/library/library.json` — 自訂原子庫
- [ ] `.claude/docs/shadcn-components.md` — **必讀，先查 shadcn 對照表**
- [ ] `queue-entry.json` — 確認 status 為 `spec-ready`

---

## 執行流程

### Step 1 — 讀設計規格

```bash
Read .claude/workspace/{ProjectName}/{ComponentName}/design-spec.json
```

從設計稿分析：
- 每個 UI 區塊（zone）的視覺結構
- 互動行為（表單、Tab、Dialog、下拉等）
- 顏色、間距、字體（對應 Tailwind class）

### Step 2 — shadcn 對照（最重要）

```bash
Read .claude/docs/shadcn-components.md
```

**對照設計稿的每個 UI 區塊，先查是否有對應的 shadcn 元件：**

```
每個區塊問自己：
  這是 Button？→ import Button
  這是 Dialog？→ import Dialog
  這是 Table？→ import Table
  ...
  都沒有？→ 自己寫
```

記錄決策（寫入頂部 comment）：
```tsx
// shadcnUsed: Dialog, Table, Button, Badge, Input, Select
// customBuilt: TimeCombobox（shadcn 無此元件）
```

### Step 3 — 自訂原子庫檢查（只針對 customBuilt 部分）

```bash
Read components/library/library.json
```

shadcn 元件 → 直接跳過，不查原子庫。
只有 `customBuilt` 的部分才進行相似度計算：
- ≥ 90% → 暫停，等使用者決定
- < 90% → 繼續 build

### Step 4 — 生成 Component

**Import 規範**：
```tsx
// shadcn 元件：
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

// 自訂原子庫：
import { TimeCombobox } from '@/components/library/atoms/TimeCombobox'
```

**樣式規範**：
- shadcn 元件用 `className` prop 覆蓋 Tailwind class（不改 components/ui/ 裡的源碼）
- 自訂部分用 Tailwind CSS class（禁止 inline style、禁止 hex）

**檔案頂部必須有生成註解**：
```tsx
// figmaNodeId: 565:10264
// figmaUrl: https://figma.com/design/...
// generatedAt: 2026-04-22T14:23:00Z
// version: 1
// status: pending
// shadcnUsed: Dialog, Table, Button, Badge
// customBuilt: TimeCombobox
// libraryDeps: { TimeCombobox: "v1" }
```

**評論層**：
```tsx
const IS_REVIEW = process.env.NEXT_PUBLIC_REVIEW_MODE === 'true'
{IS_REVIEW && <ReviewOverlay componentName="{ComponentName}" />}
```

### Step 5 — 建立版本快照

```bash
node .claude/scripts/queue-update.js {ComponentName} version 1
node .claude/scripts/snapshot.js {ComponentName}
# → 確認 { "written": true, "version": 1 }
```

### Step 6 — 寫入 library-candidates.json（只記錄 customBuilt）

```json
{
  "componentName": "{ComponentName}",
  "version": 1,
  "generatedAt": "{ISO timestamp}",
  "shadcnUsed": ["Dialog", "Table", "Button"],
  "candidates": [
    {
      "atomName": "TimeCombobox",
      "similarity": 0.0,
      "autoApprove": false,
      "reason": "自訂業務元件，shadcn 無對應",
      "sourceZone": "time-picker"
    }
  ]
}
```

### Step 7 — 更新 queue-entry

```bash
node .claude/scripts/queue-update.js {ComponentName} --set \
  '{"status":"built","version":1,"totalIterations":1}'
```

---

## 輸出規範

- 新建 `projects/{ProjectName}/components/pending/{ComponentName}/{ComponentName}.tsx`
- 新建 `projects/{ProjectName}/components/pending/{ComponentName}/{ComponentName}.types.ts`
- 新建 `.claude/workspace/{ProjectName}/{ComponentName}/versions/v1.tsx`
- 新建 `.claude/workspace/{ProjectName}/{ComponentName}/library-candidates.json`
- 更新 `.claude/workspace/{ProjectName}/{ComponentName}/queue-entry.json`

---

## 回傳給 Orchestrator（< 150 字）

```
✅ {ComponentName} v1 生成完成（shadcn-first）
- shadcn import：{元件列表}
- 自訂元件：{customBuilt 列表 或 "無"}
- 原子庫候選：{N} 個
- 預估省 token：~{%}%（vs 全自訂）
- 下一步：SA-3 測試
```

> 如果有相似度 ≥ 90% 的自訂原子，改為輸出比對卡片並暫停，等使用者決定。
