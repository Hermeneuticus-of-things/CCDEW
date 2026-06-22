#!/usr/bin/env node
'use strict';
/**
 * Tests for Convergent/Divergent Engine
 * References: .claude/mcp/ccdew-convergent-divergent.cjs
 */

const assert = require('assert');

// ── Replicate the wing generation logic from ccdew-convergent-divergent.cjs ──

const WINGS = [
  { id: 'maha',     category: 'zoom',     name: 'Zoom-wing: Maha',             desc: 'Systemic/cosmic overview' },
  { id: 'macro',    category: 'zoom',     name: 'Zoom-wing: Macro',            desc: 'Structural inter-component view' },
  { id: 'mezzo',    category: 'zoom',     name: 'Zoom-wing: Mezzo',            desc: 'Process/flow view' },
  { id: 'micro',    category: 'zoom',     name: 'Zoom-wing: Micro',            desc: 'Intra-component view' },
  { id: 'nano',     category: 'zoom',     name: 'Zoom-wing: Nano',             desc: 'Atomic/microsecond view' },
  { id: 'stylistic',   category: 'lens',  name: 'Lens-wing: Stylistic',         desc: 'Aesthetic/literary filter' },
  { id: 'doctrinal',   category: 'lens',  name: 'Lens-wing: Doctrinal',         desc: 'Source fidelity filter' },
  { id: 'structural',  category: 'lens',  name: 'Lens-wing: Structural',        desc: 'Architectural filter' },
  { id: 'regression',  category: 'lens',  name: 'Lens-wing: Regression',        desc: 'What doesn\'t work filter' },
  { id: 'memory',      category: 'lens',  name: 'Lens-wing: Memory',            desc: 'Continuity with past filter' },
  { id: 'agent',    category: 'perspective', name: 'Perspective-wing: Agent',   desc: 'From actor viewpoint' },
  { id: 'observer', category: 'perspective', name: 'Perspective-wing: Observer', desc: 'From neutral external viewpoint' },
  { id: 'cosmic',   category: 'perspective', name: 'Perspective-wing: Cosmic',   desc: 'From systemic viewpoint' },
  { id: 'sakshi',   category: 'perspective', name: 'Perspective-wing: Sakshi',   desc: 'From non-involved witness viewpoint' },
  { id: 'descriptive', category: 'modality', name: 'Modality-wing: Descriptive', desc: 'As it is' },
  { id: 'normative',   category: 'modality', name: 'Modality-wing: Normative',   desc: 'As it should be' },
  { id: 'generative',  category: 'modality', name: 'Modality-wing: Generative',  desc: 'What if' },
  { id: 'critical',    category: 'modality', name: 'Modality-wing: Critical',    desc: 'What doesn\'t work' },
];

const DOMAIN_WINGS = {
  'editorial':     ['doctrinal', 'stylistic', 'structural', 'memory', 'regression'],
  'code-review':   ['regression', 'nano', 'critical', 'normative', 'structural'],
  'architecture':  ['macro', 'cosmic', 'normative', 'critical', 'memory'],
  'bug':           ['regression', 'nano', 'observer', 'critical', 'micro'],
  'content':       ['generative', 'stylistic', 'agent', 'descriptive', 'sakshi'],
  'research':      ['macro', 'memory', 'critical', 'doctrinal', 'mezzo'],
  'default':       ['maha', 'macro', 'mezzo', 'micro', 'nano'],
};

function pickWings(task, count) {
  const lower = (task || '').toLowerCase();
  let domain = 'default';
  for (const key of Object.keys(DOMAIN_WINGS)) {
    if (key !== 'default' && lower.includes(key)) {
      domain = key;
      break;
    }
  }
  const candidates = DOMAIN_WINGS[domain];
  return candidates.slice(0, count).map(id => WINGS.find(w => w.id === id)).filter(Boolean);
}

