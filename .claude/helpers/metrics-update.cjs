'use strict';
/**
 * metrics-update.cjs (v6.1 Micro)
 * Rulat la SessionEnd:
 *   1. Salvează codeburn export JSON în _METRICS/
 *   2. Actualizează _DASHBOARD.md cu secțiunea CodeBurn
 *   3. Scrie _METRICS/codeburn-optimize-latest.md (sugestii waste)
 */

const fs             = require('fs');
const path           = require('path');
const { execSync, spawn } = require('child_process');

const WORKSPACE     = process.cwd();
const METRICS_DIR   = path.join(WORKSPACE, '_METRICS');
const DASHBOARD_PATH= path.join(WORKSPACE, '_DASHBOARD.md');
const FLAGS_PATH    = path.join(__dirname, 'feature-flags.json');

const CODEBURN_BIN  = (() => {
  const home = process.env.HOME || process.env.USERPROFILE || '';
  const candidates = [
    path.join(home, '.npm-global', 'bin', 'codeburn'),
    path.join(home, '.local', 'bin', 'codeburn'),
    '/usr/local/bin/codeburn',
    '/usr/bin/codeburn',
  ];
  for (const c of candidates) { if (fs.existsSync(c)) return c; }
  try { return execSync('which codeburn',{encoding:'utf-8',timeout:2000}).trim(); } catch { return null; }
})();

function loadFlags() {
  try { return JSON.parse(fs.readFileSync(FLAGS_PATH,'utf-8')); } catch { return {}; }
}

function ensureMetrics() {
  if (!fs.existsSync(METRICS_DIR)) fs.mkdirSync(METRICS_DIR, { recursive: true });
}

// ── 1. Export JSON snapshot — fire-and-forget (non-blocking) ────────────────

function exportSnapshot() {
  if (!CODEBURN_BIN) return;
  ensureMetrics();
  const ts   = new Date().toISOString().replace(/[:.]/g,'-').slice(0,19);
  const file = path.join(METRICS_DIR, `codeburn-${ts}.json`);
  // spawn detached — nu blochează session-end
  try {
    const child = spawn(CODEBURN_BIN, ['export', '--format', 'json'], {
      detached: true, stdio: ['ignore', fs.openSync(file, 'w'), 'ignore'],
    });
    child.unref();
  } catch { /* non-fatal */ }
}

// ── 2. codeburn status → optimize suggestions ────────────────────────────────

function writeOptimizeSuggestions(statusData) {
  ensureMetrics();
  const ts   = new Date().toISOString();
  const lines = [
    `# CodeBurn Optimize — ${ts}`,
    '',
    '## Status curent',
    `- **Today:** $${(statusData.today_cost||0).toFixed(2)} / ${statusData.today_calls||0} calls`,
    `- **Month:** $${(statusData.month_cost||0).toFixed(2)} / ${statusData.month_calls||0} calls`,
    '',
    '## Sugestii automate',
  ];

  // Simple heuristic suggestions based on data
  const costPerCall = statusData.today_calls > 0 ? statusData.today_cost / statusData.today_calls : 0;
  if (costPerCall > 0.05) lines.push(`- ⚠️ Cost mediu per call ridicat ($${costPerCall.toFixed(3)}/call) → verifică prompturi lungi`);
  if (statusData.today_calls > 150) lines.push(`- ⚠️ Multe calls azi (${statusData.today_calls}) → grupează task-uri mici`);
  if (statusData.today_cost > 8) lines.push(`- 🔴 Cost zilnic ridicat ($${statusData.today_cost.toFixed(2)}) → folosește /cost optimize`);
  if (lines[lines.length-1] === '## Sugestii automate') lines.push('- ✅ Consum în parametri normali');

  lines.push('', `_Generat automat la SessionEnd. Rulează \`codeburn report\` pentru detalii._`);

  fs.writeFileSync(path.join(METRICS_DIR, 'codeburn-optimize-latest.md'), lines.join('\n'), 'utf-8');
}

// ── 3. _DASHBOARD.md update ──────────────────────────────────────────────────

const DASHBOARD_MARKER_START = '<!-- CODEBURN-START -->';
const DASHBOARD_MARKER_END   = '<!-- CODEBURN-END -->';

function updateDashboard(statusData) {
  const ts      = new Date().toISOString();
  const section = [
    DASHBOARD_MARKER_START,
    '## 🔥 CodeBurn — Token Observability',
    `_Actualizat: ${ts}_`,
    '',
    `| Metric | Valoare |`,
    `|---|---|`,
    `| Today cost | **$${(statusData.today_cost||0).toFixed(2)}** |`,
    `| Today calls | ${statusData.today_calls||0} |`,
    `| Month cost | **$${(statusData.month_cost||0).toFixed(2)}** |`,
    `| Month calls | ${statusData.month_calls||0} |`,
    `| Cost/call azi | $${statusData.today_calls > 0 ? (statusData.today_cost/statusData.today_calls).toFixed(3) : '0.000'} |`,
    '',
    `> Detalii complete: \`/cost report\` | Optimizare: \`/cost optimize\``,
    DASHBOARD_MARKER_END,
  ].join('\n');

  let content = '';
  if (fs.existsSync(DASHBOARD_PATH)) {
    content = fs.readFileSync(DASHBOARD_PATH, 'utf-8');
    // Replace existing section if present
    const re = new RegExp(`${DASHBOARD_MARKER_START}[\\s\\S]*?${DASHBOARD_MARKER_END}`, 'g');
    if (re.test(content)) {
      content = content.replace(re, section);
    } else {
      content += '\n\n' + section;
    }
  } else {
    content = `# Dashboard Workspace\n\n${section}`;
  }
  fs.writeFileSync(DASHBOARD_PATH, content, 'utf-8');
}

// ── Main export ──────────────────────────────────────────────────────────────

function run(statusData) {
  const flags = loadFlags();
  if (!flags.components || !flags.components.codeburn) return;
  if (!statusData || statusData.source === 'unavailable') return;

  try { writeOptimizeSuggestions(statusData); } catch { /* non-fatal */ }
  try { updateDashboard(statusData); } catch { /* non-fatal */ }
  // Export snapshot in background (non-blocking)
  try { exportSnapshot(); } catch { /* non-fatal */ }
}

module.exports = { run, updateDashboard, writeOptimizeSuggestions };
