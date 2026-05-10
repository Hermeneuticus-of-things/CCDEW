'use strict';
/**
 * Session snapshot — captures everything a session learned + cost + perf
 * into a single JSON, so future sessions can diff/compare/analyze.
 *
 * Triggered by:
 *   - /exit slash command (manual)
 *   - SessionEnd hook (automatic, end of every session)
 *
 * Stored at .claude-flow/sessions/session-<localISO>.json
 *
 * Schema (v1.0):
 *   {
 *     version: '1.0',
 *     session_id, started_at, ended_at, duration_sec,
 *     cost: { today_start, today_end, today_delta, calls_delta },
 *     safla: { sessions, total_feedbacks, nodes_summary },
 *     instincts: { patterns_count, log_entries },
 *     skills: { suggested_total, by_skill, dead_skills },
 *     perf: { metric_name -> { p95, latest } },
 *     audit: { last_pass, last_warn, last_fail, last_ts },
 *     errors: { count_24h, top_3_scopes },
 *     workspace: { loc, modules, tests }
 *   }
 */

const fs = require('fs');
const path = require('path');
const { writeAtomicJson } = require('./atomic-write.cjs');
const { todayLocal, isoLocal } = require('./local-date.cjs');

const WORK = process.cwd();
const SESSIONS_DIR = path.join(WORK, '.claude-flow', 'sessions');
const DATA_DIR = path.join(WORK, '.claude-flow', 'data');
const REPORTS_DIR = path.join(WORK, '.claude-flow', 'reports');
const LOGS_DIR = path.join(WORK, '.claude-flow', 'logs');
const OBSIDIAN_SESSIONS_DIR = path.join(WORK, '_MEMORY', 'sessions');

function ensureDir() {
  if (!fs.existsSync(SESSIONS_DIR)) fs.mkdirSync(SESSIONS_DIR, { recursive: true });
}

function readJSON(p) {
  try { if (fs.existsSync(p)) return JSON.parse(fs.readFileSync(p, 'utf-8')); } catch {}
  return null;
}

function captureCost() {
  try {
    const codeburn = require('../codeburn.cjs');
    const t = codeburn.totals({ fresh: true });
    return {
      source: t.source,
      today_cost: t.today_cost,
      today_calls: t.today_calls,
      month_cost: t.month_cost,
      month_calls: t.month_calls,
    };
  } catch { return { source: 'unavailable' }; }
}

function captureSafla() {
  const data = readJSON(path.join(DATA_DIR, 'safla.json'));
  if (!data) return null;
  const nodes = {};
  for (const [k, v] of Object.entries(data.nodes || {})) {
    if (!/^[1-9]$/.test(k)) continue;
    const total = (v.success || 0) + (v.failure || 0);
    nodes[k] = {
      success: v.success || 0,
      failure: v.failure || 0,
      rate: total > 0 ? +(v.success / total).toFixed(3) : 0,
      weight_adj: +(v.weight_adj || 0).toFixed(3),
    };
  }
  return {
    sessions: data.sessions || 0,
    total_feedbacks: data.total_feedbacks || 0,
    nodes,
  };
}

function captureInstincts() {
  try {
    const ins = require('../instincts.cjs');
    return ins.stats();
  } catch { return null; }
}

function captureSkills() {
  try {
    const sa = require('../skills-activator.cjs');
    const stats = sa.usageStats ? sa.usageStats() : { total: 0, by_skill: {} };
    const dead = sa.deadSkills ? sa.deadSkills() : [];
    return {
      suggested_total: stats.total,
      unique_skills: Object.keys(stats.by_skill).length,
      top_5: Object.entries(stats.by_skill).sort((a, b) => b[1] - a[1]).slice(0, 5),
      dead_count: dead.length,
    };
  } catch { return null; }
}

function capturePerf() {
  try {
    const perf = require('./perf-baseline.cjs');
    return perf.summary();
  } catch { return null; }
}

function captureAudit() {
  if (!fs.existsSync(REPORTS_DIR)) return null;
  const files = fs.readdirSync(REPORTS_DIR).filter(f => f.startsWith('evaluate-')).sort();
  if (files.length === 0) return null;
  const latest = readJSON(path.join(REPORTS_DIR, files[files.length - 1]));
  if (!latest || !latest.summary) return null;
  return {
    pass: latest.summary.pass,
    warn: latest.summary.warn,
    fail: latest.summary.fail,
    audits_total: files.length,
  };
}

