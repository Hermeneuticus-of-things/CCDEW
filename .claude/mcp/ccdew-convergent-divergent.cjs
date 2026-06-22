#!/usr/bin/env node
'use strict';
/**
 * CCDEW Convergent/Divergent Engine — MCP Server
 *
 * Tools:
 *   ccdew_divergent          — Generates N divergent agent prompts with distinct Enneagram wings
 *   ccdew_convergent         — Synthesizes N divergent outputs into unified result
 *   ccdew_divergent_convergent — Full pipeline: divergent + convergent in one call
 *
 * Reference: _SETTINGS/RULES/multi_agent_divergent_convergent.md
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} = require('@modelcontextprotocol/sdk/types.js');

// ── Wings Registry (18 wings from the protocol document) ──────────

const WINGS = [
  { id: 'maha',            category: 'zoom',     name: 'Zoom-wing Maha',       desc: 'Cosmic/systemic overview' },
  { id: 'macro',           category: 'zoom',     name: 'Zoom-wing Macro',      desc: 'Structural inter-component view' },
  { id: 'mezzo',           category: 'zoom',     name: 'Zoom-wing Mezzo',      desc: 'Process/flow view' },
  { id: 'micro',           category: 'zoom',     name: 'Zoom-wing Micro',      desc: 'Intra-component view' },
  { id: 'nano',            category: 'zoom',     name: 'Zoom-wing Nano',       desc: 'Atomic/microsecond view' },
  { id: 'stylistic',       category: 'lens',     name: 'Lens-wing stylistic',  desc: 'Aesthetic/literary filter' },
  { id: 'doctrinal',       category: 'lens',     name: 'Lens-wing doctrinal',  desc: 'Source fidelity filter' },
  { id: 'structural',      category: 'lens',     name: 'Lens-wing structural',  desc: 'Architectural filter' },
  { id: 'regression',      category: 'lens',     name: 'Lens-wing regression',   desc: 'What doesn\'t work filter' },
  { id: 'memory',          category: 'lens',     name: 'Lens-wing memory',      desc: 'Continuity with past filter' },
  { id: 'agent-perspective',  category: 'perspective', name: 'Perspective-wing agent',  desc: 'From actor viewpoint' },
  { id: 'observer-perspective', category: 'perspective', name: 'Perspective-wing observer', desc: 'From neutral external viewpoint' },
  { id: 'cosmic-perspective',   category: 'perspective', name: 'Perspective-wing cosmos',   desc: 'From systemic viewpoint' },
  { id: 'sakshi-perspective',   category: 'perspective', name: 'Perspective-wing Sākṣī',   desc: 'From non-involved witness viewpoint' },
  { id: 'descriptive',     category: 'modality',  name: 'Modality-wing descriptive', desc: 'As it is' },
  { id: 'normative',       category: 'modality',  name: 'Modality-wing normative',   desc: 'As it should be' },
  { id: 'generative',      category: 'modality',  name: 'Modality-wing generative',  desc: 'What if' },
  { id: 'critical',        category: 'modality',  name: 'Modality-wing critical',     desc: 'What doesn\'t work' },
];

// ── Domain-to-Wing mapping ────────────────────────────────────────

const DOMAIN_WINGS = {
  'editorial':     ['doctrinal', 'stylistic', 'structural', 'memory', 'regression'],
  'code-review':   ['regression', 'nano', 'critical', 'normative', 'structural'],
  'architecture':  ['macro', 'cosmic-perspective', 'normative', 'critical', 'memory'],
  'bug':           ['regression', 'nano', 'observer-perspective', 'critical', 'micro'],
  'content':       ['generative', 'stylistic', 'agent-perspective', 'descriptive', 'sakshi-perspective'],
  'research':      ['macro', 'memory', 'critical', 'doctrinal', 'mezzo'],
  'default':       ['maha', 'macro', 'mezzo', 'micro', 'nano'],
};

// ── Utils ─────────────────────────────────────────────────────────

function pickWings(task, count) {
  const lower = (task || '').toLowerCase();
  let domain = 'default';
  for (const [key, wings] of Object.entries(DOMAIN_WINGS)) {
    if (key !== 'default' && lower.includes(key)) {
      domain = key;
      break;
    }
  }
  const candidates = DOMAIN_WINGS[domain] || DOMAIN_WINGS.default;
  const available = candidates.slice(0, count);
  return available.map(id => WINGS.find(w => w.id === id) || WINGS.find(w => w.id === 'macro'));
}

function wingToPrompt(wing, task) {
  return `Approach this task ONLY through ${wing.name}: ${wing.desc}.

DO NOT use other angles. Your output is the pure "${wing.name}" perspective on the following task.

Task: ${task}

Rules:
- Be 100% faithful to the assigned perspective
- Do not try to cover other angles (other agents cover them)
- Clearly report which angle you are speaking from
- Output can be short (1-3 paragraphs) but complete from your perspective`;
}

function generateDivergent(task, count) {
  const wings = pickWings(task, count);
  const agents = wings.map((wing, i) => ({
    agent_id: `agent-${i + 1}`,
    wing: wing,
    prompt: wingToPrompt(wing, task),
  }));
  return agents;
}

function buildConvergentPrompt(task, outputs) {
  const outputsText = outputs.map((o, i) =>
    `=== Output Agent ${o.agent_id} (${o.wing?.name || 'unknown'}) ===\n${o.content}`
  ).join('\n\n');

  return `You are the Convergent Reformer/Synthesizer. You receive ${outputs.length} divergent perspectives on the same task.

Your task:
1. Identify CONVERGENCES — where all perspectives agree
2. Identify PRODUCTIVE DIVERGENCES — where perspectives say different and useful things
3. Identify UNRESOLVED TENSIONS — where perspectives contradict and CANNOT be reconciled
4. Produce a UNIFIED OUTPUT that preserves perspective diversity but gives an integrated verdict

Original task: ${task}

${outputsText}

--
Respond with:
## Convergences
...
## Productive divergences
...
## Unresolved tensions
...
## Integrated verdict
...`;
}

// ── Server ───────────────────────────────────────────────────────

const server = new Server(
  { name: 'ccdew-convergent-divergent', version: '1.0.0' },
  { capabilities: { tools: {} } }
);

const TOOLS = [
  {
    name: 'ccdew_divergent',
    description: 'Generates N divergent agents with distinct Enneagram wings for a task',
    inputSchema: {
      type: 'object',
      properties: {
        task: { type: 'string', description: 'Task description' },
        count: { type: 'number', description: 'Number of divergent agents (default 5, max 18)' },
        domain: { type: 'string', description: 'Domain (editorial, code-review, architecture, bug, content, research)' },
      },
      required: ['task'],
    },
  },
  {
    name: 'ccdew_convergent',
    description: 'Synthesizes N divergent outputs into an integrated verdict',
    inputSchema: {
      type: 'object',
      properties: {
        task: { type: 'string', description: 'Original task' },
        outputs: {
          type: 'array',
          items: {
            type: 'object',
            properties: {
              agent_id: { type: 'string' },
              wing: { type: 'object' },
              content: { type: 'string' },
            },
            required: ['agent_id', 'content'],
          },
          description: 'Outputs of divergent agents',
        },
      },
      required: ['task', 'outputs'],
    },
  },
  {
    name: 'ccdew_divergent_convergent',
    description: 'Full pipeline: pick wings + generate divergent prompts + convergent',
    inputSchema: {
      type: 'object',
      properties: {
        task: { type: 'string', description: 'Task description' },
        count: { type: 'number', description: 'Number of divergent agents (default 5)' },
        domain: { type: 'string', description: 'Optional domain' },
      },
      required: ['task'],
    },
  },
  {
    name: 'ccdew_wings_list',
    description: 'List all available Enneagram wings (18 wings)',
    inputSchema: { type: 'object', properties: {} },
  },
  {
    name: 'ccdew_domain_wings',
    description: 'Show domain → recommended wings mapping',
    inputSchema: { type: 'object', properties: {} },
  },
];

server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools: TOOLS }));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {

      case 'ccdew_divergent': {
        const task = args.task;
        const count = Math.min(args.count || 5, 18);
        const agents = generateDivergent(task, count);
        return {
          content: [{
            type: 'text',
            text: JSON.stringify({
              task,
              count: agents.length,
              agents,
              usage: 'Use these prompts as input for the real agents, then collect the outputs and send them to ccdew_convergent.',
            }, null, 2),
          }],
        };
      }

      case 'ccdew_convergent': {
        const task = args.task;
        const outputs = args.outputs || [];
        if (outputs.length < 2) {
          return {
            content: [{ type: 'text', text: 'You need at least 2 divergent outputs for synthesis.' }],
            isError: true,
          };
        }
        const convergentPrompt = buildConvergentPrompt(task, outputs);
        return {
          content: [{
            type: 'text',
            text: JSON.stringify({
              task,
              convergent_prompt: convergentPrompt,
              output_count: outputs.length,
              note: 'Send this prompt to a Reformer agent for final synthesis.',
            }, null, 2),
          }],
        };
      }

      case 'ccdew_divergent_convergent': {
        const task = args.task;
        const count = Math.min(args.count || 5, 18);
        const agents = generateDivergent(task, count);
        const placeholderOutputs = agents.map(a => ({
          agent_id: a.agent_id,
          wing: a.wing,
          content: `[PLACEHOLDER — replace with the actual output of agent ${a.agent_id}]`,
        }));
        const convergentPrompt = buildConvergentPrompt(task, placeholderOutputs);
        return {
          content: [{
            type: 'text',
            text: JSON.stringify({
              task,
              phase: 'divergent_convergent',
              divergent: agents,
              convergent: {
                agent: { name: 'Reformer / QA', node: 1 },
                prompt: convergentPrompt,
              },
              workflow: [
                '1. Run each divergent agent with its prompt (parallel)',
                '2. Collect all outputs',
                '3. Send outputs to ccdew_convergent with the original task',
                '4. Send convergent_prompt to a Reformer agent for final synthesis',
              ],
            }, null, 2),
          }],
        };
      }

      case 'ccdew_wings_list': {
        const byCategory = {};
        WINGS.forEach(w => {
          if (!byCategory[w.category]) byCategory[w.category] = [];
          byCategory[w.category].push(w);
        });
        return {
          content: [{
            type: 'text',
            text: JSON.stringify({
              total: WINGS.length,
              wings: byCategory,
            }, null, 2),
          }],
        };
      }

      case 'ccdew_domain_wings': {
        return {
          content: [{
            type: 'text',
            text: JSON.stringify({
              domains: Object.fromEntries(
                Object.entries(DOMAIN_WINGS).map(([d, ids]) => [
                  d,
                  ids.map(id => WINGS.find(w => w.id === id)).filter(Boolean),
                ])
              ),
            }, null, 2),
          }],
        };
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
  process.stderr.write('[CCDEW Convergent/Divergent v1] 🟢 Started\n');
}

main().catch(e => {
  process.stderr.write(`[CCDEW Convergent/Divergent v1] ❌ ${e.message}\n`);
  process.exit(1);
});
