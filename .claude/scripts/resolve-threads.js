#!/usr/bin/env node
/**
 * resolve-threads.js
 * 批次 resolve Vercel Toolbar threads + 回覆訊息
 *
 * 用法：
 *   node .claude/scripts/resolve-threads.js <threadId> [threadId...]
 *   node .claude/scripts/resolve-threads.js <threadId> --msg "自訂回覆訊息"
 *
 * 範例：
 *   node .claude/scripts/resolve-threads.js abc123 def456
 *   node .claude/scripts/resolve-threads.js abc123 --msg "✅ 已在 v3 修正"
 *
 * 輸出（stdout）：JSON array，每筆含 { id, resolved, replied, error }
 */

const { execSync } = require('child_process')

// ── Config ────────────────────────────────────────────────────────────────────
const VERCEL_TEAM_ID = 'team_1Ji8DksAu90LooEd5b32TT1t'
const VERCEL_PROJECT_ID = 'prj_eRnFk1onOZWmwaxXcPczc5MTDKDl'

// ── Args ──────────────────────────────────────────────────────────────────────
const args = process.argv.slice(2)
const msgIdx = args.indexOf('--msg')
const replyMsg = msgIdx !== -1 ? args[msgIdx + 1] : '✅ 已修正'
const threadIds = args.filter((a, i) => a !== '--msg' && i !== msgIdx + 1)

if (threadIds.length === 0) {
  process.stderr.write('Usage: resolve-threads.js <threadId> [threadId...] [--msg "message"]\n')
  process.exit(1)
}

// ── Helper ────────────────────────────────────────────────────────────────────
function apiCall(path, method, body) {
  const bodyFlag = body ? `-d '${JSON.stringify(body).replace(/'/g, "\\'")}'` : ''
  try {
    const out = execSync(
      `vercel api "${path}?teamId=${VERCEL_TEAM_ID}" --method ${method} ${bodyFlag}`,
      { encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'] }
    )
    return { ok: true, body: out }
  } catch (e) {
    return { ok: false, error: e.message }
  }
}

// ── Process each thread ───────────────────────────────────────────────────────
const results = []

for (const id of threadIds) {
  const entry = { id, resolved: false, replied: false, error: null }

  // 1. Mark resolved
  const resolveRes = apiCall(`/v1/toolbar/threads/${id}`, 'PATCH', { resolved: true })
  if (!resolveRes.ok) {
    entry.error = `resolve failed: ${resolveRes.error}`
    results.push(entry)
    continue
  }
  entry.resolved = true

  // 2. Reply
  const replyRes = apiCall(`/v1/toolbar/threads/${id}/messages`, 'POST', { text: replyMsg })
  if (!replyRes.ok) {
    entry.error = `reply failed: ${replyRes.error}`
  } else {
    entry.replied = true
  }

  results.push(entry)
}

process.stdout.write(JSON.stringify(results, null, 2) + '\n')

// Exit 1 if any failed
if (results.some(r => r.error)) process.exit(1)
