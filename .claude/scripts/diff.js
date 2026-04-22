#!/usr/bin/env node
/**
 * diff.js
 * 比較兩個版本快照，輸出 diff + 變更清單
 *
 * 用法：
 *   node .claude/scripts/diff.js <ComponentName>
 *   node .claude/scripts/diff.js <ComponentName> --from v1 --to v2
 *   node .claude/scripts/diff.js <ComponentName> --project PlanA
 *
 * 預設：比較最後兩個版本（vN-1 vs vN）
 *
 * 輸出（stdout）：JSON
 * {
 *   "from": "v1",
 *   "to": "v2",
 *   "diff": "--- v1\n+++ v2\n@@ ... @@\n...",
 *   "changedFunctions": ["EditClassDialog", "handleSubmit"],
 *   "changedZones": ["edit-dialog", "header"],
 *   "addedLines": 42,
 *   "removedLines": 18,
 *   "summary": "Changed 2 functions, 2 zones (+42 / -18 lines)"
 * }
 */

const fs = require('fs')
const path = require('path')

// ── Config ────────────────────────────────────────────────────────────────────
const ROOT = path.resolve(__dirname, '../..')

// ── Args ──────────────────────────────────────────────────────────────────────
const args = process.argv.slice(2)

const projectIdx = args.indexOf('--project')
const project = projectIdx !== -1 ? args[projectIdx + 1] : null

const fromIdx = args.indexOf('--from')
const fromVersion = fromIdx !== -1 ? args[fromIdx + 1] : null

const toIdx = args.indexOf('--to')
const toVersion = toIdx !== -1 ? args[toIdx + 1] : null

const skipIndices = new Set([
  ...(projectIdx !== -1 ? [projectIdx, projectIdx + 1] : []),
  ...(fromIdx !== -1 ? [fromIdx, fromIdx + 1] : []),
  ...(toIdx !== -1 ? [toIdx, toIdx + 1] : []),
])
const positional = args.filter((a, i) => !a.startsWith('--') && !skipIndices.has(i))
const componentName = positional[0]

