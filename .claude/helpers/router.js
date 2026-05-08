#!/usr/bin/env node
/**
 * Claude Flow Agent Router — Enneagram Edition
 * Deterministic routing via Enneagram topology (9 nodes, 27 arcs).
 * Replaces ambiguous regex with O(1) lookup + partial-match fallback.
 * Output compatible with hook-handler.cjs: { agent, confidence, reason, node, node_name }
 */

// ─── ENNEAGRAM TOPOLOGY ──────────────────────────────────────────────────────
// Original arcs: hexad 1→4→2→8→5→7→1 + triangle 3→6→9→3
// Wings: 1↔2, 2↔3, 3↔4, 4↔5, 5↔6, 6↔7, 7↔8, 8↔9, 9↔1

const ENNEAGRAM_NODES = {
  1: { name: 'Reformer/QA',        agent: 'reviewer',           cycle: 'hexad'    },
  2: { name: 'Integrator',         agent: 'backend-dev',        cycle: 'hexad'    },
  3: { name: 'Builder',            agent: 'coder',              cycle: 'triangle' },
  4: { name: 'Contextualizer',     agent: 'researcher',         cycle: 'hexad'    },
  5: { name: 'Analyzer',           agent: 'analyst',            cycle: 'hexad'    },
  6: { name: 'Validator',          agent: 'tester',             cycle: 'triangle' },
  7: { name: 'Architect',          agent: 'architecture',       cycle: 'hexad'    },
  8: { name: 'Orchestrator',       agent: 'sparc-orchestrator', cycle: 'hexad'    },
  9: { name: 'Memory/Consolidator',agent: 'memory-specialist',  cycle: 'triangle' },
};

// Keyword → node (exact lookup, O(1))
const ENNEAGRAM_ROUTING = {
  // Node 1 — QA / Reviewer
  review: 1, qa: 1, quality: 1, audit: 1, security: 1, check: 1, validate_quality: 1,

  // Node 2 — Integrator / Backend-dev
  integrate: 2, integration: 2, api: 2, connect: 2, backend: 2, database: 2,
  server: 2, endpoint: 2, authentication: 2,

  // Node 3 — Builder / Coder
  build: 3, implement: 3, code: 3, write: 3, create: 3, add: 3, feature: 3,
  refactor: 3, fix: 3, debug_code: 3,

  // Node 4 — Contextualizer / Researcher
  research: 4, context: 4, docs: 4, search: 4, find: 4, explore: 4,
  documentation: 4, summarize: 4, analyze_docs: 4,

  // Node 5 — Analyzer / Analyst
  debug: 5, analyze: 5, profile: 5, inspect: 5, diagnose: 5, bottleneck: 5,
  performance: 5, trace: 5,

  // Node 6 — Validator / Tester
  test: 6, validate: 6, regression: 6, coverage: 6, spec: 6, unit: 6,
  integration_test: 6, edge: 6,

  // Node 7 — Architect
  design: 7, plan: 7, architect: 7, structure: 7, scalability: 7, pattern: 7,
  system: 7, architecture: 7,

  // Node 8 — Orchestrator
  orchestrate: 8, route: 8, coordinate: 8, dispatch: 8, prioritize: 8,
  swarm: 8, manage: 8, deploy: 8, ci: 8, cd: 8, pipeline: 8, infrastructure: 8,
  docker: 8, devops: 8,

  // Node 9 — Memory / Consolidator
  memory: 9, consolidate: 9, obsidian: 9, persist: 9, sync: 9, save: 9,
  summarize_session: 9, checkpoint: 9,
};

// UI/frontend → Node 3 (Builder) or Node 7 (Architect) depending on context
const UI_KEYWORDS = ['ui', 'frontend', 'component', 'react', 'css', 'style', 'layout'];

