#!/usr/bin/env node
/**
 * queue-update.js
 * 更新 queue-entry.json 的指定欄位（不覆蓋整個檔案）
 *
 * 用法：
 *   node .claude/scripts/queue-update.js <ComponentName> <field> <value>
 *   node .claude/scripts/queue-update.js <ComponentName> --set '{"status":"in-review","previewUrl":"https://..."}'
 *
 * 範例（單一欄位）：
 *   node .claude/scripts/queue-update.js ClassManagement status in-review
 *   node .claude/scripts/queue-update.js ClassManagement version 3
 *   node .claude/scripts/queue-update.js ClassManagement testPassed true
 *
 * 範例（批次欄位）：
 *   node .claude/scripts/queue-update.js ClassManagement --set '{"status":"test-passed","testPassed":true,"autoFixApplied":false}'
 *
 * 輸出（stdout）：更新後的 queue-entry.json 內容
 */

const fs = require('fs')
const path = require('path')

// ── Config ────────────────────────────────────────────────────────────────────
const ROOT = path.resolve(__dirname, '../..')

// ── Args ──────────────────────────────────────────────────────────────────────
const args = process.argv.slice(2)

// --project override
const projectIdx = args.indexOf('--project')
const project = projectIdx !== -1 ? args[projectIdx + 1] : null

// --set batch mode
const setIdx = args.indexOf('--set')
const setBatch = setIdx !== -1 ? args[setIdx + 1] : null

// Positional: ComponentName [field] [value]
const skipIndices = new Set([
  ...(projectIdx !== -1 ? [projectIdx, projectIdx + 1] : []),
  ...(setIdx !== -1 ? [setIdx, setIdx + 1] : []),
])
const positional = args.filter((a, i) => !a.startsWith('--') && !skipIndices.has(i))

const componentName = positional[0]
const field = positional[1]
const rawValue = positional[2]

if (!componentName) {
  process.stderr.write('Usage: queue-update.js <ComponentName> <field> <value>\n')
  process.stderr.write('       queue-update.js <ComponentName> --set \'{"field":"value"}\'\n')
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
  return 'PlanA'
}

const projectName = resolveProject()

// ── Read queue entry ──────────────────────────────────────────────────────────
const queuePath = path.join(ROOT, '.claude', 'workspace', projectName, componentName, 'queue-entry.json')

if (!fs.existsSync(queuePath)) {
  process.stderr.write(`queue-update: not found: ${queuePath}\n`)
  process.exit(1)
}

const entry = JSON.parse(fs.readFileSync(queuePath, 'utf8'))

// ── Parse value ───────────────────────────────────────────────────────────────
function parseValue(v) {
  if (v === 'true') return true
  if (v === 'false') return false
  if (v === 'null') return null
  const n = Number(v)
  if (!isNaN(n) && v !== '') return n
  return v
}

// ── Apply updates ─────────────────────────────────────────────────────────────
if (setBatch) {
  // Batch mode: --set '{"field":"value",...}'
  let updates
  try {
    updates = JSON.parse(setBatch)
  } catch (e) {
    process.stderr.write('queue-update: invalid JSON in --set\n')
    process.exit(1)
  }
  Object.assign(entry, updates)
} else if (field) {
  // Single field mode
  entry[field] = parseValue(rawValue)
} else {
  process.stderr.write('queue-update: specify <field> <value> or --set\n')
  process.exit(1)
}

// Always update updatedAt
entry.updatedAt = new Date().toISOString()

// ── Write back ────────────────────────────────────────────────────────────────
fs.writeFileSync(queuePath, JSON.stringify(entry, null, 2) + '\n', 'utf8')

process.stdout.write(JSON.stringify(entry, null, 2) + '\n')
