#!/usr/bin/env node
'use strict';
/**
 * Hook Handler v3.0 — lazy-require dispatcher
 * Top-level imports: path, fs, lib/flags, lib/platform only.
 * Per-command modules are loaded on demand.
 */

const path = require('path');
const fs = require('fs');
const { isEnabled, load: loadFlags } = require('./lib/flags.cjs');
const { findPython } = require('./lib/platform.cjs');
const { t } = require('./lib/strings.cjs');

const helpersDir = __dirname;
const PYTHON_BIN = findPython() || 'python3';

const _moduleCache = {};
function lazy(name) {
  if (name in _moduleCache) return _moduleCache[name];
  const candidates = [
    path.join(helpersDir, name + '.cjs'),
    path.join(helpersDir, name + '.js'),
    path.join(helpersDir, name, 'index.cjs'),
    path.join(helpersDir, name, 'index.js'),
  ];
  for (const c of candidates) {
    if (!fs.existsSync(c)) continue;
    try {
      const origLog = console.log, origErr = console.error;
      console.log = () => {}; console.error = () => {};
      try { _moduleCache[name] = require(c); }
      finally { console.log = origLog; console.error = origErr; }
      return _moduleCache[name];
    } catch { /* try next */ }
  }
  _moduleCache[name] = null;
  return null;
}

const NODE_MAP_PATH = path.join(helpersDir, 'workspace_node_map.json');
let _nodeMap = null;
function loadNodeMap() {
  if (_nodeMap) return _nodeMap;
  try {
    if (fs.existsSync(NODE_MAP_PATH)) _nodeMap = JSON.parse(fs.readFileSync(NODE_MAP_PATH, 'utf8'));
  } catch { /* non-fatal */ }
  return _nodeMap || {};
}

const HEXAD_NODES = new Set([1, 2, 4, 5, 7, 8]);
const TRIANGLE_NODES = new Set([3, 6, 9]);

function selectWorkflow(task, routeResult) {
  const nodeMap = loadNodeMap();
  const templates = nodeMap.workflow_templates || {};
  const i18n = require('./lib/i18n.cjs');
  const words = i18n.tokensOf(task);
  const hexadKws    = (templates.hexad    || {}).trigger_keywords || [];
  const triangleKws = (templates.triangle || {}).trigger_keywords || [];
  let hexadScore    = words.filter(w => hexadKws.includes(w) || i18n.KEYWORDS_HEXAD.has(w)).length;
  let triangleScore = words.filter(w => triangleKws.includes(w) || i18n.KEYWORDS_TRIANGLE.has(w)).length;
  if (routeResult && routeResult.node) {
    if (HEXAD_NODES.has(routeResult.node))    hexadScore += 1;
    if (TRIANGLE_NODES.has(routeResult.node)) triangleScore += 1;
  }
  const type = hexadScore > triangleScore ? 'hexad' : 'triangle';
  const tmpl = templates[type] || {};
  return {
    type, path: tmpl.path || [], agents: tmpl.agents || [],
    description: tmpl.description || '',
    hexadScore, triangleScore,
    confidence: hexadScore !== triangleScore ? 'high' : 'low',
  };
}

const INTELLIGENCE_TIMEOUT_MS = 3000;
function runWithTimeout(fn, label) {
  return new Promise((resolve) => {
    let settled = false;
    const timer = setTimeout(() => {
      if (settled) return;
      settled = true;
      process.stderr.write(`[WARN] ${label} timed out after ${INTELLIGENCE_TIMEOUT_MS}ms\n`);
      resolve(null);
    }, INTELLIGENCE_TIMEOUT_MS);
    Promise.resolve().then(() => fn()).then((r) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve(r);
    }).catch(() => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve(null);
    });
  });
}

const [,, command, ...args] = process.argv;

async function readStdin() {
  if (process.stdin.isTTY) return '';
  return new Promise((resolve) => {
    let data = '';
    const timer = setTimeout(() => {
      process.stdin.removeAllListeners();
      process.stdin.pause();
      resolve(data);
    }, 500);
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', (c) => { data += c; });
    process.stdin.on('end', () => { clearTimeout(timer); resolve(data); });
    process.stdin.on('error', () => { clearTimeout(timer); resolve(data); });
    process.stdin.resume();
  });
}

