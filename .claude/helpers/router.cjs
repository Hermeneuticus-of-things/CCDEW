#!/usr/bin/env node
'use strict';
/**
 * router.cjs — Enneagram 9-Node Task Router (v6.1 SLIM)
 *
 * Routes tasks to the optimal Enneagram node based on keyword analysis,
 * pattern matching (instincts), and SAFLA weight adjustments.
 *
 * API:
 *   routeTask(prompt) → { node, agent, confidence, reason }
 *   getAgentName(node) → string
 *   analyzeTask(prompt) → detailed analysis
 */

const path = require('path');

// Lazy-load optional dependencies
function lazy(name) {
  try { return require(path.join(__dirname, name + '.cjs')); } catch { return null; }
}

// ── Enneagram Node Definitions ──────────────────────────────────────────────
const NODES = {
  1: { name: 'Perfectionist',  agent: 'quality-audit',    keywords: ['lint', 'quality', 'standard', 'format', 'clean', 'refactor', 'convention', 'style', 'check', 'validate', 'test', 'unit test', 'coverage'] },
  2: { name: 'Helper',         agent: 'docs-helper',      keywords: ['document', 'doc', 'readme', 'guide', 'tutorial', 'explain', 'how to', 'help', 'write', 'comment', 'api doc', 'javadoc', 'jsdoc'] },
  3: { name: 'Achiever',       agent: 'test-ci',          keywords: ['test', 'ci', 'pipeline', 'deploy', 'build', 'release', 'automate', 'benchmark', 'performance', 'speed', 'optimize', 'fast'] },
  4: { name: 'Individualist',  agent: 'architect',        keywords: ['architecture', 'design', 'pattern', 'structure', 'module', 'component', 'system', 'plan', 'spec', 'adr', 'ddd', 'bounded'] },
  5: { name: 'Investigator',   agent: 'debug-security',   keywords: ['debug', 'bug', 'error', 'crash', 'security', 'vulnerability', 'cve', 'exploit', 'audit', 'scan', 'investigate', 'root cause', 'trace'] },
  6: { name: 'Loyalist',       agent: 'error-handler',    keywords: ['error handling', 'try catch', 'fallback', 'retry', 'resilience', 'robust', 'safe', 'guard', 'validate', 'input', 'edge case', 'defensive'] },
  7: { name: 'Enthusiast',     agent: 'prototype',        keywords: ['prototype', 'explore', 'experiment', 'idea', 'new', 'creative', 'feature', 'brainstorm', 'spike', 'proof of concept', 'poc', 'draft'] },
  8: { name: 'Challenger',     agent: 'infrastructure',   keywords: ['infra', 'server', 'docker', 'kubernetes', 'deploy', 'pipeline', 'ci/cd', 'network', 'database', 'migration', 'provision', 'terraform', 'cloud'] },
  9: { name: 'Peacemaker',     agent: 'review-merge',     keywords: ['review', 'merge', 'pr', 'pull request', 'consolidate', 'summarize', 'cleanup', 'organize', 'sync', 'align', 'harmonize', 'balance'] },
};

// ── Keyword Scoring ─────────────────────────────────────────────────────────
function scoreNode(nodeId, prompt) {
  const node = NODES[nodeId];
  if (!node) return 0;

  const lower = prompt.toLowerCase();
  let score = 0;

  for (const kw of node.keywords) {
    if (lower.includes(kw)) {
      // Multi-word keywords score higher
      const weight = kw.includes(' ') ? 2 : 1;
      score += weight;
    }
  }

  return score;
}

// ── Main Router ─────────────────────────────────────────────────────────────
function routeTask(prompt) {
  if (!prompt || typeof prompt !== 'string' || !prompt.trim()) {
    return { node: 5, agent: 'debug-security', confidence: 0.3, reason: 'Empty prompt — default to Investigator' };
  }

  const trimmed = prompt.trim();

  // Check instincts for pattern match first
  const instincts = lazy('instincts');
  if (instincts && instincts.suggest) {
    const suggestion = instincts.suggest(trimmed);
    if (suggestion && suggestion.confidence > 0.7) {
      const node = suggestion.node;
      return {
        node,
        agent: NODES[node]?.agent || 'unknown',
        confidence: Math.min(0.95, suggestion.confidence),
        reason: `Instinct pattern match (${suggestion.samples} samples, ${Math.round(suggestion.success_rate * 100)}% success)`,
      };
    }
  }

  // Score all nodes
  const scores = {};
  for (const nodeId of Object.keys(NODES)) {
    scores[nodeId] = scoreNode(parseInt(nodeId, 10), trimmed);
  }

  // Find best node
  let bestNode = 5; // default: Investigator
  let bestScore = 0;
  for (const [nodeId, score] of Object.entries(scores)) {
    if (score > bestScore) {
      bestScore = score;
      bestNode = parseInt(nodeId, 10);
    }
  }

  // Apply SAFLA weight adjustment
  const safla = lazy('safla');
  let confidence = 0.5;
  if (bestScore > 0) {
    confidence = Math.min(0.9, 0.4 + bestScore * 0.1);
  }

  if (safla && safla.getWeightAdj) {
    const adj = safla.getWeightAdj(bestNode);
    if (adj && !isNaN(adj)) {
      confidence = Math.max(0.1, Math.min(0.95, confidence + adj));
    }
  }

  // Build reason
  const matchedKw = NODES[bestNode].keywords.filter(kw => trimmed.toLowerCase().includes(kw));
  const reason = matchedKw.length > 0
    ? `Keywords: ${matchedKw.slice(0, 3).join(', ')}`
    : 'No strong keyword match — default routing';

  return {
    node: bestNode,
    agent: NODES[bestNode].agent,
    confidence: +confidence.toFixed(2),
    reason,
  };
}

// ── Helpers ─────────────────────────────────────────────────────────────────
function getAgentName(nodeId) {
  return NODES[nodeId]?.name || 'Unknown';
}

function analyzeTask(prompt) {
  if (!prompt) return { prompt: '', scores: {}, recommendation: routeTask('') };

  const scores = {};
  for (const nodeId of Object.keys(NODES)) {
    scores[nodeId] = scoreNode(parseInt(nodeId, 10), prompt);
  }

  return {
    prompt,
    scores,
    recommendation: routeTask(prompt),
    allNodes: Object.entries(NODES).map(([id, n]) => ({
      node: parseInt(id, 10),
      name: n.name,
      agent: n.agent,
      score: scores[id] || 0,
    })).sort((a, b) => b.score - a.score),
  };
}

// ── CLI ─────────────────────────────────────────────────────────────────────
if (require.main === module) {
  const args = process.argv.slice(2);
  const cmd = args[0];

  if (cmd === 'analyze') {
    const result = analyzeTask(args.slice(1).join(' '));
    console.log(JSON.stringify(result, null, 2));
  } else if (cmd === 'nodes') {
    for (const [id, n] of Object.entries(NODES)) {
      console.log(`Node ${id}: ${n.name} (${n.agent})`);
      console.log(`  Keywords: ${n.keywords.join(', ')}`);
    }
  } else {
    const result = routeTask(args.join(' '));
    console.log(`Node ${result.node}: ${getAgentName(result.node)} (${result.agent})`);
    console.log(`Confidence: ${(result.confidence * 100).toFixed(0)}%`);
    console.log(`Reason: ${result.reason}`);
  }
}

module.exports = { routeTask, getAgentName, analyzeTask, NODES };
