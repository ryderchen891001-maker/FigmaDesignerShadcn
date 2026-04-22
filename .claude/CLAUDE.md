# FigmaDesignerShadcn — 核心規則

Claude Code 扮演 **Orchestrator** 角色。
你說話 → Claude Code 決定呼叫哪個 subagent → 管理狀態 → 推進流程。

**技術棧**：Next.js 14 + Tailwind CSS + TypeScript + **shadcn/ui**
**部署平台**：Vercel（preview + production）
**專案根目錄**：`C:/hand2design/figmadesignershadcn`

詳細文件：
- 工作流程 → `.claude/docs/workflow.md`
- Subagent 職責 → `.claude/docs/agents.md`
- CLI 工具手冊 → `.claude/docs/cli-tools.md`
- **shadcn 對照表** → `.claude/docs/shadcn-components.md` ← SA-2 每次必讀
- SA-2 新建模式 → `.claude/templates/sa2-new.md`
- SA-2 疊代模式 → `.claude/templates/sa2-revision.md`
- SA-3 Diff 掃描 → `.claude/templates/sa3-diff.md`

---

## ⭐ shadcn-first 核心原則（最高優先）

**SA-2 每次 build 前必須先查 `.claude/docs/shadcn-components.md`。**

```
能用 shadcn 的 → import，不寫新 code
shadcn 沒有的 → 才自己 build
```

| shadcn 能做 | 自己寫 |
|---|---|
| Button, Input, Dialog, Table, Badge | 業務邏輯 combobox |
| Card, Tabs, Select, Sheet | 自訂課表、甘特圖 |
| Checkbox, Switch, RadioGroup | 複雜動畫元件 |
| Calendar, Popover, Command | 特殊版面結構 |

**shadcn import 路徑**：`@/components/ui/{component}`
**自訂原子庫路徑**：`@/components/library/atoms/{Component}`

---

## 目錄結構

```
figmadesignershadcn/
├── active-project.json
├── components/
│   ├── ui/                      ← shadcn 元件（npx shadcn add 管理，不手動編輯）
│   └── library/                 ← 自訂原子庫（非 shadcn 的跨專案元件）
│       ├── atoms/
│       ├── molecules/
│       └── library.json
├── projects/{ProjectName}/
│   ├── project.json
│   ├── tokens.json
│   ├── manifest.json
│   ├── components/pending/{ComponentName}/
│   └── components/archived/{ComponentName}-v{N}/
├── .claude/
│   ├── CLAUDE.md
│   ├── docs/
│   ├── templates/
│   ├── scripts/                 ← 11 個 CLI 腳本
│   └── workspace/{ProjectName}/{ComponentName}/
│       ├── queue-entry.json
│       ├── design-spec.json
│       ├── comments.json
│       ├── test-report.json
│       ├── changed-zones.json
│       ├── library-candidates.json
│       └── versions/v{N}.tsx
└── app/api/                     ← SA-9 生成
```

---

## Queue 狀態機

```
todo → spec-ready → built → testing → test-passed → in-review
                                    ↘ needs-human   ↓
                          approved ← ─ ─ ─ ─ ─ ─  needs-revision
                             ↓
                          archived
```

### queue-entry.json 格式

```json
{
  "componentName": "ClassManagement",
  "status": "in-review",
  "figmaUrl": "https://figma.com/design/...",
  "figmaNodeId": "565:10264",
  "version": 2,
  "previewUrl": "https://xxx.vercel.app",
  "createdAt": "2026-04-22T10:00:00Z",
  "updatedAt": "2026-04-22T14:30:00Z",
  "totalIterations": 2,
  "pendingComments": 0,
  "testPassed": true,
  "autoFixApplied": false,
  "shadcnUsed": ["Dialog", "Table", "Button", "Badge"],
  "customBuilt": ["TimeCombobox"],
  "libraryDecision": null,
  "backendConnected": false,
  "connectedEndpoints": [],
  "connectedFields": [],
  "apiVersion": null
}
```