function generatePrompt(wing, task) {
  return `Approach this task ONLY through ${wing.name}: ${wing.desc}.

DO NOT use other angles. Your output is the pure perspective of "${wing.name}" on the following task.

Task: ${task}

Rules:
- Be 100% faithful to the assigned perspective
- Do not try to cover other angles (other agents are covering them)
- Clearly report which angle you speak from
- Output can be short (1-3 paragraphs) but complete from your perspective`;
}

function buildConvergentPrompt(task, outputs) {
  const outputsText = outputs.map((o, i) =>
    `=== Output ${o.agent_id} (${o.wing?.name || 'unknown'}) ===\n${o.content}`
  ).join('\n\n');
  return `You are the Convergent Reformer/Synthesizer. You receive ${outputs.length} divergent perspectives on the same task.

Your task:
1. Identify CONVERGENCES — where all perspectives agree
2. Identify PRODUCTIVE DIVERGENCES — where perspectives say different and useful things
3. Identify UNRESOLVED TENSIONS — where perspectives contradict and CANNOT be reconciled
4. Produce a UNIFIED OUTPUT that preserves diversity of perspectives but gives an integrated verdict

Original task: ${task}

${outputsText}

--
Respond with:
## Convergences
...
## Productive Divergences
...
## Unresolved Tensions
...
## Integrated Verdict
...`;
}

function countCategories(wings) {
  const cats = {};
  wings.forEach(w => { cats[w.category] = (cats[w.category] || 0) + 1; });
  return cats;
}

// ── Tests ────────────────────────────────────────────────────────

let passed = 0;
let failed = 0;

function test(name, fn) {
  try {
    fn();
    passed++;
    console.log(`  ✓ ${name}`);
  } catch (e) {
    failed++;
    console.log(`  ✗ ${name}: ${e.message}`);
  }
}

// 1. Wing count
test('WINGS has exactly 18 entries', () => {
  assert.strictEqual(WINGS.length, 18);
});

// 2. Wing categories
test('WINGS has 4 categories', () => {
  const cats = new Set(WINGS.map(w => w.category));
  assert.strictEqual(cats.size, 4);
  assert.ok(cats.has('zoom'));
  assert.ok(cats.has('lens'));
  assert.ok(cats.has('perspective'));
  assert.ok(cats.has('modality'));
});

test('ZOOM category has 5 wings', () => {
  assert.strictEqual(WINGS.filter(w => w.category === 'zoom').length, 5);
});

test('LENS category has 5 wings', () => {
  assert.strictEqual(WINGS.filter(w => w.category === 'lens').length, 5);
});

test('PERSPECTIVE category has 4 wings', () => {
  assert.strictEqual(WINGS.filter(w => w.category === 'perspective').length, 4);
});

test('MODALITY category has 4 wings', () => {
  assert.strictEqual(WINGS.filter(w => w.category === 'modality').length, 4);
});

// 3. Domain wings mapping
test('DOMAIN_WINGS has 6 domain entries + default', () => {
  assert.strictEqual(Object.keys(DOMAIN_WINGS).length, 7);
});

for (const [domain, wingIds] of Object.entries(DOMAIN_WINGS)) {
  test(`Domain "${domain}" has exactly 5 wings`, () => {
    assert.strictEqual(wingIds.length, 5);
  });

  test(`Domain "${domain}" wings are all valid`, () => {
    wingIds.forEach(id => {
      assert.ok(WINGS.find(w => w.id === id), `Invalid wing id: ${id}`);
    });
  });
}

// 4. pickWings returns correct number
test('pickWings returns requested count', () => {
  const wings = pickWings('review code for bugs', 3);
  assert.strictEqual(wings.length, 3);
});

test('pickWings respects max count (18)', () => {
  const wings = pickWings('test task', 99);
  assert.strictEqual(wings.length, 5); // domain has only 5
});

// 5. Domain detection
test('pickWings detects "editorial" domain', () => {
  const wings = pickWings('editorial merge paragraphs', 5);
  const ids = wings.map(w => w.id);
  assert.deepStrictEqual(ids, ['doctrinal', 'stylistic', 'structural', 'memory', 'regression']);
});

