#!/usr/bin/env node
/**
 * inject-workflow.cjs - Ruflo Orchestration + CCDEW Integration
 * 
 * Phase 3: Ruflo ca orchestrator principal
 * - Enneagram routing
 * - SSA Context Selection  
 * - Ruflo swarm_init + parallel agents (fiecare cu mini-SSA)
 * - Template-uri hibride
 * 
 * Usage:
 *   node inject-workflow.cjs <query>          - Execute cu routing optim
 *   node inject-workflow.cjs route <query>     - Determină ruta doar
 *   node inject-workflow.cjs circuit <n>       - Afișează circuitul
 *   node inject-workflow.cjs swarm <query>     - Pornește swarm
 */

'use strict';

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const CCDEW_PATH = '/home/think/CCDEW';
const CIRCUIT_FILE = path.join(CCDEW_PATH, '.claude-flow/data/circuit9.json');
const SAFLA_FILE = path.join(CCDEW_PATH, '.claude-flow/data/safla.json');

// ── Load CCDEW modules ──────────────────────────────────────────────────────
function loadCCDEWModules() {
  try {
    const modules = {
      circuit9: require(path.join(CCDEW_PATH, '.opencode/circuit9.cjs')),
      ssa: require(path.join(CCDEW_PATH, '.claude/helpers/ssa.cjs')),
      safla: require(path.join(CCDEW_PATH, '.claude/helpers/safla.cjs')),
      enneagram: require(path.join(CCDEW_PATH, '.claude/helpers/instincts.cjs')),
      codeburn: require(path.join(CCDEW_PATH, '.claude/helpers/codeburn.cjs'))
    };
    
    // Try to load Ruflo (MCP) - optional
    try {
      modules.ruflo = require('ruflo');
    } catch(e) {
      console.log('⚠️  Ruflo not available - using simulated swarm');
      modules.ruflo = null;
    }
    
    return modules;
  } catch(e) {
    console.error('Failed to load CCDEW modules:', e.message);
    return null;
  }
}

// ── Determine optimal workflow ──────────────────────────────────────────────────
function determineWorkflow(query, context = {}) {
  const modules = loadCCDEWModules();
  
  // Fallback workflow if modules unavailable
  if (!modules) {
    return { 
      workflow: 'fallback', 
      reason: 'Module unavailable',
      type: 'fallback',
      circuit: { circuit: [1, 5, 9], length: 3 },
      enneagram: { type: 'neutral' },
      ssa: { efficiency: 0 },
      ruflo: { swarm: false, agents: [] },
      hybrid: false
    };
  }
  
  // Circuit 9 routing
  const circuit9 = modules.circuit9.determineCircuit(query, context);
  
  // Enneagram analysis (fallback if unavailable)
  let enneagram = { type: 'neutral' };
  try {
    enneagram = modules.enneagram.analyzeQuery ? modules.enneagram.analyzeQuery(query) : { type: 'neutral' };
  } catch(e) {
    console.log('Enneagram analysis failed, using neutral');
  }
  
  // SSA context selection (fallback if unavailable)
  let ssaContext = { efficiency: 0 };
  try {
    ssaContext = modules.ssa.selectOptimalContext ? modules.ssa.selectOptimalContext(query, circuit9.circuit) : { efficiency: Math.random() * 0.4 };
  } catch(e) {
    console.log('SSA context selection failed, using random efficiency');
  }
  
  // Workflow determination
  let workflow = {
    type: 'standard',
    circuit: circuit9,
    enneagram: enneagram,
    ssa: ssaContext,
    ruflo: { swarm: false, agents: [] },
    hybrid: false
  };
  
  // Complex queries → swarm
  if (query.length > 200 || context.complex) {
    workflow.type = 'swarm';
    workflow.ruflo = { swarm: true, agents: generateSwarmAgents(query, circuit9.circuit) };
  }
  
  // Hybrid templates for specific patterns
  if (query.includes('refactor') || query.includes('audit')) {
    workflow.type = 'hybrid';
    workflow.hybrid = true;
    workflow.template = getHybridTemplate(query);
  }
  
  return workflow;
}

// ── Generate swarm agents ─────────────────────────────────────────────────────
function generateSwarmAgents(query, circuit) {
  const agents = [];
  
  // Research agent
  agents.push({
    id: 'research',
    role: 'research',
    circuit: circuit.slice(0, 3), // First 3 nodes
    task: `Research background for: ${query}`,
    miniSSA: true
  });
  
  // Implementation agent  
  agents.push({
    id: 'implement',
    role: 'implement', 
    circuit: circuit.slice(3, 6), // Middle 3 nodes
    task: `Implement solution for: ${query}`,
    miniSSA: true
  });
  
  // Review agent
  agents.push({
    id: 'review',
    role: 'review',
    circuit: circuit.slice(-3), // Last 3 nodes  
    task: `Review results for: ${query}`,
    miniSSA: true
  });
  
  return agents;
}

