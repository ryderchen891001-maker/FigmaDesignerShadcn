#!/usr/bin/env node
/**
 * health-check.js
 * 掃描 workspace，診斷所有 component 的健康狀態
 *
 * 用法：
 *   node .claude/scripts/health-check.js
 *   node .claude/scripts/health-check.js --project PlanA
 *   node .claude/scripts/health-check.js --component ClassManagement
 *   node .claude/scripts/health-check.js --json
 *   node .claude/scripts/health-check.js --fix   # 自動修復可修的問題
 *
 * 檢查項目：
 *   1. versions/ 快照是否跟 queue version 號對得上
 *   2. pending comments 有沒有超過 7 天沒處理
 *   3. test-report.json 跟 queue-entry testPassed 是否一致
 *   4. preview URL 是否還活著（HTTP HEAD）
 *   5. TSX 檔案是否存在於 pending/
 *   6. queue-entry.json 必要欄位是否齊全
 */

const fs = require('fs')
const path = require('path')
const https = require('https')
const http = require('http')

// ── Config ────────────────────────────────────────────────────────────────────
const ROOT = path.resolve(__dirname, '../..')
const PENDING_COMMENT_DAYS = 7
const REQUIRED_FIELDS = ['componentName', 'status', 'version', 'figmaUrl', 'createdAt']

// ── Args ──────────────────────────────────────────────────────────────────────
const args = process.argv.slice(2)

const projectIdx = args.indexOf('--project')
const project = projectIdx !== -1 ? args[projectIdx + 1] : null

const compIdx = args.indexOf('--component')
const filterComponent = compIdx !== -1 ? args[compIdx + 1] : null

const jsonMode = args.includes('--json')
const fixMode = args.includes('--fix')

// ── Resolve project ───────────────────────────────────────────────────────────
function resolveProject() {
  if (project) return project
  const activeFile = path.join(ROOT, 'active-project.json')
  if (fs.existsSync(activeFile)) {
    const active = JSON.parse(fs.readFileSync(activeFile, 'utf8'))
    return active.name
  }
  return null
}

const targetProject = resolveProject()

// ── Resolve pending dir ───────────────────────────────────────────────────────
function getPendingDir(projName) {
  const projectFile = path.join(ROOT, 'projects', projName, 'project.json')
  if (fs.existsSync(projectFile)) {
    const proj = JSON.parse(fs.readFileSync(projectFile, 'utf8'))
    if (proj.pendingDir) return path.join(ROOT, proj.pendingDir)
  }
  return path.join(ROOT, 'projects', projName, 'components', 'pending')
}

// ── HTTP HEAD check ───────────────────────────────────────────────────────────
function checkUrl(url) {
  return new Promise((resolve) => {
    if (!url) return resolve({ ok: false, status: null, reason: 'no url' })
    try {
      const lib = url.startsWith('https') ? https : http
      const req = lib.request(url, { method: 'HEAD', timeout: 5000 }, (res) => {
        resolve({ ok: res.statusCode < 400, status: res.statusCode, reason: null })
      })
      req.on('error', (e) => resolve({ ok: false, status: null, reason: e.message }))
      req.on('timeout', () => { req.destroy(); resolve({ ok: false, status: null, reason: 'timeout' }) })
      req.end()
    } catch (e) {
      resolve({ ok: false, status: null, reason: e.message })
    }
  })
}

// ── Days ago ──────────────────────────────────────────────────────────────────
function daysAgo(isoString) {
  if (!isoString) return null
  return Math.floor((Date.now() - new Date(isoString).getTime()) / 86400000)
}

