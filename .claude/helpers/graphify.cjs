'use strict';
const fs = require('fs');
const path = require('path');
const { isEnabled } = require('./lib/flags.cjs');
const { isValidNodeId } = require('./lib/validate.cjs');

const DATA_DIR    = path.join(process.cwd(), '.claude-flow', 'data');
const REPORTS_DIR = path.join(process.cwd(), '.claude-flow', 'reports');

const NODE_NAMES = {
  '1': 'Reformer', '2': 'Integrator', '3': 'Builder',
  '4': 'Contextualizer', '5': 'Analyzer', '6': 'Validator',
  '7': 'Innovator', '8': 'Orchestrator', '9': 'Consolidator',
};

function readJSON(p) {
  try { if (fs.existsSync(p)) return JSON.parse(fs.readFileSync(p, 'utf-8')); } catch {}
  return null;
}

function ensureDirs() {
  if (!fs.existsSync(DATA_DIR))    fs.mkdirSync(DATA_DIR,    { recursive: true });
  if (!fs.existsSync(REPORTS_DIR)) fs.mkdirSync(REPORTS_DIR, { recursive: true });
}

function getBurnData() {
  const c = readJSON(path.join(DATA_DIR, 'codeburn-cache.json'));
  if (c && c.today_cost !== undefined) {
    return { today_cost: c.today_cost, month_cost: c.month_cost,
             today_calls: c.today_calls, month_calls: c.month_calls };
  }
  return null;
}

function getSaflaData() {
  const d = readJSON(path.join(DATA_DIR, 'safla.json'));
  if (!d) return null;
  const validNodes = {};
  for (const [k, v] of Object.entries(d.nodes || {})) {
    if (isValidNodeId(k)) validNodes[k] = v;
  }
  return {
    sessions: d.sessions || 0,
    feedbacks: d.total_feedbacks || 0,
    nodes: validNodes,
  };
}

function getGraphData() {
  const d = readJSON(path.join(DATA_DIR, 'graph-state.json'));
  if (!d) return null;
  return { nodes: Object.keys(d.nodes || {}).length, edges: (d.edges || []).length };
}

function getOptData() {
  const p = path.join(DATA_DIR, 'auto-optimize.jsonl');
  if (!fs.existsSync(p)) return null;
  try {
    const lines = fs.readFileSync(p, 'utf-8').trim().split('\n').filter(Boolean);
    const entries = lines.map(l => { try { return JSON.parse(l); } catch { return null; } }).filter(Boolean);
    if (entries.length === 0) return null;
    const avg = Math.round(entries.reduce((s, e) => s + (e.savedPct || 0), 0) / entries.length);
    return { prompts: entries.length, avg_saved_pct: avg };
  } catch { return null; }
}

function getObsidianData() {
  const p = path.join(DATA_DIR, 'session-critical-index.json');
  const idx = readJSON(p);
  if (!idx) return null;
  const all = idx.all || Object.values(idx.by_project || {}).flat();
  return {
    entries: all.length,
    tags: Object.keys(idx.by_tag || {}).length,
    projects: Object.keys(idx.by_project || {}).length,
  };
}

function bar(value, max, width = 20) {
  const filled = max > 0 ? Math.round((value / max) * width) : 0;
  return '█'.repeat(Math.max(0, Math.min(width, filled))) + '░'.repeat(Math.max(0, width - filled));
}

function buildReport() {
  const burn  = getBurnData();
  const safla = getSaflaData();
  const graph = getGraphData();
  const opt   = getOptData();
  const obs   = getObsidianData();

  const out = [];
  out.push('# Graphify Session Report');
  out.push(`**Generated:** ${new Date().toISOString()}`);
  out.push('');
  out.push('## CodeBurn (real)');
  if (burn) {
    out.push(`- Today: **$${burn.today_cost.toFixed(2)}** (${burn.today_calls} calls)`);
    out.push(`- Month: **$${burn.month_cost.toFixed(2)}** (${burn.month_calls} calls)`);
  } else {
    out.push('_No data — run: codeburn status_');
  }
  out.push('');
  out.push('## SAFLA — Agent Performance');
  if (safla && safla.feedbacks > 0) {
    out.push(`- Sessions: ${safla.sessions} | Total feedbacks: ${safla.feedbacks}`);
    out.push('');
    out.push('| Node | Name | Success% | Adj | Last task |');
    out.push('|---|---|---|---|---|');
    for (const [nid, node] of Object.entries(safla.nodes)) {
      const total = (node.success || 0) + (node.failure || 0);
      if (total === 0) continue;
      const rate = Math.round((node.success / total) * 100);
      const adj = (node.weight_adj || 0) >= 0
        ? '+' + (node.weight_adj || 0).toFixed(2)
        : (node.weight_adj || 0).toFixed(2);
      out.push(`| ${nid} | ${NODE_NAMES[nid] || '?'} | ${rate}% | ${adj} | ${node.last_task || '-'} |`);
    }
  } else {
    out.push('_No feedback recorded yet_');
  }
  out.push('');
  out.push('## Intelligence Graph');
  out.push(graph ? `- Nodes: ${graph.nodes} | Edges: ${graph.edges}` : '_No graph data_');
  out.push('');
  out.push('## Auto-Optimize');
  if (opt) {
    out.push(`- Prompts analyzed: ${opt.prompts}`);
    out.push(`- Average token savings: ${opt.avg_saved_pct}%`);
  } else {
    out.push('_No optimization data_');
  }
  out.push('');
  out.push('## Obsidian Context');
  if (obs) {
    out.push(`- Entries loaded: ${obs.entries}`);
    out.push(`- Tags: ${obs.tags} | Projects: ${obs.projects}`);
  } else {
    out.push('_No Obsidian index_');
  }
  return out.join('\n');
}

function generateReport() {
  if (!isEnabled('graphify')) return null;
  ensureDirs();
  const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
  const file = path.join(REPORTS_DIR, `session-${ts}.md`);
  fs.writeFileSync(file, buildReport(), 'utf-8');
  return file;
}

function printASCII() {
  if (!isEnabled('graphify')) return;
  const burn = getBurnData();
  const safla = getSaflaData();
  const opt = getOptData();
  console.log('┌─────────────── Graphify Summary ───────────────┐');
  if (burn) {
    const pct = Math.min(burn.today_cost / 15, 1);
    console.log(`│ 🔥 Today  ${bar(pct * 20, 20)} $${burn.today_cost.toFixed(2)} / ${burn.today_calls} calls    │`);
  }
  if (safla && safla.feedbacks > 0) {
    const acc = Object.values(safla.nodes).reduce((s, n) => {
      const total = (n.success || 0) + (n.failure || 0);
      return total > 0 ? { s: s.s + n.success, t: s.t + total } : s;
    }, { s: 0, t: 0 });
    const pct = acc.t > 0 ? Math.round(acc.s / acc.t * 100) : 0;
    console.log(`│ 🤖 SAFLA  ${bar(pct, 100)}  ${pct}% ok           │`);
  }
  if (opt) {
    console.log(`│ ⚡ OptSav ${bar(opt.avg_saved_pct, 100)}  ${opt.avg_saved_pct}% saved        │`);
  }
  console.log('└────────────────────────────────────────────────┘');
}

module.exports = { generateReport, printASCII };
