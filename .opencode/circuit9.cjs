#!/usr/bin/env node
/**
 * circuit9.cjs
 * Rutare adaptivă cu 9 straturi + Circuit 9
 * 
 * Usage:
 *   node circuit9.cjs route <query>     - Routează un query
 *   node circuit9.cjs circuit <n>      - Afișează circuitul de n noduri
 *   node circuit9.cjs execute <query> - Execută query cu circuitul optim
 */

'use strict';

const fs = require('fs');
const path = require('path');

const CCDEW_PATH = '/home/think/CCDEW';
const CIRCUIT_FILE = path.join(CCDEW_PATH, '.claude-flow/data/circuit9.json');
const SAFLA_FILE = path.join(CCDEW_PATH, '.claude-flow/data/safla.json');

const COLORS = {
  reset: '\x1b[0m', green: '\x1b[32m', cyan: '\x1b[36m',
  yellow: '\x1b[33m', red: '\x1b[31m', bold: '\x1b[1m'
};

function log(msg, c = 'reset') { console.log(COLORS[c] + msg + COLORS.reset); }

// Load Circuit 9 config
function loadCircuit() {
  if (fs.existsSync(CIRCUIT_FILE)) {
    return JSON.parse(fs.readFileSync(CIRCUIT_FILE, 'utf-8'));
  }
  return null;
}

// Load SAFLA weights
function loadSAFLA() {
  if (fs.existsSync(SAFLA_FILE)) {
    return JSON.parse(fs.readFileSync(SAFLA_FILE, 'utf-8'));
  }
  return null;
}

// Determine optimal circuit length
function determineCircuit(query, context = {}) {
  const len = query.length;
  
  // Ultra-rapid: 3 noduri
  if (len < 60 || context.fast === true) {
    return { length: 3, circuit: [1, 5, 9], reason: 'Ultra-rapid (task simplu)' };
  }
  
  // Task mediu: 5 noduri
  if (len < 200 || context.medium === true || context.needs_skills === true) {
    return { length: 5, circuit: [1, 3, 5, 7, 9], reason: 'Optim (balanță calitate-viteză)' };
  }
  
  // Task complex: 9 noduri
  return { length: 9, circuit: [1, 2, 3, 4, 5, 6, 7, 8, 9], reason: 'Complet (calitate maximă)' };
}

// Score Enneagram type with 5D scoring
function scoreEnneagramType(node, query, circuit) {
  const cfg = loadCircuit();
  const safla = loadSAFLA();
  
  if (!cfg || !safla) return 1.0;
  
  const weights = cfg.arc_weights || {};
  const ssa = cfg.ssa_scoring || {};
  
  // Get base weight from SAFLA
  const baseWeight = safla.nodes?.[node]?.weight || safla.default?.[node] || 1.0;
  
  // Arc weight contribution
  const inferTarget = (q) => {
    if (q.includes('cum') || q.includes('mai bine')) return node + 2; // growth
    if (q.includes('nu') || q.includes('e greșit')) return node + 5; // stress
    return node + 1;
  };
  const arcW = weights[`${node}→${inferTarget(query)}`] || 1.0;
  
  // Stress/Growth scoring
  const stress = cfg.stress_growth?.stress?.[`${node}→${inferTarget(query)}`] || 1.0;
  const growth = cfg.stress_growth?.growth?.[`${node}→${inferTarget(query)}`] || 1.0;
  
  // Recent success from SAFLA
  const recentSuccess = safla.nodes?.[node]?.success_rate || 0.5;
  
  // 5D scoring formula
  const score = (
    (arcW * (ssa.arc_weight || 0.4)) +
    (stress * (ssa.stress_arc || 0.2)) +
    (growth * (ssa.growth_arc || 0.2)) +
    (baseWeight * (ssa.recent_success || 0.1))
  );
  
  return Math.min(Math.max(score, 0.5), 3.0);
}

// Execute circuit step
async function executeStep(step, query, state) {
  const stepInfo = {
    1: { name: 'Intrare', desc: 'Parsare + intent detection' },
    2: { name: 'Context', desc: 'Loader context relevant' },
    3: { name: 'Skills', desc: 'Activează skills necesare' },
    4: { name: 'Routing', desc: 'Determină nodul Enneagram' },
    5: { name: 'Execuție', desc: 'Rulează task-ul principal' },
    6: { name: 'Verificare', desc: 'Quality gate + validation' },
    7: { name: 'Skills Update', desc: 'Verifică + actualizează skills' },
    8: { name: 'Memorie', desc: 'Salvează în memorie hibridă' },
    9: { name: 'Consolidare', desc: 'Pruning + feedback' }
  };
  
  log(`  ${COLORS.cyan}→ Strat ${step}${COLORS.reset}: ${stepInfo[step].name}`, 'cyan');
  log(`    ${stepInfo[step].desc}`, 'yellow');
  
  // Simulate processing
  await new Promise(r => setTimeout(r, 50));
  
  return { step, ...stepInfo[step], state };
}

