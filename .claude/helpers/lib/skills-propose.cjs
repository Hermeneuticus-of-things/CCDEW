'use strict';
/**
 * Skills proposer — when a gap is detected (manually via /skills-propose or
 * auto from /infer), search GitHub for mature open-source skills and propose
 * the best candidate. NEVER clones or imports code automatically — only
 * generates a SKILL.md template inspired by the candidate's metadata.
 *
 * Why: the user said "să nu preluăm din greșeală în skills meritorios" —
 * we want skills that already passed real-world use (stars, forks, recent
 * push), not invented from scratch.
 *
 * Network: uses GitHub Search API (60 req/h unauth, 5000 with GITHUB_TOKEN).
 * Cache: 1h TTL at .claude-flow/data/skills-search-cache.json.
 */

const fs = require('fs');
const path = require('path');
const https = require('https');
const { writeAtomicJson } = require('./atomic-write.cjs');
const { redactString } = require('./redact.cjs');

const DATA_DIR = path.join(process.cwd(), '.claude-flow', 'data');
const CACHE_PATH = path.join(DATA_DIR, 'skills-search-cache.json');
const CACHE_TTL_MS = 60 * 60 * 1000;

const QUALITY_FILTER = {
  min_stars: 10,
  max_age_days_since_push: 365,
  allowed_licenses: new Set(['mit', 'apache-2.0', 'isc', 'bsd-3-clause', 'bsd-2-clause', 'mpl-2.0']),
};

function ensureDir() {
  if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });
}

function readCache(key) {
  try {
    if (!fs.existsSync(CACHE_PATH)) return null;
    const c = JSON.parse(fs.readFileSync(CACHE_PATH, 'utf-8'));
    const entry = c[key];
    if (!entry) return null;
    if ((Date.now() - entry.ts) > CACHE_TTL_MS) return null;
    return entry.data;
  } catch { return null; }
}

function writeCache(key, data) {
  ensureDir();
  let c = {};
  try { if (fs.existsSync(CACHE_PATH)) c = JSON.parse(fs.readFileSync(CACHE_PATH, 'utf-8')); } catch {}
  c[key] = { ts: Date.now(), data };
  try { writeAtomicJson(CACHE_PATH, c); } catch {}
}

function ghSearch(query, opts = {}) {
  return new Promise((resolve, reject) => {
    const headers = {
      'User-Agent': 'CCDEW-skills-propose/1.0',
      'Accept': 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
    };
    if (process.env.GITHUB_TOKEN) headers['Authorization'] = `Bearer ${process.env.GITHUB_TOKEN}`;
    const q = encodeURIComponent(query);
    const url = `https://api.github.com/search/repositories?q=${q}&sort=stars&order=desc&per_page=${opts.perPage || 10}`;
    const req = https.get(url, { headers, timeout: 8000 }, (res) => {
      let body = '';
      res.on('data', chunk => { body += chunk; if (body.length > 2_000_000) { req.destroy(); reject(new Error('response too large')); }});
      res.on('end', () => {
        if (res.statusCode === 200) {
          try { resolve(JSON.parse(body)); } catch (e) { reject(e); }
        } else if (res.statusCode === 403) {
          reject(new Error(`GitHub rate limit (${res.statusCode}) — set GITHUB_TOKEN to raise`));
        } else {
          reject(new Error(`GitHub HTTP ${res.statusCode}`));
        }
      });
    });
    req.on('timeout', () => { req.destroy(); reject(new Error('GitHub timeout 8s')); });
    req.on('error', reject);
  });
}

function filterMature(items, opts = {}) {
  const now = Date.now();
  const maxAgeMs = QUALITY_FILTER.max_age_days_since_push * 24 * 60 * 60 * 1000;
  const allowUnknown = opts.allowUnknownLicense === true;
  return items.filter(r => {
    if ((r.stargazers_count || 0) < QUALITY_FILTER.min_stars) return false;
    if (r.archived) return false;
    if (r.disabled) return false;
    if (!r.license || !r.license.key) {
      if (!allowUnknown) return false;
    } else if (!QUALITY_FILTER.allowed_licenses.has(r.license.key)) {
      return false;
    }
    if (r.pushed_at) {
      const pushedMs = new Date(r.pushed_at).getTime();
      if (now - pushedMs > maxAgeMs) return false;
    }
    return true;
  });
}

function summarize(repo) {
  return {
    name: repo.full_name,
    stars: repo.stargazers_count || 0,
    forks: repo.forks_count || 0,
    license: (repo.license && repo.license.spdx_id) || 'unknown',
    description: redactString((repo.description || '').slice(0, 200)),
    pushed_at: repo.pushed_at,
    url: repo.html_url,
    topics: (repo.topics || []).slice(0, 6),
    language: repo.language,
  };
}

