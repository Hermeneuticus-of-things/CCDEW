'use strict';
/**
 * CCDEW Agent Harness v1.0
 * ─────────────────────────────────────────────────────────────────────────────
 * Canonical contract for all Hermes / CCDEW agent tools.
 *
 * OBSERVATION CONTRACT (every tool must return this shape):
 *   { status, summary, next_actions, artifacts, data, meta }
 *
 * GRANULARITY:
 *   micro  — high-risk: deploy, permissions, migration  (explicit confirm gate)
 *   medium — common loops: read/edit/search             (default)
 *   macro  — batches when round-trip is dominant cost   (explicit opt-in)
 *
 * BENCHMARKING:
 *   Tracks completion_rate, retries, pass@1, pass@3, cost_per_task
 *   Written to .claude-flow/data/harness-bench.json
 *
 * ARCHITECTURE: Hybrid ReAct + typed tool execution
 *   Planning  → ReAct (free-form reasoning over tool outputs)
 *   Execution → typed tools (schema-first, deterministic outputs)
 */

const fs   = require('fs');
const path = require('path');

const CCDEW_ROOT = (() => {
  // Works both when required and when run directly
  const d = __dirname;
  return path.resolve(d, '../..');
})();

const DATA_DIR   = path.join(CCDEW_ROOT, '.claude-flow', 'data');
const BENCH_PATH = path.join(DATA_DIR, 'harness-bench.json');

// ── Observation factory ───────────────────────────────────────────────────────

/**
 * Build a canonical observation object.
 * @param {'success'|'warning'|'error'} status
 * @param {string} summary  one-line human-readable result
 * @param {string[]} next_actions  actionable follow-ups
 * @param {string[]} [artifacts]  file paths / IDs produced
 * @param {*} [data]  structured payload
 * @param {object} [meta]  timing, retries, granularity
 */
function observe(status, summary, next_actions = [], artifacts = [], data = null, meta = {}) {
  return {
    status,                          // 'success' | 'warning' | 'error'
    summary,                         // "Loaded 310 nodes from graph-state.json"
    next_actions,                    // ["Run /compact to reduce context", ...]
    artifacts,                       // ["/home/think/CCDEW/.claude-flow/data/graph-state.json"]
    data,                            // raw payload
    meta: {
      ts: new Date().toISOString(),
      granularity: meta.granularity || 'medium',
      retries: meta.retries || 0,
      duration_ms: meta.duration_ms || 0,
      ...meta,
    },
  };
}

function ok(summary, next_actions, artifacts, data, meta) {
  return observe('success', summary, next_actions, artifacts, data, meta);
}

function warn(summary, next_actions, artifacts, data, meta) {
  return observe('warning', summary, next_actions, artifacts, data, meta);
}

/**
 * Error observation with recovery hints.
 * @param {string} summary
 * @param {string} root_cause  what went wrong
 * @param {string} retry_instruction  safe way to retry
 * @param {string} stop_condition  when to give up
 */
function err(summary, root_cause, retry_instruction, stop_condition, data) {
  return observe('error', summary,
    [`ROOT: ${root_cause}`, `RETRY: ${retry_instruction}`, `STOP IF: ${stop_condition}`],
    [], data, { granularity: 'micro' }
  );
}

// ── Tool Registry ─────────────────────────────────────────────────────────────

/**
 * Registry of available agent tools.
 * Each entry: { name, granularity, description, fn }
 */
const TOOLS = {};

function registerTool(name, granularity, description, fn) {
  if (!['micro', 'medium', 'macro'].includes(granularity)) {
    throw new Error(`Invalid granularity: ${granularity}`);
  }
  TOOLS[name] = { name, granularity, description, fn };
}

// ── Built-in tools ────────────────────────────────────────────────────────────

registerTool('memory.read', 'medium', 'Read memory layer status and stats', () => {
  try {
    const mem = require(path.join(CCDEW_ROOT, '.claude', 'helpers', 'memory-layers.cjs'));
    const raw = mem.status ? mem.status() : null;
    if (raw) {
      const total = Object.values(raw).reduce((s, l) => s + (l.count || l.tasks || 0), 0);
      return ok(
        `Memory: ${Object.keys(raw).length} layers, ~${total} items`,
        ['Use memory.search to find specific items', 'Use memory.compact if L0/L1 overflows'],
        [], raw
      );
    }
    return warn('Memory layers module loaded but status() returned null', ['Check .claude-flow/data/ exists'], []);
  } catch (e) {
    return err('Failed to read memory layers', e.message,
      'Ensure CCDEW_ROOT is set and .claude-flow/data/ exists',
      'Stop if directory missing after mkdir attempt');
  }
});

