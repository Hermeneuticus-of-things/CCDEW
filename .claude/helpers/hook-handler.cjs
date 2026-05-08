#!/usr/bin/env node
/**
 * Claude Flow Hook Handler v6.1 Micro (Cross-Platform)
 * Dispatches hook events to the appropriate helper modules.
 *
 * Usage: node hook-handler.cjs <command> [args...]
 *
 * Commands:
 *   inject-workflow - Inject workflow suggestion before every user prompt
 *   route           - Route a task to optimal agent (reads PROMPT from env/stdin)
 *   swarm-route     - Return JSON params ready for swarm_init
 *   pre-bash        - Validate command safety before execution
 *   post-edit       - Record edit outcome for learning
 *   session-restore - Restore previous session state
 *   session-end     - End session and persist state
 *   pre-task        - Record task start
 *   post-task       - Record task completion
 *   stats           - Show intelligence diagnostics
 *   burn            - Show CodeBurn token usage
 */

const path = require('path');
const fs = require('fs');

const helpersDir = __dirname;

// Safe require with stdout suppression
function safeRequire(modulePath) {
  try {
    if (fs.existsSync(modulePath)) {
      const origLog = console.log;
      const origError = console.error;
      console.log = () => {};
      console.error = () => {};
      try {
        const mod = require(modulePath);
        return mod;
      } finally {
        console.log = origLog;
        console.error = origError;
      }
    }
  } catch (e) {
    // silently fail
  }
  return null;
}

const router      = safeRequire(path.join(helpersDir, 'router.js'));
const session     = safeRequire(path.join(helpersDir, 'session.js'));
const memory      = safeRequire(path.join(helpersDir, 'memory.js'));
const intelligence= safeRequire(path.join(helpersDir, 'intelligence.cjs'));

// ── v6.1 Micro modules ───────────────────────────────────────────────────────
const codeburn    = safeRequire(path.join(helpersDir, 'codeburn.cjs'));
const redHat      = safeRequire(path.join(helpersDir, 'red-hat-evaluator.cjs'));
const ssa         = safeRequire(path.join(helpersDir, 'ssa.cjs'));
const autoOptimize= safeRequire(path.join(helpersDir, 'auto-optimize.cjs'));
const safla       = safeRequire(path.join(helpersDir, 'safla.cjs'));
const graphify    = safeRequire(path.join(helpersDir, 'graphify.cjs'));
const langGraph   = safeRequire(path.join(helpersDir, 'langgraph-micro.cjs'));
const metricsUpdate = safeRequire(path.join(helpersDir, 'metrics-update.cjs'));

function loadFeatureFlags() {
  try {
    const p = path.join(helpersDir, 'feature-flags.json');
    if (fs.existsSync(p)) return JSON.parse(fs.readFileSync(p, 'utf-8'));
  } catch { /* non-fatal */ }
  return { components: {} };
}

// ── Enneagram workflow selection (hexad vs triangle) ─────────────────────────
const NODE_MAP_PATH = path.join(helpersDir, 'workspace_node_map.json');
let _nodeMap = null;

function loadNodeMap() {
  if (_nodeMap) return _nodeMap;
  try {
    if (fs.existsSync(NODE_MAP_PATH)) {
      _nodeMap = JSON.parse(fs.readFileSync(NODE_MAP_PATH, 'utf8'));
    }
  } catch (e) { /* non-fatal */ }
  return _nodeMap || {};
}

// Cycle membership by node number
const HEXAD_NODES    = new Set([1, 2, 4, 5, 7, 8]);
const TRIANGLE_NODES = new Set([3, 6, 9]);

/**
 * Selects optimal workflow (hexad or triangle) for a task.
 * Scoring: trigger_keywords (+1 each) + natural cycle of routed node (+1)
 * Tie-break: triangle (faster, fewer agents)
 */
