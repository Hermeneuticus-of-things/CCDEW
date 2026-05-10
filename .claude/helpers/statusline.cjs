#!/usr/bin/env node
'use strict';
/**
 * Statusline — single-line summary printed by Claude Code at every prompt.
 * Lazy-load only what's needed. Total budget: <80ms.
 */

const path = require('path');
const fs = require('fs');

const helpersDir = __dirname;

function safeRequire(name) {
  try {
    const candidates = [
      path.join(helpersDir, name + '.cjs'),
      path.join(helpersDir, name + '.js'),
    ];
    for (const c of candidates) if (fs.existsSync(c)) return require(c);
  } catch { /* */ }
  return null;
}

function fmt(n, d = 2) {
  return Number.isFinite(n) ? n.toFixed(d) : '?';
}

const parts = [];

try {
  const codeburn = safeRequire('codeburn');
  if (codeburn) {
    const t = codeburn.totals();
    if (t.source === 'real' || t.source === 'native') {
      const cpc = t.today_calls > 0 ? t.today_cost / t.today_calls : 0;
      const flag = cpc > 0.05 ? ' ⚠' : '';
      parts.push(`💰 $${fmt(t.today_cost)}/d · ${t.today_calls}c${flag}`);
    } else if (t.source === 'unavailable') {
      parts.push('💰 n/a');
    }
  }
} catch { /* */ }

try {
  const safla = safeRequire('safla');
  if (safla && safla.stats) {
    const s = safla.stats();
    const validRates = Object.values(s.nodes).filter(n => (n.success + n.failure) >= 3);
    if (validRates.length > 0) {
      const avgRate = validRates.reduce((sum, n) => sum + n.rate, 0) / validRates.length;
      const pct = Math.round(avgRate * 100);
      parts.push(`🤖 ${pct}% ok·${s.total_feedbacks}fb`);
    }
  }
} catch { /* */ }

try {
  const ps = safeRequire('project-scope');
  if (ps && ps.getActive) {
    const active = ps.getActive('');
    if (active && active.name) {
      parts.push(`📂 ${active.name}`);
    }
  }
} catch { /* */ }

try {
  const pd = safeRequire('platform-detect');
  if (pd && pd.detectPlatform) {
    const p = pd.detectPlatform();
    if (p.name && p.name !== 'unknown' && p.name !== 'claude-code') {
      parts.push(`🖥️ ${p.name}`);
    }
  }
} catch { /* */ }

console.log(parts.length > 0 ? parts.join(' │ ') : '🔧 CCDEW v3');
