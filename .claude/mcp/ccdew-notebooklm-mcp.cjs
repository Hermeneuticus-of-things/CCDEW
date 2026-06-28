#!/usr/bin/env node
'use strict';
/**
 * CCDEW Orchestrator MCP v2.1 — Divergent/Convergent stable
 * Bridge via HTTP (in-memory, no race condition)
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} = require('@modelcontextprotocol/sdk/types.js');

const path = require('path');
const fs = require('fs');
const http = require('http');

const MEMORY_DIR = process.env.HERMES_MEMORY_DIR || '/home/think/.hermes/memories';
const BRIDGE_HOST = '127.0.0.1';
const BRIDGE_PORT = 18777;

// ── Bridge via HTTP (elimină race condition din JSON file) ───────
let _bridgeCache = null;
let _bridgeCacheTs = 0;
const BRIDGE_CACHE_TTL = 2000; // 2s cache

function fetchBridge() {
  const now = Date.now();
  if (_bridgeCache && now - _bridgeCacheTs < BRIDGE_CACHE_TTL) return _bridgeCache;
  try {
    const url = `http://${BRIDGE_HOST}:${BRIDGE_PORT}/bridge.json`;
    const data = JSON.parse(
      require('child_process').execSync(
        `curl -sf --max-time 1 '${url}' 2>/dev/null || wget -qO- --timeout=1 '${url}' 2>/dev/null || echo 'null'`
      , { encoding: 'utf-8', timeout: 2000 })
    );
    if (data && data.pathway) {
      _bridgeCache = data;
      _bridgeCacheTs = now;
      return data;
    }
  } catch {}
  // Fallback: file bridge (dacă HTTP nu e disponibil)
  try {
    const file = path.join(MEMORY_DIR, 'pathway-bridge.json');
    const data = JSON.parse(fs.readFileSync(file, 'utf-8'));
    if (data && data.pathway) {
      _bridgeCache = data;
      _bridgeCacheTs = now;
      return data;
    }
  } catch {}
  return null;
}

function readJSON(filePath) {
  try { return JSON.parse(fs.readFileSync(filePath, 'utf-8')); } catch { return null; }
}

// ── Enneagram routing table ──────────────────────────────────────
const NODES = {
  1: { name: 'Perfectionist', role: 'reviewer',     keywords: ['review', 'quality', 'audit', 'check'] },
  2: { name: 'Helper',        role: 'inbox-triage', keywords: ['help', 'support', 'issue', 'bug'] },
  3: { name: 'Achiever',      role: 'builder',      keywords: ['build', 'implement', 'code', 'create', 'fix'] },
  4: { name: 'Individualist',  role: 'strategist',   keywords: ['strategy', 'plan', 'design', 'architecture'] },
  5: { name: 'Investigator',   role: 'researcher',   keywords: ['research', 'analyze', 'investigate', 'learn'] },
  6: { name: 'Loyalist',       role: 'ops-watch',    keywords: ['monitor', 'security', 'test', 'verify'] },
  7: { name: 'Enthusiast',     role: 'km-agent',     keywords: ['knowledge', 'document', 'discover', 'explore'] },
  8: { name: 'Challenger',     role: 'maintainer',   keywords: ['maintain', 'deploy', 'release', 'decide'] },
  9: { name: 'Peacemaker',     role: 'orchestrator', keywords: ['coordinate', 'merge', 'integrate', 'balance'] },
};

function getPathway() {
  return fetchBridge();
}

function routeTask(task) {
  const lower = task.toLowerCase();
  const pathway = getPathway();
  let best = { node: 9, score: 0 };
  for (const [id, node] of Object.entries(NODES)) {
    let score = node.keywords.filter(k => lower.includes(k)).length;
    if (pathway) {
      const pw = pathway.pathway || 'circle';
      const preferred = pathway.preferred_nodes || [9,8,7,6,5,4,3,2,1];
      if (preferred.includes(parseInt(id))) score += 1;
    }
    if (score > best.score) best = { node: parseInt(id), score };
  }
  return { ...best, ...NODES[best.node] };
}

// ── Server ───────────────────────────────────────────────────────
const server = new Server(
  { name: 'ccdew-orchestrator', version: '2.1.0' },
  { capabilities: { tools: {} } }
);

const TOOLS = [
  { name: 'ccdew_route', description: 'Route task to best Enneagram node', inputSchema: { type: 'object', properties: { task: { type: 'string' } }, required: ['task'] } },
  { name: 'ccdew_hermes', description: 'Enneagram routing info', inputSchema: { type: 'object', properties: { task: { type: 'string' } }, required: ['task'] } },
  { name: 'ccdew_pathway', description: 'Show current Enneagram pathway state', inputSchema: { type: 'object', properties: {} } },
  { name: 'ccdew_graphify', description: 'ASCII graph report', inputSchema: { type: 'object', properties: {} } },
  { name: 'ccdew_snapshot', description: 'Session snapshot', inputSchema: { type: 'object', properties: {} } },
];

server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools: TOOLS }));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  try {
    switch (name) {
      case 'ccdew_route':
        const route = routeTask(args.task);
        return { content: [{ type: 'text', text: `## Routing: "${args.task}"\n\n**Node:** ${route.node} — ${route.name}\n**Role:** ${route.role}\n**Score:** ${route.score}` }] };

      case 'ccdew_hermes':
        const r = routeTask(args.task);
        const pw = getPathway();
        const pwLine = pw ? `\nPathway: ${pw.pathway_label} | Node: ${pw.active_node} | Confidence: ${(pw.confidence*100).toFixed(0)}%` : '';
        return { content: [{ type: 'text', text: `## Hermes → ${r.name} (${r.role})\n\nTask: "${args.task}"\nRouting to node ${r.node}${pwLine}` }] };

      case 'ccdew_pathway':
        const p = getPathway();
        if (!p) return { content: [{ type: 'text', text: 'Pathway bridge not available. Inner Observer may not be running.' }] };
        const best = p.best_label ? `\nBest pathway: ${p.best_label} (${(p.best_score*100).toFixed(0)}%)` : '';
        return { content: [{ type: 'text', text: `## Current Enneagram Pathway\n\nActive: ${p.pathway_label}\nActive Node: ${p.active_node}\nConfidence: ${(p.confidence*100).toFixed(0)}%\nFlow: ${(p.flow*100).toFixed(0)}%\nConfusion: ${(p.confusion*100).toFixed(0)}%${best}\nRouting Hint: ${p.routing_hint}\nSAFLA Hint: ${p.safla_hint}` }] };

      case 'ccdew_graphify':
        const episodes = [];
        try {
          const content = fs.readFileSync(path.join(MEMORY_DIR, 'episodic.jsonl'), 'utf-8');
          content.split('\n').filter(Boolean).forEach(l => { try { episodes.push(JSON.parse(l)); } catch {} });
        } catch {}
        const types = {};
        episodes.forEach(ep => { types[ep.type] = (types[ep.type] || 0) + 1; });
        const graph = Object.entries(types).map(([t, c]) => `  ${t}: ${c}`).join('\n');
        return { content: [{ type: 'text', text: `## Intelligence Graph\n\n**Episoade:** ${episodes.length}\n\n**Tipuri:**\n${graph || '  (gol)'}` }] };

      case 'ccdew_snapshot':
        const ts = new Date().toISOString();
        const snapPath = path.join('/tmp', `ccdew-snapshot-${Date.now()}.json`);
        fs.writeFileSync(snapPath, JSON.stringify({ timestamp: ts, pid: process.pid, uptime: process.uptime() }, null, 2));
        return { content: [{ type: 'text', text: `## Snapshot salvat\n\n${snapPath}\n**Timp:** ${ts}` }] };

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
  process.stderr.write('[CCDEW Orchestrator v2.1] 🟢 Started (HTTP bridge)\n');
}

main().catch(e => {
  process.stderr.write(`[CCDEW Orchestrator v2.1] ❌ ${e.message}\n`);
  process.exit(1);
});
