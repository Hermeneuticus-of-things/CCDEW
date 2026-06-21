#!/usr/bin/env node
'use strict';
/**
 * CCDEW Orchestrator MCP v2 — Lightweight, Stable
 * Enneagram routing + basic orchestration
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} = require('@modelcontextprotocol/sdk/types.js');

const path = require('path');
const fs = require('fs');

const MEMORY_DIR = process.env.HERMES_MEMORY_DIR || '/home/think/.hermes/memories';

function readJSON(filePath) {
  try { return JSON.parse(fs.readFileSync(filePath, 'utf-8')); } catch { return null; }
}

// ── Enneagram routing table ──────────────────────────────────────
const NODES = {
  1: { name: 'Perfectionist', role: 'reviewer', keywords: ['review', 'quality', 'audit', 'check'] },
  2: { name: 'Helper', role: 'inbox-triage', keywords: ['help', 'support', 'issue', 'bug'] },
  3: { name: 'Achiever', role: 'builder', keywords: ['build', 'implement', 'code', 'create', 'fix'] },
  4: { name: 'Individualist', role: 'strategist', keywords: ['strategy', 'plan', 'design', 'architecture'] },
  5: { name: 'Investigator', role: 'researcher', keywords: ['research', 'analyze', 'investigate', 'learn'] },
  6: { name: 'Loyalist', role: 'ops-watch', keywords: ['monitor', 'security', 'test', 'verify'] },
  7: { name: 'Enthusiast', role: 'km-agent', keywords: ['knowledge', 'document', 'discover', 'explore'] },
  8: { name: 'Challenger', role: 'maintainer', keywords: ['maintain', 'deploy', 'release', 'decide'] },
  9: { name: 'Peacemaker', role: 'orchestrator', keywords: ['coordinate', 'merge', 'integrate', 'balance'] },
};

function routeTask(task) {
  const lower = task.toLowerCase();
  let best = { node: 9, score: 0 };
  for (const [id, node] of Object.entries(NODES)) {
    const score = node.keywords.filter(k => lower.includes(k)).length;
    if (score > best.score) best = { node: parseInt(id), score };
  }
  return { ...best, ...NODES[best.node] };
}

// ── Server ───────────────────────────────────────────────────────
const server = new Server(
  { name: 'ccdew-orchestrator', version: '2.0.0' },
  { capabilities: { tools: {} } }
);

const TOOLS = [
  { name: 'ccdew_route', description: 'Route task to best Enneagram node', inputSchema: { type: 'object', properties: { task: { type: 'string' } }, required: ['task'] } },
  { name: 'ccdew_hermes', description: 'Enneagram routing info', inputSchema: { type: 'object', properties: { task: { type: 'string' } }, required: ['task'] } },
  { name: 'ccdew_graphify', description: 'ASCII graph report', inputSchema: { type: 'object', properties: {} } },
  { name: 'ccdew_snapshot', description: 'Session snapshot', inputSchema: { type: 'object', properties: {} } },
];

server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools: TOOLS }));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case 'ccdew_route': {
        const route = routeTask(args.task);
        return { content: [{ type: 'text', text: `## Routing: "${args.task}"\n\n**Node:** ${route.node} — ${route.name}\n**Role:** ${route.role}\n**Score:** ${route.score}` }] };
      }

      case 'ccdew_hermes': {
        const route = routeTask(args.task);
        return { content: [{ type: 'text', text: `## Hermes → ${route.name} (${route.role})\n\nTask: "${args.task}"\nRouting to node ${route.node}` }] };
      }

      case 'ccdew_graphify': {
        const episodes = [];
        try {
          const content = fs.readFileSync(path.join(MEMORY_DIR, 'episodic.jsonl'), 'utf-8');
          content.split('\n').filter(Boolean).forEach(l => {
            try { episodes.push(JSON.parse(l)); } catch {}
          });
        } catch {}

        const types = {};
        episodes.forEach(ep => { types[ep.type] = (types[ep.type] || 0) + 1; });

        const graph = Object.entries(types).map(([t, c]) => `  ${t}: ${c}`).join('\n');
        return { content: [{ type: 'text', text: `## Intelligence Graph\n\n**Episoade:** ${episodes.length}\n\n**Tipuri:**\n${graph || '  (gol)'}` }] };
      }

      case 'ccdew_snapshot': {
        const ts = new Date().toISOString();
        const snapshot = { timestamp: ts, pid: process.pid, uptime: process.uptime() };
        const snapPath = path.join('/tmp', `ccdew-snapshot-${Date.now()}.json`);
        fs.writeFileSync(snapPath, JSON.stringify(snapshot, null, 2));
        return { content: [{ type: 'text', text: `## Snapshot salvat\n\n${snapPath}\n**Timp:** ${ts}` }] };
      }

      default:
        return { content: [{ type: 'text', text: `Unknown: ${name}` }], isError: true };
    }
  } catch (e) {
    return { content: [{ type: 'text', text: `Error: ${e.message}` }], isError: true };
  }
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  process.stderr.write('[CCDEW Orchestrator v2] 🟢 Started\n');
}

main().catch(e => {
  process.stderr.write(`[CCDEW Orchestrator v2] ❌ ${e.message}\n`);
  process.exit(1);
});
