'use strict';
/**
 * LangGraph Micro (v6.1 Micro)
 * Lightweight workflow state machine — NO Python, NO external deps.
 * Inspired by LangGraph concepts (nodes, edges, state) but pure CJS.
 *
 * What it does:
 *   - Tracks multi-step task workflows as a directed state graph
 *   - Persists active workflow state across hook calls
 *   - Injects [WORKFLOW] status into route output
 *
 * Data: .claude-flow/data/langgraph-state.json
 *
 * Concepts mapped from LangGraph:
 *   Node    → a task step with a handler function
 *   Edge    → conditional transition between steps
 *   State   → shared context object updated at each node
 *   Graph   → the workflow definition
 */

const fs   = require('fs');
const path = require('path');

const DATA_DIR  = path.join(process.cwd(), '.claude-flow', 'data');
const STATE_PATH= path.join(DATA_DIR, 'langgraph-state.json');
const FLAGS_PATH= path.join(__dirname, 'feature-flags.json');

function loadFlags() {
  try { return JSON.parse(fs.readFileSync(FLAGS_PATH, 'utf-8')); } catch { return {}; }
}

function ensureDataDir() {
  if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });
}

function loadState() {
  ensureDataDir();
  try {
    if (fs.existsSync(STATE_PATH)) return JSON.parse(fs.readFileSync(STATE_PATH, 'utf-8'));
  } catch { /* start fresh */ }
  return { active: null, history: [], graphs: {} };
}

function saveState(state) {
  ensureDataDir();
  // Keep history to last 100 entries
  if (state.history.length > 100) state.history = state.history.slice(-100);
  fs.writeFileSync(STATE_PATH, JSON.stringify(state, null, 2), 'utf-8');
}

// ── Built-in workflow graphs ──────────────────────────────────────────────────

const BUILTIN_GRAPHS = {
  /**
   * Standard task workflow:
   * route → plan → execute → review → done
   */
  standard: {
    name: 'Standard Task',
    nodes: ['route', 'plan', 'execute', 'review', 'done'],
    edges: {
      route:   { next: 'plan',    condition: 'always' },
      plan:    { next: 'execute', condition: 'always' },
      execute: { next: 'review',  condition: 'always' },
      review:  { next: 'done',    condition: 'success', fallback: 'execute' },
      done:    { next: null },
    },
    description: 'route→plan→execute→review→done',
  },

  /**
   * Architecture workflow (hexad path):
   * spec → research → design → implement → test → deploy
   */
  architecture: {
    name: 'Architecture',
    nodes: ['spec', 'research', 'design', 'implement', 'test', 'deploy'],
    edges: {
      spec:       { next: 'research',  condition: 'always' },
      research:   { next: 'design',    condition: 'always' },
      design:     { next: 'implement', condition: 'always' },
      implement:  { next: 'test',      condition: 'always' },
      test:       { next: 'deploy',    condition: 'success', fallback: 'implement' },
      deploy:     { next: null },
    },
    description: 'spec→research→design→implement→test→deploy',
  },

  /**
   * Quick fix workflow (triangle path):
   * diagnose → fix → verify
   */
  quick_fix: {
    name: 'Quick Fix',
    nodes: ['diagnose', 'fix', 'verify'],
    edges: {
      diagnose: { next: 'fix',    condition: 'always' },
      fix:      { next: 'verify', condition: 'always' },
      verify:   { next: null },
    },
    description: 'diagnose→fix→verify',
  },
};

/**
 * Detect best workflow graph for a prompt.
 * Conservative: only triggers for prompts ≥12 words with STRONG intent keywords.
 * Returns null if the prompt is too short or ambiguous (no workflow started).
 */
function detectGraph(prompt) {
  const words = (prompt || '').trim().split(/\s+/);
  if (words.length < 12) return null; // Too short for multi-step workflow

  const lower = prompt.toLowerCase();

  // Strong architecture signals — must have BOTH a verb AND a noun
  const archVerbs = ['implementeaz', 'implement', 'creeaz', 'create', 'refactor', 'migrat', 'rescri', 'rewrit', 'design'];
  const archNouns = ['arhitectur', 'architect', 'sistem', 'system', 'serviciu', 'service', 'modul', 'module', 'api', 'baza de date', 'database'];
  const hasArchVerb = archVerbs.some(k => lower.includes(k));
  const hasArchNoun = archNouns.some(k => lower.includes(k));
  if (hasArchVerb && hasArchNoun) return 'architecture';

  // Strong fix signals
  const fixKws = ['bug', 'eroare', 'error', 'crash', 'broken', 'nu functioneaz', 'not working', 'repara', 'fix'];
  if (fixKws.some(k => lower.includes(k))) return 'quick_fix';

  // Standard only for explicit multi-step task prompts
  const taskVerbs = ['implementeaz', 'implement', 'adaug', 'add', 'creeaz', 'create', 'dezvolt', 'build'];
  if (taskVerbs.some(k => lower.includes(k))) return 'standard';

  return null; // No workflow — don't add overhead
}