// Record feedback to SAFLA
function recordFeedback(nodeId, success, costDelta) {
  const safla = loadSAFLA();
  if (!safla) return;
  
  // Apply cost-aware adjustment
  if (costDelta > 0.2) {
    // Penalize high cost
    if (safla.nodes?.[nodeId]) {
      safla.nodes[nodeId].weight *= 0.9;
    }
  } else if (costDelta < -0.1) {
    // Reward low cost
    if (safla.nodes?.[nodeId]) {
      safla.nodes[nodeId].weight *= 1.1;
    }
  }
  
  if (!success) {
    // Extra penalty on failure
    if (safla.nodes?.[nodeId]) {
      safla.nodes[nodeId].weight *= 0.85;
    }
  }
  
  // Clamp to [0.5, 3.0]
  if (safla.nodes?.[nodeId]) {
    safla.nodes[nodeId].weight = Math.min(3.0, Math.max(0.5, safla.nodes[nodeId].weight));
  }
  
  // Increment feedbacks
  safla.total_feedbacks = (safla.total_feedbacks || 0) + 1;
  
  fs.writeFileSync(SAFLA_FILE, JSON.stringify(safla, null, 2));
}

// Main routing
async function routeQuery(query, context = {}) {
  log(`\n${COLORS.bold}🔄 Circuit 9 Router${COLORS.reset}`, 'cyan');
  log(`Query: "${query}"`, 'reset');
  
  // Determine circuit
  const { length, circuit, reason } = determineCircuit(query, context);
  log(`\nCircuit: ${length} noduri | ${reason}`, 'green');
  log(`Noduri: ${circuit.join(' → ')}\n`, 'cyan');
  
  // Execute circuit
  log(`${COLORS.bold}Executare:${COLORS.reset}`, 'reset');
  let state = { query, startTime: Date.now() };
  
  for (const step of circuit) {
    await executeStep(step, query, state);
  }
  
  const duration = Date.now() - state.startTime;
  log(`\n${COLORS.green}✅ Completat în ${duration}ms${COLORS.reset}`, 'green');
  
  return { length, circuit, duration };
}

// CLI
const args = process.argv.slice(2);
const cmd = args[0];

if (!cmd || cmd === 'help') {
  console.log(`
${COLORS.cyan}Circuit 9 — Rutare Adaptivă cu 9 Straturi${COLORS.reset}

Usage:
  node circuit9.cjs route "<query>"    - Routează query cu circuitul optim
  node circuit9.cjs circuit <n>       - Afișează circuitul de n noduri
  node circuit9.cjs weights           - Afișează ponderile curente
  node circuit9.cjs exec <query>      - Execută query complet

Circuits:
  3 noduri  → Ultra-rapid (1 → 5 → 9)
  5 noduri  → Optim (1 → 3 → 5 → 7 → 9)
  9 noduri  → Complet (1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9)
`);
} else if (cmd === 'route') {
  const query = args.slice(1).join(' ') || 'Test query';
  routeQuery(query);
} else if (cmd === 'circuit') {
  const n = parseInt(args[1]) || 3;
  const circuits = {
    3: [1, 5, 9],
    5: [1, 3, 5, 7, 9],
    9: [1, 2, 3, 4, 5, 6, 7, 8, 9]
  };
  log(`Circuit ${n}: ${circuits[n]?.join(' → ') || circuits[3].join(' → ')}`, 'cyan');
} else if (cmd === 'weights') {
  const cfg = loadCircuit();
  const safla = loadSAFLA();
  log('\nArc Weights:', 'cyan');
  Object.entries(cfg?.arc_weights || {}).forEach(([k, v]) => log(`  ${k}: ${v}`));
  log('\nSAFLA Nodes:', 'green');
  Object.entries(safla?.nodes || {}).forEach(([k, v]) => log(`  Node ${k}: weight=${v.weight || 1.0}`));
} else if (cmd === 'exec') {
  const query = args.slice(1).join(' ') || 'Test';
  routeQuery(query);
}

module.exports = { determineCircuit, scoreEnneagramType, recordFeedback, routeQuery };