test('pickWings detects "bug" domain', () => {
  const wings = pickWings('investigate crash bug in renderer', 5);
  const ids = wings.map(w => w.id);
  assert.deepStrictEqual(ids, ['regression', 'nano', 'observer', 'critical', 'micro']);
});

test('pickWings detects "architecture" domain', () => {
  const wings = pickWings('design system architecture', 5);
  const ids = wings.map(w => w.id);
  assert.deepStrictEqual(ids, ['macro', 'cosmic', 'normative', 'critical', 'memory']);
});

test('pickWings uses default for unknown domain', () => {
  const wings = pickWings('random unknown task', 5);
  const ids = wings.map(w => w.id);
  assert.deepStrictEqual(ids, ['maha', 'macro', 'mezzo', 'micro', 'nano']);
});

// 6. Prompt generation
test('generatePrompt contains wing name', () => {
  const wing = WINGS[0];
  const prompt = generatePrompt(wing, 'test task');
  assert.ok(prompt.includes(wing.name));
  assert.ok(prompt.includes(wing.desc));
  assert.ok(prompt.includes('DO NOT use other angles'));
});

test('generatePrompt contains task', () => {
  const prompt = generatePrompt(WINGS[0], 'refactor database schema');
  assert.ok(prompt.includes('refactor database schema'));
});

// 7. Convergent prompt
test('buildConvergentPrompt contains all outputs', () => {
  const outputs = [
    { agent_id: 'agent-1', wing: WINGS[0], content: 'Output 1' },
    { agent_id: 'agent-2', wing: WINGS[1], content: 'Output 2' },
  ];
  const prompt = buildConvergentPrompt('test task', outputs);
  assert.ok(prompt.includes('Output 1'));
  assert.ok(prompt.includes('Output 2'));
  assert.ok(prompt.includes('CONVERGENCES'));
  assert.ok(prompt.includes('PRODUCTIVE DIVERGENCES'));
  assert.ok(prompt.includes('UNRESOLVED TENSIONS'));
  assert.ok(prompt.includes('UNIFIED OUTPUT'));
});

test('buildConvergentPrompt handles single output gracefully', () => {
  const outputs = [
    { agent_id: 'agent-1', wing: WINGS[0], content: 'Only output' },
  ];
  const prompt = buildConvergentPrompt('test task', outputs);
  assert.ok(prompt.includes('1 divergent perspectives'));
});

// 8. No duplicate wings in a single pick
test('pickWings returns unique wings', () => {
  const wings = pickWings('test', 18);
  const ids = wings.map(w => w.id);
  const unique = new Set(ids);
  assert.strictEqual(ids.length, unique.size);
});

// 9. Each wing has all required fields
test('Each wing has id, category, name, desc', () => {
  WINGS.forEach(w => {
    assert.ok(w.id, `Missing id in wing: ${JSON.stringify(w)}`);
    assert.ok(w.category, `Missing category in wing: ${w.id}`);
    assert.ok(w.name, `Missing name in wing: ${w.id}`);
    assert.ok(w.desc, `Missing desc in wing: ${w.id}`);
  });
});

// 10. No two wings share the same id
test('All wing IDs are unique', () => {
  const ids = WINGS.map(w => w.id);
  assert.strictEqual(ids.length, new Set(ids).size);
});

// 11. Categories are balanced
test('Zoom + Lens = 10 (majority)', () => {
  const cats = countCategories(WINGS);
  assert.strictEqual(cats.zoom + cats.lens, 10);
});

test('Perspective + Modality = 8', () => {
  const cats = countCategories(WINGS);
  assert.strictEqual(cats.perspective + cats.modality, 8);
});

// 12. All domain wing references are unique per domain
for (const [domain, wingIds] of Object.entries(DOMAIN_WINGS)) {
  if (domain === 'default') continue;
  test(`Domain "${domain}" has no duplicate wings`, () => {
    assert.strictEqual(wingIds.length, new Set(wingIds).size);
  });
}

// ── Summary ───────────────────────────────────────────────────────

console.log(`\nConvergent/Divergent Engine Tests: ${passed} passed, ${failed} failed\n`);
process.exit(failed > 0 ? 1 : 0);