/**
 * Start a new workflow for a prompt. Saves active workflow state.
 */
function startWorkflow(prompt, graphId) {
  const flags = loadFlags();
  if (!flags.components || !flags.components.langraph) return null;

  const gid   = graphId || detectGraph(prompt);
  if (!gid) return null; // Prompt too short/ambiguous — skip silently
  const graph  = BUILTIN_GRAPHS[gid];
  if (!graph) return null;

  const state = loadState();
  const wf = {
    id:          `wf-${Date.now()}`,
    graph_id:    gid,
    graph_name:  graph.name,
    current_node: graph.nodes[0],
    nodes:       graph.nodes,
    edges:       graph.edges,
    prompt:      (prompt || '').substring(0, 100),
    started_at:  new Date().toISOString(),
    updated_at:  new Date().toISOString(),
    status:      'running',
    step:        0,
  };

  state.active = wf;
  state.history.push({ id: wf.id, graph: gid, started: wf.started_at, status: 'started' });
  saveState(state);
  return wf;
}

/**
 * Advance the active workflow to the next node.
 * @param {boolean} success — whether the current step succeeded
 */
function advance(success = true) {
  const flags = loadFlags();
  if (!flags.components || !flags.components.langraph) return null;

  const state = loadState();
  if (!state.active || state.active.status !== 'running') return null;

  const wf   = state.active;
  const edge = (wf.edges || {})[wf.current_node];
  if (!edge) { wf.status = 'done'; state.active = null; saveState(state); return null; }

  const nextNode = (success || edge.condition === 'always') ? edge.next : (edge.fallback || edge.next);

  if (!nextNode) {
    wf.status = 'done';
    state.history[state.history.length - 1].status = 'done';
    state.active = null;
  } else {
    wf.current_node = nextNode;
    wf.step++;
    wf.updated_at = new Date().toISOString();
  }

  saveState(state);
  return nextNode;
}

/**
 * Get a one-line status string for the active workflow.
 */
function status() {
  const flags = loadFlags();
  if (!flags.components || !flags.components.langraph) return '';

  const state = loadState();
  if (!state.active) return '[LG] No active workflow';

  const wf    = state.active;
  const graph = BUILTIN_GRAPHS[wf.graph_id] || {};
  const desc  = graph.description || wf.nodes.join('→');
  const step  = wf.step + 1;
  const total = (wf.nodes || []).length;

  return `[LG] ${wf.graph_name} | Step ${step}/${total}: ${wf.current_node} | ${desc}`;
}

/**
 * Print full workflow info to stdout.
 */
function printStatus() {
  const flags = loadFlags();
  if (!flags.components || !flags.components.langraph) {
    console.log('[LANGGRAPH] disabled in feature-flags.json');
    return;
  }
  const state = loadState();
  if (!state.active) {
    console.log('[LANGGRAPH] No active workflow');
    console.log(`[LANGGRAPH] History: ${state.history.length} workflows`);
    return;
  }
  const wf = state.active;
  console.log(`[LANGGRAPH] Active: ${wf.graph_name} (${wf.id})`);
  console.log(`[LANGGRAPH] Step ${wf.step + 1}/${wf.nodes.length}: ${wf.current_node}`);
  console.log(`[LANGGRAPH] Path: ${wf.nodes.join(' → ')}`);
  console.log(`[LANGGRAPH] Started: ${wf.started_at}`);
}

/**
 * Clear the active workflow (call on session-end or task completion).
 */
function clearActive() {
  const flags = loadFlags();
  if (!flags.components || !flags.components.langraph) return;
  const state = loadState();
  if (state.active) {
    state.active.status = 'cleared';
    state.active = null;
    saveState(state);
  }
}

module.exports = { startWorkflow, advance, status, printStatus, clearActive, detectGraph, BUILTIN_GRAPHS };
