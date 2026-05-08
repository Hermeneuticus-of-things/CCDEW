'use strict';
/**
 * Graphify (v6.1 Micro)
 * Generates ASCII + Markdown session reports. No external dependencies.
 *
 * Aggregates data from: codeburn.json, safla.json, intelligence graph-state.json
 * Output: .claude-flow/reports/session-<date>.md
 *
 * API:
 *   generateReport()   → writes report file, returns path
 *   printASCII()       → prints ASCII summary to stdout
 */

const fs   = require('fs');
const path = require('path');

const DATA_DIR    = path.join(process.cwd(), '.claude-flow', 'data');
const REPORTS_DIR = path.join(process.cwd(), '.claude-flow', 'reports');
const FLAGS_PATH  = path.join(__dirname, 'feature-flags.json');

function loadFlags() {
  try { return JSON.parse(fs.readFileSync(FLAGS_PATH, 'utf-8')); } catch { return {}; }
}

function readJSON(p) {
  try { if (fs.existsSync(p)) return JSON.parse(fs.readFileSync(p, 'utf-8')); } catch {}
  return null;
}

function ensureDirs() {
  if (!fs.existsSync(DATA_DIR))    fs.mkdirSync(DATA_DIR,    { recursive: true });
  if (!fs.existsSync(REPORTS_DIR)) fs.mkdirSync(REPORTS_DIR, { recursive: true });
}

// ── Data collectors ──────────────────────────────────────────────────────────

function getBurnData() {
  // Preferă cache-ul real codeburn CLI
  const cache = readJSON(path.join(DATA_DIR, 'codeburn-cache.json'));
  if (cache && cache.today_cost !== undefined) {
    return {
      today_cost:  cache.today_cost,
      month_cost:  cache.month_cost,
      today_calls: cache.today_calls,
      month_calls: cache.month_calls,
      source:      'real',
    };
  }
  return null;
}

function getSaflaData() {
  const d = readJSON(path.join(DATA_DIR, 'safla.json'));
  if (!d) return null;
  return {
    sessions: d.sessions || 0,
    feedbacks: d.total_feedbacks || 0,
    nodes: d.nodes || {},
  };
}

function getGraphData() {
  const d = readJSON(path.join(DATA_DIR, 'graph-state.json'));
  if (!d) return null;
  return {
    nodes: Object.keys(d.nodes || {}).length,
    edges: (d.edges || []).length,
  };
}

function getObsidianData() {
  try {
    const p = path.join(DATA_DIR, 'session-critical-index.json');
    if (!fs.existsSync(p)) return null;
    const idx  = readJSON(p);
    const all  = idx.all || Object.values(idx.by_project || {}).flat();
    const tags = Object.keys(idx.by_tag || {});
    return { entries: all.length, tags: tags.length, projects: Object.keys(idx.by_project || {}).length };
  } catch { return null; }
}

function getOptData() {
  try {
    const p = path.join(DATA_DIR, 'auto-optimize.jsonl');
    if (!fs.existsSync(p)) return null;
    const lines = fs.readFileSync(p, 'utf-8').trim().split('\n').filter(Boolean);
    const entries = lines.map(l => { try { return JSON.parse(l); } catch { return null; } }).filter(Boolean);
    if (entries.length === 0) return null;
    const avgSaved = Math.round(entries.reduce((s, e) => s + (e.savedPct || 0), 0) / entries.length);
    return { prompts: entries.length, avg_saved_pct: avgSaved };
  } catch { return null; }
}

// ── ASCII bar chart (width=20) ────────────────────────────────────────────────

function bar(value, max, width = 20) {
  const filled = max > 0 ? Math.round((value / max) * width) : 0;
  return '█'.repeat(filled) + '░'.repeat(width - filled);
}

// ── Report builder ────────────────────────────────────────────────────────────

