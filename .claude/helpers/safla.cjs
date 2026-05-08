'use strict';
/**
 * SAFLA — Self-Adaptive Feedback Loop Architecture (v6.1 Micro)
 * Lightweight Node.js implementation. No external dependencies.
 *
 * What it does:
 *   1. Records agent outcomes (success/failure) per Enneagram node
 *   2. Adjusts routing confidence weights over time
 *   3. Surfaces "what worked last time" hints in route output
 *
 * Data: .claude-flow/data/safla.json
 */

const fs   = require('fs');
const path = require('path');

const DATA_DIR   = path.join(process.cwd(), '.claude-flow', 'data');
const SAFLA_PATH = path.join(DATA_DIR, 'safla.json');
const FLAGS_PATH = path.join(__dirname, 'feature-flags.json');

function loadFlags() {
  try { return JSON.parse(fs.readFileSync(FLAGS_PATH, 'utf-8')); } catch { return {}; }
}

function ensureDataDir() {
  if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });
}

function load() {
  ensureDataDir();
  try {
    if (fs.existsSync(SAFLA_PATH)) return JSON.parse(fs.readFileSync(SAFLA_PATH, 'utf-8'));
  } catch { /* start fresh */ }
  return {
    version: '1.0',
    updated: new Date().toISOString(),
    nodes: {},        // node_id → { success, failure, last_task, weight_adj }
    sessions: 0,
    total_feedbacks: 0,
  };
}

function save(data) {
  ensureDataDir();
  data.updated = new Date().toISOString();
  // Atomic write with pid-suffixed tmp so two concurrent saves never
  // clobber each other's tmp file before rename.
  const tmp = SAFLA_PATH + '.' + process.pid + '.' + Date.now() + '.tmp';
  fs.writeFileSync(tmp, JSON.stringify(data, null, 2), 'utf-8');
  fs.renameSync(tmp, SAFLA_PATH);
}

/**
 * Record outcome for a node after task completion.
 * @param {number|string} nodeId   — Enneagram node (1-9)
 * @param {boolean}       success  — true = worked, false = failed/reverted
 * @param {string}        task     — short task label
 */
function recordOutcome(nodeId, success, task) {
  const flags = loadFlags();
  if (!flags.components || !flags.components.safla) return;

  const data = load();
  const key  = String(nodeId);
  if (!data.nodes[key]) data.nodes[key] = { success: 0, failure: 0, last_task: '', weight_adj: 0 };

  const node = data.nodes[key];
  if (success) node.success++;
  else node.failure++;
  node.last_task = (task || '').substring(0, 80);

  // Adaptive weight: +0.05 per success, -0.1 per failure (asymmetric — penalize more)
  node.weight_adj = Math.max(-0.5, Math.min(0.5,
    node.weight_adj + (success ? 0.05 : -0.10)
  ));

  data.total_feedbacks++;
  save(data);
}

/**
 * Get adjusted confidence for a node (0..1 additive delta).
 */
function getWeightAdj(nodeId) {
  const flags = loadFlags();
  if (!flags.components || !flags.components.safla) return 0;
  const data = load();
  return (data.nodes[String(nodeId)] || {}).weight_adj || 0;
}

/**
 * Returns a one-line hint string for route output.
 * e.g. "[SAFLA] Node 3: 12 successes, +0.35 adj | last: implement auth"
 */
function hint(nodeId) {
  const flags = loadFlags();
  if (!flags.components || !flags.components.safla) return '';
  const data = load();
  const node = data.nodes[String(nodeId)];
  if (!node || (node.success + node.failure) === 0) return '';
  const total = node.success + node.failure;
  const rate  = Math.round((node.success / total) * 100);
  if (isNaN(node.weight_adj)) node.weight_adj = 0;
  const adj   = node.weight_adj >= 0 ? '+' + node.weight_adj.toFixed(2) : node.weight_adj.toFixed(2);
  return `[SAFLA] Node ${nodeId}: ${rate}% success (${total} tasks) | adj ${adj} | last: ${node.last_task || 'n/a'}`;
}

/**
 * Print full stats to stdout.
 */
function stats() {
  const flags = loadFlags();
  if (!flags.components || !flags.components.safla) {
    console.log('[SAFLA] disabled in feature-flags.json');
    return;
  }
  const data = load();
  console.log(`[SAFLA] Sessions: ${data.sessions} | Total feedbacks: ${data.total_feedbacks}`);
  for (const [nid, node] of Object.entries(data.nodes)) {
    const total = node.success + node.failure;
    if (total === 0) continue;
    const rate = Math.round((node.success / total) * 100);
    const adj  = node.weight_adj >= 0 ? '+' + node.weight_adj.toFixed(2) : node.weight_adj.toFixed(2);
    console.log(`  Node ${nid}: ${rate}% ok | adj ${adj} | last: ${node.last_task}`);
  }
}

/**
 * Mark session start (increments counter).
 */
function sessionStart() {
  const flags = loadFlags();
  if (!flags.components || !flags.components.safla) return;
  const data = load();
  data.sessions++;
  save(data);
}

/**
 * Sync cu CodeBurn: penalizează noduri cu cost/call ridicat.
 * Apelat la session-end după ce codeburn.totals() e disponibil.
 * @param {object} burnData  — { today_cost, today_calls, ... }
 * @param {object} nodeUsage — { nodeId: callCount, ... } opțional
 */
function syncWithCodeBurn(burnData, nodeUsage) {
  const flags = loadFlags();
  if (!flags.components || !flags.components.safla) return;
  if (!burnData || !burnData.today_calls) return;

  const costPerCall = burnData.today_cost / burnData.today_calls;
  // Dacă cost/call > $0.05 → penalizare ușoară pe toate nodurile active
  if (costPerCall > 0.05) {
    const data = load();
    for (const key of Object.keys(data.nodes)) {
      const node = data.nodes[key];
      if ((node.success + node.failure) > 0) {
        node.weight_adj = Math.max(-0.5, node.weight_adj - 0.02);
      }
    }
    data.updated = new Date().toISOString();
    save(data);
    process.stderr.write(`[SAFLA] CodeBurn sync: cost/call $${costPerCall.toFixed(3)} → -0.02 adj on active nodes\n`);
  }
}

module.exports = { recordOutcome, getWeightAdj, hint, stats, sessionStart, syncWithCodeBurn };
