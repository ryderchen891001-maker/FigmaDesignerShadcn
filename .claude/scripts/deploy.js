#!/usr/bin/env node
/**
 * deploy.js
 * Vercel preview deploy + 回傳最新 preview URL
 *
 * 用法：
 *   node .claude/scripts/deploy.js
 *   node .claude/scripts/deploy.js --prod    # production deploy
 *
 * 輸出（stdout）：純文字 URL
 *   https://figma-designer-review-xxx.vercel.app
 *
 * 同時寫入 stdout 一行 JSON（方便 agent parse）：
 *   { "url": "https://...", "deploymentId": "dpl_xxx", "ready": true }
 */

const { execSync, spawnSync } = require('child_process')
const path = require('path')

// ── Config ────────────────────────────────────────────────────────────────────
const ROOT = path.resolve(__dirname, '../..')
const VERCEL_PROJECT = 'figma-designer-review'
const VERCEL_SCOPE = 'ryderchen891001-1255s-projects'

// ── Args ──────────────────────────────────────────────────────────────────────
const isProd = process.argv.includes('--prod')

// ── Deploy ────────────────────────────────────────────────────────────────────
process.stderr.write(`deploying${isProd ? ' (production)' : ''}...\n`)

const deployArgs = ['deploy', '--yes']
if (isProd) deployArgs.push('--prod')

const result = spawnSync('vercel', deployArgs, {
  cwd: ROOT,
  encoding: 'utf8',
  timeout: 300_000,
})

if (result.status !== 0) {
  process.stderr.write('deploy failed:\n' + (result.stderr || result.stdout) + '\n')
  process.exit(1)
}

// ── Get latest URL ────────────────────────────────────────────────────────────
let url = null
let deploymentId = null

// Try to parse from deploy output
const output = result.stdout + result.stderr
const urlMatch = output.match(/https:\/\/figma-designer-review-[^\s]+\.vercel\.app/)
if (urlMatch) {
  url = urlMatch[0]
}

// Fallback: vercel ls to get latest
if (!url) {
  try {
    const lsOut = execSync(
      `vercel ls ${VERCEL_PROJECT} --scope ${VERCEL_SCOPE}`,
      { encoding: 'utf8', cwd: ROOT }
    )
    const lsMatch = lsOut.match(/https:\/\/figma-designer-review-[^\s]+\.vercel\.app/)
    if (lsMatch) url = lsMatch[0]
  } catch (e) {
    process.stderr.write('vercel ls fallback failed: ' + e.message + '\n')
  }
}

if (!url) {
  process.stderr.write('deploy succeeded but could not parse URL\n')
  process.exit(1)
}

// Extract deployment ID from inspect URL if present
const dplMatch = output.match(/dpl_[a-zA-Z0-9]+/)
if (dplMatch) deploymentId = dplMatch[0]

// ── Output ────────────────────────────────────────────────────────────────────
const out = { url, deploymentId, ready: true }
process.stdout.write(JSON.stringify(out, null, 2) + '\n')
