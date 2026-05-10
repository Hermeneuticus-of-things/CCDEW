#!/usr/bin/env node
'use strict';
/**
 * /review — code review orchestrator.
 *
 * Generates a structured prompt for Claude Code to spawn a 3-agent swarm
 * (reviewer + analyst + tester) over the current diff. The Agent tool is
 * only callable inside Claude Code, so this helper *prepares* the brief
 * and prints it; the actual spawn happens via the wrapping slash command.
 *
 * It also runs the cheap, deterministic pre-checks here (size, files, hot
 * spots) so the agents start with context already condensed.
 */

const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

const WORK = process.cwd();
const args = process.argv.slice(2);
const target = args[0] || '';

function git(args) {
  const r = spawnSync('git', args, {
    cwd: WORK, encoding: 'utf-8', timeout: 30_000,
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  return { code: r.status, out: r.stdout || '', err: r.stderr || '' };
}

let diffArgs = [];
if (target.startsWith('--branch')) {
  const m = target.match(/--branch[= ](.+)/);
  diffArgs = m ? [m[1]] : ['main..HEAD'];
} else if (target && !target.startsWith('--')) {
  diffArgs = ['--', target];
}

const numstat = git(['diff', ...diffArgs, '--numstat']);
const files = numstat.out.trim().split('\n').filter(Boolean).map(l => {
  const [a, d, f] = l.split('\t');
  return { file: f, add: parseInt(a, 10) || 0, del: parseInt(d, 10) || 0 };
});

if (files.length === 0) {
  console.log('[REVIEW] no changes to review');
  process.exit(0);
}

const totalAdd = files.reduce((s, f) => s + f.add, 0);
const totalDel = files.reduce((s, f) => s + f.del, 0);
const hotspots = files.filter(f => (f.add + f.del) > 50).slice(0, 5);

const diff = git(['diff', ...diffArgs]).out;
const diffSize = diff.length;

console.log('# Review brief\n');
console.log(`**Files changed:** ${files.length}`);
console.log(`**Net lines:** +${totalAdd} −${totalDel}`);
console.log(`**Diff size:** ${(diffSize / 1024).toFixed(1)} KB`);
if (hotspots.length > 0) {
  console.log(`**Hotspots (>50 lines):**`);
  for (const h of hotspots) console.log(`- \`${h.file}\` (+${h.add} −${h.del})`);
}

const swarmInstructions = `

# 3-agent review swarm — instructions for Claude Code

To execute the review, spawn three agents IN PARALLEL (single message, three Agent tool calls):

## Agent 1 — code-reviewer (Node 1, Reformer lens)
**Subagent type:** \`reviewer\` (or \`code-analyzer\`)
**Lens:** code quality, naming, simplicity, anti-patterns, function length
**Prompt template:**
> Review the diff below for code quality issues — naming, complexity, anti-patterns, dead code, SRP violations. Report HIGH/MEDIUM/NIT findings with file:line references. Do NOT cover bugs or test gaps (other agents handle that).

## Agent 2 — analyst (Node 5, Analyzer lens)
**Subagent type:** \`analyst\` (or \`code-analyzer\`)
**Lens:** logic bugs, edge cases, race conditions, perf
**Prompt template:**
> Analyze the diff for logic bugs, edge cases, null pointer / undefined handling, race conditions, performance regressions. Report HIGH/MEDIUM findings with concrete repro scenarios. Do NOT cover style or test coverage.

## Agent 3 — tester (Node 6, Validator lens)
**Subagent type:** \`tester\`
**Lens:** test coverage gaps, missing assertions, regression risk
**Prompt template:**
> Review the diff for test coverage gaps. For each public function or branch added, identify whether tests cover it. Report MISSING tests and weak assertions. Do NOT cover code style or logic bugs.

## After agents return
Merge the three reports, deduplicate findings (same file:line from multiple agents = consolidate), and present as:

\`\`\`
HIGH (must fix)
- ...

MEDIUM (should fix)
- ...

NIT (optional)
- ...
\`\`\`
`;

console.log(swarmInstructions);

if (process.argv.includes('--json')) {
  console.log(JSON.stringify({
    files: files.length, totalAdd, totalDel, hotspots,
    diff_size_kb: +(diffSize / 1024).toFixed(1),
    diff_b64_first_4k: Buffer.from(diff.slice(0, 4096)).toString('base64'),
  }, null, 2));
}
