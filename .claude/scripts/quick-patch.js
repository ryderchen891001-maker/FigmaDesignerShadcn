#!/usr/bin/env node
/**
 * quick-patch.js
 * 純文字替換，跳過 SA-2/SA-3，直接更新版本並可部署
 *
 * 適用場景：只改字串 literal（label、placeholder、aria-label 等），
 *           不改邏輯、不改結構。
 *
 * 用法：
 *   node .claude/scripts/quick-patch.js <ComponentName> --find "舊文字" --replace "新文字"
 *   node .claude/scripts/quick-patch.js <ComponentName> --find "舊" --replace "新" --all
 *   node .claude/scripts/quick-patch.js <ComponentName> --dry-run --find "舊" --replace "新"
 *   node .claude/scripts/quick-patch.js <ComponentName> --project PlanA --find "舊" --replace "新"
 *
 * --all     替換所有符合（預設只替換第一個）
 * --dry-run 只預覽，不實際修改
 *
 * 執行後：
 *   1. 替換 pending/ 的 TSX
 *   2. 版本號 +1（queue-update）
 *   3. 快照（snapshot）
 *   4. 更新 queue-entry status → built
 *   5. 輸出摘要（不呼叫 SA-2/SA-3/SA-4）
 *
 * 輸出（stdout）：JSON
 * {
 *   "replaced": 3,
 *   "newVersion": 5,
 *   "dryRun": false,
 *   "lines": [12, 45, 78],
 *   "snapshotPath": "...versions/v5.tsx"
 * }
 */

const fs = require('fs')
const path = require('path')
const { execSync } = require('child_process')

// ── Config ────────────────────────────────────────────────────────────────────
const ROOT = path.resolve(__dirname, '../..')

// ── Args ──────────────────────────────────────────────────────────────────────
const args = process.argv.slice(2)

const projectIdx = args.indexOf('--project')
const project = projectIdx !== -1 ? args[projectIdx + 1] : null

const findIdx = args.indexOf('--find')
const findText = findIdx !== -1 ? args[findIdx + 1] : null

const replaceIdx = args.indexOf('--replace')
const replaceText = replaceIdx !== -1 ? args[replaceIdx + 1] : null

const replaceAll = args.includes('--all')
const dryRun = args.includes('--dry-run')

const skipIndices = new Set([
  ...(projectIdx !== -1 ? [projectIdx, projectIdx + 1] : []),
  ...(findIdx !== -1 ? [findIdx, findIdx + 1] : []),
  ...(replaceIdx !== -1 ? [replaceIdx, replaceIdx + 1] : []),
])
const positional = args.filter((a, i) => !a.startsWith('--') && !skipIndices.has(i))
const componentName = positional[0]