registerTool('intelligence.read', 'medium', 'Read graph-state.json for pattern intelligence', () => {
  const gspath = path.join(DATA_DIR, 'graph-state.json');
  try {
    if (!fs.existsSync(gspath)) {
      return warn('graph-state.json not found — intelligence empty',
        ['Run a Claude session with hooks enabled to build graph', 'Check DATA_DIR path'],
        [gspath]);
    }
    const gs = JSON.parse(fs.readFileSync(gspath, 'utf-8'));
    const nodes = Object.keys(gs.nodes || {}).length;
    const edges = Array.isArray(gs.edges) ? gs.edges.length : 0;
    return ok(
      `Graph: ${nodes} nodes, ${edges} edges (updated ${gs.updatedAt ? new Date(gs.updatedAt).toLocaleDateString() : '?'})`,
      nodes > 500 ? ['Consider graph pruning — large graph may slow searches'] : [],
      [gspath],
      { nodes, edges, updatedAt: gs.updatedAt }
    );
  } catch (e) {
    return err('Failed to parse graph-state.json', e.message,
      'Delete graph-state.json and let hooks rebuild it',
      'Stop retrying after 3 failed parses — file may be corrupt');
  }
});

registerTool('safla.record', 'medium', 'Record task outcome into SAFLA feedback loop', ({ nodeId, success, task }) => {
  if (!nodeId || success === undefined || !task) {
    return err('safla.record: missing params', 'nodeId, success, task all required',
      'Call with {nodeId: "1-9", success: true/false, task: "description"}',
      'Stop if nodeId not in 1-9');
  }
  try {
    const safla = require(path.join(CCDEW_ROOT, '.claude', 'helpers', 'safla.cjs'));
    safla.recordOutcome(String(nodeId), success, task);
    const s = safla.stats();
    return ok(
      `SAFLA: node ${nodeId} ${success ? '✓' : '✗'} "${task}" — total ${s.total_feedbacks} feedbacks`,
      ['Monitor node rate — if <25%, consider rerouting to stronger node'],
      [],
      { node: nodeId, success, task, stats: s }
    );
  } catch (e) {
    return err('safla.record failed', e.message, 'Retry once — safla.json may be locked', 'Stop after 2 retries');
  }
});

registerTool('ssa.stats', 'medium', 'Read SSA context compression stats', () => {
  const ssaPath = path.join(DATA_DIR, 'ssa-stats.json');
  try {
    if (!fs.existsSync(ssaPath)) {
      return warn('ssa-stats.json not found — no SSA history',
        ['SSA records stats when hooks fire during Claude sessions'],
        [ssaPath]);
    }
    const raw = JSON.parse(fs.readFileSync(ssaPath, 'utf-8'));
    const ratio = raw.entries_total > 0
      ? Math.round(raw.entries_saved / raw.entries_total * 100) : 0;
    const actions = ratio < 15
      ? ['SSA below 15% — review entry selection rules in ssa.cjs']
      : ratio >= 25 ? ['SSA at target'] : ['SSA below target — normal for low-volume sessions'];
    return ok(
      `SSA: ${ratio}% compression, ${raw.calls} calls, ${raw.tokens_saved || 0} tokens saved`,
      actions, [ssaPath], raw
    );
  } catch (e) {
    return err('Failed to read ssa-stats.json', e.message,
      'Check file permissions and JSON validity',
      'Stop if parse fails 2x — may be corrupt');
  }
});

registerTool('cost.read', 'medium', 'Read current session cost from codeburn', () => {
  try {
    const cb = require(path.join(CCDEW_ROOT, '.claude', 'helpers', 'codeburn.cjs'));
    const t = cb.totals();
    const pct = ((t.today_cost / 100) * 100).toFixed(1);
    const actions = [];
    if (t.today_cost > 5) actions.push('Cost >$5 today — consider /compact to reduce tokens');
    if (t.today_cost > 15) actions.push('Cost >$15 today — review task decomposition efficiency');
    return ok(
      `Cost: $${t.today_cost.toFixed(2)} today / $${t.month_cost.toFixed(2)} month (${t.today_calls} calls)`,
      actions, [], t
    );
  } catch (e) {
    return err('Failed to read cost', e.message,
      'Ensure codeburn.cjs is available and DATA_DIR is writable',
      'Stop cost tracking if source is "unavailable" for >5 min');
  }
});

