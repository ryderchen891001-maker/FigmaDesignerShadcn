#!/usr/bin/env node
/**
 * snapshot.js
 * 把 pending/ 的最新 TSX 快照到 versions/v{N}.tsx
 *
 * 用法：
 *   node .claude/scripts/snapshot.js <ComponentName>
 *   node .claude/scripts/snapshot.js <ComponentName> --project PlanA
 *
 * 邏輯：
 *   1. 讀 queue-entry.json 取得當前 version 號
 *   2. 從 pending/{ComponentName}/{ComponentName}.tsx 複製到
 *      .claude/workspace/{ProjectName}/{ComponentName}/versions/v{N}.tsx
 *   3. 如果 v{N}.tsx 已存在且內容相同，跳過（idempotent）
 *   4. 如果 v{N}.tsx 已存在但內容不同，用 v{N}-{timestamp}.tsx 避免覆蓋
 *
 * 輸出（stdout）：JSON
 *   { "written": true, "path": "...versions/v3.tsx", "version": 3, "skipped": false }
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
  process.stderr.write('Usage: snapshot.js <ComponentName> [--project ProjectName]\n')
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

// ── Read project.json for paths ───────────────────────────────────────────────
function resolvePaths() {
  const projectFile = path.join(ROOT, 'projects', projectName, 'project.json')
  if (fs.existsSync(projectFile)) {
    const proj = JSON.parse(fs.readFileSync(projectFile, 'utf8'))
    return {
      pendingDir: path.join(ROOT, proj.pendingDir || `projects/${projectName}/components/pending`),
    }
  }
  return {
    pendingDir: path.join(ROOT, 'projects', projectName, 'components', 'pending'),
  }
}

const { pendingDir } = resolvePaths()

// ── Read queue-entry.json ─────────────────────────────────────────────────────
const queuePath = path.join(ROOT, '.claude', 'workspace', projectName, componentName, 'queue-entry.json')
if (!fs.existsSync(queuePath)) {
  process.stderr.write(`snapshot: queue-entry.json not found: ${queuePath}\n`)
  process.exit(1)
}
const entry = JSON.parse(fs.readFileSync(queuePath, 'utf8'))
const version = entry.version || 1

// ── Source: pending TSX ───────────────────────────────────────────────────────
const sourcePath = path.join(pendingDir, componentName, `${componentName}.tsx`)
if (!fs.existsSync(sourcePath)) {
  process.stderr.write(`snapshot: source TSX not found: ${sourcePath}\n`)
  process.exit(1)
}
const sourceContent = fs.readFileSync(sourcePath, 'utf8')

// ── Destination: versions/v{N}.tsx ────────────────────────────────────────────
const versionsDir = path.join(ROOT, '.claude', 'workspace', projectName, componentName, 'versions')
if (!fs.existsSync(versionsDir)) {
  fs.mkdirSync(versionsDir, { recursive: true })
}

const targetPath = path.join(versionsDir, `v${version}.tsx`)

// ── Idempotency check ─────────────────────────────────────────────────────────
if (fs.existsSync(targetPath)) {
  const existingContent = fs.readFileSync(targetPath, 'utf8')
  if (existingContent === sourceContent) {
    const result = { written: false, path: targetPath, version, skipped: true, reason: 'identical' }
    process.stdout.write(JSON.stringify(result, null, 2) + '\n')
    process.stderr.write(`snapshot: v${version}.tsx already up-to-date, skipped\n`)
    process.exit(0)
  }
  // Content differs — write with timestamp suffix to avoid silent overwrite
  const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
  const conflictPath = path.join(versionsDir, `v${version}-${ts}.tsx`)
  fs.writeFileSync(conflictPath, sourceContent, 'utf8')
  const result = {
    written: true,
    path: conflictPath,
    version,
    skipped: false,
    conflict: true,
    reason: `v${version}.tsx already exists with different content — wrote to conflict path`
  }
  process.stdout.write(JSON.stringify(result, null, 2) + '\n')
  process.stderr.write(`snapshot: conflict — wrote to ${conflictPath}\n`)
  process.exit(0)
}

// ── Write snapshot ────────────────────────────────────────────────────────────
fs.writeFileSync(targetPath, sourceContent, 'utf8')

const result = { written: true, path: targetPath, version, skipped: false }
process.stdout.write(JSON.stringify(result, null, 2) + '\n')
process.stderr.write(`snapshot: ✓ v${version}.tsx written (${sourceContent.split('\n').length} lines)\n`)