if (!componentName) {
  process.stderr.write('Usage: diff.js <ComponentName> [--from v1] [--to v2] [--project ProjectName]\n')
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
const versionsDir = path.join(ROOT, '.claude', 'workspace', projectName, componentName, 'versions')

if (!fs.existsSync(versionsDir)) {
  process.stderr.write(`diff: versions directory not found: ${versionsDir}\n`)
  process.exit(1)
}

// ── Resolve version files ─────────────────────────────────────────────────────
function getVersionFiles() {
  const files = fs.readdirSync(versionsDir)
    .filter(f => /^v\d+\.tsx$/.test(f))
    .sort((a, b) => {
      const na = parseInt(a.match(/\d+/)[0])
      const nb = parseInt(b.match(/\d+/)[0])
      return na - nb
    })
  return files
}

const versionFiles = getVersionFiles()

if (versionFiles.length < 2) {
  process.stderr.write(`diff: need at least 2 versions, found ${versionFiles.length}\n`)
  process.exit(1)
}

function resolveVersionFile(v) {
  if (!v) return null
  const fname = v.endsWith('.tsx') ? v : `${v}.tsx`
  const full = path.join(versionsDir, fname)
  if (!fs.existsSync(full)) {
    process.stderr.write(`diff: version file not found: ${full}\n`)
    process.exit(1)
  }
  return { label: v.replace('.tsx', ''), file: full }
}

let fromFile, toFile

if (fromVersion && toVersion) {
  fromFile = resolveVersionFile(fromVersion)
  toFile = resolveVersionFile(toVersion)
} else if (fromVersion) {
  fromFile = resolveVersionFile(fromVersion)
  const lastFile = versionFiles[versionFiles.length - 1]
  toFile = { label: lastFile.replace('.tsx', ''), file: path.join(versionsDir, lastFile) }
} else {
  // default: last two versions
  const secondLast = versionFiles[versionFiles.length - 2]
  const last = versionFiles[versionFiles.length - 1]
  fromFile = { label: secondLast.replace('.tsx', ''), file: path.join(versionsDir, secondLast) }
  toFile = { label: last.replace('.tsx', ''), file: path.join(versionsDir, last) }
}

// ── Read content ──────────────────────────────────────────────────────────────
const fromContent = fs.readFileSync(fromFile.file, 'utf8')
const toContent = fs.readFileSync(toFile.file, 'utf8')

// ── Generate unified diff ─────────────────────────────────────────────────────
function unifiedDiff(oldLines, newLines, fromLabel, toLabel, contextLines = 3) {
  // Simple unified diff implementation (no external deps)
  const hunks = []
  let i = 0, j = 0

  // LCS-based diff
  const lcs = computeLCS(oldLines, newLines)
  const ops = buildOps(oldLines, newLines, lcs)

  let hunkOldStart = -1, hunkNewStart = -1
  let hunkLines = []
  let pendingContext = []

  function flushHunk() {
    if (hunkLines.length === 0) return
    const oldCount = hunkLines.filter(l => l[0] !== '+').length
    const newCount = hunkLines.filter(l => l[0] !== '-').length
    hunks.push(
      `@@ -${hunkOldStart},${oldCount} +${hunkNewStart},${newCount} @@\n` +
      hunkLines.join('\n')
    )
    hunkLines = []
    hunkOldStart = -1
    hunkNewStart = -1
  }

  let oldIdx = 1, newIdx = 1

  for (let k = 0; k < ops.length; k++) {
    const op = ops[k]

    if (op.type === 'equal') {
      if (hunkLines.length > 0) {
        // trailing context
        const ctx = op.lines.slice(0, contextLines)
        hunkLines.push(...ctx.map(l => ' ' + l))
        flushHunk()
      }
      // leading context for next hunk stored in pendingContext
      pendingContext = op.lines.slice(-contextLines)
      oldIdx += op.lines.length
      newIdx += op.lines.length
    } else {
      if (hunkLines.length === 0) {
        // start new hunk with leading context
        hunkOldStart = oldIdx - pendingContext.length
        hunkNewStart = newIdx - pendingContext.length
        hunkLines.push(...pendingContext.map(l => ' ' + l))
        pendingContext = []
      }
      if (op.type === 'remove') {
        hunkLines.push(...op.lines.map(l => '-' + l))
        oldIdx += op.lines.length
      } else if (op.type === 'insert') {
        hunkLines.push(...op.lines.map(l => '+' + l))
        newIdx += op.lines.length
      }
    }
  }
  if (hunkLines.length > 0) flushHunk()

  if (hunks.length === 0) return ''

  return `--- ${fromLabel}\n+++ ${toLabel}\n` + hunks.join('\n')
}

function computeLCS(a, b) {
  // Use patience diff-lite: just track equal line positions
  // For large files, use line hashing
  const bIndex = new Map()
  b.forEach((line, i) => {
    if (!bIndex.has(line)) bIndex.set(line, [])
    bIndex.get(line).push(i)
  })

  // Simple DP LCS (works for typical component sizes < 2000 lines)
  const m = a.length, n = b.length
  if (m * n > 4_000_000) {
    // Too large: skip LCS, treat as full replace
    return []
  }

  const dp = Array.from({ length: m + 1 }, () => new Int32Array(n + 1))
  for (let i = m - 1; i >= 0; i--) {
    for (let j = n - 1; j >= 0; j--) {
      if (a[i] === b[j]) {
        dp[i][j] = dp[i + 1][j + 1] + 1
      } else {
        dp[i][j] = Math.max(dp[i + 1][j], dp[i][j + 1])
      }
    }
  }

  const lcs = []
  let i = 0, j = 0
  while (i < m && j < n) {
    if (a[i] === b[j]) {
      lcs.push([i, j])
      i++; j++
    } else if (dp[i + 1][j] >= dp[i][j + 1]) {
      i++
    } else {
      j++
    }
  }
  return lcs
}

function buildOps(a, b, lcs) {
  const ops = []
  let ai = 0, bi = 0, li = 0

  while (li < lcs.length) {
    const [la, lb] = lcs[li]
    if (ai < la) ops.push({ type: 'remove', lines: a.slice(ai, la) })
    if (bi < lb) ops.push({ type: 'insert', lines: b.slice(bi, lb) })
    // Find run of consecutive equal
    let runEnd = li
    while (
      runEnd + 1 < lcs.length &&
      lcs[runEnd + 1][0] === lcs[runEnd][0] + 1 &&
      lcs[runEnd + 1][1] === lcs[runEnd][1] + 1
    ) runEnd++

    const equalA = a.slice(lcs[li][0], lcs[runEnd][0] + 1)
    ops.push({ type: 'equal', lines: equalA })
    ai = lcs[runEnd][0] + 1
    bi = lcs[runEnd][1] + 1
    li = runEnd + 1
  }

  if (ai < a.length) ops.push({ type: 'remove', lines: a.slice(ai) })
  if (bi < b.length) ops.push({ type: 'insert', lines: b.slice(bi) })

  return ops
}

// ── Extract changed functions & zones ────────────────────────────────────────
function extractChangedFunctions(diffText) {
  const functions = new Set()
  // Match function/component declarations near changed lines
  const lines = diffText.split('\n')
  let inHunk = false
  for (const line of lines) {
    if (line.startsWith('@@')) { inHunk = true; continue }
    if (!inHunk) continue
    if (line.startsWith('-') || line.startsWith('+')) {
      // Look for function/component patterns
      const content = line.slice(1)
      const fnMatch = content.match(/(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:React\.)?(?:memo\()?(?:forwardRef\()?(?:\([^)]*\)\s*(?::\s*\w+)?\s*=>|\([^)]*\)\s*\{))/)
      if (fnMatch) {
        functions.add(fnMatch[1] || fnMatch[2])
      }
    }
  }
  return [...functions]
}

function extractChangedZones(diffText, toContent) {
  const zones = new Set()
  const lines = diffText.split('\n')

  // Find changed line numbers in the new file
  const changedLines = new Set()
  let newLine = 0
  for (const line of lines) {
    const hunkMatch = line.match(/^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@/)
    if (hunkMatch) { newLine = parseInt(hunkMatch[1]) - 1; continue }
    if (line.startsWith('---') || line.startsWith('+++')) continue
    if (line.startsWith('-')) continue // old line, skip
    newLine++
    if (line.startsWith('+')) changedLines.add(newLine)
  }

  // Scan toContent for ReviewZone ids near changed lines
  const contentLines = toContent.split('\n')
  const zonePattern = /<ReviewZone\s+id=["']([^"']+)["']/
  const dataZonePattern = /data-zone=["']([^"']+)["']/

  for (const lineNum of changedLines) {
    // Search in a window around the changed line
    const start = Math.max(0, lineNum - 30)
    const end = Math.min(contentLines.length - 1, lineNum + 5)
    for (let i = start; i <= end; i++) {
      const zMatch = contentLines[i].match(zonePattern) || contentLines[i].match(dataZonePattern)
      if (zMatch) zones.add(zMatch[1])
    }
  }

  // Also detect by changed component name proximity
  // (zone name often matches component name kebab-case)
  return [...zones]
}

// ── Count added/removed lines ─────────────────────────────────────────────────
function countChanges(diffText) {
  let added = 0, removed = 0
  for (const line of diffText.split('\n')) {
    if (line.startsWith('+') && !line.startsWith('+++')) added++
    else if (line.startsWith('-') && !line.startsWith('---')) removed++
  }
  return { added, removed }
}

// ── Main ──────────────────────────────────────────────────────────────────────
const fromLines = fromContent.split('\n')
const toLines = toContent.split('\n')

const diffText = unifiedDiff(fromLines, toLines, fromFile.label, toFile.label)

const changedFunctions = extractChangedFunctions(diffText)
const changedZones = extractChangedZones(diffText, toContent)
const { added, removed } = countChanges(diffText)

// Write changed-zones.json to workspace
const workspaceDir = path.join(ROOT, '.claude', 'workspace', projectName, componentName)
const changedZonesPath = path.join(workspaceDir, 'changed-zones.json')
const changedZonesData = {
  componentName,
  from: fromFile.label,
  to: toFile.label,
  changedFunctions,
  changedZones,
  addedLines: added,
  removedLines: removed,
  generatedAt: new Date().toISOString()
}
fs.writeFileSync(changedZonesPath, JSON.stringify(changedZonesData, null, 2) + '\n', 'utf8')

const result = {
  from: fromFile.label,
  to: toFile.label,
  diff: diffText,
  changedFunctions,
  changedZones,
  addedLines: added,
  removedLines: removed,
  summary: `Changed ${changedFunctions.length} function(s), ${changedZones.length} zone(s) (+${added} / -${removed} lines)`
}

process.stdout.write(JSON.stringify(result, null, 2) + '\n')
process.stderr.write(`✓ changed-zones.json written to ${changedZonesPath}\n`)