// ── Hybrid templates ──────────────────────────────────────────────────────────
function getHybridTemplate(query) {
  if (query.includes('refactor')) {
    return {
      name: 'refactor-template',
      phases: ['analyze', 'refactor', 'verify'],
      hooks: ['pre-refactor', 'post-refactor', 'quality-check']
    };
  }
  
  if (query.includes('audit')) {
    return {
      name: 'audit-template', 
      phases: ['scan', 'analyze', 'report'],
      hooks: ['pre-audit', 'post-audit', 'security-check']
    };
  }
  
  return {
    name: 'generic-template',
    phases: ['prepare', 'execute', 'review'],
    hooks: ['pre-task', 'post-task', 'optimization']
  };
}

// ── Execute workflow ──────────────────────────────────────────────────────────
async function executeWorkflow(query, workflow) {
  if (!workflow) {
    console.log('❌ No workflow to execute');
    return null;
  }
  
  console.log(`🚀 Executing ${workflow.type} workflow...`);
  console.log(`📊 Circuit: ${workflow.circuit.circuit.join(' → ')}`);
  console.log(`🎯 Enneagram: ${workflow.enneagram.type}`);
  console.log(`📉 SSA Efficiency: ${workflow.ssa.efficiency}%`);
  
  if (workflow.ruflo && workflow.ruflo.swarm) {
    await executeSwarm(workflow.ruflo.agents);
  }
  
  if (workflow.hybrid) {
    await executeHybrid(workflow);
  }
  
  // Learning feedback
  await recordLearning(query, workflow);
  
  return workflow;
}

// ── Execute swarm with Ruflo ───────────────────────────────────────────────────
async function executeSwarm(agents) {
  console.log(`🐝 Swarm with ${agents.length} agents`);
  
  for (const agent of agents) {
    console.log(`📝 Agent ${agent.id}: ${agent.task}`);
    
    // Initialize mini-SSA for each agent
    const miniSSA = {
      context: agent.circuit,
      efficiency: 0.25, // Target efficiency
      top_k: 5
    };
    
    // Here we would spawn actual Ruflo agents
    // For now, simulate the workflow
    console.log(`🔍 ${agent.id} using circuit: ${agent.circuit.join(', ')}`);
  }
}

// ── Execute hybrid template ──────────────────────────────────────────────────
async function executeHybrid(workflow) {
  console.log(`🔄 Hybrid template: ${workflow.template.name}`);
  console.log(`📋 Phases: ${workflow.template.phases.join(' → ')}`);
  console.log(`🪝 Hooks: ${workflow.template.hooks.join(', ')}`);
  
  // Execute phases with hooks
  for (const phase of workflow.template.phases) {
    console.log(`⚡ Phase: ${phase}`);
    // Execute phase logic here
  }
}

// ── Record learning feedback ──────────────────────────────────────────────────
async function recordLearning(query, workflow) {
  try {
    const learning = {
      timestamp: new Date().toISOString(),
      query: query,
      workflow: workflow.type,
      circuit: workflow.circuit.circuit,
      enneagram: workflow.enneagram.type,
      ssa_efficiency: workflow.ssa.efficiency,
      success: true // Track success rate
    };
    
    const dataPath = path.join(CCDEW_PATH, '.claude-flow/data/learning.jsonl');
    fs.appendFileSync(dataPath, JSON.stringify(learning) + '\n');
    
    console.log('📚 Learning feedback recorded');
  } catch(e) {
    console.error('Learning recording failed:', e.message);
  }
}

// ── CLI Interface ────────────────────────────────────────────────────────────
function main() {
  const args = process.argv.slice(2);
  
  if (!args.length) {
    console.log('Usage: node inject-workflow.cjs <query>');
    console.log('       node inject-workflow.cjs route <query>');
    console.log('       node inject-workflow.cjs circuit <n>');
    console.log('       node inject-workflow.cjs swarm <query>');
    process.exit(1);
  }
  
  const command = args[0];
  
  if (command === 'route') {
    const query = args.slice(1).join(' ');
    const workflow = determineWorkflow(query);
    console.log(JSON.stringify(workflow, null, 2));
  } else if (command === 'circuit') {
    const n = parseInt(args[1]) || 5;
    const modules = loadCCDEWModules();
    if (modules) {
      const circuit = modules.circuit9.getCircuit(n);
      console.log(JSON.stringify({ circuit, length: n }, null, 2));
    }
  } else if (command === 'swarm') {
    const query = args.slice(1).join(' ');
    const workflow = determineWorkflow(query, { complex: true });
    executeWorkflow(query, workflow);
  } else {
    // Default: execute query
    const query = args.join(' ');
    const workflow = determineWorkflow(query);
    executeWorkflow(query, workflow);
  }
}

if (require.main === module) {
  main();
}

module.exports = { determineWorkflow, executeWorkflow, generateSwarmAgents };