function captureErrors() {
  const logFile = path.join(LOGS_DIR, 'errors.jsonl');
  if (!fs.existsSync(logFile)) return { count_24h: 0, top_scopes: {} };
  try {
    const lines = fs.readFileSync(logFile, 'utf-8').trim().split('\n').filter(Boolean);
    const cutoff = Date.now() - 24 * 60 * 60 * 1000;
    const scopes = {};
    let recent = 0;
    for (const line of lines) {
      try {
        const e = JSON.parse(line);
        if (new Date(e.ts).getTime() > cutoff) {
          recent++;
          scopes[e.scope] = (scopes[e.scope] || 0) + 1;
        }
      } catch {}
    }
    const top = Object.entries(scopes).sort((a, b) => b[1] - a[1]).slice(0, 3);
    return { count_24h: recent, top_scopes: Object.fromEntries(top) };
  } catch { return { count_24h: 0, top_scopes: {} }; }
}

function captureWorkspace() {
  let loc = 0, modules = 0;
  const helpersDir = path.join(WORK, '.claude', 'helpers');
  if (fs.existsSync(helpersDir)) {
    const walk = (d) => {
      for (const f of fs.readdirSync(d)) {
        const full = path.join(d, f);
        const stat = fs.statSync(full);
        if (stat.isDirectory() && !f.startsWith('.') && f !== 'tests') walk(full);
        else if (/\.(cjs|js|mjs)$/.test(f) && !f.endsWith('.test.cjs')) {
          loc += fs.readFileSync(full, 'utf-8').split('\n').length;
          modules++;
        }
      }
    };
    walk(helpersDir);
  }
  let tests = 0;
  const testsDir = path.join(helpersDir, 'tests');
  if (fs.existsSync(testsDir)) tests = fs.readdirSync(testsDir).filter(f => f.endsWith('.test.cjs')).length;
  return { loc, modules, test_suites: tests };
}

function snapshot(opts = {}) {
  ensureDir();
  const now = new Date();
  const snap = {
    version: '1.0',
    session_id: opts.sessionId || process.env.CLAUDE_SESSION_ID || `s-${Date.now()}`,
    started_at: opts.startedAt || null,
    ended_at: isoLocal(now),
    duration_sec: opts.startedAt ? Math.round((now.getTime() - new Date(opts.startedAt).getTime()) / 1000) : null,
    cost: captureCost(),
    safla: captureSafla(),
    instincts: captureInstincts(),
    skills: captureSkills(),
    perf: capturePerf(),
    audit: captureAudit(),
    errors: captureErrors(),
    workspace: captureWorkspace(),
    note: opts.note || '',
  };
  const fileTs = todayLocal(now) + 'T' + now.toTimeString().slice(0, 8).replace(/:/g, '-') + '-' + process.pid;
  const file = path.join(SESSIONS_DIR, `session-${fileTs}.json`);
  writeAtomicJson(file, snap);

  let obsidianFile = null;
  if (fs.existsSync(path.join(WORK, '_MEMORY'))) {
    try {
      if (!fs.existsSync(OBSIDIAN_SESSIONS_DIR)) fs.mkdirSync(OBSIDIAN_SESSIONS_DIR, { recursive: true });
      obsidianFile = path.join(OBSIDIAN_SESSIONS_DIR, `session-${fileTs}.md`);
      fs.writeFileSync(obsidianFile, renderObsidian(snap), 'utf-8');
    } catch (e) {
      try { require('./error-log.cjs').logError('session-snapshot.obsidian', e); } catch {}
      obsidianFile = null;
    }
  }
  return { file, obsidianFile, snapshot: snap };
}