registerTool('sensory.write', 'medium', 'Write event to L0 sensory layer', ({ msg, type = 'event', layer = 'L0' }) => {
  if (!msg) return err('sensory.write: msg required', 'No message provided', 'Pass {msg: "..."}', 'Never');
  const sensoryPath = path.join(DATA_DIR, 'sensory.jsonl');
  try {
    const entry = JSON.stringify({ msg, type, layer, ts: Date.now() }) + '\n';
    fs.appendFileSync(sensoryPath, entry, 'utf-8');
    return ok(`Sensory event written: "${msg}"`, [], [sensoryPath], { msg, type, ts: Date.now() });
  } catch (e) {
    return err('Failed to write sensory event', e.message,
      'Check DATA_DIR is writable: ls -la ' + DATA_DIR,
      'Stop if 3 consecutive writes fail');
  }
});

// ── Benchmarking ──────────────────────────────────────────────────────────────

function loadBench() {
  try {
    if (fs.existsSync(BENCH_PATH)) return JSON.parse(fs.readFileSync(BENCH_PATH, 'utf-8'));
  } catch {}
  return { tasks: [], summary: { total: 0, success: 0, retries: 0, total_cost: 0 } };
}

function saveBench(bench) {
  try {
    if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });
    fs.writeFileSync(BENCH_PATH, JSON.stringify(bench, null, 2), 'utf-8');
  } catch {}
}

/**
 * Track a task run for benchmarking.
 * @param {string} task_id
 * @param {boolean} success
 * @param {number} retries
 * @param {number} cost  approximate cost in $
 * @param {number} duration_ms
 */
function trackTask(task_id, success, retries = 0, cost = 0, duration_ms = 0) {
  const bench = loadBench();
  const entry = { task_id, success, retries, cost, duration_ms, ts: new Date().toISOString() };
  bench.tasks.push(entry);
  // Keep last 500
  if (bench.tasks.length > 500) bench.tasks = bench.tasks.slice(-500);

  // Recompute summary
  const recent = bench.tasks.slice(-100);
  const successCount = recent.filter(t => t.success).length;
  bench.summary = {
    total: bench.tasks.length,
    recent_100: recent.length,
    completion_rate: (successCount / recent.length * 100).toFixed(1) + '%',
    avg_retries: (recent.reduce((s, t) => s + t.retries, 0) / recent.length).toFixed(2),
    pass_at_1: (recent.filter(t => t.retries === 0 && t.success).length / recent.length * 100).toFixed(1) + '%',
    pass_at_3: (recent.filter(t => t.retries <= 2 && t.success).length / recent.length * 100).toFixed(1) + '%',
    avg_cost_per_task: '$' + (recent.reduce((s, t) => s + t.cost, 0) / recent.length).toFixed(4),
    total_cost: '$' + bench.tasks.reduce((s, t) => s + t.cost, 0).toFixed(2),
    last_updated: new Date().toISOString(),
  };
  saveBench(bench);
  return bench.summary;
}

/**
 * Execute a registered tool with timing, error recovery, and benchmarking.
 * @param {string} name  tool name from TOOLS registry
 * @param {*} input  tool-specific input
 * @param {object} opts  { maxRetries, taskId, cost }
 */
function run(name, input = {}, opts = {}) {
  const { maxRetries = 2, taskId = null, cost = 0 } = opts;
  const tool = TOOLS[name];
  if (!tool) {
    return err(
      `Unknown tool: ${name}`,
      'Tool not registered in TOOLS registry',
      `Run harness.listTools() to see available tools. Register with registerTool().`,
      'Stop — no point retrying an unknown tool'
    );
  }

  let lastResult, retries = 0;
  const t0 = Date.now();

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      lastResult = tool.fn(input);
      if (lastResult.status === 'success') {
        const dur = Date.now() - t0;
        lastResult.meta.retries = retries;
        lastResult.meta.duration_ms = dur;
        if (taskId) trackTask(taskId, true, retries, cost, dur);
        return lastResult;
      }
      if (lastResult.status === 'error' && attempt < maxRetries) {
        retries++;
        // back-off
        const wait = 100 * Math.pow(2, attempt);
        // sync sleep (small, harness context)
        const end = Date.now() + wait;
        while (Date.now() < end) {}
        continue;
      }
    } catch (e) {
      lastResult = err(
        `Tool "${name}" threw: ${e.message}`,
        e.stack || e.message,
        'Check tool implementation for uncaught exception',
        'Stop after 3 throws'
      );
      if (attempt < maxRetries) { retries++; continue; }
    }
    break;
  }

  const dur = Date.now() - t0;
  if (lastResult) { lastResult.meta.retries = retries; lastResult.meta.duration_ms = dur; }
  if (taskId) trackTask(taskId, false, retries, cost, dur);
  return lastResult;
}