async function propose(keyword, opts = {}) {
  if (!keyword || typeof keyword !== 'string' || keyword.length < 3) {
    throw new Error('keyword must be at least 3 chars');
  }
  const cacheKey = keyword.toLowerCase().trim();
  const cached = readCache(cacheKey);
  if (cached && !opts.fresh) return { source: 'cache', candidates: cached };

  const queries = [
    `${keyword} claude skill`,
    `${keyword} ai-skill`,
    `${keyword} agent skill`,
    keyword,
  ];
  const seen = new Set();
  const all = [];
  for (const q of queries) {
    try {
      const r = await ghSearch(q, { perPage: 10 });
      for (const item of (r.items || [])) {
        if (seen.has(item.full_name)) continue;
        seen.add(item.full_name);
        all.push(item);
      }
      if (all.length >= 20) break;
    } catch (e) {
      try { require('./error-log.cjs').logError('skills-propose.search', e, { query: q }); } catch {}
      if (all.length === 0) throw e;
      break;
    }
  }
  const mature = filterMature(all, { allowUnknownLicense: opts.allowUnknownLicense }).slice(0, opts.top || 5).map(summarize);
  writeCache(cacheKey, mature);
  return { source: 'github', candidates: mature };
}

function generateScaffold(candidate, localSkillName, gapDescription) {
  if (!candidate || !candidate.name) throw new Error('candidate missing name');
  if (!localSkillName || !/^[a-z0-9-]+$/i.test(localSkillName)) {
    throw new Error('localSkillName must be alphanumeric with dashes');
  }
  const skillsDir = path.join(process.cwd(), '.claude', 'skills', localSkillName);
  if (fs.existsSync(skillsDir)) {
    throw new Error(`Skill ${localSkillName} already exists; choose another name`);
  }
  fs.mkdirSync(skillsDir, { recursive: true });

  const triggers = [...new Set([
    ...(candidate.topics || []),
    ...localSkillName.split('-').filter(w => w.length >= 4),
  ])].slice(0, 8);

  const skillMd = `---
name: ${localSkillName}
description: ${(candidate.description || gapDescription || localSkillName).slice(0, 160)}
triggers: [${triggers.map(t => `"${t}"`).join(', ')}]
inspired_by: ${candidate.name}
inspired_url: ${candidate.url}
inspired_stars: ${candidate.stars}
inspired_license: ${candidate.license}
created: ${new Date().toISOString().slice(0, 10)}
status: scaffold
---

# ${localSkillName}

> **Inspired by:** [${candidate.name}](${candidate.url}) — ⭐ ${candidate.stars} · ${candidate.license}
> **Gap:** ${gapDescription || '(unspecified)'}
> **Status:** SCAFFOLD — fill in implementation; this is a placeholder.

## What this skill does

(Replace this section with a description of WHAT the skill helps with. Keep it
1-2 sentences. The trigger words above are auto-extracted from the upstream
repo's topics + your local name.)

## When it activates

Skills-activator (\`.claude/helpers/skills-activator.cjs\`) auto-suggests this
skill when the user prompt contains any of: ${triggers.map(t => `\`${t}\``).join(', ')}.

## How to use

(Replace this section with concrete steps the LLM should take when this skill
activates. See similar skills under \`.claude/skills/\` for patterns.)

## Why this skill exists

CCDEW's auto-infer detected a gap in coverage: \`${gapDescription || 'no specific gap'}\`.
Rather than invent from scratch, the skill is **modeled after** a mature open-source
project: ${candidate.name} (${candidate.stars}+ stars, ${candidate.license}).

## License & attribution

This skill is a CCDEW-local scaffold inspired by upstream metadata only —
**no code copied**. If you adapt content from the upstream, follow its license
(${candidate.license}) and credit accordingly.
`;
  fs.writeFileSync(path.join(skillsDir, 'SKILL.md'), skillMd, 'utf-8');
  return { skill_path: skillsDir, file: path.join(skillsDir, 'SKILL.md') };
}

function fromInferFindings(findings) {
  const gaps = [];
  for (const f of (findings || [])) {
    if (f.zoom === 'MAHA' && /skill|coverage/i.test(f.msg || '')) {
      gaps.push(f.msg);
    }
  }
  return gaps;
}

module.exports = {
  propose,
  generateScaffold,
  filterMature,
  summarize,
  fromInferFindings,
  QUALITY_FILTER,
};