// ── Scan workspace ────────────────────────────────────────────────────────────
function getComponents() {
  const workspaceRoot = path.join(ROOT, '.claude', 'workspace')
  if (!fs.existsSync(workspaceRoot)) return []

  const results = []
  const projects = targetProject
    ? [targetProject]
    : fs.readdirSync(workspaceRoot).filter(f =>
        fs.statSync(path.join(workspaceRoot, f)).isDirectory()
      )

  for (const proj of projects) {
    const projDir = path.join(workspaceRoot, proj)
    if (!fs.existsSync(projDir)) continue

    const components = fs.readdirSync(projDir)
      .filter(f => fs.statSync(path.join(projDir, f)).isDirectory())
      .filter(f => !filterComponent || f === filterComponent)

    for (const comp of components) {
      const queuePath = path.join(projDir, comp, 'queue-entry.json')
      if (!fs.existsSync(queuePath)) continue
      try {
        const entry = JSON.parse(fs.readFileSync(queuePath, 'utf8'))
        results.push({ project: proj, workspaceDir: path.join(projDir, comp), entry })
      } catch (e) {
        results.push({ project: proj, workspaceDir: path.join(projDir, comp), entry: null, parseError: e.message })
      }
    }
  }
  return results
}

// ── Run checks ────────────────────────────────────────────────────────────────
async function checkComponent({ project: proj, workspaceDir, entry, parseError }) {
  const name = entry?.componentName || path.basename(workspaceDir)
  const issues = []
  const warnings = []
  const fixes = []

  if (parseError) {
    issues.push(`queue-entry.json 解析失敗: ${parseError}`)
    return { name, project: proj, healthy: false, issues, warnings, fixes }
  }

  const { status, version, testPassed, previewUrl, pendingComments, updatedAt } = entry

  // ── Check 1: 必要欄位 ───────────────────────────────────────────────────────
  for (const field of REQUIRED_FIELDS) {
    if (entry[field] === undefined || entry[field] === null) {
      issues.push(`缺少必要欄位: ${field}`)
    }
  }

  // ── Check 2: versions/ 快照 ─────────────────────────────────────────────────
  if (status !== 'todo' && status !== 'spec-ready') {
    const versionsDir = path.join(workspaceDir, 'versions')
    const expectedSnapshot = path.join(versionsDir, `v${version}.tsx`)
    if (!fs.existsSync(expectedSnapshot)) {
      issues.push(`versions/v${version}.tsx 遺失（queue version=${version}）`)
      if (fixMode) {
        // Try to find pending TSX and create snapshot
        const pendingDir = getPendingDir(proj)
        const pendingTsx = path.join(pendingDir, name, `${name}.tsx`)
        if (fs.existsSync(pendingTsx)) {
          if (!fs.existsSync(versionsDir)) fs.mkdirSync(versionsDir, { recursive: true })
          fs.copyFileSync(pendingTsx, expectedSnapshot)
          fixes.push(`✓ 已從 pending/ 補建 versions/v${version}.tsx`)
        }
      }
    }
  }

  // ── Check 3: TSX 檔案存在（非 archived 狀態）──────────────────────────────
  if (!['archived', 'todo', 'spec-ready'].includes(status)) {
    const pendingDir = getPendingDir(proj)
    const tsxPath = path.join(pendingDir, name, `${name}.tsx`)
    if (!fs.existsSync(tsxPath)) {
      issues.push(`pending/${name}/${name}.tsx 不存在（status: ${status}）`)
    }
  }

  // ── Check 4: test-report 一致性 ─────────────────────────────────────────────
  const testReportPath = path.join(workspaceDir, 'test-report.json')
  if (fs.existsSync(testReportPath)) {
    try {
      const report = JSON.parse(fs.readFileSync(testReportPath, 'utf8'))
      if (report.overallPassed !== testPassed) {
        warnings.push(`test-report.overallPassed(${report.overallPassed}) ≠ queue testPassed(${testPassed})`)
        if (fixMode) {
          entry.testPassed = report.overallPassed
          fs.writeFileSync(
            path.join(workspaceDir, 'queue-entry.json'),
            JSON.stringify({ ...entry, updatedAt: new Date().toISOString() }, null, 2) + '\n'
          )
          fixes.push(`✓ testPassed 已同步為 ${report.overallPassed}`)
        }
      }
    } catch (e) {
      warnings.push(`test-report.json 解析失敗: ${e.message}`)
    }
  }

  // ── Check 5: pending comments 老化 ─────────────────────────────────────────
  const commentsPath = path.join(workspaceDir, 'comments.json')
  if (fs.existsSync(commentsPath)) {
    try {
      const comments = JSON.parse(fs.readFileSync(commentsPath, 'utf8'))
      const stalePending = Object.entries(comments)
        .filter(([, c]) => c.status === 'pending')
        .filter(([, c]) => daysAgo(c.timestamp) >= PENDING_COMMENT_DAYS)
      if (stalePending.length > 0) {
        warnings.push(`${stalePending.length} 條評論超過 ${PENDING_COMMENT_DAYS} 天未處理`)
      }
    } catch (e) {
      warnings.push(`comments.json 解析失敗: ${e.message}`)
    }
  }

  // ── Check 6: preview URL ─────────────────────────────────────────────────────
  let urlCheck = null
  if (previewUrl && ['in-review', 'needs-revision', 'approved'].includes(status)) {
    urlCheck = await checkUrl(previewUrl)
    if (!urlCheck.ok) {
      warnings.push(`previewUrl 無效（${urlCheck.status || urlCheck.reason}）: ${previewUrl}`)
    }
  }

  // ── Check 7: updatedAt 超過 30 天沒動 ──────────────────────────────────────
  const idleDays = daysAgo(updatedAt)
  if (idleDays !== null && idleDays > 30 && !['archived'].includes(status)) {
    warnings.push(`超過 ${idleDays} 天沒有更新（status: ${status}）`)
  }

  const healthy = issues.length === 0

  return {
    name,
    project: proj,
    status,
    version,
    healthy,
    issues,
    warnings,
    fixes,
    urlCheck,
  }
}