// ── Bench report ──────────────────────────────────────────────────────────────

function benchReport() {
  const bench = loadBench();
  return bench.summary || { total: 0, note: 'No tasks tracked yet' };
}

function listTools() {
  return Object.values(TOOLS).map(t => ({
    name: t.name,
    granularity: t.granularity,
    description: t.description,
  }));
}

// ── OODA Loop helper ──────────────────────────────────────────────────────────

/**
 * Minimal ReAct-style OODA step runner.
 * @param {string} goal  human-readable goal
 * @param {Function[]} steps  array of () => observation
 * @param {object} opts  { maxSteps, reflectEvery }
 */
function ooda(goal, steps, opts = {}) {
  const { maxSteps = 20, reflectEvery = 3 } = opts;
  const log = [];
  let iteration = 0;

  for (const step of steps) {
    if (iteration >= maxSteps) {
      log.push({ phase: 'STOP', reason: `maxSteps (${maxSteps}) reached`, goal });
      break;
    }
    iteration++;

    // ACT
    const t0step = Date.now();
    let obs;
    try { obs = step(); } catch (e) {
      obs = err('Step threw', e.message, 'Fix step function', 'Stop if same error repeats');
    }
    const stepDur = Date.now() - t0step;
    // Auto-track each step in bench
    trackTask(`${goal.slice(0,30)}#${iteration}`, obs.status !== 'error', obs.meta?.retries || 0, 0, stepDur);

    log.push({ phase: 'OBSERVE', iteration, obs });

    // STOP condition — error with no next_actions
    if (obs.status === 'error' && (!obs.next_actions || obs.next_actions.length === 0)) {
      log.push({ phase: 'STOP', reason: 'Unrecoverable error', summary: obs.summary });
      break;
    }

    // REFLECT every N steps
    if (iteration % reflectEvery === 0) {
      const successes = log.filter(l => l.obs?.status === 'success').length;
      const errors    = log.filter(l => l.obs?.status === 'error').length;
      log.push({ phase: 'REFLECT', iteration, successes, errors,
        assessment: errors > successes ? 'HIGH_ERROR_RATE' : 'PROGRESSING' });
    }
  }

  return {
    goal,
    iterations: iteration,
    log,
    final: log[log.length - 1],
    summary: `${log.filter(l => l.obs?.status === 'success').length}/${iteration} steps succeeded`,
  };
}

// ── Exports ───────────────────────────────────────────────────────────────────

module.exports = {
  // Observation builders
  observe, ok, warn, err,
  // Tool registry
  registerTool, TOOLS, run, listTools,
  // Benchmarking
  trackTask, benchReport,
  // OODA
  ooda,
};

// ── CLI ───────────────────────────────────────────────────────────────────────

if (require.main === module) {
  const cmd = process.argv[2] || 'bench';

  if (cmd === 'bench') {
    console.log(JSON.stringify(benchReport(), null, 2));
  } else if (cmd === 'tools') {
    console.log(JSON.stringify(listTools(), null, 2));
  } else if (cmd === 'test') {
    // Self-test: run all built-in tools
    console.log('=== Agent Harness Self-Test ===');
    for (const name of Object.keys(TOOLS)) {
      const result = run(name, {}, { maxRetries: 1 });
      const icon = result.status === 'success' ? '✓' : result.status === 'warning' ? '⚠' : '✗';
      console.log(`${icon} [${result.status}] ${name}: ${result.summary}`);
      if (result.next_actions?.length) {
        result.next_actions.forEach(a => console.log(`    → ${a}`));
      }
    }
  } else if (cmd === 'ooda-demo') {
    // Demo OODA loop
    const H = module.exports;
    const result = H.ooda('Verify CCDEW system health', [
      () => H.run('memory.read'),
      () => H.run('intelligence.read'),
      () => H.run('ssa.stats'),
      () => H.run('cost.read'),
      () => H.run('safla.record', { nodeId: '9', success: true, task: 'harness-self-test' }),
    ]);
    console.log(JSON.stringify({ goal: result.goal, summary: result.summary, iterations: result.iterations }, null, 2));
    result.log.forEach(l => {
      if (l.phase === 'OBSERVE') console.log(`  [${l.iteration}] ${l.obs.status}: ${l.obs.summary}`);
      if (l.phase === 'REFLECT') console.log(`  [REFLECT] ${l.assessment} — ${l.successes} ok / ${l.errors} err`);
      if (l.phase === 'STOP') console.log(`  [STOP] ${l.reason}`);
    });
  } else {
    console.error(`Unknown command: ${cmd}. Use: bench | tools | test | ooda-demo`);
    process.exit(1);
  }
}
