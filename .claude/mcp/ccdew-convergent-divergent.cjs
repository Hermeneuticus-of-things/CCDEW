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
  { id: 'maha',            category: 'zoom',     name: 'Zoom-aripa Maha',       desc: 'Vedere de ansamblu cosmic/sistemic' },
  { id: 'macro',           category: 'zoom',     name: 'Zoom-aripa Macro',      desc: 'Vedere structurală inter-componente' },
  { id: 'mezzo',           category: 'zoom',     name: 'Zoom-aripa Mezzo',      desc: 'Vedere de proces/flux' },
  { id: 'micro',           category: 'zoom',     name: 'Zoom-aripa Micro',      desc: 'Vedere intra-componentă' },
  { id: 'nano',            category: 'zoom',     name: 'Zoom-aripa Nano',       desc: 'Vedere atomică/microsecundă' },
  { id: 'stylistic',       category: 'lens',     name: 'Lentilă-aripa stilistică',  desc: 'Filtru estetic/literar' },
  { id: 'doctrinal',       category: 'lens',     name: 'Lentilă-aripa doctrinară',  desc: 'Filtru fidelitate sursă' },
  { id: 'structural',      category: 'lens',     name: 'Lentilă-aripa structurală',  desc: 'Filtru arhitectural' },
  { id: 'regression',      category: 'lens',     name: 'Lentilă-aripa regression',   desc: 'Filtru ce nu funcționează' },
  { id: 'memory',          category: 'lens',     name: 'Lentilă-aripa memorie',      desc: 'Filtru continuitate cu trecutul' },
  { id: 'agent-perspective',  category: 'perspective', name: 'Perspectivă-aripa agent',  desc: 'Din vedere actor' },
  { id: 'observer-perspective', category: 'perspective', name: 'Perspectivă-aripa observator', desc: 'Din vedere extern neutru' },
  { id: 'cosmic-perspective',   category: 'perspective', name: 'Perspectivă-aripa cosmos',   desc: 'Din vedere sistemic' },
  { id: 'sakshi-perspective',   category: 'perspective', name: 'Perspectivă-aripa Sākṣī',   desc: 'Din vedere martor non-implicat' },
  { id: 'descriptive',     category: 'modality',  name: 'Modalitate-aripa descriptivă', desc: 'Cum este' },
  { id: 'normative',       category: 'modality',  name: 'Modalitate-aripa normativă',   desc: 'Cum ar trebui' },
  { id: 'generative',      category: 'modality',  name: 'Modalitate-aripa generativă',  desc: 'Ce-ar fi dacă' },
  { id: 'critical',        category: 'modality',  name: 'Modalitate-aripa critică',     desc: 'Ce nu merge' },
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
  return `Abordează acest task DOAR prin ${wing.name}: ${wing.desc}.

NU folosi alte unghiuri. Output-ul tău e perspectiva "${wing.name}" pură pe următorul task.

Task: ${task}

Reguli:
- Fii 100% fidel perspectivei asignate
- Nu încerca să acoperi alte unghiuri (alte agenți le acoperă)
- Raportează clar din ce unghi vorbești
- Output-ul poate fi scurt (1-3 paragrafe) dar complet din perspectiva ta`;
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

  return `Ești Reformer/Sintetizator Convergent. Primești ${outputs.length} perspective divergente pe același task.

Sarcina ta:
1. Identifică CONVERGENȚE — unde toate perspectivele sunt de acord
2. Identifică DIVERGENȚE PRODUCTIVE — unde perspectivele spun lucruri diferite și utile
3. Identifică TENSIUNI NEREZOLVATE — unde perspectivele se contrazic și NU se pot reconcilia
4. Produce un OUTPUT UNIC care păstrează diversitatea perspectivelor dar dă un verdict integrat

Task original: ${task}

${outputsText}

--
Răspunde cu:
## Convergențe
...
## Divergențe productive
...
## Tensiuni nerezolvate
...
## Verdict integrat
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
    description: 'Generează N agenți divergenți cu aripe Enneagram distincte pe un task',
    inputSchema: {
      type: 'object',
      properties: {
        task: { type: 'string', description: 'Descrierea task-ului' },
        count: { type: 'number', description: 'Număr de agenți divergenți (default 5, max 18)' },
        domain: { type: 'string', description: 'Domeniu (editorial, code-review, architecture, bug, content, research)' },
      },
      required: ['task'],
    },
  },
  {
    name: 'ccdew_convergent',
    description: 'Sintetizează N outputuri divergente într-un verdict integrat',
    inputSchema: {
      type: 'object',
      properties: {
        task: { type: 'string', description: 'Task-ul original' },
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
          description: 'Outputurile agenților divergenți',
        },
      },
      required: ['task', 'outputs'],
    },
  },
  {
    name: 'ccdew_divergent_convergent',
    description: 'Full pipeline: alege aripe + generează prompturi divergente + convergente',
    inputSchema: {
      type: 'object',
      properties: {
        task: { type: 'string', description: 'Descrierea task-ului' },
        count: { type: 'number', description: 'Număr de agenți divergenți (default 5)' },
        domain: { type: 'string', description: 'Domeniu opțional' },
      },
      required: ['task'],
    },
  },
  {
    name: 'ccdew_wings_list',
    description: 'Listează toate aripile Enneagram disponibile (18 wings)',
    inputSchema: { type: 'object', properties: {} },
  },
  {
    name: 'ccdew_domain_wings',
    description: 'Arată maparea domeniu → aripe recomandate',
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
              usage: 'Folosește aceste prompturi ca input pentru agenții reali, apoi colectează outputurile și trimite-le la ccdew_convergent.',
            }, null, 2),
          }],
        };
      }

      case 'ccdew_convergent': {
        const task = args.task;
        const outputs = args.outputs || [];
        if (outputs.length < 2) {
          return {
            content: [{ type: 'text', text: 'Ai nevoie de cel puțin 2 outputuri divergente pentru sinteză.' }],
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
              note: 'Trimite acest prompt unui agent Reformer pentru sinteză finală.',
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
          content: `[PLACEHOLDER — înlocuiește cu outputul real al agentului ${a.agent_id}]`,
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
                '1. Rulează fiecare agent divergent cu promptul său (paralel)',
                '2. Colectează toate outputurile',
                '3. Trimite outputurile la ccdew_convergent cu task-ul original',
                '4. Trimite convergent_prompt unui agent Reformer pentru sinteză finală',
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
