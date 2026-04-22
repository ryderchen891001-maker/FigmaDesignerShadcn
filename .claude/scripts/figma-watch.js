#!/usr/bin/env node
/**
 * figma-watch.js
 * 偵測 Figma 設計稿在封存後是否有更動
 *
 * 用法：
 *   node .claude/scripts/figma-watch.js
 *   node .claude/scripts/figma-watch.js --project PlanA
 *   node .claude/scripts/figma-watch.js --component ClassManagement
 *   node .claude/scripts/figma-watch.js --json
 *
 * Token 來源（優先順序）：
 *   1. 環境變數 FIGMA_TOKEN
 *   2. projects/{ProjectName}/project.json → figmaToken
 *
 * 輸出範例：
 *   ClassManagement  封存於 2026-04-21  Figma 最後更動 2026-04-23  ⚠️  設計稿有更新
 *   TutorOverview    封存於 2026-04-20  Figma 最後更動 2026-04-20  ✅ 無變更
 */

const fs = require('fs')
const path = require('path')
const https = require('https')

// ── Config ────────────────────────────────────────────────────────────────────
const ROOT = path.resolve(__dirname, '../..')

// ── Args ──────────────────────────────────────────────────────────────────────
const args = process.argv.slice(2)

const projectIdx = args.indexOf('--project')
const project = projectIdx !== -1 ? args[projectIdx + 1] : null

const compIdx = args.indexOf('--component')
const filterComponent = compIdx !== -1 ? args[compIdx + 1] : null

const jsonMode = args.includes('--json')

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

// ── Read project.json ─────────────────────────────────────────────────────────
function readProjectConfig() {
  const projectFile = path.join(ROOT, 'projects', projectName, 'project.json')
  if (fs.existsSync(projectFile)) {
    return JSON.parse(fs.readFileSync(projectFile, 'utf8'))
  }
  return {}
}

const projectConfig = readProjectConfig()

// ── Resolve Figma token ───────────────────────────────────────────────────────
const FIGMA_TOKEN = process.env.FIGMA_TOKEN || projectConfig.figmaToken || null

if (!FIGMA_TOKEN) {
  process.stderr.write(
    'figma-watch: Figma token not found.\n' +
    '  Set FIGMA_TOKEN env var, or add figmaToken to projects/' + projectName + '/project.json\n'
  )
  process.exit(1)
}

// ── Figma API helper ──────────────────────────────────────────────────────────
function figmaGet(endpoint) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'api.figma.com',
      path: `/v1/${endpoint}`,
      method: 'GET',
      headers: { 'X-Figma-Token': FIGMA_TOKEN },
      timeout: 10000,
    }
    const req = https.request(options, (res) => {
      let data = ''
      res.on('data', chunk => data += chunk)
      res.on('end', () => {
        if (res.statusCode !== 200) {
          reject(new Error(`Figma API ${res.statusCode}: ${data.slice(0, 200)}`))
        } else {
          try { resolve(JSON.parse(data)) }
          catch (e) { reject(new Error('Figma API: invalid JSON')) }
        }
      })
    })
    req.on('error', reject)
    req.on('timeout', () => { req.destroy(); reject(new Error('Figma API timeout')) })
    req.end()
  })
}

// ── Extract fileKey from Figma URL ────────────────────────────────────────────
function extractFileKey(figmaUrl) {
  if (!figmaUrl) return null
  const match = figmaUrl.match(/figma\.com\/(?:design|file)\/([A-Za-z0-9_-]+)/)
  return match ? match[1] : null
}

// ── Read manifest ─────────────────────────────────────────────────────────────
function readManifest() {
  const manifestFile = path.join(
    ROOT,
    projectConfig.manifestFile || `projects/${projectName}/manifest.json`
  )
  if (!fs.existsSync(manifestFile)) {
    process.stderr.write(`figma-watch: manifest.json not found: ${manifestFile}\n`)
    process.exit(1)
  }
  return JSON.parse(fs.readFileSync(manifestFile, 'utf8'))
}

// ── Also scan workspace for in-review components ──────────────────────────────
function getActiveComponents() {
  const workspaceRoot = path.join(ROOT, '.claude', 'workspace', projectName)
  if (!fs.existsSync(workspaceRoot)) return []

  return fs.readdirSync(workspaceRoot)
    .filter(f => !filterComponent || f === filterComponent)
    .map(comp => {
      const queuePath = path.join(workspaceRoot, comp, 'queue-entry.json')
      if (!fs.existsSync(queuePath)) return null
      try {
        const entry = JSON.parse(fs.readFileSync(queuePath, 'utf8'))
        return {
          name: comp,
          figmaUrl: entry.figmaUrl,
          referenceDate: entry.updatedAt || entry.createdAt,
          status: entry.status,
          source: 'active',
        }
      } catch { return null }
    })
    .filter(Boolean)
}