function renderObsidian(s) {
  const tags = ['session', 'snapshot', 'ccdew'];
  if (s.audit && s.audit.fail > 0) tags.push('audit-fail');
  if (s.errors && s.errors.count_24h > 5) tags.push('errors-high');

  const lines = [];
  lines.push('---');
  lines.push(`name: Session snapshot ${s.ended_at}`);
  lines.push(`description: ${s.note || 'auto-captured at session end'}`);
  lines.push(`session_id: ${s.session_id}`);
  lines.push(`ended_at: ${s.ended_at}`);
  lines.push(`type: session`);
  lines.push(`tags: [${tags.join(', ')}]`);
  if (s.cost && s.cost.source !== 'unavailable') {
    lines.push(`cost_today: ${s.cost.today_cost}`);
    lines.push(`cost_calls: ${s.cost.today_calls}`);
  }
  if (s.audit) {
    lines.push(`audit_pass: ${s.audit.pass}`);
    lines.push(`audit_fail: ${s.audit.fail}`);
  }
  if (s.workspace) {
    lines.push(`workspace_loc: ${s.workspace.loc}`);
    lines.push(`workspace_tests: ${s.workspace.test_suites}`);
  }
  lines.push('---');
  lines.push('');
  lines.push(`# Session ${s.ended_at}`);
  lines.push('');
  if (s.note) { lines.push(`> ${s.note}`); lines.push(''); }

  if (s.cost && s.cost.source !== 'unavailable') {
    lines.push('## 💰 Cost');
    lines.push(`- **Today:** $${s.cost.today_cost.toFixed(2)} (${s.cost.today_calls} calls)`);
    lines.push(`- **Month:** $${s.cost.month_cost.toFixed(2)} (${s.cost.month_calls} calls)`);
    lines.push(`- **Source:** ${s.cost.source}`);
    lines.push('');
  }

  if (s.safla) {
    lines.push('## 🤖 SAFLA');
    lines.push(`- Sessions: ${s.safla.sessions} · Total feedbacks: ${s.safla.total_feedbacks}`);
    lines.push('');
    if (Object.keys(s.safla.nodes).length > 0) {
      lines.push('| Node | Success | Failure | Rate | Adj |');
      lines.push('|---|---|---|---|---|');
      for (const [k, v] of Object.entries(s.safla.nodes).sort()) {
        lines.push(`| ${k} | ${v.success} | ${v.failure} | ${(v.rate * 100).toFixed(0)}% | ${v.weight_adj >= 0 ? '+' : ''}${v.weight_adj} |`);
      }
      lines.push('');
    }
  }

  if (s.audit) {
    lines.push('## 📊 Audit');
    lines.push(`- ${s.audit.pass} PASS · ${s.audit.warn} WARN · **${s.audit.fail} FAIL**`);
    lines.push(`- Total audits all-time: ${s.audit.audits_total}`);
    lines.push('');
  }

  if (s.skills) {
    lines.push('## 🎯 Skills');
    lines.push(`- Suggested total: ${s.skills.suggested_total}`);
    lines.push(`- Unique: ${s.skills.unique_skills}`);
    lines.push(`- **Dead:** ${s.skills.dead_count}`);
    if (s.skills.top_5 && s.skills.top_5.length > 0) {
      lines.push('- Top 5:');
      for (const [name, count] of s.skills.top_5) lines.push(`  - \`${name}\` × ${count}`);
    }
    lines.push('');
  }

  if (s.errors && s.errors.count_24h > 0) {
    lines.push('## ⚠ Errors (last 24h)');
    lines.push(`- Total: ${s.errors.count_24h}`);
    if (s.errors.top_scopes && Object.keys(s.errors.top_scopes).length > 0) {
      for (const [scope, count] of Object.entries(s.errors.top_scopes)) {
        lines.push(`  - \`${scope}\` × ${count}`);
      }
    }
    lines.push('');
  }

  if (s.workspace) {
    lines.push('## 📂 Workspace');
    lines.push(`- LOC: ${s.workspace.loc}`);
    lines.push(`- Modules: ${s.workspace.modules}`);
    lines.push(`- Test suites: ${s.workspace.test_suites}`);
    lines.push('');
  }

  if (s.perf && Object.keys(s.perf).length > 0) {
    lines.push('## ⚡ Performance baseline');
    for (const [metric, data] of Object.entries(s.perf)) {
      lines.push(`- \`${metric}\`: latest **${data.latest_ms}ms** · p95 ${data.baseline_p95_ms}ms · ${data.samples} samples`);
    }
    lines.push('');
  }

  lines.push('---');
  lines.push('## Related');
  lines.push('- [_DASHBOARD](../_DASHBOARD.md)');
  lines.push('- [Decisions Index](../decisions/INDEX.md)');

  return lines.join('\n') + '\n';
}

function listSessions(n = 10) {
  if (!fs.existsSync(SESSIONS_DIR)) return [];
  return fs.readdirSync(SESSIONS_DIR)
    .filter(f => f.startsWith('session-') && f.endsWith('.json'))
    .sort().slice(-n)
    .map(f => path.join(SESSIONS_DIR, f));
}

function compare(latestN = 5) {
  const files = listSessions(latestN);
  if (files.length < 2) return { error: `need ≥2 sessions, have ${files.length}` };
  const snaps = files.map(f => {
    const s = readJSON(f);
    if (s && !s.ended_at) {
      try { s.ended_at = fs.statSync(f).mtime.toISOString(); } catch {}
    }
    return s;
  }).filter(Boolean);
  const fields = ['cost.today_cost', 'cost.today_calls', 'safla.total_feedbacks', 'audit.pass', 'audit.fail', 'workspace.loc', 'workspace.test_suites'];
  const get = (obj, dotted) => dotted.split('.').reduce((o, k) => o == null ? null : o[k], obj);
  const rows = [];
  for (const f of fields) {
    rows.push({
      metric: f,
      values: snaps.map(s => get(s, f)),
    });
  }
  return { sessions: snaps.map(s => s.ended_at), rows };
}

module.exports = { snapshot, listSessions, compare };
