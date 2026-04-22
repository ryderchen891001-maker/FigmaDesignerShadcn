#!/usr/bin/env node
/**
 * fetch-threads.js
 * 抓 Vercel Toolbar threads，預設只回傳 open（未 resolved）的
 *
 * 用法：
 *   node .claude/scripts/fetch-threads.js
 *   node .claude/scripts/fetch-threads.js --all          # 包含已 resolved
 *   node .claude/scripts/fetch-threads.js --project PlanA
 *
 * 輸出（stdout）：JSON array
 *   [{ id, text, resolved, zone, href, attachmentUrl, figmaUrl, timestamp }, ...]
 */

const { execSync } = require('child_process')
const path = require('path')
const fs = require('fs')

// ── Config ────────────────────────────────────────────────────────────────────
const ROOT = path.resolve(__dirname, '../..')
const VERCEL_TEAM_ID = 'team_1Ji8DksAu90LooEd5b32TT1t'
const VERCEL_PROJECT_ID = 'prj_EYFx92aDPhJNlVOIeSbqzmmHUDSt'

// ── Args ──────────────────────────────────────────────────────────────────────
const args = process.argv.slice(2)
const showAll = args.includes('--all')

// ── Fetch ─────────────────────────────────────────────────────────────────────
let raw
try {
  raw = execSync(
    `vercel api "/v1/toolbar/threads?teamId=${VERCEL_TEAM_ID}&projectId=${VERCEL_PROJECT_ID}"`,
    { encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'] }
  )
} catch (e) {
  process.stderr.write('fetch-threads: vercel api failed\n' + e.message + '\n')
  process.exit(1)
}

let data
try {
  data = JSON.parse(raw)
} catch (e) {
  process.stderr.write('fetch-threads: JSON parse failed\n')
  process.exit(1)
}

const threads = (data.threads || [])

// ── Filter & Map ──────────────────────────────────────────────────────────────
const result = threads
  .filter(t => showAll || !t.resolved)
  .map(t => {
    const msg = t.messages?.[0] || {}
    const attachments = msg.attachments || []

    // Extract figmaUrl from message body links
    let figmaUrl = null
    for (const block of (msg.body || [])) {
      for (const child of (block.children || [])) {
        if (child.url?.includes('figma.com')) {
          figmaUrl = child.url
          break
        }
      }
      if (figmaUrl) break
    }

    return {
      id: t.id,
      resolved: t.resolved || false,
      text: msg.text || '',
      timestamp: msg.timestamp ? new Date(msg.timestamp).toISOString() : null,
      author: msg.author?.username || null,
      href: t.context?.href || null,
      selector: t.context?.selector || null,
      figmaUrl: figmaUrl || null,
      attachmentUrl: attachments[0]?.url || null,
    }
  })

process.stdout.write(JSON.stringify(result, null, 2) + '\n')