// ── Main ──────────────────────────────────────────────────────────────────────
async function main() {
  const components = getComponents()

  if (components.length === 0) {
    process.stdout.write('(no components found in workspace)\n')
    process.exit(0)
  }

  const results = await Promise.all(components.map(checkComponent))

  if (jsonMode) {
    process.stdout.write(JSON.stringify(results, null, 2) + '\n')
    return
  }

  // ── Human-readable output ─────────────────────────────────────────────────
  const healthy = results.filter(r => r.healthy && r.warnings.length === 0)
  const warned = results.filter(r => r.healthy && r.warnings.length > 0)
  const broken = results.filter(r => !r.healthy)

  if (broken.length > 0) {
    process.stdout.write('\n❌ 需要修復\n')
    process.stdout.write('─'.repeat(60) + '\n')
    for (const r of broken) {
      process.stdout.write(`  ${r.project}/${r.name} (v${r.version}, ${r.status})\n`)
      for (const issue of r.issues) process.stdout.write(`    ✗ ${issue}\n`)
      for (const fix of r.fixes) process.stdout.write(`    ${fix}\n`)
    }
  }

  if (warned.length > 0) {
    process.stdout.write('\n⚠️  需要注意\n')
    process.stdout.write('─'.repeat(60) + '\n')
    for (const r of warned) {
      process.stdout.write(`  ${r.project}/${r.name} (v${r.version}, ${r.status})\n`)
      for (const w of r.warnings) process.stdout.write(`    △ ${w}\n`)
      for (const fix of r.fixes) process.stdout.write(`    ${fix}\n`)
    }
  }

  if (healthy.length > 0) {
    process.stdout.write('\n✅ 健康\n')
    process.stdout.write('─'.repeat(60) + '\n')
    for (const r of healthy) {
      process.stdout.write(`  ${r.project}/${r.name} (v${r.version}, ${r.status})\n`)
    }
  }

  process.stdout.write('\n')
  process.stdout.write(`總計：${results.length} 個 component`)
  process.stdout.write(`  ✅ ${healthy.length}  ⚠️  ${warned.length}  ❌ ${broken.length}`)
  if (fixMode && results.some(r => r.fixes.length > 0)) {
    const fixCount = results.reduce((acc, r) => acc + r.fixes.length, 0)
    process.stdout.write(`  🔧 自動修復 ${fixCount} 個問題`)
  }
  process.stdout.write('\n')

  if (broken.length > 0) process.exit(1)
}

main().catch(e => {
  process.stderr.write('health-check error: ' + e.message + '\n')
  process.exit(1)
})
