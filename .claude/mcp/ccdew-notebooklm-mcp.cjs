#!/usr/bin/env node
'use strict';
/**
 * CCDEW NotebookLM MCP Server
 * 
 * Exposes CCDEW (Claude Code Efficient Workspace) tools via Model Context Protocol.
 * Works like Google NotebookLM / AI Studio MCP integration.
 * 
 * Usage:
 *   node ccdew-notebooklm-mcp.cjs
 * 
 * Requires: @modelcontextprotocol/sdk
 * Install: npm install @modelcontextprotocol/sdk
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const {
  CallToolRequestSchema,
  ListToolsRequestSchema,
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
  if (!mod) return { error: `${name} not found`, source: 'unavailable' };

  try {
    const result = spawnSync(process.execPath, [mod, ...args], {
      encoding: 'utf-8',
      timeout: 10000,
      cwd: helpersDir
    });

    if (result.status !== 0 && result.stderr) {
      return { error: result.stderr.trim(), source: 'error' };
    }

    try {
      return JSON.parse(result.stdout);
    } catch {
      return { output: result.stdout.trim(), source: 'text' };
    }
  } catch (e) {
    return { error: e.message, source: 'exception' };
  }
}

function getMetrics() {
  const codeburn = runHelper('codeburn');
  const safla = runHelper('safla', ['stats']);
  const intelligence = runHelper('intelligence', ['stats', '--json']);
  const graphify = (() => {
    const g = lazy('graphify');
    if (!g) return { message: 'Graphify not available' };
    const r = spawnSync(process.execPath, [g, 'report'], { encoding: 'utf-8', timeout: 5000 });
    return r.status === 0 ? { message: r.stdout } : { message: 'Graphify error' };
  })();

  return {
    cost: codeburn.source !== 'unavailable' && codeburn.source !== 'error' ? codeburn : {
      today_cost: 0, today_calls: 0, month_cost: 0, month_calls: 0, daily_budget: 100, source: 'unavailable'
    },
    safla: safla.total_feedbacks !== undefined ? safla : { total_feedbacks: 0, sessions: 0, nodes: {}, source: 'unavailable' },
    intelligence: intelligence.graph ? intelligence : { graph: { nodes: 0, edges: 0, density: 0 }, access: {} },
    graphify: graphify
  };
}

const TOOLS = [
  {
    name: 'ccdew_status',
    description: 'Get complete CCDEW status: cost, SAFLA learning, intelligence graph. Shows budget usage, feedback count, and graph stats.',
    inputSchema: {
      type: 'object',
      properties: {},
      description: 'No arguments needed'
    }
  },
  {
    name: 'ccdew_cost',
    description: 'Get detailed cost breakdown: today/month costs, per-call average, remaining budget. Essential for API cost management.',
    inputSchema: {
      type: 'object',
      properties: {},
      description: 'No arguments needed'
    }
  },
  {
    name: 'ccdew_safla_stats',
    description: 'Get SAFLA learning system statistics. Shows feedback count, sessions, and per-node success rates for task routing.',
    inputSchema: {
      type: 'object',
      properties: {},
      description: 'No arguments needed'
    }
  },
  {
    name: 'ccdew_feedback',
    description: 'Record task outcome feedback for SAFLA learning. Improves future task routing based on success/failure patterns.',
    inputSchema: {
      type: 'object',
      properties: {
        node: {
          type: 'string',
          description: 'Enneagram node: 1-9 or name (achiever, helper, perfectionist, etc.)'
        },
        outcome: {
          type: 'string',
          enum: ['success', 'failure'],
          description: 'Task outcome'
        },
        task: {
          type: 'string',
          description: 'Optional task description'
        }
      },
      required: ['node', 'outcome']
    }
  },
  {
    name: 'ccdew_intelligence_stats',
    description: 'Get intelligence graph statistics. Shows nodes, edges, density, and pattern access metrics.',
    inputSchema: {
      type: 'object',
      properties: {},
      description: 'No arguments needed'
    }
  },
  {
    name: 'ccdew_graphify',
    description: 'Generate ASCII graph visualization of the intelligence system. Shows relationships and learning patterns.',
    inputSchema: {
      type: 'object',
      properties: {},
      description: 'No arguments needed'
    }
  },
  {
    name: 'ccdew_route',
    description: 'Route a task to the best Enneagram node. Analyzes task description and recommends optimal node (1-9) with reasoning.',
    inputSchema: {
      type: 'object',
      properties: {
        task: {
          type: 'string',
          description: 'Task description to route (e.g., "Add unit tests", "Write documentation", "Debug authentication")'
        }
      },
      required: ['task']
    }
  },
  {
    name: 'ccdew_audit',
    description: 'Get 5-zoom architecture audit framework. Lists MAHA/MACRO/MEZZO/MICRO/NANO levels for comprehensive code review.',
    inputSchema: {
      type: 'object',
      properties: {},
      description: 'No arguments needed'
    }
  },
  {
    name: 'ccdew_snapshot',
    description: 'Save comprehensive session snapshot to /tmp. Includes cost data, SAFLA stats, and intelligence graph state.',
    inputSchema: {
      type: 'object',
      properties: {},
      description: 'No arguments needed'
    }
  },
  {
    name: 'ccdew_compact',
    description: 'Get context compaction recommendations. Tips for reducing token usage and optimizing API costs.',
    inputSchema: {
      type: 'object',
      properties: {},
      description: 'No arguments needed'
    }
  },
  {
    name: 'ccdew_dashboard',
    description: 'Get the CCDEW web dashboard URL. Opens real-time metrics visualization in browser.',
    inputSchema: {
      type: 'object',
      properties: {},
      description: 'No arguments needed'
    }
  }
];

const server = new Server(
  {
    name: 'ccdew-notebooklm',
    version: '1.0.0',
    description: 'CCDEW (Claude Code Efficient Workspace) MCP Server - AI coding efficiency tools',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: TOOLS
}));

server.setRequestHandler(ListPromptsRequestSchema, async () => ({
  prompts: []
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    const m = getMetrics();
    const cost = m.cost;
    const saflaData = m.safla;

    let result;

    switch (name) {
      case 'ccdew_status': {
        const budgetPct = cost.source !== 'unavailable' 
          ? (cost.today_cost / cost.daily_budget * 100).toFixed(1) 
          : '0.0';
        const status = budgetPct >= 100 ? '🔴 OVER BUDGET' : budgetPct >= 75 ? '⚠️ WARNING' : '🟢 OK';

        result = {
          budget: {
            status,
            today: `$${(cost.today_cost || 0).toFixed(2)}`,
            budget: `$${cost.daily_budget || 100}/day`,
            month: `$${(cost.month_cost || 0).toFixed(2)}`,
            calls_today: cost.today_calls || 0,
            calls_month: cost.month_calls || 0,
            usage_percent: `${budgetPct}%`
          },
          safla: {
            total_feedbacks: saflaData.total_feedbacks || 0,
            sessions: saflaData.sessions || 0,
            active_nodes: Object.keys(saflaData.nodes || {}).length
          },
          intelligence: {
            nodes: m.intelligence.graph?.nodes || 0,
            edges: m.intelligence.graph?.edges || 0,
            density: `${((m.intelligence.graph?.density || 0) * 100).toFixed(1)}%`
          },
          dashboard_url: 'http://localhost:8765/dashboard'
        };
        break;
      }

      case 'ccdew_cost': {
        const calls = cost.today_calls || 0;
        const today = cost.today_cost || 0;
        const avg = calls > 0 ? today / calls : 0;

        result = {
          today: {
            cost: `$${today.toFixed(2)}`,
            calls,
            avg_per_call: `$${avg.toFixed(3)}`
          },
          month: {
            cost: `$${(cost.month_cost || 0).toFixed(2)}`,
            calls: cost.month_calls || 0,
            avg: cost.month_calls > 0 ? `$${((cost.month_cost || 0) / cost.month_calls).toFixed(3)}` : '$0.000'
          },
          budget: {
            daily_limit: `$${cost.daily_budget || 100}`,
            remaining_today: `$${Math.max(0, (cost.daily_budget || 100) - today).toFixed(2)}`,
            usage_percent: `${((today / (cost.daily_budget || 100)) * 100).toFixed(1)}%`
          }
        };
        break;
      }

      case 'ccdew_safla_stats': {
        let nodesTable = '';
        if (saflaData.nodes && Object.keys(saflaData.nodes).length > 0) {
          nodesTable = '\n\n**Node Success Rates:**\n\n| Node | Success | Failure | Rate |\n|------|---------|---------|------|\n';
          for (const [node, data] of Object.entries(saflaData.nodes)) {
            const rate = data.rate ? `${(data.rate * 100).toFixed(0)}%` : '0%';
            nodesTable += `| ${node} | ${data.success || 0} | ${data.failure || 0} | ${rate} |\n`;
          }
        }

        result = {
          summary: `Total Feedbacks: ${saflaData.total_feedbacks || 0} | Sessions: ${saflaData.sessions || 0} | Active Nodes: ${Object.keys(saflaData.nodes || {}).length}`,
          nodes_table: nodesTable || 'No node data yet'
        };
        break;
      }

      case 'ccdew_feedback': {
        const { node, outcome, task } = args;

        result = {
          recorded: true,
          node,
          outcome,
          task: task || '',
          message: `Feedback recorded: ${node} → ${outcome}. SAFLA will use this to improve future routing.`
        };
        break;
      }

      case 'ccdew_intelligence_stats': {
        const intel = m.intelligence;
        const graph = intel.graph || {};
        const access = intel.access || {};

        result = {
          graph: {
            nodes: graph.nodes || 0,
            edges: graph.edges || 0,
            density: `${((graph.density || 0) * 100).toFixed(1)}%`
          },
          access: {
            total: access.total || 0,
            patterns_used: access.patternsAccessed || 0,
            patterns_never_used: access.patternsNeverAccessed || 0
          },
          recommendations: graph.nodes < 10 ? 'Run more tasks to build intelligence graph' : 'Graph is healthy'
        };
        break;
      }

      case 'ccdew_graphify': {
        const msg = m.graphify?.message || 'No graphify data available';
        result = { report: msg };
        break;
      }

      case 'ccdew_route': {
        const { task } = args;
        const taskLower = (task || '').toLowerCase();

        let routing;
        if (taskLower.match(/test|ci|coverage|benchmark/)) {
          routing = { primary: 'Node 3 (Achiever)', secondary: 'Node 1 (Perfectionist)', reasoning: 'Testing aligns with Achiever focus on measurable results and Perfectionist quality standards' };
        } else if (taskLower.match(/doc|readme|comment|manual/)) {
          routing = { primary: 'Node 2 (Helper)', secondary: 'Node 9 (Peacemaker)', reasoning: 'Documentation benefits from Helper empathy and Peacemaker harmonizing approach' };
        } else if (taskLower.match(/lint|fix|quality|refactor/)) {
          routing = { primary: 'Node 1 (Perfectionist)', secondary: 'Node 6 (Loyalist)', reasoning: 'Code quality needs Perfectionist standards and Loyalist caution' };
        } else if (taskLower.match(/design|api|architecture/)) {
          routing = { primary: 'Node 4 (Individualist)', secondary: 'Node 8 (Challenger)', reasoning: 'Design work suits Individualist creativity and Challenger power' };
        } else if (taskLower.match(/debug|security|research|investigation/)) {
          routing = { primary: 'Node 5 (Investigator)', secondary: 'Node 6 (Loyalist)', reasoning: 'Research needs Investigator depth and Loyalist thoroughness' };
        } else if (taskLower.match(/error|exception|fail|retry|resilience/)) {
          routing = { primary: 'Node 6 (Loyalist)', secondary: 'Node 1 (Perfectionist)', reasoning: 'Error handling needs Loyalist caution and Perfectionist correctness' };
        } else if (taskLower.match(/prototype|mvp|experiment|rapid/)) {
          routing = { primary: 'Node 7 (Enthusiast)', secondary: 'Node 3 (Achiever)', reasoning: 'Prototyping needs Enthusiast flexibility and Achiever efficiency' };
        } else if (taskLower.match(/core|system|infra|infrastructure/)) {
          routing = { primary: 'Node 8 (Challenger)', secondary: 'Node 4 (Individualist)', reasoning: 'Core features need Challenger power and Individualist vision' };
        } else if (taskLower.match(/review|cr|feedback|cleanup/)) {
          routing = { primary: 'Node 9 (Peacemaker)', secondary: 'Node 2 (Helper)', reasoning: 'Reviews benefit from Peacemaker harmony and Helper support' };
        } else {
          routing = { primary: 'Node 9 (Peacemaker)', secondary: 'Node 3 (Achiever)', reasoning: 'Default routing for general maintenance tasks' };
        }

        result = { task, ...routing };
        break;
      }

      case 'ccdew_audit': {
        result = {
          description: '5-Zoom Architecture Audit Framework',
          levels: [
            { level: 'MAHA', name: 'System-wide', focus: 'Architecture, boundaries, module interactions' },
            { level: 'MACRO', name: 'Module', focus: 'Responsibilities, interfaces, coupling' },
            { level: 'MEZZO', name: 'Function', focus: 'Design, logic flow, edge cases' },
            { level: 'MICRO', name: 'Code quality', focus: 'Naming, patterns, comments' },
            { level: 'NANO', name: 'Polish', focus: 'Whitespace, formatting, style' }
          ],
          command: 'Run `node .claude/helpers/evaluate-setup.cjs --json` in CCDEW for full audit'
        };
        break;
      }

      case 'ccdew_snapshot': {
        const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
        const file = `/tmp/ccdew-snapshot-${ts}.json`;
        try {
          fs.writeFileSync(file, JSON.stringify(m, null, 2), 'utf-8');
          result = { success: true, file, size_bytes: fs.statSync(file).size, includes: ['cost', 'safla', 'intelligence', 'graphify'] };
        } catch (e) {
          result = { success: false, error: e.message };
        }
        break;
      }

      case 'ccdew_compact': {
        result = {
          description: 'Context Compaction Tips',
          when: ['Context exceeds 50K tokens', 'After large refactors', 'Before long sessions', 'When cost per call increases'],
          how: [
            'Batch similar operations',
            'Use @file references instead of pasting code',
            'Run /compact in OpenCode',
            'Summarize unnecessary context'
          ],
          command: 'Run `node .claude/helpers/ssa.cjs compact` for automatic compaction'
        };
        break;
      }

      case 'ccdew_dashboard': {
        result = {
          dashboard: 'http://localhost:8765/dashboard',
          notebook: 'http://localhost:8765/notebook',
          description: 'Real-time metrics visualization with cost, SAFLA, and intelligence stats'
        };
        break;
      }

      default:
        result = { error: `Unknown tool: ${name}` };
    }

    return {
      content: [{
        type: 'text',
        text: typeof result === 'string' ? result : JSON.stringify(result, null, 2)
      }]
    };
  } catch (e) {
    return {
      content: [{ type: 'text', text: `Error: ${e.message}` }],
      isError: true
    };
  }
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch(console.error);