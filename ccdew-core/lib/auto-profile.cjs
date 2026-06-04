#!/usr/bin/env node
/**
 * auto-profile.cjs — Automatic Profile Switching (SLIM)
 * Usage: node auto-profile.cjs [current|switch <mode>|auto|status|config]
 */
'use strict';
const fs = require('fs'), path = require('path');
const CCDEW_PATH = '/home/think/CCDEW';
const DATA_DIR = path.join(CCDEW_PATH, '.claude-flow/data');
const FLAGS_FILE = path.join(CCDEW_PATH, '.claude/helpers/feature-flags.json');

const PROFILES = {
  lite: { name:'Lite', threshold:0.75, components:{enneagram:true,ssa:true,safla:false,codeburn:false,ruflo:false,graphify:false,langraph:false,project_scope:false,intelligence:false,auto_optimize:true,instincts:false,secret_scan:false}, ssa:{target:0.15,top_k:5}, circuit:3 },
  full: { name:'Full', threshold:0.50, components:{enneagram:true,ssa:true,safla:true,codeburn:true,ruflo:true,graphify:true,langraph:true,project_scope:true,intelligence:true,auto_optimize:true,instincts:true,secret_scan:true}, ssa:{target:0.25,top_k:10}, circuit:5 },
  'ssa-max': { name:'SSA-Max', threshold:0.90, components:{enneagram:true,ssa:true,safla:true,codeburn:true,ruflo:false,graphify:false,langraph:false,project_scope:true,intelligence:false,auto_optimize:false,instincts:false,secret_scan:true}, ssa:{target:0.12,top_k:3}, circuit:3 }
};

function loadCurrent() {
  try { if (fs.existsSync(FLAGS_FILE)) return JSON.parse(fs.readFileSync(FLAGS_FILE, 'utf-8')); } catch {}
  return { profile: 'full', mode: 'full' };
}

function saveProfile(name) {
  const p = PROFILES[name]; if (!p) { console.log('Unknown: ' + name); return; }
  const flags = { profile:name, mode:name, components:p.components, ssa:p.ssa, circuit:{default_length:p.circuit}, auto_switch:true, budget_threshold:p.threshold, last_updated:new Date().toISOString() };
  fs.writeFileSync(FLAGS_FILE, JSON.stringify(flags, null, 2));
  console.log('Switched: ' + name + ' (' + Object.values(p.components).filter(v=>v).length + '/13 components)');
}

function getBudget() {
  let cost = 0;
  try { const c = JSON.parse(fs.readFileSync(path.join(DATA_DIR, 'codeburn-cache.json'), 'utf-8')); cost = parseFloat(c.today_cost) || 0; } catch {}
  return { cost, budget:100, pct: cost };
}

function autoSwitch() {
  const b = getBudget(), cur = loadCurrent().profile;
  let target = cur;
  if (b.pct > 90) { target = 'ssa-max'; console.log('Critical: switch to SSA-Max'); }
  else if (b.pct > 75) { target = 'lite'; console.log('High: switch to Lite'); }
  else if (cur !== 'full') { target = 'full'; console.log('OK: switch to Full'); }
  if (target !== cur) saveProfile(target);
  return target;
}

function showStatus() {
  const cur = loadCurrent().profile, b = getBudget();
  console.log('\n=== AUTO-PROFILE ===\nBudget: ' + b.pct.toFixed(1) + '% ($' + b.cost.toFixed(2) + '/$' + b.budget + ')\n');
  for (const [n, p] of Object.entries(PROFILES)) {
    const active = cur === n ? ' [ACTIVE]' : '';
    console.log((active ? '●' : '○') + ' ' + n.toUpperCase() + active + ' | ' + Math.round(p.threshold*100) + '% threshold | ' + Object.values(p.components).filter(v=>v).length + '/13');
  }
  console.log('\nRules: >90%→ssa-max, >75%→lite, <75%→full\n');
}

function main() {
  const args = process.argv.slice(2), cmd = args[0];
  if (!cmd) { showStatus(); return; }
  if (cmd === 'current') { const c = loadCurrent(); console.log('Current: ' + c.profile); }
  else if (cmd === 'switch') { saveProfile(args[1] || 'full'); }
  else if (cmd === 'auto') { autoSwitch(); }
  else if (cmd === 'status') { showStatus(); }
  else if (cmd === 'config') { const c = loadCurrent(); console.log(JSON.stringify(PROFILES[c.profile] || PROFILES.full, null, 2)); }
  else { console.log('Usage: current|switch <mode>|auto|status|config'); }
}

if (require.main === module) main();
module.exports = { PROFILES, loadCurrent, saveProfile, autoSwitch, getBudget, showStatus };