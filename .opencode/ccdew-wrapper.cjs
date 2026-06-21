#!/usr/bin/env node
'use strict';
/**
 * CCDEW-OpenCode Bridge v1.0
 * Integrates CCDEW features into OpenCode GUI
 */

const path = require('path');
const fs = require('fs');

const CCDEW_ROOT = path.resolve(process.cwd());
const helpersDir = path.join(CCDEW_ROOT, '.claude', 'helpers');

function lazy(name) {
  const candidates = [
    path.join(helpersDir, name + '.cjs'),
    path.join(helpersDir, name + '.js'),
  ];
  for (const c of candidates) {
    try { return require(c); } catch {}
  }
  return null;
}

const [, , command, ...args] = process.argv;

const handlers = {
  status: () => {
    const codeburn = lazy('codeburn');
    if (codeburn) {
      try {
        const t = codeburn.totals();
        if (t.source !== 'unavailable') {
          console.log(`💰 $${t.today_cost.toFixed(2)}/${t.daily_budget || 100}/day · ${t.today_calls}c`);
        } else {
          console.log('📊 CCDEW active (codeburn unavailable)');
        }
      } catch { console.log('📊 CCDEW active'); }
    } else {
      console.log('📊 CCDEW bridge ready');
    }
  },

  route: () => {
    const input = args.join(' ') || process.env.PROMPT || '';
    const router = lazy('router');
    const safla = lazy('safla');
    
    if (!router || !router.routeTask) {
      console.log('[ROUTE] Router not available — use Claude Code for full routing');
      return;
    }
    
    const result = router.routeTask(input);
    const saflaAdj = safla ? safla.getWeightAdj(result.node) : 0;
    
    console.log(`🎯 Node ${result.node} (${result.agent}) | confidence: ${((result.confidence + saflaAdj) * 100).toFixed(0)}%`);
    console.log(`   Reason: ${result.reason || 'adaptive routing'}`);
  },

  cost: () => {
    const codeburn = lazy('codeburn');
    if (!codeburn) { console.log('[COST] CodeBurn not available'); return; }
    const t = codeburn.totals();
    if (t.source === 'unavailable') { console.log('[COST] Tracking unavailable'); return; }
    const lvl = t.today_cost > t.daily_budget * 0.75 ? '⚠️' : '✓';
    console.log(`${lvl} Today: $${t.today_cost.toFixed(2)} (${t.today_calls} calls) | Month: $${t.month_cost.toFixed(2)}`);
  },

  snapshot: () => {
    try {
      const ss = require(path.join(helpersDir, 'lib', 'session-snapshot.cjs'));
      const r = ss.snapshot({ note: 'OpenCode GUI snapshot' });
      console.log(`📸 Snapshot saved: ${path.basename(r.file)}`);
      if (r.snapshot && r.snapshot.cost) console.log(`   💰 $${r.snapshot.cost.today_cost.toFixed(2)} today`);
    } catch (e) { console.log('[SNAPSHOT] Error: ' + e.message); }
  },

  audit: () => {
    const evaluate = require(path.join(helpersDir, 'evaluate-setup.cjs'));
    evaluate({ silent: false });
  },

  skills: () => {
    const sa = lazy('skills-activator');
    const prompt = args.join(' ') || process.env.PROMPT || '';
    if (!sa) { console.log('[SKILLS] Activator not available'); return; }
    const active = sa.activateForPrompt(prompt);
    console.log(active.length === 0 ? '[SKILLS] No matches' : `[SKILLS] Suggested: ${active.join(', ')}`);
  },

  help: () => {
    console.log(`
CCDEW-OpenCode Bridge v1.0
==========================
Commands:
  status      - Show CCDEW status and cost
  route <msg> - Route message to Enneagram node
  cost        - Show detailed cost tracking
  snapshot    - Save session snapshot
  audit       - Run 5-zoom audit
  skills <p>  - Suggest skills for prompt
  help        - Show this help

Examples:
  node .opencode/ccdew-wrapper.cjs status
  PROMPT="refactor auth" node .opencode/ccdew-wrapper.cjs route
`);
  }
};

if (command && handlers[command]) {
  try { handlers[command](); }
  catch (e) { console.error('[ERROR] ' + e.message); }
} else {
  handlers.help();
}