'use strict';
/**
 * Red Hat Evaluator (v6.1 Micro)
 * Injects a critical-thinking challenge into UserPromptSubmit output.
 * Purpose: force Claude to surface risks / assumptions before building.
 *
 * Prints a [RED-HAT] block to stdout — picked up as system-reminder by Claude Code.
 */

const fs = require('fs');
const path = require('path');

const FLAGS_PATH = path.join(__dirname, 'feature-flags.json');

function loadFlags() {
  try { return JSON.parse(fs.readFileSync(FLAGS_PATH, 'utf-8')); } catch { return {}; }
}

// Keywords that trigger architecture-level scrutiny
const ARCH_KEYWORDS = [
  'arhitectur', 'architect', 'design', 'refactor', 'migrat', 'rewrit', 'integrat',
  'implementeaz', 'implement', 'creaz', 'create', 'build', 'sistem', 'system',
  'deploy', 'produc', 'release', 'optimi',
];

const RISK_TEMPLATES = [
  'Ce presupuneri tacite conțin această soluție?',
  'Care sunt cele 2 moduri prin care aceasta poate eșua în producție?',
  'Există o abordare mai simplă cu ≤50% din complexitate?',
  'Ce efect de bord neașteptat poate apărea în 30 de zile?',
  'Dacă această decizie este greșită, cât costă să o revoci?',
];

function pickRisks(prompt, count = 2) {
  // Deterministic selection based on prompt length to avoid randomness in hooks
  const seed = prompt.length % RISK_TEMPLATES.length;
  const result = [];
  for (let i = 0; i < count; i++) {
    result.push(RISK_TEMPLATES[(seed + i) % RISK_TEMPLATES.length]);
  }
  return result;
}

function isArchTask(prompt) {
  const lower = prompt.toLowerCase();
  return ARCH_KEYWORDS.some(kw => lower.includes(kw));
}

/**
 * Evaluate a prompt and print [RED-HAT] block if warranted.
 * @param {string} prompt
 */
function evaluate(prompt) {
  const flags = loadFlags();
  if (!flags.components || !flags.components.red_hat) return;

  const cfg      = flags.red_hat || {};
  const minWords = cfg.trigger_min_words || 10;
  const words    = prompt.trim().split(/\s+/);

  if (words.length < minWords) return;

  const isArch   = isArchTask(prompt);
  const alwaysOn = cfg.always_on_for_architecture !== false;

  if (!isArch && Math.random() > 0.4) return; // 40% chance on non-arch tasks

  const questions = pickRisks(prompt, isArch ? 3 : 2);

  const lines = [
    '[RED-HAT] Evaluare critică înainte de execuție:',
    ...questions.map((q, i) => `  ${i + 1}. ${q}`),
    isArch ? '  → Răspunde la aceste întrebări ÎNAINTE să scrii cod.' : '',
  ].filter(Boolean);

  process.stdout.write(lines.join('\n') + '\n');
}

module.exports = { evaluate };
