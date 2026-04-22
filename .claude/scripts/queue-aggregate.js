#!/usr/bin/env node
/**
 * queue-aggregate.js
 * 掃描所有 queue-entry.json，輸出全局狀態總覽
 *
 * 用法：
 *   node .claude/scripts/queue-aggregate.js
 *   node .claude/scripts/queue-aggregate.js --project PlanA
 *   node .claude/scripts/queue-aggregate.js --status in-review
 *   node .claude/scripts/queue-aggregate.js --json
 *
 * 預設輸出（人類可讀）：
 *   ComponentName       status        v  pendingComments  updatedAt
 *   ─────────────────── ───────────── ── ──────────────── ─────────────────────
 *   ClassManagement     archived      2  0                2026-04-22T05:57:01Z
 *   TutorOverview       in-review     1  3                2026-04-22T08:12:00Z
 *
 * --json 輸出：完整 JSON 陣列
 */

const fs = require('fs')
const path = require('path')

// ── Config ────────────────────────────────────────────────────────────────────
const ROOT = path.resolve(__dirname, '../..')

// ── Args ──────────────────────────────────────────────────────────────────────
const args = process.argv.slice(2)

const projectIdx = args.indexOf('--project')
const project = projectIdx !== -1 ? args[projectIdx + 1] : null

const statusIdx = args.indexOf('--status')
const filterStatus = statusIdx !== -1 ? args[statusIdx + 1] : null

const jsonMode = args.includes('--json')

// ── Resolve project ───────────────────────────────────────────────────────────
function resolveProject() {
  if (project) return project
  const activeFile = path.join(ROOT, 'active-project.json')
  if (fs.existsSync(activeFile)) {
    const active = JSON.parse(fs.readFileSync(activeFile, 'utf8'))
    return active.name
  }
  return null // null = scan all projects
}

const targetProject = resolveProject()

// ── Scan all queue-entry.json files ──────────────────────────────────────────
function scanWorkspace() {
  const workspaceRoot = path.join(ROOT, '.claude', 'workspace')
  if (!fs.existsSync(workspaceRoot)) return []

  const entries = []

  const projects = targetProject
    ? [targetProject]
    : fs.readdirSync(workspaceRoot).filter(f =>
        fs.statSync(path.join(workspaceRoot, f)).isDirectory()
      )

  for (const proj of projects) {
    const projDir = path.join(workspaceRoot, proj)
    if (!fs.existsSync(projDir)) continue

    const components = fs.readdirSync(projDir).filter(f =>
      fs.statSync(path.join(projDir, f)).isDirectory()
    )

    for (const comp of components) {
      const queuePath = path.join(projDir, comp, 'queue-entry.json')
      if (!fs.existsSync(queuePath)) continue

      try {
        const entry = JSON.parse(fs.readFileSync(queuePath, 'utf8'))
        entries.push({ project: proj, ...entry })
      } catch (e) {
        process.stderr.write(`queue-aggregate: failed to parse ${queuePath}: ${e.message}\n`)
      }
    }
  }

  return entries
}

let entries = scanWorkspace()

// ── Filter by status ──────────────────────────────────────────────────────────
if (filterStatus) {
  entries = entries.filter(e => e.status === filterStatus)
}

// Sort: by status priority, then by updatedAt desc
const STATUS_ORDER = {
  'needs-human': 0,
  'needs-revision': 1,
  'in-review': 2,
  'test-passed': 3,
  'auto-fixing': 4,
  'testing': 5,
  'built': 6,
  'spec-ready': 7,
  'todo': 8,
  'approved': 9,
  'archived': 10,
}

entries.sort((a, b) => {
  const sa = STATUS_ORDER[a.status] ?? 99
  const sb = STATUS_ORDER[b.status] ?? 99
  if (sa !== sb) return sa - sb
  return (b.updatedAt || '').localeCompare(a.updatedAt || '')
})

// ── Output ────────────────────────────────────────────────────────────────────
if (jsonMode) {
  process.stdout.write(JSON.stringify(entries, null, 2) + '\n')
  process.exit(0)
}

// Human-readable table
const STATUS_EMOJI = {
  'todo': '⏳',
  'spec-ready': '📋',
  'built': '🔨',
  'testing': '🧪',
  'auto-fixing': '🔧',
  'test-passed': '✅',
  'in-review': '👀',
  'needs-revision': '📝',
  'needs-human': '🚨',
  'approved': '👍',
  'archived': '📦',
}

if (entries.length === 0) {
  process.stdout.write('(no components found)\n')
  process.exit(0)
}

// Column widths
const COL = {
  project: Math.max(7, ...entries.map(e => (e.project || '').length)),
  name: Math.max(9, ...entries.map(e => (e.componentName || '').length)),
  status: 14,
  version: 3,
  comments: 8,
  updated: 20,
}

function pad(str, len) {
  return String(str || '').padEnd(len).slice(0, len)
}

const header = [
  pad('Project', COL.project),
  pad('Component', COL.name),
  pad('Status', COL.status),
  pad('v', COL.version),
  pad('Cmts', COL.comments),
  pad('Updated', COL.updated),
].join('  ')

const divider = [
  '─'.repeat(COL.project),
  '─'.repeat(COL.name),
  '─'.repeat(COL.status),
  '─'.repeat(COL.version),
  '─'.repeat(COL.comments),
  '─'.repeat(COL.updated),
].join('  ')

process.stdout.write(header + '\n')
process.stdout.write(divider + '\n')

for (const e of entries) {
  const emoji = STATUS_EMOJI[e.status] || ' '
  const statusStr = `${emoji} ${e.status}`
  const updatedShort = (e.updatedAt || '').slice(0, 19).replace('T', ' ')
  const row = [
    pad(e.project, COL.project),
    pad(e.componentName, COL.name),
    pad(statusStr, COL.status),
    pad(e.version || 1, COL.version),
    pad(e.pendingComments || 0, COL.comments),
    pad(updatedShort, COL.updated),
  ].join('  ')
  process.stdout.write(row + '\n')
}

process.stdout.write('\n')
process.stdout.write(`Total: ${entries.length} component(s)`)
if (filterStatus) process.stdout.write(` [filtered: ${filterStatus}]`)
process.stdout.write('\n')
