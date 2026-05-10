#!/usr/bin/env node
'use strict';
/**
 * /diff-explain backend — plain-English summary of git diff.
 * Categorizes changes (feat/fix/refactor/test/docs/chore) per file.
 *
 * Usage: node diff-explain.cjs [<git-range>|<file>]
 *   default: uncommitted (working tree vs HEAD)
 *   --staged: index vs HEAD
 *   <range>: e.g. main..HEAD or HEAD~3..HEAD
 *   <file>: specific file
 */

const path = require('path');
const { spawnSync } = require('child_process');

const WORK = process.cwd();
const arg = process.argv[2] || '';

function git(args) {
  const r = spawnSync('git', args, {
    cwd: WORK, encoding: 'utf-8', timeout: 30_000,
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  return { code: r.status, out: r.stdout || '', err: r.stderr || '' };
}

let range = [];
if (arg === '--staged') range = ['--cached'];
else if (arg.includes('..')) range = [arg];
else if (arg && !arg.startsWith('--')) range = ['--', arg];

const numstat = git(['diff', ...range, '--numstat']);
if (numstat.code !== 0) {
  console.error('[DIFF-EXPLAIN] git diff failed:', numstat.err.slice(0, 200));
  process.exit(1);
}

const files = numstat.out.trim().split('\n').filter(Boolean).map(line => {
  const [add, del, file] = line.split('\t');
  return {
    file,
    add: parseInt(add, 10) || 0,
    del: parseInt(del, 10) || 0,
  };
});

if (files.length === 0) {
  console.log('[DIFF-EXPLAIN] no changes detected');
  process.exit(0);
}

function classify(filePath, addLines, delLines) {
  const f = filePath.toLowerCase();
  if (/test|spec|__tests__|\.test\./i.test(f)) return 'test';
  if (/\.md$|docs?\//i.test(f)) return 'docs';
  if (/\.(json|ya?ml|toml|cfg|ini)$/i.test(f) && !/package\.json/.test(f)) return 'config';
  if (/^\.(claude|github|circleci|gitignore|editorconfig|eslintrc|prettierrc)/i.test(f)) return 'chore';
  if (/package\.json|requirements\.txt|cargo\.toml|go\.mod|pnpm-lock|yarn\.lock|package-lock/i.test(f)) return 'deps';
  if (delLines > addLines * 2) return 'refactor';
  if (addLines > 0 && delLines === 0) return 'feat';
  if (delLines > 0 && addLines > 0) return 'fix?';
  return 'change';
}

const grouped = {};
let totalAdd = 0, totalDel = 0;
for (const f of files) {
  const tag = classify(f.file, f.add, f.del);
  (grouped[tag] = grouped[tag] || []).push(f);
  totalAdd += f.add;
  totalDel += f.del;
}

const TAG_LABELS = {
  feat: '🟢 feat (additions)',
  fix:  '🔧 fix (modifications)',
  'fix?': '🔧 fix? (mixed +/-)',
  refactor: '🔁 refactor (deletions dominant)',
  test: '🧪 test',
  docs: '📝 docs',
  config: '⚙️  config',
  chore: '🛠️  chore (tooling)',
  deps: '📦 deps',
  change: '✏️  change',
};

console.log('\n# Diff summary\n');
console.log(`**Scope:** ${arg || '(uncommitted)'}`);
console.log(`**Files:** ${files.length} | **Lines:** +${totalAdd} -${totalDel}\n`);

for (const tag of Object.keys(grouped)) {
  console.log(`## ${TAG_LABELS[tag] || tag}`);
  for (const f of grouped[tag].sort((a, b) => (b.add + b.del) - (a.add + a.del))) {
    console.log(`- \`${f.file}\` (+${f.add} −${f.del})`);
  }
  console.log('');
}

// Risk assessment heuristics
const risks = [];
if (files.some(f => /lock\.json|pnpm-lock|yarn\.lock|package-lock/.test(f.file))) {
  risks.push('⚠ Dependency lock file changed — verify CI runs install fresh');
}
if (files.some(f => /\.env|secrets?\./i.test(f.file))) {
  risks.push('🚨 Sensitive filename touched — run /verify before commit');
}
if (totalDel > totalAdd * 3) {
  risks.push(`⚠ Net deletion (${totalDel} − > ${totalAdd} +) — possible API removal, check downstream callers`);
}
if (files.some(f => /migration|schema/i.test(f.file))) {
  risks.push('⚠ Schema/migration file changed — verify backwards compat');
}
if (files.length > 20) {
  risks.push(`⚠ Large diff (${files.length} files) — consider splitting`);
}

if (risks.length > 0) {
  console.log('## Risk\n');
  for (const r of risks) console.log(`- ${r}`);
  console.log('');
} else {
  console.log('## Risk\n- LOW: no obvious red flags\n');
}

// Suggested commit type
const dominantTag = Object.entries(grouped).sort((a, b) => b[1].length - a[1].length)[0];
const conventionalType = dominantTag && {
  feat: 'feat', fix: 'fix', 'fix?': 'fix', refactor: 'refactor',
  test: 'test', docs: 'docs', config: 'chore', chore: 'chore', deps: 'chore(deps)',
}[dominantTag[0]] || 'chore';
console.log(`## Suggested commit type\n\`${conventionalType}: ...\``);
