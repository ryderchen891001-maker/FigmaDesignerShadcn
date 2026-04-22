# 工作流程說明

## 完整流程

```
1. 給 Figma URL（可同時給多個）
   SA-1 平行讀設計稿，各自建立 workspace + queue-entry.json
   queue: todo → spec-ready

2. 生成 component（可平行）
   Orchestrator 偵測多個 spec-ready → 詢問是否平行
   SA-2 各自 build，查詢原子庫，寫 library-candidates.json
   SA-2 完成後 → snapshot.js → diff.js → 呼叫 SA-10 合併 library-candidates
   queue: spec-ready → built

3. 自動測試（你不用做任何事）
   SA-3 讀 changed-zones.json → diff 掃描或全檔掃描
   queue: built → testing → test-passed（或 needs-human）

4. 部署外網
   SA-4 → deploy.js → 回傳外網 URL
   queue: test-passed → in-review

5. 審查
   你和設計師留評論 → SA-4 用 fetch-threads.js 同步到 comments.json

6. 疊代（有評論要改時）
   純文字改動 → quick-patch.js → 直接 SA-4 部署
   邏輯/結構改動 → SA-2（讀 sa2-revision.md 模板）→ SA-3（讀 sa3-diff.md 模板）→ SA-4
   queue: needs-revision → built → ... → in-review

7. 封存
   你：「封存」
   SA-8 → Storybook stories（選用）
   SA-5 → git tag + 移檔 + manifest 更新
   SA-11 → figma-annotation.json
   queue: approved → archived

8. 後端（所有 component 封存完成後）
   你：「開始接後端」
   SA-9 → API + Zod schema + DB model
```

---

## Queue 狀態機

```
todo → spec-ready → built → testing → auto-fixing → test-passed
                                    ↘ needs-human
test-passed → in-review → needs-revision → built（循環）
                        → approved → archived

失敗路徑：needs-human → 人工決定 → built 或放棄
```

---

## 平行執行規則

觸發：2 個以上 `spec-ready` 的 component。
Orchestrator 詢問確認後，**同一訊息發出多個 Agent tool call**（真平行）。

平行安全：
- queue-entry.json 各自獨立 → 零衝突
- library.json SA-2 不直接寫，只寫 library-candidates.json
- manifest.json 平行期間不寫，封存時才由 SA-5 更新

平行完成後 → Orchestrator 統一呼叫 SA-10 合併所有 library-candidates。

---

## Token 優化策略

| 情境 | 做法 |
|---|---|
| 全新 build | SA-2 讀 `.claude/templates/sa2-new.md` |
| 疊代（有評論） | SA-2 讀 `.claude/templates/sa2-revision.md`，只讀 diff + 評論 |
| 純文字改動 | `quick-patch.js`，跳過 SA-2/SA-3 |
| SA-3 測試 | 讀 `changed-zones.json`，只掃改動區塊 |
| Orchestrator 看全局 | `queue-aggregate.js --json` |

SA-3 規模判斷：
- `addedLines + removedLines < 50` → 只測 changedZones（層一 + 層四）
- `50–200 行` → 測 changedZones（四層）
- `> 200 行` → 全檔模式

---

## 多專案管理

```bash
# 讀當前專案
cat active-project.json

# 切換專案
# → 更新 active-project.json → { "name": "ProjectB", "projectFile": "..." }
```

路徑從 `project.json` 動態讀取，禁止 hardcode 專案名稱。

---

## 原子庫規則

SA-2 每次 build 前：
1. 讀 `library.json`
2. figmaComponents 內的 → autoApprove，跳過相似度
3. 不在其中的 → 相似度計算
   - ≥ 90% → 暫停，等使用者決定
   - < 90% → build 完後寫 library-candidates.json

Non-breaking 更新 → SA-10 自動同步 + SA-3 回歸
Breaking 更新 → SA-10 暫停，列受影響清單問使用者