const AGENT_CAPABILITIES = {
  reviewer:             ['code-review', 'security-audit', 'quality-check', 'best-practices'],
  'backend-dev':        ['api', 'database', 'server', 'authentication', 'integration'],
  coder:                ['code-generation', 'refactoring', 'debugging', 'implementation'],
  researcher:           ['web-search', 'documentation', 'analysis', 'summarization'],
  analyst:              ['profiling', 'bottleneck-analysis', 'pattern-detection', 'debugging'],
  tester:               ['unit-testing', 'integration-testing', 'coverage', 'test-generation'],
  architecture:         ['system-design', 'architecture', 'patterns', 'scalability'],
  'sparc-orchestrator': ['task-routing', 'coordination', 'deployment', 'ci-cd', 'docker'],
  'memory-specialist':  ['memory-consolidation', 'obsidian-sync', 'session-state'],
};

// ─── ROUTING ─────────────────────────────────────────────────────────────────

function routeTask(task) {
  if (!task) return { agent: 'coder', confidence: 0.5, reason: 'No task provided', node: 3, node_name: 'Builder' };

  const words = task.toLowerCase().replace(/[^a-z0-9 _]/g, ' ').split(/\s+/).filter(Boolean);

  // 1. Exact keyword match (confidence 1.0)
  for (const word of words) {
    const node = ENNEAGRAM_ROUTING[word];
    if (node) {
      const n = ENNEAGRAM_NODES[node];
      return {
        agent: n.agent,
        confidence: 1.0,
        reason: `Enneagram node ${node} (${n.name}) — keyword: "${word}"`,
        node,
        node_name: n.name,
        cycle: n.cycle,
      };
    }
  }

  // 2. UI keywords → Builder (node 3) if implementation task, else Architect (node 7)
  const hasUI = words.some(w => UI_KEYWORDS.includes(w));
  if (hasUI) {
    const isDesign = words.some(w => ['design', 'plan', 'structure', 'layout'].includes(w));
    const node = isDesign ? 7 : 3;
    const n = ENNEAGRAM_NODES[node];
    return {
      agent: n.agent,
      confidence: 0.85,
      reason: `UI keywords detected → node ${node} (${n.name})`,
      node,
      node_name: n.name,
      cycle: n.cycle,
    };
  }

  // 3. Partial match on first 6 task keywords
  const scores = {};
  for (const word of words.slice(0, 6)) {
    for (const [kw, node] of Object.entries(ENNEAGRAM_ROUTING)) {
      if (kw.startsWith(word) || word.startsWith(kw.split('_')[0])) {
        scores[node] = (scores[node] || 0) + 1;
      }
    }
  }
  if (Object.keys(scores).length > 0) {
    const bestNode = Number(Object.entries(scores).sort((a, b) => b[1] - a[1])[0][0]);
    const n = ENNEAGRAM_NODES[bestNode];
    return {
      agent: n.agent,
      confidence: 0.7,
      reason: `Partial match → node ${bestNode} (${n.name})`,
      node: bestNode,
      node_name: n.name,
      cycle: n.cycle,
    };
  }

  // 4. Default → Builder (node 3, most common task)
  const def = ENNEAGRAM_NODES[3];
  return {
    agent: def.agent,
    confidence: 0.5,
    reason: 'Default → node 3 (Builder)',
    node: 3,
    node_name: def.name,
    cycle: def.cycle,
  };
}

// ─── CLI ─────────────────────────────────────────────────────────────────────

const task = process.argv.slice(2).join(' ');
if (task) {
  const result = routeTask(task);
  console.log(JSON.stringify(result, null, 2));
} else {
  console.log('Usage: router.js <task description>');
  console.log('Enneagram nodes:', Object.entries(ENNEAGRAM_NODES)
    .map(([n, r]) => `${n}=${r.agent}`).join(', '));
}

module.exports = { routeTask, ENNEAGRAM_NODES, ENNEAGRAM_ROUTING, AGENT_CAPABILITIES };
