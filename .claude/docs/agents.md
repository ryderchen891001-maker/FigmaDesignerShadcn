# Subagent 職責說明

| 代號 | Agent | 職責 | 觸發時機 | 輸入 | 輸出 |
|---|---|---|---|---|---|
| SA-1 | `figma-reader` | 讀設計稿（三段式）、偵測 Slot、提取 tokens | 給 Figma URL | Figma URL | design-spec.json |
| SA-2 | `component-builder` | 生成 Next.js component + 評論層、查詢原子庫 | SA-1 完成後 | design-spec.json + comments.json | .tsx + library-candidates.json |
| SA-3 | `component-tester` | 四層測試 + 自動修一次 | SA-2 完成後 | .tsx + design-spec.json | test-report.json |
| SA-4 | `review-server` | 部署 Vercel + 同步外部留言 | SA-3 通過後 | pending/ component | preview URL + comments.json |
| SA-5 | `archiver` | git tag + 移檔 + 更新 manifest | 說「封存」 | approved component | archived/ + manifest.json |
| SA-6 | `token-extractor` | 提取 design tokens，生成 styles.css | 新 component 第一次 build | design-spec.json | tokens.json + styles.css |
| SA-7 | `diff-checker` | 列出版本差異，確認評論都被處理 | 疊代後自動 | v{N-1} vs v{N} | 差異報告 |
| SA-8 | `storybook-gen` | 生成所有 variant 的 Storybook stories | approved 前 | .tsx + .types.ts | .stories.tsx |
| SA-9 | `backend-connector` | 生成 API route + Zod schema + DB model | 所有 component 封存後 | archived/ | app/api/ + lib/schemas/ |
| SA-10 | `library-manager` | 管理原子庫、合併 candidates、處理更新連鎖 | 平行 build 完成後 | library-candidates.json | library.json |
| SA-11 | `figma-tagger` | 生成 figma-annotation.json，引導 Plugin 標記 | SA-5 封存後 | manifest.json | figma-annotation.json |

---

## SA-1 Token 節省規則（強制）

三段式讀取：
1. `get_variable_defs` → 顏色 token
2. `get_metadata` → 結構樹 + 偵測 slot
3. `get_design_context` → 完整樣式（只取需要欄位）

回傳給 Orchestrator 只能包含：design-spec.json 路徑、componentName、figmaNodeId、摘要（< 200 字）。
**禁止把原始 MCP JSON 帶進回傳訊息。**

---

## SA-2 模板使用規則

- 全新 build → 讀 `.claude/templates/sa2-new.md`
- 疊代 → 讀 `.claude/templates/sa2-revision.md`

每次 build 結束必須：
```bash
node .claude/scripts/queue-update.js {ComponentName} version {N}
node .claude/scripts/snapshot.js {ComponentName}
node .claude/scripts/diff.js {ComponentName}   # 疊代時才需要
```

---

## SA-3 Diff 掃描規則

讀 `.claude/templates/sa3-diff.md`。
先讀 `changed-zones.json`，按規模決定掃描範圍。
`changed-zones.json` 不存在 → fallback 全檔模式。

---

## SA-4 Thread 同步流程

```bash
node .claude/scripts/fetch-threads.js > threads.json
# 按 href URL 或留言前綴 [ComponentName] 分流到對應 component
# 寫入 comments.json（CRDT 格式）
# 部署後：
node .claude/scripts/resolve-threads.js {id1} {id2} --msg "✅ 已在 v{N} 修正"
```

---

## SA-5 封存順序

1. 確認 status = approved
2. git commit + git tag `comp/{Name}-v{N}`
3. 移動 pending/ → archived/
4. 複製 design-spec.json、comments.json 到 archived/
5. 更新 manifest.json
6. 更新 queue-entry → archived
7. 呼叫 SA-11
8. 同步 figma-annotation.json 到 public/
9. 重新部署 Vercel

---

## 所有 Agent 共同禁止事項

- SA-1 禁止把原始 MCP JSON 帶進回傳訊息
- 不能刪除 `archived/` 裡的任何檔案
- 不能修改 `design-spec.json`
- 不能自行決定封存（等使用者明確說）
- 不能把 `needs-human` 自動推進下一個流程
- 不能直接 push 到 main branch
- SA-3 自動修正只能執行一次
- 不能覆蓋 `versions/` 歷史快照
- 不能直接寫 `library.json`（只有 SA-10）
- 不能直接寫全局 `queue.json`（只有 Orchestrator）
- 禁止用 Python / curl 呼叫 MCP 工具
- 禁止連接 localhost / 127.0.0.1
