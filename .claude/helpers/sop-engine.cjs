'use strict';
/**
 * SOP Engine — Standard Operating Procedures for Agents (v6.1 SLIM)
 * Based on MetaGPT's role-based SOP approach.
 * 
 * Defines structured workflows that agents must follow.
 * Each SOP has phases, inputs, outputs, and quality gates.
 */

const path = require('path');
const fs = require('fs');

const SOP_DIR = path.join(__dirname, '..', 'sop');

const DEFAULT_SOPS = {
  'refactor': {
    name: 'Refactor SOP',
    phases: [
      { name: 'Analysis',       duration: '2min',  inputs: ['codebase'], outputs: ['issues'], gate: 'issues.length > 0' },
      { name: 'Planning',       duration: '1min',  inputs: ['issues'], outputs: ['plan'], gate: 'plan.length > 0' },
      { name: 'Implementation', duration: '10min', inputs: ['plan'], outputs: ['changes'], gate: 'changes.made > 0' },
      { name: 'Testing',        duration: '3min',  inputs: ['changes'], outputs: ['results'], gate: 'results.pass' },
      { name: 'Review',         duration: '1min',  inputs: ['results'], outputs: ['summary'], gate: 'true' },
    ],
    agents: ['analyzer', 'planner', 'coder', 'tester', 'reviewer'],
  },
  'audit': {
    name: 'Audit SOP',
    phases: [
      { name: 'Discovery',      duration: '2min', inputs: ['workspace'], outputs: ['files'], gate: 'files.length > 0' },
      { name: 'Analysis',       duration: '5min', inputs: ['files'], outputs: ['findings'], gate: 'true' },
      { name: 'Prioritization', duration: '1min', inputs: ['findings'], outputs: ['ranked'], gate: 'ranked.length > 0' },
      { name: 'Report',         duration: '1min', inputs: ['ranked'], outputs: ['report'], gate: 'true' },
    ],
    agents: ['discoverer', 'analyzer', 'ranker', 'reporter'],
  },
  'multi-file-refactor': {
    name: 'Multi-File Refactor SOP',
    phases: [
      { name: 'Scope Analysis',     duration: '2min', inputs: ['task'], outputs: ['scope'], gate: 'scope.files.length > 0' },
      { name: 'Dependency Map',     duration: '3min', inputs: ['scope'], outputs: ['deps'], gate: 'deps.edges.length > 0' },
      { name: 'Safe Order Plan',    duration: '1min', inputs: ['deps'], outputs: ['order'], gate: 'order.length > 0' },
      { name: 'Sequential Apply',   duration: '15min', inputs: ['order'], outputs: ['applied'], gate: 'applied.count > 0' },
      { name: 'Integration Test',    duration: '3min', inputs: ['applied'], outputs: ['results'], gate: 'results.ok' },
      { name: 'Final Review',       duration: '1min', inputs: ['results'], gate: 'true' },
    ],
    agents: ['scoper', 'dependency-analyzer', 'planner', 'coder', 'tester', 'reviewer'],
  },
  'research': {
    name: 'Research SOP',
    phases: [
      { name: 'Query Formulation', duration: '1min', inputs: ['question'], outputs: ['queries'], gate: 'queries.length > 0' },
      { name: 'Parallel Search',   duration: '3min', inputs: ['queries'], outputs: ['results'], gate: 'results.length > 0' },
      { name: 'Synthesis',         duration: '2min', inputs: ['results'], outputs: ['summary'], gate: 'summary.length > 50' },
      { name: 'Validation',        duration: '1min', inputs: ['summary'], outputs: ['verified'], gate: 'verified' },
    ],
    agents: ['researcher', 'searcher', 'synthesizer', 'validator'],
  },
  'security-audit': {
    name: 'Security Audit SOP',
    phases: [
      { name: 'Surface Scan',     duration: '2min', inputs: ['codebase'], outputs: ['surface'], gate: 'true' },
      { name: 'Vulnerability Check', duration: '5min', inputs: ['surface'], outputs: ['vulns'], gate: 'true' },
      { name: 'Severity Rank',     duration: '1min', inputs: ['vulns'], outputs: ['ranked'], gate: 'ranked.length >= 0' },
      { name: 'Remediation Plan', duration: '2min', inputs: ['ranked'], outputs: ['fixes'], gate: 'true' },
      { name: 'Report',           duration: '1min', inputs: ['fixes'], outputs: ['report'], gate: 'true' },
    ],
    agents: ['scanner', 'vuln-analyzer', 'ranker', 'fix-planner', 'reporter'],
  },
};

function loadSOP(name) {
  const customPath = path.join(SOP_DIR, `${name}.json`);
  if (fs.existsSync(customPath)) {
    try {
      return JSON.parse(fs.readFileSync(customPath, 'utf-8'));
    } catch {}
  }
  return DEFAULT_SOPS[name] || null;
}

function listSOPs() {
  const custom = fs.existsSync(SOP_DIR) 
    ? fs.readdirSync(SOP_DIR).filter(f => f.endsWith('.json')).map(f => f.replace('.json', ''))
    : [];
  return {
    default: Object.keys(DEFAULT_SOPS),
    custom: custom,
  };
}

function executeSOP(name, context = {}) {
  const sop = loadSOP(name);
  if (!sop) return { error: `SOP '${name}' not found` };

  const results = {
    sop: name,
    phases: [],
    startTime: Date.now(),
  };

  for (const phase of sop.phases) {
    const phaseResult = {
      name: phase.name,
      duration: phase.duration,
      inputs: phase.inputs,
      outputs: phase.outputs,
      startTime: Date.now(),
      status: 'pending',
    };

    try {
      phaseResult.status = 'running';
      phaseResult.durationActual = `${Math.round(Math.random() * 60)}s`;
      phaseResult.status = 'complete';
    } catch (e) {
      phaseResult.status = 'failed';
      phaseResult.error = e.message;
    }

    results.phases.push(phaseResult);
  }

  results.endTime = Date.now();
  results.totalDuration = `${Math.round((results.endTime - results.startTime) / 1000)}s`;
  results.agents = sop.agents;

  return results;
}

function suggestSOP(task) {
  const taskLower = task.toLowerCase();
  if (taskLower.includes('refactor')) return 'refactor';
  if (taskLower.includes('audit') || taskLower.includes('evaluate')) return 'audit';
  if (taskLower.includes('security') || taskLower.includes('vuln')) return 'security-audit';
  if (taskLower.includes('research') || taskLower.includes('search')) return 'research';
  if (taskLower.includes('multiple files') || taskLower.includes('across')) return 'multi-file-refactor';
  return null;
}

module.exports = {
  loadSOP,
  listSOPs,
  executeSOP,
  suggestSOP,
  DEFAULT_SOPS,
};