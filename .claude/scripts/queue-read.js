#!/usr/bin/env node
/**
 * queue-read.js
 * 讀取指定 component 的 queue-entry.json
 *
 * 用法：
 *   node .claude/scripts/queue-read.js <ComponentName>
 *   node .claude/scripts/queue-read.js <ComponentName> --project PlanA
 *
 * 範例：
 *   node .claude/scripts/queue-read.js ClassManagement
 *
 * 輸出（stdout）：queue-entry.json 內容（pretty JSON）
 */

const fs = require('fs')
const path = require('path')

// ── Config ────────────────────────────────────────────────────────────────────
const ROOT = path.resolve(__dirname, '../..')

// ── Args ──────────────────────────────────────────────────────────────────────
const args = process.argv.slice(2)
const projectIdx = args.indexOf('--project')
const project = projectIdx !== -1 ? args[projectIdx + 1] : null
const skipIndices = new Set(projectIdx !== -1 ? [projectIdx, projectIdx + 1] : [])
const componentName = args.find((a, i) => !a.startsWith('--') && !skipIndices.has(i))

if (!componentName) {
  process.stderr.write('Usage: queue-read.js <ComponentName> [--project ProjectName]\n')
  process.exit(1)
}

// ── Resolve project ───────────────────────────────────────────────────────────
function resolveProject() {
  if (project) return project
  const activeFile = path.join(ROOT, 'active-project.json')
  if (fs.existsSync(activeFile)) {
    const active = JSON.parse(fs.readFileSync(activeFile, 'utf8'))
    return active.name
  }
  return 'PlanA' // fallback
}

const projectName = resolveProject()

// ── Read queue entry ──────────────────────────────────────────────────────────
const queuePath = path.join(ROOT, '.claude', 'workspace', projectName, componentName, 'queue-entry.json')

if (!fs.existsSync(queuePath)) {
  process.stderr.write(`queue-read: not found: ${queuePath}\n`)
  process.exit(1)
}

const entry = JSON.parse(fs.readFileSync(queuePath, 'utf8'))
process.stdout.write(JSON.stringify(entry, null, 2) + '\n')