> `shadcnUsed` 和 `customBuilt` 是此專案新增的欄位，由 SA-2 在 build 後寫入。

---

## 路徑解析規則（所有 Agent 必須遵守）

從 `active-project.json` → `project.json` 動態讀取，**禁止 hardcode 專案名稱**。

---

## 快速決策樹（Orchestrator 每次進入時）

```
1. 先跑 health-check：
   node .claude/scripts/health-check.js

2. 看全局狀態：
   node .claude/scripts/queue-aggregate.js

3. 依狀態決定：
   needs-human  → 告知使用者，等決定
   needs-revision → 純文字改？quick-patch.js
                    邏輯/結構？SA-2（sa2-revision.md）→ SA-3 → SA-4
   test-passed  → SA-4 部署
   spec-ready   → SA-2（sa2-new.md，shadcn-first）
   approved     → 等使用者說「封存」
```

---

## SA-2 的 shadcn 使用記錄規範

SA-2 每次 build 完成後，必須更新 `queue-entry.json` 的這兩個欄位：

```bash
node .claude/scripts/queue-update.js {Comp} --set \
  '{"shadcnUsed":["Dialog","Table"],"customBuilt":["TimeCombobox"]}'
```

並在 `.tsx` 檔案頂部記錄：
```tsx
// shadcnUsed: Dialog, Table, Button, Badge
// customBuilt: TimeCombobox
```

---

## Component 輸出規範

### 技術規格
- React functional component + TypeScript
- **shadcn 元件 import 優先**（查 `.claude/docs/shadcn-components.md`）
- Tailwind CSS class 覆蓋 shadcn 樣式（用 `className` prop）
- 禁止 inline style、禁止 hex 顏色
- 自訂元件 import：`@/components/library/atoms/{Component}`

### 檔案頂部必要註解
```tsx
// figmaNodeId: 565:10264
// figmaUrl: https://figma.com/design/...
// generatedAt: 2026-04-22T14:23:00Z
// version: 1
// status: pending
// shadcnUsed: Dialog, Table, Button
// customBuilt: TimeCombobox
// libraryDeps: { TimeCombobox: "v1" }
```

---

## Workspace 檔案規則

| 檔案 | 誰建立 | 誰可以修改 |
|---|---|---|
| queue-entry.json | SA-1 | 各 agent 只改自己負責的欄位 |
| design-spec.json | SA-1 | 只有 SA-1（唯讀基準） |
| comments.json | SA-4 | SA-4 新增；SA-2 只更新 status/resolvedInVersion |
| test-report.json | SA-3 | 只有 SA-3 |
| changed-zones.json | diff.js | SA-3 讀取 |
| library-candidates.json | SA-2 | SA-2 寫；SA-10 讀後刪 |
| versions/v{N}.tsx | snapshot.js | 不能覆蓋舊版 |

---

## 共同禁止事項

- **不能手動編輯 `components/ui/` 裡的 shadcn 源碼**（用 `className` 覆蓋）
- SA-1 禁止把原始 MCP JSON 帶進回傳訊息
- 不能刪除 `archived/` 裡的任何檔案
- 不能修改 `design-spec.json`
- 不能自行決定封存（等使用者明確說「封存」）
- 不能把 `needs-human` 自動推進下一個流程
- 不能直接 push 到 main branch
- SA-3 自動修正只能執行一次
- 不能覆蓋 `versions/` 歷史快照
- 不能直接寫 `library.json`（只有 SA-10）
- 禁止用 Python / curl 呼叫 MCP 工具

---

## 命名規範

| 類型 | 格式 | 範例 |
|---|---|---|
| Component | PascalCase | `ClassManagement` |
| shadcn 元件 | 原始名稱 | `Dialog`, `Button` |
| Git tag | `comp/{Name}-v{N}` | `comp/ClassManagement-v2` |
| Archived 目錄 | `{Name}-v{N}` | `ClassManagement-v2` |

---

最後更新：2026-04-22
版本：v1（shadcn-first 架構）
