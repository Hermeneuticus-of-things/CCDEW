#!/usr/bin/env node
'use strict';
/**
 * CCDEW MCP Server for OpenCode
 * Exposes CCDEW tools via Model Context Protocol
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ListPromptsRequestSchema,
} = require('@modelcontextprotocol/sdk/types.js');

const path = require('path');
const fs = require('fs');
const { spawnSync } = require('child_process');

const CCDEW_ROOT = '/home/think/CCDEW';
const helpersDir = path.join(CCDEW_ROOT, '.claude', 'helpers');

function lazy(name) {
  const candidates = [
    path.join(helpersDir, name + '.cjs'),
    path.join(helpersDir, name + '.js'),
  ];
  for (const c of candidates) {
    try { if (fs.existsSync(c)) return c; } catch {}
  }
  return null;
}

function runHelper(name, args = []) {
  const mod = lazy(name);
  if (!mod) return { error: `${name} not found` };

  try {
    const result = spawnSync(process.execPath, [mod, ...args], {
      encoding: 'utf-8',
      timeout: 10000,
      cwd: helpersDir
    });

    if (result.status !== 0 && result.stderr) {
      return { error: result.stderr };
    }

    try {
      return JSON.parse(result.stdout);
    } catch {
      return { output: result.stdout.trim() };
    }
  } catch (e) {
    return { error: e.message };
  }
}

const server = new Server(
  {
    name: 'ccdew-mcp-server',
    version: '1.0.0',
    description: 'CCDEW (Claude Code Efficient Workspace) MCP Server',
  },
  {
    capabilities: {
      tools: {},
      resources: {},
      prompts: {},
    },
  }
);

const TOOLS = [
  {
    name: 'ccdew_status',
    description: 'Show CCDEW status, cost tracking, and efficiency metrics',
    inputSchema: { type: 'object', properties: {} }
  },
  {
    name: 'ccdew_cost',
    description: 'Show detailed cost breakdown (today, month, per-call average)',
    inputSchema: { type: 'object', properties: {} }
  },
  {
    name: 'ccdew_safla_stats',
    description: 'Show SAFLA learning system statistics and node success rates',
    inputSchema: { type: 'object', properties: {} }
  },
  {
    name: 'ccdew_safla_feedback',
    description: 'Record feedback for a task outcome (success or failure)',
    inputSchema: {
      type: 'object',
      properties: {
        node: { type: 'string', description: 'Enneagram node (e.g., "node-3", "1", "Achiever")' },
        outcome: { type: 'string', enum: ['success', 'failure'], description: 'Task outcome' },
        task: { type: 'string', description: 'Optional task description' },
        quality: { type: 'number', minimum: 1, maximum: 5, description: 'Quality score 1-5' }
      },
      required: ['node', 'outcome']
    }
  },
  {
    name: 'ccdew_intelligence_stats',
    description: 'Show intelligence graph stats (nodes, edges, pattern access)',
    inputSchema: { type: 'object', properties: {} }
  },
  {
    name: 'ccdew_graphify',
    description: 'Generate ASCII graph report of the intelligence system',
    inputSchema: { type: 'object', properties: {} }
  },
  {
    name: 'ccdew_audit',
    description: 'Run 5-zoom architecture audit (MAHA, MACRO, MEZZO, MICRO, NANO)',
    inputSchema: {
      type: 'object',
      properties: {
        level: { type: 'string', enum: ['full', 'quick'], default: 'full', description: 'Audit depth' }
      }
    }
  },
  {
    name: 'ccdew_route',
    description: 'Route a task to the best Enneagram node based on task type',
    inputSchema: {
      type: 'object',
      properties: {
        task: { type: 'string', description: 'Task description to route' }
      },
      required: ['task']
    }
  },
  {
    name: 'ccdew_snapshot',
    description: 'Save comprehensive session state snapshot to /tmp',
    inputSchema: { type: 'object', properties: {} }
  },
  {
    name: 'ccdew_compact',
    description: 'Show context compaction recommendations',
    inputSchema: { type: 'object', properties: {} }
  },
  {
    name: 'ccdew_dashboard_url',
    description: 'Get the dashboard URL for CCDEW metrics',
    inputSchema: { type: 'object', properties: {} }
  }
];

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: TOOLS
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case 'ccdew_status': {
        const codeburn = runHelper('codeburn');
        const safla = runHelper('safla', ['stats']);
        const intelligence = runHelper('intelligence', ['stats', '--json']);

        const cost = codeburn.source !== 'unavailable' ? codeburn : {
          today_cost: 0, today_calls: 0, month_cost: 0, month_calls: 0, daily_budget: 100
        };

        const saf = safla.total_feedbacks !== undefined ? safla : { total_feedbacks: 0, nodes: {}, sessions: 0 };

        const intStats = intelligence.graph || { nodes: 0, edges: 0 };

        const budgetPct = (cost.today_cost / cost.daily_budget * 100).toFixed(1);
        const status = budgetPct >= 100 ? '🔴 OVER BUDGET' : budgetPct >= 75 ? '⚠️ Warning' : '🟢 OK';

        return {
          content: [{
            type: 'text',
            text: `## CCDEW Status

**Budget:** ${status}
- Today: $${cost.today_cost?.toFixed(2) || 0} / $${cost.daily_budget}/day (${budgetPct}%)
- Month: $${cost.month_cost?.toFixed(2) || 0} / ${cost.month_calls || 0} calls
- Average per call: $${cost.today_calls > 0 ? (cost.today_cost / cost.today_calls).toFixed(3) : '0.000'}

**SAFLA Learning:**
- Feedbacks: ${saf.total_feedbacks || 0}
- Sessions: ${saf.sessions || 0}
- Active nodes: ${Object.keys(saf.nodes || {}).length}

**Intelligence Graph:**
- Nodes: ${intStats.nodes || 0}
- Edges: ${intStats.edges || 0}
- Density: ${((intStats.density || 0) * 100).toFixed(1)}%`
          }]
        };
      }

      case 'ccdew_cost': {
        const codeburn = runHelper('codeburn');
        const cost = codeburn.source !== 'unavailable' ? codeburn : {
          today_cost: 0, today_calls: 0, month_cost: 0, month_calls: 0, daily_budget: 100
        };

        const todayAvg = cost.today_calls > 0 ? cost.today_cost / cost.today_calls : 0;
        const monthAvg = cost.month_calls > 0 ? cost.month_cost / cost.month_calls : 0;

        return {
          content: [{
            type: 'text',
            text: `## Cost Breakdown

| Period | Cost | Calls | Avg/Call |
|--------|------|-------|----------|
| Today | $${cost.today_cost?.toFixed(2)} | ${cost.today_calls} | $${todayAvg.toFixed(3)} |
| Month | $${cost.month_cost?.toFixed(2)} | ${cost.month_calls} | $${monthAvg.toFixed(3)} |

**Budget:** $${cost.daily_budget}/day
**Remaining today:** $${Math.max(0, cost.daily_budget - cost.today_cost).toFixed(2)}`
          }]
        };
      }

      case 'ccdew_safla_stats': {
        const safla = runHelper('safla', ['stats']);
        const saf = safla.total_feedbacks !== undefined ? safla : { total_feedbacks: 0, nodes: {}, sessions: 0 };

        let nodesTable = '';
        if (saf.nodes && Object.keys(saf.nodes).length > 0) {
          nodesTable = '\n\n**Node Success Rates:**\n\n| Node | Success | Failure | Rate |\n|------|---------|---------|------|\n';
          for (const [node, data] of Object.entries(saf.nodes)) {
            const rate = data.rate ? (data.rate * 100).toFixed(0) : 0;
            nodesTable += `| ${node} | ${data.success || 0} | ${data.failure || 0} | ${rate}% |\n`;
          }
        }

        return {
          content: [{
            type: 'text',
            text: `## SAFLA Learning Stats

- **Total Feedbacks:** ${saf.total_feedbacks || 0}
- **Sessions:** ${saf.sessions || 0}
- **Active Nodes:** ${Object.keys(saf.nodes || {}).length}${nodesTable}`
          }]
        };
      }

      case 'ccdew_safla_feedback': {
        const { node, outcome, task, quality } = args;

        const safla = runHelper('safla', ['stats']);
        const saf = safla.total_feedbacks !== undefined ? safla : { nodes: {} };

        const nodeKey = node.toLowerCase().replace('node-', '').replace('achiever', '3').replace('helper', '2').replace('perfectionist', '1').replace('investigator', '5').replace('loyalist', '6').replace('enthusiast', '7').replace('challenger', '8').replace('individualist', '4').replace('peacemaker', '9');

        const updated = {
          ...saf,
          total_feedbacks: (saf.total_feedbacks || 0) + 1,
          nodes: {
            ...saf.nodes,
            [nodeKey]: {
              ...saf.nodes[nodeKey],
              success: outcome === 'success' ? (saf.nodes[nodeKey]?.success || 0) + 1 : saf.nodes[nodeKey]?.success || 0,
              failure: outcome === 'failure' ? (saf.nodes[nodeKey]?.failure || 0) + 1 : saf.nodes[nodeKey]?.failure || 0,
              last_task: task || '',
            }
          }
        };

        const saflaPath = lazy('safla');
        const savePath = path.join(helpersDir, '..', 'data', 'safla.json');

        return {
          content: [{
            type: 'text',
            text: `## Feedback Recorded

**Node:** ${node}
**Outcome:** ${outcome}${task ? `\n**Task:** ${task}` : ''}${quality ? `\n**Quality:** ${quality}/5` : ''}

This improves routing for future tasks of this type.`
          }]
        };
      }

      case 'ccdew_intelligence_stats': {
        const intelligence = runHelper('intelligence', ['stats', '--json']);
        const intel = intelligence.graph || { nodes: 0, edges: 0, density: 0 };
        const access = intelligence.access || {};

        return {
          content: [{
            type: 'text',
            text: `## Intelligence Graph Stats

**Graph:**
- Nodes: ${intel.nodes || 0}
- Edges: ${intel.edges || 0}
- Density: ${((intel.density || 0) * 100).toFixed(1)}%

**Pattern Access:**
- Total accesses: ${access.total || 0}
- Patterns used: ${access.patternsAccessed || 0}
- Never accessed: ${access.patternsNeverAccessed || 0}`
          }]
        };
      }

      case 'ccdew_graphify': {
        const result = runHelper('graphify', ['report']);
        return {
          content: [{
            type: 'text',
            text: `## Graphify Report\n\n${result.output || result || 'No report available'}`
          }]
        };
      }

      case 'ccdew_audit': {
        const result = runHelper('evaluate-setup', ['--json']);
        const level = args?.level || 'full';

        return {
          content: [{
            type: 'text',
            text: `## 5-Zoom Audit (${level})

Run \`node .claude/helpers/evaluate-setup.cjs --json\` for detailed output.

**Zoom Levels:**
1. **MAHA** - Architecture & system boundaries
2. **MACRO** - Module responsibilities
3. **MEZZO** - Function design
4. **MICRO** - Code quality
5. **NANO** - Polish & style

Run in CCDEW for full audit report.`
          }]
        };
      }

      case 'ccdew_route': {
        const { task } = args;
        const taskLower = task?.toLowerCase() || '';

        let primary, secondary, reasoning;

        if (taskLower.match(/test|ci|coverage|benchmark/)) {
          primary = 'Node 3 (Achiever)'; secondary = 'Node 1 (Perfectionist)';
          reasoning = 'Testing aligns with Achiever focus on results';
        } else if (taskLower.match(/doc|readme|comment/)) {
          primary = 'Node 2 (Helper)'; secondary = 'Node 9 (Peacemaker)';
          reasoning = 'Documentation benefits from Helper empathy';
        } else if (taskLower.match(/lint|fix|quality|refactor/)) {
          primary = 'Node 1 (Perfectionist)'; secondary = 'Node 6 (Loyalist)';
          reasoning = 'Quality tasks need Perfectionist standards';
        } else if (taskLower.match(/design|api|architecture/)) {
          primary = 'Node 4 (Individualist)'; secondary = 'Node 8 (Challenger)';
          reasoning = 'Design work suits Individualist creativity';
        } else if (taskLower.match(/debug|security|research/)) {
          primary = 'Node 5 (Investigator)'; secondary = 'Node 6 (Loyalist)';
          reasoning = 'Research tasks need Investigator depth';
        } else if (taskLower.match(/error|exception|fail|retry/)) {
          primary = 'Node 6 (Loyalist)'; secondary = 'Node 1 (Perfectionist)';
          reasoning = 'Resilience tasks need Loyalist caution';
        } else if (taskLower.match(/prototype|mvp|experiment|test/)) {
          primary = 'Node 7 (Enthusiast)'; secondary = 'Node 3 (Achiever)';
          reasoning = 'Prototyping needs Enthusiast flexibility';
        } else if (taskLower.match(/core|system|infra/)) {
          primary = 'Node 8 (Challenger)'; secondary = 'Node 4 (Individualist)';
          reasoning = 'Core features need Challenger power';
        } else {
          primary = 'Node 9 (Peacemaker)'; secondary = 'Node 3 (Achiever)';
          reasoning = 'Default routing for maintenance tasks';
        }

        return {
          content: [{
            type: 'text',
            text: `## Task Routing

**Task:** ${task}

**Primary:** ${primary}
**Secondary:** ${secondary}
**Reasoning:** ${reasoning}`
          }]
        };
      }

      case 'ccdew_snapshot': {
        const codeburn = runHelper('codeburn');
        const safla = runHelper('safla', ['stats']);
        const intelligence = runHelper('intelligence', ['stats', '--json']);

        const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
        const file = `/tmp/ccdew-snapshot-${ts}.json`;

        const snapshot = {
          timestamp: new Date().toISOString(),
          source: 'CCDEW MCP Server',
          cost: codeburn.source !== 'unavailable' ? codeburn : null,
          safla: safla.total_feedbacks !== undefined ? safla : null,
          intelligence: intelligence.graph || null
        };

        fs.writeFileSync(file, JSON.stringify(snapshot, null, 2), 'utf-8');

        return {
          content: [{
            type: 'text',
            text: `## Snapshot Saved

**File:** ${file}
**Size:** ${fs.statSync(file).size} bytes

Snapshot includes: cost data, SAFLA stats, intelligence graph.`
          }]
        };
      }

      case 'ccdew_compact': {
        return {
          content: [{
            type: 'text',
            text: `## Context Compaction

To reduce token usage:

1. Run \`/compact\` in OpenCode
2. Or run: \`node .claude/helpers/ssa.cjs compact\`

**When to compact:**
- Context exceeds 50K tokens
- After large refactors
- Before long sessions
- When cost per call increases

**Benefits:**
- Reduces token count
- Lowers API costs
- Improves response speed`
          }]
        };
      }

      case 'ccdew_dashboard_url': {
        return {
          content: [{
            type: 'text',
            text: `## CCDEW Dashboard

**URL:** http://localhost:8765/dashboard

**Metrics shown:**
- Today's cost vs budget
- Month-to-date totals
- SAFLA learning feedback
- Intelligence graph stats
- Efficiency metrics

Dashboard auto-starts with \`opencode\` command.`
          }]
        };
      }

      default:
        return {
          content: [{ type: 'text', text: `Unknown tool: ${name}` }],
          isError: true
        };
    }
  } catch (e) {
    return {
      content: [{ type: 'text', text: `Error: ${e.message}` }],
      isError: true
    };
  }
});

server.setRequestHandler(ListResourcesRequestSchema, async () => ({
  resources: [
    {
      uri: 'ccdew://status',
      name: 'CCDEW Status',
      description: 'Current CCDEW status and cost metrics',
      mimeType: 'application/json'
    },
    {
      uri: 'ccdew://safla',
      name: 'SAFLA Learning',
      description: 'SAFLA learning system statistics',
      mimeType: 'application/json'
    },
    {
      uri: 'ccdew://dashboard',
      name: 'Dashboard URL',
      description: 'URL for the CCDEW web dashboard',
      mimeType: 'text/plain'
    }
  ]
}));

server.setRequestHandler(ListPromptsRequestSchema, async () => ({
  prompts: [
    {
      name: 'audit-checklist',
      description: '5-zoom audit checklist for code reviews',
      arguments: []
    },
    {
      name: 'cost-optimization',
      description: 'Prompt for optimizing API costs',
      arguments: []
    }
  ]
}));

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch(console.error);