async function main() {
  const safetyTimer = setTimeout(() => {
    process.stderr.write('[WARN] Hook handler global timeout (5s)\n');
    process.exit(0);
  }, 5000);
  safetyTimer.unref();

  let stdinData = '';
  try { stdinData = await readStdin(); } catch { /* ignore */ }
  let hookInput = {};
  if (stdinData.trim()) {
    try { hookInput = JSON.parse(stdinData); } catch { /* ignore */ }
  }
  const toolInput = hookInput.toolInput || hookInput.tool_input || {};
  const prompt = hookInput.prompt
    || hookInput.command
    || toolInput.command
    || toolInput.file_path
    || toolInput.prompt
    || process.env.PROMPT
    || args.join(' ')
    || '';

  const handlers = {
    'route': () => {
      const ssa = lazy('ssa');
      const intelligence = lazy('intelligence');
      const autoOptimize = lazy('auto-optimize');
      const redHat = lazy('red-hat-evaluator');
      const langGraph = lazy('langgraph-micro');
      const router = lazy('router');
      const safla = lazy('safla');

      if (ssa) {
        try {
          if (intelligence && intelligence.getContext) {
            const ctx = intelligence.getContext(prompt);
            if (ctx) console.log(typeof ctx === 'string' ? ctx : JSON.stringify(ctx));
          }
          const obsEntries = ssa.loadObsidianEntries ? ssa.loadObsidianEntries() : [];
          if (obsEntries.length > 0) {
            const filtered = ssa.filterContext(prompt, obsEntries, { top_k: 3, min_score: 0.1 });
            if (filtered.length > 0) {
              const titles = filtered.map(e => e.title || e.id).filter(Boolean).join(', ');
              console.log(`[OBS] Context relevant: ${titles}`);
            }
          }
        } catch { /* non-fatal */ }
      }
      if (autoOptimize) { try { autoOptimize.analyze(prompt); } catch { /* non-fatal */ } }
      if (redHat) { try { redHat.evaluate(prompt); } catch { /* non-fatal */ } }
      if (langGraph && prompt) {
        try {
          const wf = langGraph.startWorkflow(prompt);
          if (wf) console.log(`[LG] Started: ${wf.graph_name} | ${wf.nodes.join('→')}`);
        } catch { /* non-fatal */ }
      }
      if (router && router.routeTask) {
        const result = router.routeTask(prompt);
        if (safla) {
          try {
            const adj = safla.getWeightAdj(result.node);
            if (adj && !isNaN(adj)) result.confidence = Math.max(0, Math.min(1, result.confidence + adj));
            const h = safla.hint(result.node);
            if (h) console.log(h);
          } catch { /* non-fatal */ }
        }
        const wf = selectWorkflow(prompt, result);
        const seq = wf.agents.join(' → ');
        console.log([
          `[INFO] Routing task: ${prompt.substring(0, 80) || '(no prompt)'}`,
          '+------------------- Primary Recommendation -------------------+',
          `| Agent: ${result.agent.padEnd(53)}|`,
          `| Node:  ${('Node ' + result.node + ' — ' + (result.node_name || '')).substring(0, 53).padEnd(53)}|`,
          `| Confidence: ${(result.confidence * 100).toFixed(1)}%${' '.repeat(44)}|`,
          `| Reason: ${(result.reason || '').substring(0, 53).padEnd(53)}|`,
          '+--------------------------------------------------------------+',
          `| Workflow: ${wf.type.toUpperCase()} [${wf.confidence}]`.padEnd(63) + '|',
          `| Path: ${seq.substring(0, 55).padEnd(55)}|`,
          '+--------------------------------------------------------------+',
        ].join('\n'));
      } else {
        console.log('[INFO] Router not available');
      }
    },

    'pre-bash': () => {
      const cmd = (hookInput.command || prompt || '').toLowerCase();
      const dangerous = [
        /(^|[;&|`]|\$\()\s*rm\s+-rf\s+\/(\s|$)/,
        /(^|[;&|`]|\$\()\s*format\s+c:/,
        /(^|[;&|`]|\$\()\s*del\s+\/s\s+\/q\s+c:\\/,
        /:\(\)\s*\{\s*:\|:&\s*\}\s*;:/,
      ];
      for (const re of dangerous) {
        if (re.test(cmd)) {
          console.error(`[BLOCKED] Dangerous command: ${re}`);
          process.exit(1);
        }
      }

      const isCommit = /\bgit\s+commit\b/i.test(cmd);
      const isPush   = /\bgit\s+push\b/i.test(cmd) && !/--no-verify/i.test(cmd);
      if ((isCommit || isPush) && process.env.HOOKS_SKIP !== '1') {
        try {
          const { spawnSync } = require('child_process');
          const which = isPush ? 'quality-gate' : 'verify';
          const r = spawnSync(process.execPath, [path.join(helpersDir, which + '.cjs')], {
            encoding: 'utf-8', timeout: 60_000, stdio: ['ignore', 'pipe', 'pipe'],
          });
          if (r.status !== 0) {
            console.error(`[AUTO-${which.toUpperCase()}] FAILED before ${isPush ? 'push' : 'commit'}. Bypass: HOOKS_SKIP=1`);
            process.exit(1);
          }
          console.log(`[AUTO-${which.toUpperCase()}] passed`);
        } catch { /* don't block on hook bug */ }
      }
      console.log('[OK] Command validated');
    },

    'auto-audit': () => {
      try {
        const lastP = path.join(process.cwd(), '.claude-flow', 'reports', 'auto-audit-last.json');
        if (fs.existsSync(lastP)) {
          const last = JSON.parse(fs.readFileSync(lastP, 'utf8'));
          const ageH = (Date.now() - new Date(last.ts).getTime()) / 36e5;
          if (ageH < 24) { console.log(`[AUTO-AUDIT] last run ${ageH.toFixed(1)}h ago — skipping`); return; }
        }
        const { spawnSync } = require('child_process');
        const r = spawnSync(process.execPath, [path.join(helpersDir, 'evaluate-setup.cjs'), '--json'], {
          encoding: 'utf-8', timeout: 15_000, stdio: ['ignore', 'pipe', 'ignore'],
        });
        const lines = (r.stdout || '').split('\n').filter(l => l.trim().startsWith('{'));
        const json = lines.length > 0 ? JSON.parse(lines[lines.length - 1]) : null;
        if (json && json.summary) {
          fs.mkdirSync(path.dirname(lastP), { recursive: true });
          fs.writeFileSync(lastP, JSON.stringify({ ts: new Date().toISOString(), summary: json.summary }), 'utf-8');
          if (json.summary.fail > 0 || json.summary.warn > 2) {
            console.log(`[AUTO-AUDIT] ⚠ ${json.summary.fail} FAIL · ${json.summary.warn} WARN — run: npm run audit:fix`);
          } else {
            console.log(`[AUTO-AUDIT] ✓ ${json.summary.pass} PASS`);
          }
        }
      } catch (e) { try { require('./lib/error-log.cjs').logError('auto-audit', e); } catch {} }
    },

    'pre-edit': () => {
      const file = toolInput.file_path || process.env.TOOL_INPUT_file_path || '';
      const newContent = toolInput.content || toolInput.new_string || '';

      const secretScan = lazy('secret-scan');
      if (secretScan && (file || newContent)) {
        const r = secretScan.check({ filePath: file, content: newContent });
        if (!r.safe) {
          console.error(`[BLOCKED] Secret leak risk: ${r.reason}`);
          process.exit(1);
        }
      }

      const sensitive = ['.claude/settings.json', 'CLAUDE.md', '.gitignore'];
      if (file && sensitive.some(s => file.endsWith(s))) {
        console.log(`[PRE-EDIT] ⚠️  Editing sensitive file: ${path.basename(file)}`);
      }
      const projectScope = lazy('project-scope');
      if (file && projectScope) {
        try {
          const active = projectScope.getActive(prompt);
          const warn = projectScope.preEditWarning(file, active);
          if (warn) console.log(warn);
        } catch { /* non-fatal */ }
      }
      console.log('[OK] Edit validated');
    },

    'post-bash': () => {
      const exitCode = hookInput.exit_code ?? hookInput.exitCode ?? null;
      const userTask = process.env.CLAUDE_USER_PROMPT || '';
      if (exitCode !== null && exitCode >= 2 && userTask.trim().split(/\s+/).length >= 4) {
        const safla = lazy('safla');
        const router = lazy('router');
        if (safla && router && router.routeTask) {
          try {
            const r = router.routeTask(userTask);
            safla.recordOutcome(r.node, false, `bash exit:${exitCode}`);
          } catch { /* non-fatal */ }
        }
      }
      console.log('[OK] Bash completed');
    },

    'post-edit': () => {
      const session = lazy('session');
      const intelligence = lazy('intelligence');
      const codeburn = lazy('codeburn');
      const editedFile = hookInput.file_path || toolInput.file_path
        || process.env.TOOL_INPUT_file_path || args[0] || '';
      if (session && session.metric) { try { session.metric('edits'); } catch { /* */ } }
      if (intelligence && intelligence.recordEdit) {
        try { intelligence.recordEdit(editedFile); } catch { /* */ }
      }
      if (codeburn) {
        try {
          const s = codeburn.statusLine();
          if (s) console.log(s);
        } catch { /* */ }
      }
      console.log('[OK] Edit recorded');
    },

    'status': () => {
      const flags = loadFlags();
      const active = Object.entries(flags.components || {}).filter(([,v]) => v).map(([k]) => k).join(', ');
      const codeburn = lazy('codeburn');
      if (codeburn) {
        try {
          const t = codeburn.totals();
          if (t.source !== 'unavailable') {
            console.log(`[STATUS] $${(t.today_cost||0).toFixed(2)} today | ${t.today_calls||0} calls | Active: ${active}`);
            return;
          }
        } catch { /* */ }
      }
      console.log(`[STATUS] Session active | Components: ${active}`);
    },

    'notify': () => {
      const msg = hookInput.message || hookInput.notification || prompt || '';
      console.log(msg ? `[NOTIFY] ${msg.substring(0, 120)}` : '[NOTIFY] Notification received');
    },

    'session-restore': async () => {
      const session = lazy('session');
      const intelligence = lazy('intelligence');
      const safla = lazy('safla');
      if (session) {
        const existing = session.restore && session.restore();
        if (!existing && session.start) session.start();
      } else {
        console.log('[INFO] Session restored');
      }
      if (intelligence && intelligence.init) {
        const r = await runWithTimeout(() => intelligence.init(), 'intelligence.init()');
        if (r && r.nodes > 0) console.log(`[INTELLIGENCE] Loaded ${r.nodes} patterns, ${r.edges} edges`);
      }
      if (safla) { try { safla.sessionStart(); } catch { /* */ } }
      try {
        const { execSync } = require('child_process');
        const obsScript = path.join(helpersDir, 'obsidian-session-context.py');
        if (fs.existsSync(obsScript)) {
          const out = execSync(`${PYTHON_BIN} "${obsScript}"`, {
            encoding: 'utf-8', timeout: 5000, stdio: ['ignore', 'pipe', 'ignore'],
          }).trim();
          if (out) console.log(out);
        }
      } catch { /* non-fatal — Python or script may be absent */ }
    },

    'session-end': async () => {
      const intelligence = lazy('intelligence');
      const codeburn = lazy('codeburn');
      const graphify = lazy('graphify');
      const metricsUpdate = lazy('metrics-update');
      const safla = lazy('safla');
      const langGraph = lazy('langgraph-micro');
      const session = lazy('session');

      if (intelligence && intelligence.consolidate) {
        const r = await runWithTimeout(() => intelligence.consolidate(), 'intelligence.consolidate()');
        if (r && r.entries > 0) console.log(`[INTELLIGENCE] Consolidated: ${r.entries} entries, ${r.edges} edges`);
      }
      if (codeburn) {
        try {
          const t = codeburn.totals();
          if (t.source !== 'unavailable') {
            console.log(`[CODEBURN] Today $${(t.today_cost||0).toFixed(2)} / ${t.today_calls||0} calls | Month $${(t.month_cost||0).toFixed(2)}`);
          }
        } catch { /* */ }
      }
      if (graphify) {
        try {
          const p = graphify.generateReport();
          if (p) console.log(`[GRAPHIFY] Report: ${p}`);
          graphify.printASCII();
        } catch { /* */ }
      }
      if (metricsUpdate && codeburn) {
        try {
          const t = codeburn.totals();
          if (metricsUpdate.run) metricsUpdate.run(t);
          if (safla && safla.syncWithCodeBurn) safla.syncWithCodeBurn(t);
        } catch { /* */ }
      }
      if (langGraph && langGraph.clearActive) { try { langGraph.clearActive(); } catch { /* */ } }
      try {
        const ss = require(path.join(helpersDir, 'lib', 'session-snapshot.cjs'));
        const r = ss.snapshot({ note: 'auto-saved at SessionEnd' });
        console.log(`[SESSION-SNAPSHOT] saved: ${path.basename(r.file)}`);
      } catch { /* non-fatal */ }
      try {
        const perf = require(path.join(helpersDir, 'lib', 'perf-baseline.cjs'));
        const ssa = lazy('ssa');
        if (ssa && ssa.filterContext) {
          const corpus = Array.from({ length: 50 }, (_, i) => ({ id: 'e-' + i, text: 'note ' + i, pinned: i < 2, score: 0.5 }));
          const t0 = process.hrtime.bigint();
          ssa.filterContext('refactor', corpus, { topK: 12 });
          const ms = Number(process.hrtime.bigint() - t0) / 1e6;
          const r = perf.record('ssa.filterContext', ms);
          if (r && r.regression) console.log(`[PERF] 🚨 ssa.filterContext regression: ${r.current_ms}ms vs baseline ${r.baseline_p95_ms}ms (+${r.delta_pct}%)`);
        }
      } catch { /* non-fatal */ }
      if (session && session.end) session.end();
      else console.log('[OK] Session ended');
    },

    'compact-save': async () => {
      const codeburn = lazy('codeburn');
      const safla = lazy('safla');
      const metricsUpdate = lazy('metrics-update');
      if (codeburn) {
        try {
          const t = codeburn.totals();
          if (t.source !== 'unavailable') {
            if (safla && safla.syncWithCodeBurn) safla.syncWithCodeBurn(t);
            if (metricsUpdate && metricsUpdate.run) metricsUpdate.run(t);
            console.log(`[COMPACT-SAVE] $${(t.today_cost||0).toFixed(2)} today | dashboard updated`);
          }
        } catch { /* */ }
      }
    },

    'pre-task': () => {
      const session = lazy('session');
      const router = lazy('router');
      if (session && session.metric) { try { session.metric('tasks'); } catch { /* */ } }
      if (router && router.routeTask && prompt) {
        const r = router.routeTask(prompt);
        const wf = selectWorkflow(prompt, r);
        console.log(`[INFO] Task → Node ${r.node} (${r.agent}) | ${wf.type.toUpperCase()} [${wf.agents.join('→')}]`);
      } else {
        console.log('[OK] Task started');
      }
    },

    'inject-workflow': () => {
      const router = lazy('router');
      if (!router || !router.routeTask || !prompt) return;
      const words = prompt.trim().split(/\s+/);
      if (words.length < 4) return;

      const result = router.routeTask(prompt);
      const wf = selectWorkflow(prompt, result);
      const ssa = lazy('ssa');
      const safla = lazy('safla');
      const projectScope = lazy('project-scope');

      // AUTO-PROFILE SWITCHER — based on token budget and task complexity
      const currentFlags = loadFlags();
      const currentMode = currentFlags.mode || 'full';
      const todayCost = (() => {
        const cb = lazy('codeburn');
        if (cb) try { return cb.totals().today_cost || 0; } catch {}
        return 0;
      })();
      const budget = currentFlags.codeburn?.daily_budget_usd || 100;
      
      // Auto-switch logic
      let autoProfile = null;
      if (todayCost > budget * 0.9 && currentMode !== 'ssa-max') {
        autoProfile = 'ssa-max';
      } else if (todayCost > budget * 0.75 && currentMode === 'full') {
        autoProfile = 'lite';
      }
      
      if (autoProfile && autoProfile !== currentMode) {
        const profile = currentFlags.profiles?.[autoProfile];
        if (profile) {
          try {
            const FLAGS_PATH = path.join(helpersDir, 'feature-flags.json');
            const updated = JSON.parse(fs.readFileSync(FLAGS_PATH, 'utf-8'));
            updated.mode = autoProfile;
            updated.components = profile.components;
            if (profile.ssa) updated.ssa = profile.ssa;
            fs.writeFileSync(FLAGS_PATH, JSON.stringify(updated, null, 2));
            console.log(`[AUTO-PROFILE] Switched from ${currentMode} → ${autoProfile} (budget ${Math.round(todayCost/budget*100)}% used)`);
          } catch {}
        }
      }

      // Ruflo integration — auto-swarm for complex tasks
      const rufloEnabled = currentFlags.components?.ruflo;
      let rufloHint = '';
      if (rufloEnabled && wf.confidence === 'high' && wf.agents.length >= 3) {
        const ruflo = lazy('ruflo');
        if (ruflo && ruflo.swarmInit) {
          try {
            const swarm = ruflo.swarmInit({
              topology: 'hierarchical',
              maxAgents: wf.type === 'hexad' ? 6 : 3,
              strategy: 'specialized',
              agents: wf.agents,
            });
            if (swarm.ok) {
              rufloHint = ` [RUFLO:${swarm.swarmId}]`;
            }
          } catch { /* non-fatal */ }
        }
      }

      let ssaZoom = 'nano';
      if (words.length > 30) ssaZoom = 'maha';
      else if (words.length > 15) ssaZoom = 'micro';
      const ssaHint = currentFlags.components?.ssa ? `SSA:${ssaZoom.toUpperCase()}` : '';
      const saflaAdj = currentFlags.components?.safla ? (safla ? safla.getWeightAdj(result.node) : 0) : 0;
      const saflaHint = saflaAdj !== 0 ? ` SAFLA:${saflaAdj > 0 ? '+' : ''}${saflaAdj.toFixed(2)}` : '';

      const seq = wf.agents.join(' → ');
      const bfs = wf.path.join('→');
      const maxA = wf.type === 'hexad' ? 6 : 3;
      const altType = wf.type === 'hexad' ? 'TRIANGLE' : 'HEXAD';
      const altAgents = wf.type === 'hexad'
        ? 'coder → tester → memory-specialist (3→6→9)'
        : 'reviewer → researcher → backend-dev → sparc-orchestrator → analyst → architecture (1→4→2→8→5→7)';
      const altMax = wf.type === 'hexad' ? 3 : 6;

      let composeHint = '';
      if (wf.type === 'hexad' && words.length >= 8) {
        try {
          const { spawnSync } = require('child_process');
          const composeScript = path.join(helpersDir, 'enneagram_compose.py');
          if (fs.existsSync(composeScript)) {
            const m = prompt.match(/\b(\d+)\s*(files?|fi[șs]iere|components?|componente|module?s?)\b/i);
            const fileCount = m ? parseInt(m[1], 10) : 5;
            const r = spawnSync(PYTHON_BIN, [composeScript, prompt.substring(0, 120), '--files', String(fileCount), '--json'], {
              encoding: 'utf-8', timeout: 2500, stdio: ['ignore', 'pipe', 'ignore'],
            });
            if (r.status === 0 && r.stdout) {
              const c = JSON.parse(r.stdout);
              if (c.complexity) {
                const ph1 = c.phases && c.phases[0];
                const phLabel = ph1 ? ` → ${(ph1.phase || '').split('—')[0].trim()}` : '';
                composeHint = `Compose: ${c.complexity}${phLabel} (${c.phases ? c.phases.length : 0} phases)`;
                if (c.warnings && c.warnings.length > 0) composeHint += ` ⚠️ ${c.warnings[0].substring(0, 60)}`;
              }
            }
          }
        } catch { /* */ }
      }

      const lines = wf.confidence === 'high' ? [
        `[AUTO-SWARM DIRECTIVE] ${prompt.substring(0, 65)}`,
        `Node ${result.node} (${result.node_name || result.agent}) | ${wf.type.toUpperCase()} | ${ssaHint}${saflaHint}${rufloHint}`,
        `SPAWN: ${seq}`,
        `swarm_init(topology=hierarchical, maxAgents=${maxA}, strategy=specialized)`,
        `BFS: ${bfs}`,
      ] : [
        `[WORKFLOW SUGGESTION] ${prompt.substring(0, 65)}`,
        `Node ${result.node} (${result.node_name || result.agent}) | ${ssaHint}${saflaHint} | ambiguous`,
        `Option A ${wf.type.toUpperCase()} (maxAgents=${maxA}): ${seq} (${bfs})`,
        `Option B ${altType} (maxAgents=${altMax}): ${altAgents}`,
        `Choose A for simple/fast task, B for complex/cross-project`,
      ];
      if (composeHint) lines.push(composeHint);
      if (projectScope) {
        try {
          const active = projectScope.getActive(prompt);
          const h = projectScope.hintLine(active);
          if (h) lines.push(h);
        } catch { /* */ }
      }
      const skillsActivator = lazy('skills-activator');
      if (skillsActivator) {
        try {
          const active = skillsActivator.activateForPrompt(prompt);
          if (active.length > 0) lines.push(`[SKILLS] suggested: ${active.join(', ')}`);
        } catch { /* */ }
      }
      const ins = lazy('instincts');
      if (ins && ins.suggest) {
        try {
          const inst = ins.suggest(prompt);
          if (inst) lines.push(`[INSTINCT] ${inst.suggestion}`);
        } catch { /* */ }
      }
      console.log(lines.join('\n'));
    },

    'swarm-route': () => {
      const router = lazy('router');
      if (!router || !router.routeTask) {
        console.log(JSON.stringify({ error: 'router not available' }));
        return;
      }
      const r = router.routeTask(prompt);
      const wf = selectWorkflow(prompt, r);
      console.log(JSON.stringify({
        workflow: wf.type, description: wf.description, confidence: wf.confidence,
        path: wf.path, agents: wf.agents,
        primary_agent: r.agent, primary_node: r.node, primary_cycle: r.cycle || wf.type,
        swarm_init_hint: {
          topology: 'hierarchical',
          maxAgents: wf.type === 'hexad' ? 6 : 3,
          strategy: 'specialized', agents: wf.agents,
        },
      }, null, 2));
    },

    'post-task': () => {
      const intelligence = lazy('intelligence');
      const safla = lazy('safla');
      const router = lazy('router');
      const langGraph = lazy('langgraph-micro');

      if (intelligence && intelligence.feedback) { try { intelligence.feedback(true); } catch { /* */ } }
      let postTaskNode = null;
      const words = (prompt || '').trim().split(/\s+/).filter(Boolean);
      if (safla && router && router.routeTask && words.length >= 4) {
        try {
          const r = router.routeTask(prompt);
          postTaskNode = r.node;
          safla.recordOutcome(r.node, true, prompt.substring(0, 60));
          const ins = lazy('instincts');
          if (ins && ins.record) ins.record({ prompt, node: r.node, success: true });
        } catch { /* */ }
      }
      if (postTaskNode !== null && router && router.nextNode) {
        try {
          const nxt = router.nextNode(postTaskNode);
          if (nxt && router.ENNEAGRAM_NODES && router.ENNEAGRAM_NODES[nxt]) {
            console.log(`[ENNEAGRAM] Next hop: node ${postTaskNode} → ${nxt} (${router.ENNEAGRAM_NODES[nxt].agent})`);
          }
        } catch { /* */ }
      }
      if (langGraph && langGraph.advance) {
        try {
          const before = langGraph.status && langGraph.status();
          const wasActive = before && before.active;
          const next = langGraph.advance(true);
          if (next) console.log(`[LG] → ${next}`);
          else if (wasActive) console.log('[LG] Workflow complete');
        } catch { /* */ }
      }
      console.log('[OK] Task completed');
    },

    'compact-manual': async () => {
      console.log('[COMPACT] Manual compaction triggered');
      const intelligence = lazy('intelligence');
      if (intelligence && intelligence.consolidate) {
        await runWithTimeout(() => intelligence.consolidate(), 'intelligence.consolidate()');
      }
    },

    'compact-auto': () => {
      console.log('[COMPACT] Auto compaction triggered');
      const codeburn = lazy('codeburn');
      const safla = lazy('safla');
      const metricsUpdate = lazy('metrics-update');
      if (codeburn) {
        try {
          const t = codeburn.totals();
          if (t.source !== 'unavailable') {
            if (safla && safla.syncWithCodeBurn) safla.syncWithCodeBurn(t);
            if (metricsUpdate && metricsUpdate.run) metricsUpdate.run(t);
          }
        } catch { /* */ }
      }
    },

    'stats': () => {
      const intelligence = lazy('intelligence');
      if (intelligence && intelligence.stats) intelligence.stats(args.includes('--json'));
      else console.log('[WARN] Intelligence not available');
    },

    'burn': () => {
      const codeburn = lazy('codeburn');
      if (!codeburn) { console.log('[WARN] CodeBurn module not available'); return; }
      const t = codeburn.totals();
      if (t.source === 'unavailable') {
        console.log('[CODEBURN] ' + require('./lib/strings.cjs').t('codeburn.unavailable'));
      } else if (t.source === 'disabled') {
        console.log('[CODEBURN] disabled in feature-flags.json');
      } else {
        const lvl = t.today_cost > 10 ? 'ALERT' : t.today_cost > 5 ? 'WARN' : 'OK';
        console.log(`[CODEBURN] ${lvl} | Today $${t.today_cost.toFixed(2)} (${t.today_calls} calls) | Month $${t.month_cost.toFixed(2)} (${t.month_calls} calls)`);
      }
      if (args.includes('--json')) console.log(JSON.stringify(t, null, 2));
    },

    'flags': () => {
      const flags = loadFlags();
      console.log('[FLAGS] v3.0 feature state:');
      for (const [k, v] of Object.entries(flags.components || {})) {
        console.log(`  ${v ? '✓' : '✗'} ${k}`);
      }
    },

    'scope-status': () => {
      const projectScope = lazy('project-scope');
      if (!projectScope) { console.log('[SCOPE] module unavailable'); return; }
      const active = projectScope.getActive(prompt, { force: true });
      if (!active) {
        const projects = projectScope.listProjects();
        console.log(`[SCOPE] No active project. Available: ${projects.join(', ') || '(none)'}`);
        return;
      }
      console.log(`[SCOPE] Active: ${active.path} (detected via ${active.detected_from})`);
      console.log(`        Structure: ${(active.structure || []).join(', ')}`);
    },

    'scope-set': () => {
      const projectScope = lazy('project-scope');
      if (!projectScope) { console.log('[SCOPE] module unavailable'); return; }
      const name = (args[0] || '').trim();
      if (!name) {
        console.log('Usage: hook-handler.cjs scope-set <project>');
        console.log('Available:', projectScope.listProjects().join(', '));
        return;
      }
      const state = projectScope.setActive(name);
      if (!state) {
        console.log(`[SCOPE] '${name}' not found under PROJECTS/`);
        return;
      }
      console.log(`[SCOPE] Active project set to ${state.path} (manual)`);
    },

    'graphify': () => {
      const graphify = lazy('graphify');
      if (!graphify) { console.log('[WARN] Graphify not available'); return; }
      graphify.printASCII();
      const p = graphify.generateReport();
      if (p) console.log(`[GRAPHIFY] Report saved: ${p}`);
    },

    'safla': () => {
      const safla = lazy('safla');
      if (!safla) { console.log('[WARN] SAFLA not available'); return; }
      if (safla.printStats) safla.printStats();
      else console.log(JSON.stringify(safla.stats(), null, 2));
    },

    'evaluate-setup': () => {
      const { spawnSync } = require('child_process');
      const r = spawnSync(process.execPath, [path.join(helpersDir, 'evaluate-setup.cjs'), ...args], {
        stdio: 'inherit', encoding: 'utf-8',
      });
      process.exit(r.status || 0);
    },

    'verify': () => {
      const { spawnSync } = require('child_process');
      const r = spawnSync(process.execPath, [path.join(helpersDir, 'verify.cjs'), ...args], {
        stdio: 'inherit', encoding: 'utf-8',
      });
      process.exit(r.status || 0);
    },

    'review': () => {
      const { spawnSync } = require('child_process');
      const r = spawnSync(process.execPath, [path.join(helpersDir, 'review.cjs'), ...args], {
        stdio: 'inherit', encoding: 'utf-8',
      });
      process.exit(r.status || 0);
    },

    'quality-gate': () => {
      const { spawnSync } = require('child_process');
      const r = spawnSync(process.execPath, [path.join(helpersDir, 'quality-gate.cjs'), ...args], {
        stdio: 'inherit', encoding: 'utf-8',
      });
      process.exit(r.status || 0);
    },

    'diff-explain': () => {
      const { spawnSync } = require('child_process');
      const r = spawnSync(process.execPath, [path.join(helpersDir, 'diff-explain.cjs'), ...args], {
        stdio: 'inherit', encoding: 'utf-8',
      });
      process.exit(r.status || 0);
    },

    'platform': () => {
      const pd = lazy('platform-detect');
      if (!pd) { console.log('[WARN] platform-detect not available'); return; }
      const info = pd.getCapabilities();
      console.log(`[PLATFORM] ${info.platform.name} (${info.platform.source})`);
      console.log(`  hooks=${info.capabilities.hooks} slashCommands=${info.capabilities.slashCommands} mcpServers=${info.capabilities.mcpServers} subAgents=${info.capabilities.subAgents}`);
      if (!info.capabilities.hooks) {
        console.log('  ⚠ Current platform does NOT support hooks — features depending on UserPromptSubmit/SessionEnd will not run');
      }
      if (!info.capabilities.slashCommands) {
        console.log('  ⚠ Current platform does NOT support slash commands — /verify, /review etc. unavailable');
      }
    },

    'skills-active': () => {
      const sa = lazy('skills-activator');
      if (!sa) { console.log('[WARN] skills-activator not available'); return; }
      const active = sa.activateForPrompt(prompt);
      if (active.length === 0) console.log('[SKILLS] no matches for current prompt');
      else console.log(`[SKILLS] activated: ${active.join(', ')}`);
    },

    'instincts': () => {
      const ins = lazy('instincts');
      if (!ins) { console.log('[WARN] instincts not available'); return; }
      if (args.includes('--rebuild')) {
        const patterns = ins.buildPatterns();
        console.log(`[INSTINCTS] rebuilt ${Object.keys(patterns).length} patterns`);
        return;
      }
      if (args.includes('--suggest') && prompt) {
        const s = ins.suggest(prompt);
        if (s) console.log(`[INSTINCTS] ${s.suggestion}`);
        else console.log('[INSTINCTS] no pattern matches yet');
        return;
      }
      const s = ins.stats();
      console.log(`[INSTINCTS] ${s.patterns} patterns from ${s.log_entries} log entries`);
    },

    'errors': () => {
      const log = lazy('lib/error-log');
      if (!log) {
        try {
          const direct = require(path.join(helpersDir, 'lib', 'error-log.cjs'));
          const recent = direct.readRecent(20);
          if (recent.length === 0) { console.log('[ERRORS] log empty'); return; }
          for (const e of recent) console.log(`[${e.ts}] ${e.scope}: ${e.message}`);
        } catch { console.log('[ERRORS] log not initialized'); }
        return;
      }
    },

    'infer': () => {
      try {
        const ai = require(path.join(helpersDir, 'lib', 'auto-infer.cjs'));
        const s = ai.summary();
        if (args.includes('--json')) { console.log(JSON.stringify(s, null, 2)); return; }
        const sym = { HIGH: '✗', WARN: '⚠', INFO: 'ℹ' };
        console.log(`[INFER] ${s.total} findings · HIGH:${s.bySeverity.HIGH} WARN:${s.bySeverity.WARN} INFO:${s.bySeverity.INFO}`);
        for (const zoom of ['MAHA', 'MACRO', 'MEZZO', 'MICRO', 'NANO']) {
          const list = s.byZoom[zoom];
          if (list.length === 0) continue;
          console.log(`\n${zoom}:`);
          for (const f of list) {
            const loc = f.line ? `${f.file}:${f.line}` : f.file;
            console.log(`  [${sym[f.severity] || '?'}] ${loc} — ${f.msg}`);
            if (f.suggestion) console.log(`      → ${f.suggestion}`);
          }
        }
      } catch (e) { console.log('[INFER] error: ' + e.message); }
    },

    'bench': () => {
      try {
        const perf = require(path.join(helpersDir, 'lib', 'perf-baseline.cjs'));
        const ssa = lazy('ssa');
        const safla = lazy('safla');
        const corpus = Array.from({ length: 50 }, (_, i) => ({ id: 'e-' + i, text: 'note ' + i, pinned: i < 2, score: 0.5 }));
        const benches = [];
        if (ssa && ssa.filterContext) {
          const t0 = process.hrtime.bigint();
          for (let i = 0; i < 5; i++) ssa.filterContext('refactor', corpus, { topK: 12 });
          const ms = Number(process.hrtime.bigint() - t0) / 5e6;
          const r = perf.record('ssa.filterContext', ms);
          benches.push({ metric: 'ssa.filterContext', ms: +ms.toFixed(2), regression: r && r.regression });
        }
        if (safla && safla.recordOutcome) {
          const t0 = process.hrtime.bigint();
          for (let i = 0; i < 5; i++) safla.recordOutcome((i % 9) + 1, true, 'bench-' + i);
          const ms = Number(process.hrtime.bigint() - t0) / 5e6;
          const r = perf.record('safla.recordOutcome', ms);
          benches.push({ metric: 'safla.recordOutcome', ms: +ms.toFixed(2), regression: r && r.regression });
        }
        console.log('[BENCH] ' + benches.length + ' metric(s) recorded:');
        for (const b of benches) {
          const flag = b.regression ? ' 🚨 REGRESSION' : '';
          console.log('  ' + b.metric.padEnd(30) + ' ' + String(b.ms).padStart(7) + 'ms' + flag);
        }
        if (args.includes('--summary')) {
          console.log('\n[BENCH] baseline summary:');
          console.log(JSON.stringify(perf.summary(), null, 2));
        }
      } catch (e) { console.log('[BENCH] error: ' + e.message); }
    },

    'exit': () => {
      try {
        const ss = require(path.join(helpersDir, 'lib', 'session-snapshot.cjs'));
        const note = args.filter(a => !a.startsWith('--')).join(' ') || '';
        const r = ss.snapshot({ note });
        console.log(`[EXIT] session snapshot saved: ${r.file}`);
        const s = r.snapshot;
        if (s.cost && s.cost.source !== 'unavailable') {
          console.log(`  💰 cost today: $${s.cost.today_cost.toFixed(2)} (${s.cost.today_calls} calls)`);
        }
        if (s.safla) console.log(`  🤖 safla: ${s.safla.total_feedbacks} feedbacks across ${Object.keys(s.safla.nodes).length} nodes`);
        if (s.skills) console.log(`  🎯 skills: ${s.skills.suggested_total} suggestions, ${s.skills.unique_skills} unique, ${s.skills.dead_count} dead`);
        if (s.audit) console.log(`  📊 audit: ${s.audit.pass} PASS · ${s.audit.warn} WARN · ${s.audit.fail} FAIL`);
        if (s.errors) console.log(`  ⚠ errors 24h: ${s.errors.count_24h}`);
        console.log(`  📂 workspace: ${s.workspace.loc} LOC · ${s.workspace.modules} modules · ${s.workspace.test_suites} test suites`);
        if (args.includes('--json')) console.log(JSON.stringify(s, null, 2));
      } catch (e) { console.log('[EXIT] error: ' + e.message); }
    },

    'sessions-compare': () => {
      try {
        const ss = require(path.join(helpersDir, 'lib', 'session-snapshot.cjs'));
        const n = parseInt(args.find(a => /^\d+$/.test(a)) || '5', 10);
        const r = ss.compare(n);
        if (r.error) { console.log('[SESSIONS-COMPARE] ' + r.error); return; }
        console.log(`[SESSIONS-COMPARE] last ${r.sessions.length} sessions:`);
        for (let i = 0; i < r.sessions.length; i++) console.log(`  [${i}] ${r.sessions[i]}`);
        console.log('');
        console.log('  metric                          ' + r.sessions.map((_, i) => `[${i}]`.padStart(12)).join(''));
        console.log('  ' + '-'.repeat(32 + 12 * r.sessions.length));
        for (const row of r.rows) {
          const line = '  ' + row.metric.padEnd(32) + row.values.map(v => String(v == null ? '-' : v).padStart(12)).join('');
          console.log(line);
        }
        if (args.includes('--json')) console.log(JSON.stringify(r, null, 2));
      } catch (e) { console.log('[SESSIONS-COMPARE] error: ' + e.message); }
    },

    'skills-propose': async () => {
      const sp = lazy('lib/skills-propose');
      if (!sp) {
        try { return require(path.join(helpersDir, 'lib', 'skills-propose.cjs')); } catch (e) { console.log('[SKILLS-PROPOSE] error: ' + e.message); return; }
      }
      const real = sp || require(path.join(helpersDir, 'lib', 'skills-propose.cjs'));
      const keyword = args.find(a => !a.startsWith('--')) || prompt;
      if (!keyword || keyword.length < 3) {
        console.log('Usage: hook-handler.cjs skills-propose <keyword> [--scaffold <local-name>]');
        return;
      }
      try {
        const r = await real.propose(keyword, { fresh: args.includes('--fresh') });
        console.log(`[SKILLS-PROPOSE] keyword="${keyword}" source=${r.source} found ${r.candidates.length} mature candidate(s)\n`);
        for (let i = 0; i < r.candidates.length; i++) {
          const c = r.candidates[i];
          console.log(`  ${i + 1}. ${c.name} ⭐ ${c.stars} · ${c.license} · ${c.language || '?'}`);
          console.log(`     ${c.description || '(no description)'}`);
          console.log(`     ${c.url}`);
          if (c.topics && c.topics.length > 0) console.log(`     topics: ${c.topics.join(', ')}`);
          console.log('');
        }
        if (r.candidates.length === 0) {
          console.log('  (no mature candidates — try a different keyword or set GITHUB_TOKEN to raise rate limit)');
          return;
        }
        const scaffoldIdx = args.indexOf('--scaffold');
        if (scaffoldIdx >= 0 && args[scaffoldIdx + 1]) {
          const localName = args[scaffoldIdx + 1];
          const top = r.candidates[0];
          const sc = real.generateScaffold(top, localName, keyword);
          console.log(`[SKILLS-PROPOSE] scaffold created at ${sc.skill_path}`);
          console.log(`  inspired by: ${top.name} (⭐ ${top.stars}, ${top.license})`);
          console.log(`  edit ${sc.file} to fill in the implementation`);
        } else {
          console.log('To create a local scaffold from the top candidate, run:');
          console.log(`  hook-handler.cjs skills-propose ${keyword} --scaffold <local-name>`);
        }
      } catch (e) {
        console.log('[SKILLS-PROPOSE] error: ' + e.message);
      }
    },

    'optimize': () => {
      try {
        const opt = require(path.join(helpersDir, 'lib', 'auto-optimize.cjs'));
        const mode = args.find(a => !a.startsWith('--')) || 'nano';
        const dryRun = args.includes('--dry-run');
        let result;
        switch (mode) {
          case 'nano':  result = opt.optimizeNano({ dryRun }); break;
          case 'micro': result = opt.optimizeMicroPlan(); break;
          case 'mezzo': case 'macro': result = opt.optimizeMezzoPlan(); break;
          case 'maha':  result = opt.optimizeMahaPlan(); break;
          default: console.log('[OPTIMIZE] mode must be: nano|micro|mezzo|macro|maha'); return;
        }
        if (args.includes('--json')) { console.log(JSON.stringify(result, null, 2)); return; }
        console.log(`[OPTIMIZE ${mode.toUpperCase()}] ${result.dryRun ? '(DRY-RUN) ' : ''}${result.changes_count != null ? result.changes_count + ' file(s) modified' : (result.proposals || []).length + ' proposal(s)'}`);
        if (result.changes) for (const c of result.changes) console.log(`  ${c.file}: ${c.ops.join(', ')}`);
        if (result.proposals) {
          for (const p of result.proposals.slice(0, 20)) console.log(`  ${p.file}${p.line ? ':' + p.line : ''} → ${p.action || p.why}`);
          if (result.proposals.length > 20) console.log(`  ... and ${result.proposals.length - 20} more`);
        }
      } catch (e) { console.log('[OPTIMIZE] error: ' + e.message); }
    },

    'mcp-health': () => {
      try {
        const home = process.env.USERPROFILE || process.env.HOME;
        const cfgPath = path.join(home, '.claude.json');
        if (!fs.existsSync(cfgPath)) {
          console.log('[MCP-HEALTH] ~/.claude.json not found');
          return;
        }
        const cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf-8'));
        const servers = cfg.mcpServers || {};
        const names = Object.keys(servers);
        console.log('[MCP-HEALTH] ' + names.length + ' server(s) configured: ' + names.join(', '));
        for (const name of names) {
          const s = servers[name];
          const cmdArgs = s.args || [];
          const looksHelpOnly = (s.command || '').endsWith('node.exe') && cmdArgs.length === 1 && cmdArgs[0].endsWith('cli.js');
          const status = looksHelpOnly ? '⚠ MISCONFIGURED (likely prints help and exits)' : (s.command ? '✓ command set' : '✗ no command');
          console.log('  - ' + name + ': ' + status);
          if (looksHelpOnly) console.log('    fix: append "mcp", "start" to args');
        }
      } catch (e) { console.log('[MCP-HEALTH] error: ' + e.message); }
    },

    'safla-clean': () => {
      const safla = lazy('safla');
      if (!safla) { console.log('[WARN] SAFLA not available'); return; }
      const dataPath = path.join(process.cwd(), '.claude-flow', 'data', 'safla.json');
      if (!fs.existsSync(dataPath)) { console.log('[SAFLA-CLEAN] no state file'); return; }
      try {
        const data = JSON.parse(fs.readFileSync(dataPath, 'utf-8'));
        const before = Object.keys(data.nodes || {}).length;
        for (const k of Object.keys(data.nodes || {})) {
          if (!/^[1-9]$/.test(k)) delete data.nodes[k];
        }
        const after = Object.keys(data.nodes).length;
        const { writeAtomicJson } = require('./lib/atomic-write.cjs');
        writeAtomicJson(dataPath, data);
        console.log(`[SAFLA-CLEAN] removed ${before - after} invalid keys (${before} → ${after})`);
      } catch (e) {
        console.log(`[SAFLA-CLEAN] error: ${e.message}`);
      }
    },

    'lg': () => {
      const langGraph = lazy('langgraph-micro');
      if (!langGraph) { console.log('[WARN] LangGraph not available'); return; }
      if (langGraph.printStatus) langGraph.printStatus();
      else console.log(JSON.stringify(langGraph.getActive ? langGraph.getActive() : null, null, 2));
    },

    'profile': () => {
      const profileName = args[0] || args.find(a => ['lite', 'full', 'ssa-max'].includes(a)) || '';
      const flags = loadFlags();
      const profiles = flags.profiles || {};

      if (!profileName || profileName === 'status') {
        const current = flags.mode || 'full';
        console.log(`[PROFILE] Current mode: ${current}`);
        console.log('Available profiles: lite, full, ssa-max');
        console.log('\nProfile components:');
        for (const [name, cfg] of Object.entries(profiles)) {
          const active = Object.values(cfg.components || {}).filter(Boolean).length;
          const total = Object.keys(cfg.components || {}).length;
          console.log(`  ${name}: ${active}/${total} components active`);
        }
        return;
      }

      if (!profiles[profileName]) {
        console.log(`[PROFILE] Unknown profile: ${profileName}`);
        console.log('Available: lite, full, ssa-max');
        return;
      }

      const newProfile = profiles[profileName];
      const FLAGS_PATH = path.join(helpersDir, 'feature-flags.json');
      try {
        const currentFlags = JSON.parse(fs.readFileSync(FLAGS_PATH, 'utf-8'));
        currentFlags.mode = profileName;
        currentFlags.components = newProfile.components;
        if (newProfile.ssa) currentFlags.ssa = newProfile.ssa;
        if (newProfile.codeburn) currentFlags.codeburn = { ...currentFlags.codeburn, ...newProfile.codeburn };
        fs.writeFileSync(FLAGS_PATH, JSON.stringify(currentFlags, null, 2));
        const activeCount = Object.values(newProfile.components || {}).filter(Boolean).length;
        console.log(`[PROFILE] Switched to ${profileName} (${activeCount} components active)`);
      } catch (e) {
        console.log(`[PROFILE] Error: ${e.message}`);
      }
    },

    'ruflo-status': () => {
      const ruflo = lazy('ruflo');
      if (!ruflo) { console.log('[RUFLO] module unavailable'); return; }
      if (ruflo.status) {
        const s = ruflo.status();
        console.log('[RUFLO] Status: ' + (s.status || 'unknown'));
        if (s.swarm_id) console.log('  Swarm: ' + s.swarm_id);
        if (s.agents) console.log('  Agents: ' + (typeof s.agents === 'object' ? JSON.stringify(s.agents) : s.agents));
      } else if (ruflo.health) {
        const h = ruflo.health();
        console.log('[RUFLO] Health: ' + JSON.stringify(h));
      } else {
        console.log('[RUFLO] No status method available');
      }
    },

    'scheduled-task': () => {
      const safla = lazy('safla');
      const ssa = lazy('ssa');
      const cb = lazy('codeburn');
      const i18n = require('./lib/i18n.cjs');
      const now = new Date().toISOString().replace('T', ' ').slice(0, 19);
      console.log(`[SCHEDULED] Task started at ${now}`);
      if (safla) {
        const stats = safla.stats();
        console.log('[SCHEDULED] SAFLA: ' + stats.total_outcomes + ' outcomes, efficiency: ' + Math.round(stats.efficiency * 100) + '%');
      }
      if (ssa) {
        const eff = ssa.getSSAEfficiency();
        console.log('[SCHEDULED] SSA: ' + eff.tokens_saved + '/' + eff.total_tokens + ' tokens saved (' + Math.round(eff.ratio * 100) + '%)');
      }
      if (cb) {
        cb.totals().then(t => {
          console.log('[SCHEDULED] CodeBurn: $' + (t.today?.total_cost || 0).toFixed(2) + ' today, $' + (t.month?.total_cost || 0).toFixed(2) + ' this month');
        }).catch(() => console.log('[SCHEDULED] CodeBurn: unavailable'));
      }
    },

    'loop-task': () => {
      const now = new Date().toISOString().replace('T', ' ').slice(0, 19);
      console.log(`[LOOP] Loop task at ${now}`);
      const flags = loadFlags();
      const cfg = flags.ssa || {};
      const topK = cfg.top_k || 6;
      console.log('[LOOP] SSA top_k: ' + topK + ', min_score: ' + (cfg.min_score || 0.25));
      if (flags.mode) console.log('[LOOP] Profile: ' + flags.mode);
      console.log('[LOOP] Loop active — monitoring for optimization opportunities');
    },

    'sop': () => {
      const sop = require('./sop-engine.cjs');
      const sopName = args[0] || '';
      if (!sopName || sopName === 'list') {
        const sops = sop.listSOPs();
        console.log('[SOP] Available SOPs:');
        console.log('  Default:', sops.default.join(', '));
        if (sops.custom.length > 0) console.log('  Custom:', sops.custom.join(', '));
        return;
      }
      const s = sop.loadSOP(sopName);
      if (!s) {
        console.log(`[SOP] '${sopName}' not found. Run 'sop list' for available SOPs.`);
        return;
      }
      console.log(`[SOP] ${s.name}`);
      console.log(`  Phases: ${s.phases.map(p => p.name).join(' → ')}`);
      console.log(`  Agents: ${s.agents.join(', ')}`);
    },

    'sop-execute': () => {
      const sop = require('./sop-engine.cjs');
      const sopName = args[0];
      if (!sopName) {
        console.log('Usage: hook-handler.cjs sop-execute <sop-name>');
        return;
      }
      const result = sop.executeSOP(sopName, { prompt, args });
      if (result.error) {
        console.log(`[SOP] Error: ${result.error}`);
        return;
      }
      console.log(`[SOP] Executed: ${result.sop}`);
      console.log(`  Duration: ${result.totalDuration}`);
      console.log(`  Phases: ${result.phases.map(p => `${p.name}[${p.status}]`).join(' → ')}`);
    },
  };

  if (command && handlers[command]) {
    try { await Promise.resolve(handlers[command]()); }
    catch (e) {
      try {
        const errLog = require(path.join(helpersDir, 'lib', 'error-log.cjs'));
        errLog.logError('hook-handler.' + command, e, { args: args.slice(0, 3) });
      } catch { /* logger itself failed */ }
      console.log(`[WARN] Hook ${command} error: ${e.message}`);
    }
  } else if (command) {
    console.log(`[OK] Hook: ${command}`);
  } else {
    console.log('Usage: hook-handler.cjs <route|inject-workflow|swarm-route|pre-bash|pre-edit|post-bash|post-edit|session-restore|session-end|compact-save|compact-manual|compact-auto|pre-task|post-task|status|notify|stats|burn|flags|scope-status|scope-set|graphify|safla|lg|evaluate-setup|verify|review|quality-gate|diff-explain|platform|skills-active|safla-clean|instincts|errors>');
  }
}

process.exitCode = 0;
main().catch((e) => {
  try { console.log(`[WARN] Hook handler error: ${e.message}`); } catch {}
}).finally(() => {
  process.exit(0);
});