// ── Build check list ──────────────────────────────────────────────────────────
function buildCheckList() {
  const items = []
  const seen = new Set()

  // Archived components from manifest
  const manifest = readManifest()
  for (const [compName, compData] of Object.entries(manifest.components || {})) {
    if (filterComponent && compName !== filterComponent) continue
    const latest = compData.versions?.[compData.latestVersion]
    if (!latest) continue
    items.push({
      name: compName,
      figmaUrl: latest.figmaUrl,
      referenceDate: latest.archivedAt,
      status: 'archived',
      source: 'manifest',
    })
    seen.add(compName)
  }

  // Active components not in manifest
  for (const comp of getActiveComponents()) {
    if (!seen.has(comp.name)) items.push(comp)
  }

  return items
}

// ── Cache for fileKey → lastModified ─────────────────────────────────────────
const fileCache = new Map()

async function getFigmaLastModified(fileKey) {
  if (fileCache.has(fileKey)) return fileCache.get(fileKey)
  const data = await figmaGet(`files/${fileKey}?depth=1`)
  const lastModified = data.lastModified
  fileCache.set(fileKey, lastModified)
  return lastModified
}

// ── Main ──────────────────────────────────────────────────────────────────────
async function main() {
  const checkList = buildCheckList()

  if (checkList.length === 0) {
    process.stdout.write('(no components to check)\n')
    process.exit(0)
  }

  process.stderr.write(`figma-watch: checking ${checkList.length} component(s)...\n`)

  const results = []

  for (const item of checkList) {
    const fileKey = extractFileKey(item.figmaUrl)
    if (!fileKey) {
      results.push({ ...item, error: 'cannot extract fileKey from figmaUrl', changed: null })
      continue
    }

    try {
      const lastModified = await getFigmaLastModified(fileKey)
      const refDate = item.referenceDate
      const changed = refDate ? new Date(lastModified) > new Date(refDate) : null
      const daysDiff = refDate
        ? Math.floor((new Date(lastModified) - new Date(refDate)) / 86400000)
        : null

      results.push({
        name: item.name,
        status: item.status,
        referenceDate: refDate ? refDate.slice(0, 10) : null,
        figmaLastModified: lastModified ? lastModified.slice(0, 10) : null,
        changed,
        daysDiff,
        fileKey,
        error: null,
      })
    } catch (e) {
      results.push({ name: item.name, status: item.status, error: e.message, changed: null })
    }
  }

  if (jsonMode) {
    process.stdout.write(JSON.stringify(results, null, 2) + '\n')
    return
  }

  // ── Human-readable output ─────────────────────────────────────────────────
  const changed = results.filter(r => r.changed === true)
  const unchanged = results.filter(r => r.changed === false)
  const errored = results.filter(r => r.error)

  if (changed.length > 0) {
    process.stdout.write('\n⚠️  設計稿在參考時間後有更新\n')
    process.stdout.write('─'.repeat(70) + '\n')
    for (const r of changed) {
      process.stdout.write(
        `  ${r.name.padEnd(24)} 參考日期: ${r.referenceDate}  ` +
        `Figma 更新: ${r.figmaLastModified}  (+${r.daysDiff} 天)\n`
      )
      process.stdout.write(`  → 建議重新執行 SA-1 讀取最新設計稿\n`)
    }
  }

  if (unchanged.length > 0) {
    process.stdout.write('\n✅ 設計稿無變更\n')
    process.stdout.write('─'.repeat(70) + '\n')
    for (const r of unchanged) {
      process.stdout.write(
        `  ${r.name.padEnd(24)} 參考日期: ${r.referenceDate}  ` +
        `Figma 更新: ${r.figmaLastModified}\n`
      )
    }
  }

  if (errored.length > 0) {
    process.stdout.write('\n❌ 檢查失敗\n')
    process.stdout.write('─'.repeat(70) + '\n')
    for (const r of errored) {
      process.stdout.write(`  ${r.name}: ${r.error}\n`)
    }
  }

  process.stdout.write(`\n總計：${results.length} 個  ⚠️  ${changed.length} 個有更新  ✅ ${unchanged.length} 個無變更\n`)

  if (changed.length > 0) process.exit(2) // exit 2 = "has updates"
}

main().catch(e => {
  process.stderr.write('figma-watch error: ' + e.message + '\n')
  process.exit(1)
})