if (!componentName || !findText || replaceText === null || replaceText === undefined) {
  process.stderr.write('Usage: quick-patch.js <ComponentName> --find "text" --replace "text" [--all] [--dry-run]\n')
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

// ── Read project paths ────────────────────────────────────────────────────────
function getPendingDir() {
  const projectFile = path.join(ROOT, 'projects', projectName, 'project.json')
  if (fs.existsSync(projectFile)) {
    const proj = JSON.parse(fs.readFileSync(projectFile, 'utf8'))
    if (proj.pendingDir) return path.join(ROOT, proj.pendingDir)
  }
  return path.join(ROOT, 'projects', projectName, 'components', 'pending')
}

// ── Read queue-entry ──────────────────────────────────────────────────────────
const queuePath = path.join(ROOT, '.claude', 'workspace', projectName, componentName, 'queue-entry.json')
if (!fs.existsSync(queuePath)) {
  process.stderr.write(`quick-patch: queue-entry.json not found: ${queuePath}\n`)
  process.exit(1)
}
const entry = JSON.parse(fs.readFileSync(queuePath, 'utf8'))
const currentVersion = entry.version || 1

// ── Read TSX ──────────────────────────────────────────────────────────────────
const pendingDir = getPendingDir()
const tsxPath = path.join(pendingDir, componentName, `${componentName}.tsx`)
if (!fs.existsSync(tsxPath)) {
  process.stderr.write(`quick-patch: TSX not found: ${tsxPath}\n`)
  process.exit(1)
}

const originalContent = fs.readFileSync(tsxPath, 'utf8')

// ── Find matches ──────────────────────────────────────────────────────────────
const lines = originalContent.split('\n')
const matchedLines = []

lines.forEach((line, idx) => {
  if (line.includes(findText)) {
    matchedLines.push(idx + 1) // 1-based line numbers
  }
})

if (matchedLines.length === 0) {
  process.stderr.write(`quick-patch: "${findText}" 在 ${componentName}.tsx 中找不到\n`)
  process.exit(1)
}

// ── Preview (dry-run) ────────────────────────────────────────────────────────
if (dryRun) {
  process.stdout.write(`\n[DRY RUN] ${componentName} — "${findText}" → "${replaceText}"\n`)
  process.stdout.write(`找到 ${matchedLines.length} 處，將替換 ${replaceAll ? matchedLines.length : 1} 處\n\n`)

  const previewLines = replaceAll ? matchedLines : matchedLines.slice(0, 1)
  for (const lineNum of previewLines) {
    const before = lines[lineNum - 1]
    const after = before.split(findText).join(replaceText)
    process.stdout.write(`  行 ${lineNum}:\n`)
    process.stdout.write(`    - ${before.trim()}\n`)
    process.stdout.write(`    + ${after.trim()}\n`)
  }

  const result = {
    replaced: 0,
    wouldReplace: replaceAll ? matchedLines.length : 1,
    newVersion: currentVersion + 1,
    dryRun: true,
    lines: replaceAll ? matchedLines : matchedLines.slice(0, 1),
    snapshotPath: null,
  }
  process.stdout.write('\n' + JSON.stringify(result, null, 2) + '\n')
  process.exit(0)
}

// ── Apply replacement ─────────────────────────────────────────────────────────
let newContent
let replacedCount

if (replaceAll) {
  newContent = originalContent.split(findText).join(replaceText)
  replacedCount = matchedLines.length
} else {
  // Replace only first occurrence
  newContent = originalContent.replace(findText, replaceText)
  replacedCount = 1
}

// Update version comment in file header
const newVersion = currentVersion + 1
newContent = newContent.replace(
  /^(\/\/ version:\s*)\d+/m,
  `$1${newVersion}`
)
newContent = newContent.replace(
  /^(\/\/ generatedAt:\s*).+/m,
  `$1${new Date().toISOString()}`
)

// ── Write TSX ────────────────────────────────────────────────────────────────
fs.writeFileSync(tsxPath, newContent, 'utf8')
process.stderr.write(`quick-patch: ✓ 替換 ${replacedCount} 處\n`)

// ── Update queue version ──────────────────────────────────────────────────────
execSync(
  `node "${path.join(ROOT, '.claude', 'scripts', 'queue-update.js')}" ${componentName} version ${newVersion} --project ${projectName}`,
  { cwd: ROOT, encoding: 'utf8' }
)

// ── Snapshot ──────────────────────────────────────────────────────────────────
const snapshotOut = execSync(
  `node "${path.join(ROOT, '.claude', 'scripts', 'snapshot.js')}" ${componentName} --project ${projectName}`,
  { cwd: ROOT, encoding: 'utf8' }
)
const snapshotResult = JSON.parse(snapshotOut.trim())

// ── Update status to built ────────────────────────────────────────────────────
execSync(
  `node "${path.join(ROOT, '.claude', 'scripts', 'queue-update.js')}" ${componentName} --set '{"status":"built","testPassed":false}' --project ${projectName}`,
  { cwd: ROOT, encoding: 'utf8' }
)

// ── Output ────────────────────────────────────────────────────────────────────
const result = {
  replaced: replacedCount,
  find: findText,
  replacement: replaceText,
  newVersion,
  dryRun: false,
  lines: replaceAll ? matchedLines : matchedLines.slice(0, 1),
  snapshotPath: snapshotResult.path,
}

process.stdout.write(JSON.stringify(result, null, 2) + '\n')
process.stderr.write(`\n✅ ${componentName} v${newVersion} quick-patch 完成\n`)
process.stderr.write(`   替換：${replacedCount} 處 "${findText}" → "${replaceText}"\n`)
process.stderr.write(`   快照：${snapshotResult.path}\n`)
process.stderr.write(`   狀態：built（可呼叫 SA-4 直接部署，跳過 SA-2/SA-3）\n`)