function buildReport() {
  const burn  = getBurnData();
  const safla = getSaflaData();
  const graph = getGraphData();
  const opt   = getOptData();
  const now   = new Date().toISOString();

  const lines = [];
  lines.push(`# Graphify Session Report`);
  lines.push(`**Generated:** ${now}`);
  lines.push('');

  // Token burn
  lines.push('## CodeBurn (real)');
  if (burn) {
    lines.push(`- Today: **$${burn.today_cost.toFixed(2)}** (${burn.today_calls} calls)`);
    lines.push(`- Month: **$${burn.month_cost.toFixed(2)}** (${burn.month_calls} calls)`);
  } else {
    lines.push('_No data yet — run: codeburn status_');
  }
  lines.push('');

  // SAFLA
  lines.push('## SAFLA — Agent Performance');
  if (safla && safla.feedbacks > 0) {
    lines.push(`- Sessions: ${safla.sessions} | Total feedbacks: ${safla.feedbacks}`);
    lines.push('');
    lines.push('| Node | Success% | Adj | Last task |');
    lines.push('|---|---|---|---|');
    const NODE_NAMES = { 1:'Reformer',2:'Integrator',3:'Builder',4:'Contextualizer',5:'Analyzer',6:'Validator',7:'Innovator',8:'Orchestrator',9:'Consolidator' };
    for (const [nid, node] of Object.entries(safla.nodes)) {
      const total = (node.success || 0) + (node.failure || 0);
      if (total === 0) continue;
      const rate = Math.round((node.success / total) * 100);
      const adj  = (node.weight_adj || 0) >= 0 ? '+' + (node.weight_adj || 0).toFixed(2) : (node.weight_adj || 0).toFixed(2);
      lines.push(`| ${nid} ${NODE_NAMES[nid]||''} | ${rate}% | ${adj} | ${node.last_task || '-'} |`);
    }
  } else {
    lines.push('_No feedback recorded yet_');
  }
  lines.push('');

  // Intelligence graph
  lines.push('## Intelligence Graph');
  if (graph) {
    lines.push(`- Nodes: ${graph.nodes} | Edges: ${graph.edges}`);
  } else {
    lines.push('_No graph data_');
  }
  lines.push('');

  // Auto-Optimize
  lines.push('## Auto-Optimize');
  if (opt) {
    lines.push(`- Prompts analyzed: ${opt.prompts}`);
    lines.push(`- Average token savings: ${opt.avg_saved_pct}%`);
  } else {
    lines.push('_No optimization data_');
  }
  lines.push('');

  // Obsidian
  const obs = getObsidianData();
  lines.push('## Obsidian Context');
  if (obs) {
    lines.push(`- Entries loaded: ${obs.entries}`);
    lines.push(`- Tags: ${obs.tags} | Projects: ${obs.projects}`);
  } else {
    lines.push('_No Obsidian index — run obsidian-session-context.py_');
  }

  return lines.join('\n');
}

/**
 * Write report to .claude-flow/reports/session-<timestamp>.md
 */
function generateReport() {
  const flags = loadFlags();
  if (!flags.components || !flags.components.graphify) return null;

  ensureDirs();
  const ts       = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
  const filePath = path.join(REPORTS_DIR, `session-${ts}.md`);
  const content  = buildReport();
  fs.writeFileSync(filePath, content, 'utf-8');
  return filePath;
}

/**
 * Print a compact ASCII summary to stdout.
 */
function printASCII() {
  const flags = loadFlags();
  if (!flags.components || !flags.components.graphify) return;

  const burn  = getBurnData();
  const safla = getSaflaData();
  const opt   = getOptData();

  console.log('┌─────────────── Graphify Summary ───────────────┐');

  if (burn) {
    const burnPct = Math.min(burn.today_cost / 15, 1);
    console.log(`│ 🔥 Today  ${bar(burnPct * 20, 20)} $${burn.today_cost.toFixed(2)} / ${burn.today_calls} calls    │`);
  }

  if (safla && safla.feedbacks > 0) {
    const successRate = Object.values(safla.nodes).reduce((s, n) => {
      const total = (n.success || 0) + (n.failure || 0);
      return total > 0 ? { s: s.s + n.success, t: s.t + total } : s;
    }, { s: 0, t: 0 });
    const pct = successRate.t > 0 ? Math.round(successRate.s / successRate.t * 100) : 0;
    console.log(`│ 🤖 SAFLA  ${bar(pct, 100)}  ${pct}% ok           │`);
  }

  if (opt) {
    console.log(`│ ⚡ OptSav ${bar(opt.avg_saved_pct, 100)}  ${opt.avg_saved_pct}% saved        │`);
  }

  console.log('└────────────────────────────────────────────────┘');
}

module.exports = { generateReport, printASCII };
