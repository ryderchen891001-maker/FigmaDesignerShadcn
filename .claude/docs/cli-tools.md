# CLI 工具手冊

腳本位置：`.claude/scripts/`，用 `node` 執行，不需額外安裝套件。
（與 FigmaDesigner 相同，完整說明見 FigmaDesigner 的 cli-tools.md）

---

## 快速參考

```bash
# 健康診斷（每次 session 開始先跑）
node .claude/scripts/health-check.js [--fix]

# 全局狀態總覽
node .claude/scripts/queue-aggregate.js [--status in-review] [--json]

# 純文字替換（跳過 SA-2/SA-3）
node .claude/scripts/quick-patch.js {Comp} --find "舊" --replace "新" [--dry-run]

# 版本快照（SA-2 每次 build 後必須呼叫）
node .claude/scripts/queue-update.js {Comp} version {N}
node .claude/scripts/snapshot.js {Comp}

# 生成 diff + changed-zones.json（疊代後呼叫）
node .claude/scripts/diff.js {Comp}

# Queue 操作
node .claude/scripts/queue-read.js {Comp}
node .claude/scripts/queue-update.js {Comp} status in-review
node .claude/scripts/queue-update.js {Comp} --set '{"status":"built","testPassed":false}'

# Vercel Toolbar 留言
node .claude/scripts/fetch-threads.js [--all]
node .claude/scripts/resolve-threads.js {id1} {id2} --msg "✅ 已在 v{N} 修正"

# 部署
node .claude/scripts/deploy.js
node .claude/scripts/deploy.js --prod

# 偵測設計稿更新（需要 FIGMA_TOKEN）
node .claude/scripts/figma-watch.js
```

---

## shadcn 專屬操作

```bash
# 安裝新的 shadcn 元件
cd C:/hand2design/figmadesignershadcn
npx shadcn@latest add {component-name}

# 查看已安裝的 shadcn 元件
ls components/ui/

# 安裝後更新 .claude/docs/shadcn-components.md 的已安裝清單
```
