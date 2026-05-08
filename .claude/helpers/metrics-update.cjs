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
// Dashboard lives under _METRICS/ to keep the workspace root clean.
// Older versions wrote it at root; on first run we migrate the legacy file.
const DASHBOARD_PATH      = path.join(WORKSPACE, '_METRICS', '_DASHBOARD.md');
const LEGACY_DASHBOARD_AT_ROOT = path.join(WORKSPACE, '_DASHBOARD.md');
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

/**
 * Keep at most `keepN` files matching prefix in dir; delete oldest first.
 * Prevents unbounded growth of session snapshots over months of 7/24 use.
 */
function pruneOldSnapshots(dir, prefix, keepN) {
  try {
    if (!fs.existsSync(dir)) return;
    const files = fs.readdirSync(dir)
      .filter(f => f.startsWith(prefix))
      .map(f => ({ name: f, full: path.join(dir, f), mtime: fs.statSync(path.join(dir, f)).mtimeMs }))
      .sort((a, b) => b.mtime - a.mtime);
    for (const f of files.slice(keepN)) {
      try { fs.unlinkSync(f.full); } catch { /* non-fatal */ }
    }
  } catch { /* non-fatal */ }
}

function exportSnapshot() {
  if (!CODEBURN_BIN) return;
  ensureMetrics();
  const ts   = new Date().toISOString().replace(/[:.]/g,'-').slice(0,19);
  const file = path.join(METRICS_DIR, `codeburn-${ts}.json`);
  // Fix #5 — close the fd if spawn throws to avoid descriptor leak on 7/24.
  let fd = null;
  try {
    fd = fs.openSync(file, 'w');
    const child = spawn(CODEBURN_BIN, ['export', '--format', 'json'], {
      detached: true, stdio: ['ignore', fd, 'ignore'],
    });
    child.unref();
    // child inherits the fd — safe to close ours
    fs.closeSync(fd);
  } catch {
    if (fd !== null) { try { fs.closeSync(fd); } catch { /* already closed */ } }
  }
}

// ── 2. codeburn status → optimize suggestions ────────────────────────────────

function writeOptimizeSuggestions(statusData) {
  ensureMetrics();
  const ts   = new Date().toISOString();
  const lines = [
    `# CodeBurn Optimize — ${ts}`,
    '',
    '## Current status',
    `- **Today:** $${(statusData.today_cost||0).toFixed(2)} / ${statusData.today_calls||0} calls`,
    `- **Month:** $${(statusData.month_cost||0).toFixed(2)} / ${statusData.month_calls||0} calls`,
    '',
    '## Automatic suggestions',
  ];

  // Simple heuristic suggestions based on data
  const costPerCall = statusData.today_calls > 0 ? statusData.today_cost / statusData.today_calls : 0;
  if (costPerCall > 0.05) lines.push(`- ⚠️ High average cost per call ($${costPerCall.toFixed(3)}/call) → review long prompts`);
  if (statusData.today_calls > 150) lines.push(`- ⚠️ Many calls today (${statusData.today_calls}) → batch small tasks`);
  if (statusData.today_cost > 8) lines.push(`- 🔴 High daily cost ($${statusData.today_cost.toFixed(2)}) → run /cost optimize`);
  if (lines[lines.length-1] === '## Automatic suggestions') lines.push('- ✅ Usage within normal parameters');

  lines.push('', `_Auto-generated at SessionEnd. Run \`codeburn report\` for details._`);

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

  // One-time migration: move legacy root _DASHBOARD.md into _METRICS/
  ensureMetrics();
  if (!fs.existsSync(DASHBOARD_PATH) && fs.existsSync(LEGACY_DASHBOARD_AT_ROOT)) {
    try { fs.renameSync(LEGACY_DASHBOARD_AT_ROOT, DASHBOARD_PATH); }
    catch { /* fall through — fresh dashboard will be written below */ }
  } else if (fs.existsSync(LEGACY_DASHBOARD_AT_ROOT)) {
    // both exist (post-migration leftover) — keep the canonical one, drop legacy
    try { fs.unlinkSync(LEGACY_DASHBOARD_AT_ROOT); } catch { /* non-fatal */ }
  }

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
  // Bounded-disk: keep last 30 of each rotating artifact
  try {
    pruneOldSnapshots(METRICS_DIR, 'codeburn-', 30);
    pruneOldSnapshots(path.join(WORKSPACE, '.claude-flow', 'reports'), 'session-', 30);
    pruneOldSnapshots(path.join(WORKSPACE, '.claude-flow', 'sessions'), 'session-', 30);
  } catch { /* non-fatal */ }
}

module.exports = { run, updateDashboard, writeOptimizeSuggestions };