function selectWorkflow(task, routeResult) {
  const nodeMap = loadNodeMap();
  const templates = nodeMap.workflow_templates || {};
  const words = task.toLowerCase().replace(/[^a-z0-9 ]/g, ' ').split(/\s+/).filter(Boolean);

  const hexadKws    = (templates.hexad    || {}).trigger_keywords || [];
  const triangleKws = (templates.triangle || {}).trigger_keywords || [];

  let hexadScore    = words.filter(w => hexadKws.includes(w)).length;
  let triangleScore = words.filter(w => triangleKws.includes(w)).length;

  // Bias toward the natural cycle of the routed node
  if (routeResult && routeResult.node) {
    if (HEXAD_NODES.has(routeResult.node))    hexadScore    += 1;
    if (TRIANGLE_NODES.has(routeResult.node)) triangleScore += 1;
  }

  const type = hexadScore > triangleScore ? 'hexad' : 'triangle';
  const tmpl = templates[type] || {};

  return {
    type,
    path:        tmpl.path        || [],
    agents:      tmpl.agents      || [],
    description: tmpl.description || '',
    hexadScore,
    triangleScore,
    confidence: hexadScore !== triangleScore ? 'high' : 'low',
  };
}

// ── Intelligence timeout protection ────────────────────────────────────────
const INTELLIGENCE_TIMEOUT_MS = 3000;
function runWithTimeout(fn, label) {
  return new Promise((resolve) => {
    const timer = setTimeout(() => {
      process.stderr.write("[WARN] " + label + " timed out after " + INTELLIGENCE_TIMEOUT_MS + "ms, skipping\n");
      resolve(null);
    }, INTELLIGENCE_TIMEOUT_MS);
    try {
      const result = fn();
      clearTimeout(timer);
      resolve(result);
    } catch (e) {
      clearTimeout(timer);
      resolve(null);
    }
  });
}

// Get the command from argv
const [,, command, ...args] = process.argv;

// Read stdin with timeout
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
    process.stdin.on('data', (chunk) => { data += chunk; });
    process.stdin.on('end', () => { clearTimeout(timer); resolve(data); });
    process.stdin.on('error', () => { clearTimeout(timer); resolve(data); });
    process.stdin.resume();
  });
}

