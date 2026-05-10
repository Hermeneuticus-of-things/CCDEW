'use strict';
const fs = require('fs');
const path = require('path');
const { writeAtomicJson } = require('./lib/atomic-write.cjs');
const { isEnabled } = require('./lib/flags.cjs');
const { isValidNodeId, asString, clampNumber } = require('./lib/validate.cjs');
const { withLock } = require('./lib/file-lock.cjs');

const DATA_DIR   = path.join(process.cwd(), '.claude-flow', 'data');
const SAFLA_PATH = path.join(DATA_DIR, 'safla.json');

function ensureDataDir() {
  if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });
}

function emptyState() {
  return {
    version: '2.0',
    updated: new Date().toISOString(),
    nodes: {},
    sessions: 0,
    total_feedbacks: 0,
  };
}

function load() {
  ensureDataDir();
  try {
    if (fs.existsSync(SAFLA_PATH)) {
      let data = JSON.parse(fs.readFileSync(SAFLA_PATH, 'utf-8'));
      if (data && typeof data === 'object' && data.nodes) {
        const { migrate } = require('./lib/migrate.cjs');
        data = migrate(data, 'safla', [
          { from: '1.0', to: '2.0', up: d => ({ ...d, version: '2.0' }) },
        ]);
        return data;
      }
    }
  } catch (e) { try { require('./lib/error-log.cjs').logError('safla.load', e); } catch {} }
  return emptyState();
}

function save(data) {
  ensureDataDir();
  data.updated = new Date().toISOString();
  writeAtomicJson(SAFLA_PATH, data);
}

function recordOutcome(nodeId, success, task) {
  if (!isEnabled('safla')) return;
  if (!isValidNodeId(nodeId)) return;
  ensureDataDir();
  // Cross-process critical section — read-modify-write must be atomic
  // across multiple Claude sessions writing safla.json simultaneously.
  try {
    withLock(SAFLA_PATH, () => {
      const data = load();
      const key = String(nodeId);
      if (!data.nodes[key]) {
        data.nodes[key] = { success: 0, failure: 0, last_task: '', weight_adj: 0 };
      }
      const node = data.nodes[key];
      if (success) node.success++; else node.failure++;
      node.last_task = asString(task, 80);
      node.weight_adj = clampNumber(
        node.weight_adj + (success ? 0.05 : -0.10), -0.5, 0.5
      );
      data.total_feedbacks++;
      save(data);
    }, { timeoutMs: 5000 });
  } catch (e) {
    try { require('./lib/error-log.cjs').logError('safla.recordOutcome.lock', e); } catch {}
  }
}

function getWeightAdj(nodeId) {
  if (!isEnabled('safla') || !isValidNodeId(nodeId)) return 0;
  const data = load();
  return (data.nodes[String(nodeId)] || {}).weight_adj || 0;
}

function getWeights() {
  if (!isEnabled('safla')) return {};
  const data = load();
  const out = {};
  for (const [k, v] of Object.entries(data.nodes)) {
    if (isValidNodeId(k)) out[k] = v.weight_adj;
  }
  return out;
}

function hint(nodeId) {
  if (!isEnabled('safla') || !isValidNodeId(nodeId)) return '';
  const data = load();
  const node = data.nodes[String(nodeId)];
  if (!node || (node.success + node.failure) < 3) return '';
  const rate = node.success / (node.success + node.failure);
  if (rate >= 0.75) return `[SAFLA] node ${nodeId}: ${(rate * 100).toFixed(0)}% ok over ${node.success + node.failure} runs`;
  if (rate <= 0.25) return `[SAFLA] node ${nodeId}: only ${(rate * 100).toFixed(0)}% ok — consider alt route`;
  return '';
}

function stats() {
  if (!isEnabled('safla')) return { sessions: 0, total_feedbacks: 0, nodes: {} };
  const data = load();
  return {
    sessions: data.sessions || 0,
    total_feedbacks: data.total_feedbacks || 0,
    nodes: Object.fromEntries(
      Object.entries(data.nodes)
        .filter(([k]) => isValidNodeId(k))
        .map(([k, v]) => [k, {
          success: v.success, failure: v.failure,
          rate: v.success + v.failure > 0
            ? +(v.success / (v.success + v.failure)).toFixed(2) : 0,
          weight_adj: +v.weight_adj.toFixed(2),
          last_task: v.last_task || '',
        }])
    ),
  };
}

function sessionStart() {
  if (!isEnabled('safla')) return;
  const data = load();
  data.sessions = (data.sessions || 0) + 1;
  save(data);
}

function syncWithCodeBurn(burnTotals) {
  if (!isEnabled('safla') || !burnTotals || burnTotals.source === 'unavailable') return;
  const costPerCall = burnTotals.today_calls > 0
    ? burnTotals.today_cost / burnTotals.today_calls : 0;
  if (costPerCall <= 0.05) return;
  const data = load();
  for (const k of Object.keys(data.nodes)) {
    if (!isValidNodeId(k)) continue;
    const n = data.nodes[k];
    const recent = n.success + n.failure;
    if (recent >= 5) {
      n.weight_adj = clampNumber(n.weight_adj - 0.02, -0.5, 0.5);
    }
  }
  save(data);
}

function printStats() {
  const s = stats();
  console.log(`[SAFLA] Sessions: ${s.sessions} | Total feedbacks: ${s.total_feedbacks}`);
  for (const [nid, n] of Object.entries(s.nodes)) {
    const adj = n.weight_adj >= 0 ? '+' + n.weight_adj.toFixed(2) : n.weight_adj.toFixed(2);
    console.log(`  Node ${nid}: ${Math.round(n.rate * 100)}% ok | adj ${adj} | last: ${n.last_task || '-'}`);
  }
}

module.exports = {
  recordOutcome, getWeightAdj, getWeights,
  hint, stats, printStats, sessionStart, syncWithCodeBurn,
};