async function main() {
  // Global safety timeout: hooks must NEVER hang
  const safetyTimer = setTimeout(() => {
    process.stderr.write("[WARN] Hook handler global timeout (5s), forcing exit\n");
    process.exit(0);
  }, 5000);
  safetyTimer.unref();

  let stdinData = '';
  try { stdinData = await readStdin(); } catch (e) { /* ignore */ }

  let hookInput = {};
  if (stdinData.trim()) {
    try { hookInput = JSON.parse(stdinData); } catch (e) { /* ignore */ }
  }

  // Normalize snake_case/camelCase
  const toolInput = hookInput.toolInput || hookInput.tool_input || {};
  const toolName  = hookInput.toolName  || hookInput.tool_name  || '';

  const prompt = hookInput.prompt
    || hookInput.command
    || toolInput.command
    || toolInput.file_path
    || toolInput.prompt
    || process.env.PROMPT
    || process.env.TOOL_INPUT_command
    || args.join(' ')
    || '';

const handlers = {
  'route': () => {
    // SSA: filter intelligence context + Obsidian entries
    if (ssa) {
      try {
        // 1. Intelligence context (returns pre-ranked string — print directly)
        if (intelligence && intelligence.getContext) {
          const ctx = intelligence.getContext(prompt);
          if (ctx) console.log(typeof ctx === 'string' ? ctx : JSON.stringify(ctx));
        }
        // 2. Obsidian entries — filtrate prin SSA, injectate ca hint
        const obsEntries = ssa.loadObsidianEntries ? ssa.loadObsidianEntries() : [];
        if (obsEntries.length > 0) {
          const obsFiltered = ssa.filterContext(prompt, obsEntries, { top_k: 3, min_score: 0.1 });
          if (obsFiltered.length > 0) {
            const titles = obsFiltered.map(e => e.title || e.id).filter(Boolean).join(', ');
            console.log(`[OBS] Context relevant: ${titles}`);
          }
        }
      } catch { /* non-fatal */ }
    }

    // Auto-Optimize: hint on token-bloated prompts
    if (autoOptimize) {
      try { autoOptimize.analyze(prompt); } catch { /* non-fatal */ }
    }

    // Red Hat: inject critical questions for substantial prompts
    if (redHat) {
      try { redHat.evaluate(prompt); } catch { /* non-fatal */ }
    }

    // LangGraph: start workflow for this prompt
    if (langGraph && prompt) {
      try {
        const wfResult = langGraph.startWorkflow(prompt);
        if (wfResult) console.log(`[LG] Started: ${wfResult.graph_name} | ${wfResult.nodes.join('→')}`);
      } catch { /* non-fatal */ }
    }

    if (router && router.routeTask) {
      const result = router.routeTask(prompt);

      // SAFLA: apply adaptive weight_adj to confidence and show hint
      if (safla) {
        try {
          const adj = safla.getWeightAdj(result.node);
          if (adj && !isNaN(adj)) {
            result.confidence = Math.max(0, Math.min(1, result.confidence + adj));
          }
          const sfHint = safla.hint(result.node);
          if (sfHint) console.log(sfHint);
        } catch { /* non-fatal */ }
      }

      const wf = selectWorkflow(prompt, result);
      const agentSeq = wf.agents.join(' → ');
      const wfLabel  = `${wf.type.toUpperCase()} [${wf.confidence}]`;
      const output = [
        `[INFO] Routing task: ${prompt.substring(0, 80) || '(no prompt)'}`,
        '',
        '+------------------- Primary Recommendation -------------------+',
        `| Agent: ${result.agent.padEnd(53)}|`,
        `| Node:  ${('Node ' + result.node + ' — ' + (result.node_name || '')).substring(0, 53).padEnd(53)}|`,
        `| Confidence: ${(result.confidence * 100).toFixed(1)}%${' '.repeat(44)}|`,
        `| Reason: ${(result.reason || '').substring(0, 53).padEnd(53)}|`,
        '+--------------------------------------------------------------+',
        `| Workflow: ${wfLabel.padEnd(50)}|`,
        `| Path: ${agentSeq.substring(0, 55).padEnd(55)}|`,
        `| ${wf.description.substring(0, 61).padEnd(61)}|`,
        '+--------------------------------------------------------------+',
        `| swarm-route: node hook-handler.cjs swarm-route "<task>"     |`,
        '+--------------------------------------------------------------+',
      ];
      console.log(output.join('\n'));
    } else {
      console.log('[INFO] Router not available, using default routing');
    }
  },

  'pre-bash': () => {
    const cmd = (hookInput.command || prompt).toLowerCase();
    const dangerous = ['rm -rf /', 'format c:', 'del /s /q c:\\', ':(){:|:&};:'];
    for (const d of dangerous) {
      if (cmd.includes(d)) {
        console.error(`[BLOCKED] Dangerous command detected: ${d}`);
        process.exit(1);
      }
    }
    console.log('[OK] Command validated');
  },

  'pre-edit': () => {
    const file = toolInput.file_path || process.env.TOOL_INPUT_file_path || '';
    // Warn on direct edits to sensitive workspace files
    const sensitive = ['.claude/settings.json', 'CLAUDE.md', '.gitignore'];
    if (file && sensitive.some(s => file.endsWith(s))) {
      console.log(`[PRE-EDIT] ⚠️  Editing sensitive file: ${path.basename(file)}`);
    }
    console.log('[OK] Edit validated');
  },

  'post-bash': () => {
    const exitCode = hookInput.exit_code ?? hookInput.exitCode ?? null;
    // Only record SAFLA failure on exit ≥2 (actual errors).
    // Exit code 1 is used legitimately by grep (no match), diff (files differ), etc.
    if (exitCode !== null && exitCode >= 2) {
      if (safla && router && router.routeTask && prompt) {
        try {
          const result = router.routeTask(prompt);
          safla.recordOutcome(result.node, false, `bash exit:${exitCode}`);
        } catch { /* non-fatal */ }
      }
    }
    console.log('[OK] Bash completed');
  },

  'status': () => {
    const sessionId = process.env.CLAUDE_SESSION_ID || 'unknown';
    const flags = loadFeatureFlags();
    const active = Object.entries(flags.components || {}).filter(([,v]) => v).map(([k]) => k).join(', ');
    if (codeburn) {
      try {
        const cached = codeburn.totals();
        if (cached.source !== 'unavailable') {
          console.log(`[STATUS] $${(cached.today_cost||0).toFixed(2)} today | ${cached.today_calls||0} calls | Active: ${active}`);
          return;
        }
      } catch { /* non-fatal */ }
    }
    console.log(`[STATUS] Session active | Components: ${active}`);
  },

  'notify': () => {
    const msg = hookInput.message || hookInput.notification || prompt || '';
    if (msg) console.log(`[NOTIFY] ${msg.substring(0, 120)}`);
    else console.log('[NOTIFY] Notification received');
  },

  'post-edit': () => {
    if (session && session.metric) {
      try { session.metric('edits'); } catch (e) { /* no active session */ }
    }
    const editedFile = hookInput.file_path || toolInput.file_path
      || process.env.TOOL_INPUT_file_path || args[0] || '';
    if (intelligence && intelligence.recordEdit) {
      try { intelligence.recordEdit(editedFile); } catch (e) { /* non-fatal */ }
    }
    // CodeBurn: estimate tokens from file size (rough: 1 token ≈ 4 chars)
    if (codeburn) {
      try {
        const fsize = editedFile && fs.existsSync(editedFile)
          ? fs.statSync(editedFile).size : 0;
        const estTokens = Math.round(fsize / 4);
        const data = codeburn.record(estTokens, 0, 'post-edit');
        if (data) console.log(codeburn.status());
      } catch { /* non-fatal */ }
    }
    console.log('[OK] Edit recorded');
  },

  'session-restore': async () => {
    if (session) {
      const existing = session.restore && session.restore();
      if (!existing) {
        session.start && session.start();
      }
    } else {
      const sessionId = `session-${Date.now()}`;
      console.log(`[INFO] Session restored`);
      console.log(`New session ID: ${sessionId}`);
    }
    if (intelligence && intelligence.init) {
      const initResult = await runWithTimeout(() => intelligence.init(), 'intelligence.init()');
      if (initResult && initResult.nodes > 0) {
        console.log(`[INTELLIGENCE] Loaded ${initResult.nodes} patterns, ${initResult.edges} edges`);
      }
    }
    // SAFLA: increment session counter
    if (safla) { try { safla.sessionStart(); } catch { /* non-fatal */ } }
    // Obsidian: populează session-critical-index (Python helper)
    try {
      const { execSync } = require('child_process');
      const obsScript = path.join(helpersDir, 'obsidian-session-context.py');
      if (require('fs').existsSync(obsScript)) {
        const obsOut = execSync(`python3 "${obsScript}" 2>/dev/null`, { encoding: 'utf-8', timeout: 5000 }).trim();
        if (obsOut) console.log(obsOut);
      }
    } catch { /* non-fatal — Obsidian index opțional */ }
  },

  'session-end': async () => {
    if (intelligence && intelligence.consolidate) {
      const consResult = await runWithTimeout(() => intelligence.consolidate(), 'intelligence.consolidate()');
      if (consResult && consResult.entries > 0) {
        console.log(`[INTELLIGENCE] Consolidated: ${consResult.entries} entries, ${consResult.edges} edges`);
      }
    }
    // CodeBurn: print session summary at end (real data)
    if (codeburn) {
      try {
        const t = codeburn.totals();
        if (t.source !== 'unavailable') {
          console.log(`[CODEBURN] Today $${(t.today_cost||0).toFixed(2)} / ${t.today_calls||0} calls | Month $${(t.month_cost||0).toFixed(2)}`);
        }
      } catch { /* non-fatal */ }
    }
    // Graphify: generate session report on end
    if (graphify) {
      try {
        const reportPath = graphify.generateReport();
        if (reportPath) console.log(`[GRAPHIFY] Report: ${reportPath}`);
        graphify.printASCII();
      } catch { /* non-fatal */ }
    }
    // Metrics: update _DASHBOARD.md + _METRICS/ cu date reale codeburn
    if (metricsUpdate && codeburn) {
      try {
        const burnTotals = codeburn.totals();
        metricsUpdate.run(burnTotals);
        // SAFLA × CodeBurn: ajustează weights pe baza costului sesiunii
        if (safla) safla.syncWithCodeBurn(burnTotals);
      } catch { /* non-fatal */ }
    }
    // LangGraph: clear any active workflow
    if (langGraph) { try { langGraph.clearActive(); } catch { /* non-fatal */ } }
    if (session && session.end) {
      session.end();
    } else {
      console.log('[OK] Session ended');
    }
  },

  // Lightweight checkpoint at PreCompact — CodeBurn + SAFLA + metrics only (no Graphify/intelligence)
  'compact-save': async () => {
    if (codeburn) {
      try {
        const t = codeburn.totals();
        if (t.source !== 'unavailable') {
          if (safla) safla.syncWithCodeBurn(t);
          if (metricsUpdate) metricsUpdate.run(t);
          console.log(`[COMPACT-SAVE] $${(t.today_cost||0).toFixed(2)} today | dashboard updated`);
        }
      } catch { /* non-fatal */ }
    }
  },

  'pre-task': () => {
    if (session && session.metric) {
      try { session.metric('tasks'); } catch (e) { /* no active session */ }
    }
    if (router && router.routeTask && prompt) {
      const result = router.routeTask(prompt);
      const wf = selectWorkflow(prompt, result);
      console.log(`[INFO] Task → Node ${result.node} (${result.agent}) | Workflow: ${wf.type.toUpperCase()} [${wf.agents.join('→')}]`);
    } else {
      console.log('[OK] Task started');
    }
  },

  // Injects context in UserPromptSubmit — Claude Code sees it as system-reminder
  // HIGH confidence → [AUTO-SWARM DIRECTIVE]: Claude spawns swarm automatically
  // LOW confidence  → [WORKFLOW SUGGESTION]:  Claude chooses explicitly
  'inject-workflow': () => {
    // Guard: skip short messages (yes/ok/thanks)
    if (!router || !router.routeTask || !prompt) return;
    const words = prompt.trim().split(/\s+/);
    if (words.length < 4) return;

    const result = router.routeTask(prompt);
    const wf     = selectWorkflow(prompt, result);

    // SSA Context Zoom: estimează nivelul de context necesar
    let ssaZoom = 'nano'; // default: context minim
    if (words.length > 30) ssaZoom = 'maha';      // prompt lung → context maxim
    else if (words.length > 15) ssaZoom = 'micro'; // prompt mediu → context mediu
    const ssaHint = ssa ? `SSA:${ssaZoom.toUpperCase()}` : '';

    // SAFLA: weight adjustment pentru agentul recomandat
    const saflaAdj = safla ? safla.getWeightAdj(result.node) : 0;
    const saflaHint = saflaAdj !== 0 ? ` SAFLA:${saflaAdj > 0 ? '+' : ''}${saflaAdj.toFixed(2)}` : '';

    const agentSeq  = wf.agents.join(' → ');
    const bfsPath   = wf.path.join('→');
    const maxAgents = wf.type === 'hexad' ? 6 : 3;
    const altType   = wf.type === 'hexad' ? 'TRIANGLE' : 'HEXAD';
    const altAgents = wf.type === 'hexad'
      ? 'coder → tester → memory-specialist (3→6→9)'
      : 'reviewer → researcher → backend-dev → sparc-orchestrator → analyst → architecture (1→4→2→8→5→7)';
    const altMax    = wf.type === 'hexad' ? 3 : 6;

    // enneagram_compose: multi-zoom composition for hexad tasks
    let composeHint = '';
    if (wf.type === 'hexad' && words.length >= 8) {
      try {
        const { spawnSync } = require('child_process');
        const composeScript = path.join(helpersDir, 'enneagram_compose.py');
        if (fs.existsSync(composeScript)) {
          const fileM = prompt.match(/\b(\d+)\s*(files?|fi[șs]iere|components?|componente|module?s?)\b/i);
          const fileCount = fileM ? parseInt(fileM[1]) : (wf.type === 'hexad' ? 5 : 1);
          const res = spawnSync('python3', [composeScript, prompt.substring(0, 120), '--files', String(fileCount), '--json'], {
            encoding: 'utf-8', timeout: 2500, stdio: ['ignore', 'pipe', 'ignore'],
          });
          if (res.status === 0 && res.stdout) {
            const comp = JSON.parse(res.stdout);
            if (comp.complexity) {
              const ph1 = comp.phases && comp.phases[0];
              const phLabel = ph1 ? ` → ${(ph1.phase||'').split('—')[0].trim()}` : '';
              composeHint = `Compose: ${comp.complexity}${phLabel} (${comp.phases ? comp.phases.length : 0} phases)`;
              if (comp.warnings && comp.warnings.length > 0) composeHint += ` ⚠️ ${comp.warnings[0].substring(0,60)}`;
            }
          }
        }
      } catch { /* non-fatal */ }
    }

    let lines;
    if (wf.confidence === 'high') {
      lines = [
        `[AUTO-SWARM DIRECTIVE] ${prompt.substring(0, 65)}`,
        `Node ${result.node} (${result.node_name || result.agent}) | ${wf.type.toUpperCase()} | ${ssaHint}${saflaHint}`,
        `SPAWN: ${agentSeq}`,
        `swarm_init(topology=hierarchical, maxAgents=${maxAgents}, strategy=specialized)`,
        `BFS: ${bfsPath}`,
      ];
    } else {
      lines = [
        `[WORKFLOW SUGGESTION] ${prompt.substring(0, 65)}`,
        `Node ${result.node} (${result.node_name || result.agent}) | ${ssaHint}${saflaHint} | ambiguous`,
        `Option A ${wf.type.toUpperCase()} (maxAgents=${maxAgents}): ${agentSeq} (${bfsPath})`,
        `Option B ${altType} (maxAgents=${altMax}): ${altAgents}`,
        `Choose A for simple/fast task, B for complex/cross-project`,
      ];
    }
    if (composeHint) lines.push(composeHint);
    console.log(lines.join('\n'));
  },

  // Returns JSON with params ready for swarm_init
  'swarm-route': () => {
    if (!router || !router.routeTask) {
      console.log(JSON.stringify({ error: 'router not available' }));
      return;
    }
    const result = router.routeTask(prompt);
    const wf     = selectWorkflow(prompt, result);
    const output = {
      workflow:       wf.type,
      description:    wf.description,
      confidence:     wf.confidence,
      path:           wf.path,
      agents:         wf.agents,
      primary_agent:  result.agent,
      primary_node:   result.node,
      primary_cycle:  result.cycle || wf.type,
      swarm_init_hint: {
        topology:  'hierarchical',
        maxAgents: wf.type === 'hexad' ? 6 : 3,
        strategy:  'specialized',
        agents:    wf.agents,
      },
    };
    console.log(JSON.stringify(output, null, 2));
  },

  'post-task': () => {
    if (intelligence && intelligence.feedback) {
      try { intelligence.feedback(true); } catch (e) { /* non-fatal */ }
    }
    // SAFLA: record success outcome for last routed node
    let postTaskNode = null;
    if (safla && router && router.routeTask && prompt) {
      try {
        const result = router.routeTask(prompt);
        postTaskNode = result.node;
        safla.recordOutcome(result.node, true, prompt.substring(0, 60));
      } catch { /* non-fatal */ }
    }
    // enneagram_compose: reinforce adaptive topology on success
    if (postTaskNode !== null) {
      try {
        const { spawnSync } = require('child_process');
        const composeScript = path.join(helpersDir, 'enneagram_compose.py');
        if (fs.existsSync(composeScript)) {
          const cr = spawnSync('python3', ['-c',
            `import sys; sys.path.insert(0,${JSON.stringify(helpersDir)}); ` +
            `from enneagram_compose import reinforce_enneagram; ` +
            `r = reinforce_enneagram('default', ${postTaskNode}, True); ` +
            `print(f'[COMPOSE] Node ${postTaskNode} trust: {r:.3f}')`
          ], { encoding: 'utf-8', timeout: 2000, stdio: ['ignore', 'pipe', 'pipe'] });
          if (cr.stdout && cr.stdout.trim()) process.stdout.write(cr.stdout);
        }
      } catch { /* non-fatal */ }
    }
    // LangGraph: advance workflow to next node
    if (langGraph) {
      try {
        const next = langGraph.advance(true);
        if (next) console.log(`[LG] → ${next}`);
        else console.log('[LG] Workflow complete');
      } catch { /* non-fatal */ }
    }
    console.log('[OK] Task completed');
  },

  'compact-manual': () => {
    console.log('[COMPACT] Manual compaction triggered — saving state');
    if (intelligence && intelligence.consolidate) {
      try { intelligence.consolidate(); } catch { /* non-fatal */ }
    }
  },

  'compact-auto': () => {
    console.log('[COMPACT] Auto compaction triggered — context limit reached');
  },

  'stats': () => {
    if (intelligence && intelligence.stats) {
      intelligence.stats(args.includes('--json'));
    } else {
      console.log('[WARN] Intelligence module not available. Run session-restore first.');
    }
  },

  'burn': () => {
    if (codeburn) {
      const t = codeburn.totals();
      // Real codeburn API: { today_cost, month_cost, today_calls, month_calls }
      if (t.source === 'unavailable') {
        console.log('[CODEBURN] CLI unavailable — install: npm install -g codeburn');
      } else {
        const level = t.today_cost > 10 ? 'ALERT' : t.today_cost > 5 ? 'WARN' : 'OK';
        console.log(`[CODEBURN] ${level} | Today $${(t.today_cost||0).toFixed(2)} (${t.today_calls||0} calls) | Month $${(t.month_cost||0).toFixed(2)} (${t.month_calls||0} calls)`);
      }
      if (args.includes('--json')) console.log(JSON.stringify(t, null, 2));
    } else {
      console.log('[WARN] CodeBurn module not available');
    }
  },

  'flags': () => {
    const flags = loadFeatureFlags();
    console.log('[FLAGS] v6.1 Micro feature state:');
    for (const [k, v] of Object.entries(flags.components || {})) {
      console.log(`  ${v ? '✓' : '✗'} ${k}`);
    }
  },

  'graphify': () => {
    if (graphify) {
      graphify.printASCII();
      const p = graphify.generateReport();
      if (p) console.log(`[GRAPHIFY] Report saved: ${p}`);
    } else {
      console.log('[WARN] Graphify module not available');
    }
  },

  'safla': () => {
    if (safla) safla.stats();
    else console.log('[WARN] SAFLA module not available');
  },

  'lg': () => {
    if (langGraph) langGraph.printStatus();
    else console.log('[WARN] LangGraph module not available');
  },
};

  if (command && handlers[command]) {
    try {
      await Promise.resolve(handlers[command]());
    } catch (e) {
      console.log(`[WARN] Hook ${command} encountered an error: ${e.message}`);
    }
  } else if (command) {
    console.log(`[OK] Hook: ${command}`);
  } else {
    console.log('Usage: hook-handler.cjs <inject-workflow|route|swarm-route|pre-bash|post-edit|session-restore|session-end|pre-task|post-task|stats>');
  }
}

process.exitCode = 0;
main().catch((e) => {
  try { console.log(`[WARN] Hook handler error: ${e.message}`); } catch (_) {}
}).finally(() => {
  process.exit(0);
});
