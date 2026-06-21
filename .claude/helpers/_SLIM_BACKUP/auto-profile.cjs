#!/usr/bin/env node
/**
 * auto-profile.cjs — Automatic Profile Switching
 * 
 * Phase 4: Moduri Lite/Full/SSA-Max
 * - Automatic profile switching based on budget
 * - Different component configurations per mode
 * - Smooth transitions
 * - Override capabilities
 * 
 * Usage:
 *   node auto-profile.cjs current    - Show current profile
 *   node auto-profile.cjs switch <mode> - Switch mode
 *   node auto-profile.cjs status     - Show all modes
 */

'use strict';

const fs = require('fs');
const path = require('path');

const CCDEW_PATH = '/home/think/CCDEW';
const DATA_DIR = path.join(CCDEW_PATH, '.claude-flow/data');
const FLAGS_FILE = path.join(CCDEW_PATH, '.claude/helpers/feature-flags.json');

// ── Profile definitions ─────────────────────────────────────────────────────
const PROFILES = {
  lite: {
    name: 'Lite',
    description: 'Minimal resource usage, maximum savings',
    budget_threshold: 0.75, // 75% of budget
    components: {
      enneagram: true,
      ssa: true,
      safla: false,
      codeburn: false,
      ruflo: false,
      graphify: false,
      langraph: false,
      project_scope: false,
      intelligence: false,
      auto_optimize: true,
      instincts: false,
      secret_scan: false
    },
    ssa: {
      efficiency_target: 0.15,
      context_zoom: 'nano',
      top_k: 5
    },
    circuit: {
      default_length: 3,
      fast_mode: true
    },
    icons: {
      emoji: '🔋',
      color: 'green'
    }
  },
  
  full: {
    name: 'Full',
    description: 'All components active, balanced performance',
    budget_threshold: 0.50, // 50% of budget
    components: {
      enneagram: true,
      ssa: true,
      safla: true,
      codeburn: true,
      ruflo: true,
      graphify: true,
      langraph: true,
      project_scope: true,
      intelligence: true,
      auto_optimize: true,
      instincts: true,
      secret_scan: true
    },
    ssa: {
      efficiency_target: 0.25,
      context_zoom: 'auto',
      top_k: 10
    },
    circuit: {
      default_length: 5,
      fast_mode: false
    },
    icons: {
      emoji: '⚡',
      color: 'cyan'
    }
  },
  
  'ssa-max': {
    name: 'SSA-Max',
    description: 'Maximum SSA efficiency, minimum token usage',
    budget_threshold: 0.90, // 90% of budget (critical)
    components: {
      enneagram: true,
      ssa: true,
      safla: true,
      codeburn: true,
      ruflo: false,
      graphify: false,
      langraph: false,
      project_scope: true,
      intelligence: false,
      auto_optimize: false,
      instincts: false,
      secret_scan: true
    },
    ssa: {
      efficiency_target: 0.12,
      context_zoom: 'nano',
      top_k: 3
    },
    circuit: {
      default_length: 3,
      fast_mode: true
    },
    icons: {
      emoji: '🎯',
      color: 'orange'
    }
  }
};

// ── Load current state ──────────────────────────────────────────────────────
function loadCurrentProfile() {
  let current = 'full';
  let components = {};
  let mode = 'full';
  
  if (fs.existsSync(FLAGS_FILE)) {
    try {
      const flags = JSON.parse(fs.readFileSync(FLAGS_FILE, 'utf-8'));
      current = flags.profile || 'full';
      components = flags.components || {};
      mode = flags.mode || 'full';
    } catch(e) {}
  }
  
  return { current, components, mode };
}

function saveProfile(profileName) {
  const profile = PROFILES[profileName];
  if (!profile) {
    console.log(`❌ Unknown profile: ${profileName}`);
    return false;
  }
  
  const flags = {
    profile: profileName,
    mode: profileName,
    components: profile.components,
    ssa: profile.ssa,
    circuit: profile.circuit,
    auto_switch: true,
    budget_threshold: profile.budget_threshold,
    last_updated: new Date().toISOString()
  };
  
  fs.writeFileSync(FLAGS_FILE, JSON.stringify(flags, null, 2));
  console.log(`✅ Switched to profile: ${profileName}`);
  console.log(`   ${profile.description}`);
  console.log(`   Active components: ${Object.values(profile.components).filter(v => v).length}/13`);
  
  return true;
}

// ── Calculate budget usage ──────────────────────────────────────────────────
function getBudgetUsage() {
  const cacheFile = path.join(DATA_DIR, 'codeburn-cache.json');
  let today_cost = 0;
  const daily_budget = 100; // $100/day
  
  if (fs.existsSync(cacheFile)) {
    try {
      const cache = JSON.parse(fs.readFileSync(cacheFile, 'utf-8'));
      today_cost = parseFloat(cache.today_cost) || 0;
    } catch(e) {}
  }
  
  return {
    cost: today_cost,
    budget: daily_budget,
    percentage: (today_cost / daily_budget) * 100,
    remaining: daily_budget - today_cost
  };
}

// ── Auto-switch based on budget ─────────────────────────────────────────────
function autoSwitch() {
  const budget = getBudgetUsage();
  const current = loadCurrentProfile();
  
  console.log(`\n📊 Budget Usage: ${budget.percentage.toFixed(1)}% ($${budget.cost.toFixed(2)}/$${budget.budget})`);
  console.log(`   Current profile: ${current.current}`);
  
  // Determine target profile
  let target = current.current;
  
  if (budget.percentage > 90) {
    target = 'ssa-max';
    console.log(`   ⚠️  Budget critical (>90%) → Switching to SSA-Max`);
  } else if (budget.percentage > 75) {
    target = 'lite';
    console.log(`   ⚠️  Budget high (>75%) → Switching to Lite`);
  } else if (target === 'ssa-max' || target === 'lite') {
    target = 'full';
    console.log(`   ✅ Budget OK → Switching to Full`);
  }
  
  if (target !== current.current) {
    console.log(`\n🔄 Auto-switching from ${current.current} to ${target}...`);
    saveProfile(target);
  } else {
    console.log(`\n✅ No switch needed, staying at ${current.current}`);
  }
  
  return target;
}

// ── Show status ─────────────────────────────────────────────────────────────
function showStatus() {
  const current = loadCurrentProfile();
  const budget = getBudgetUsage();
  
  console.log('\n═══════════════════════════════════════════════════════');
  console.log('  AUTO-PROFILE SWITCHING — STATUS');
  console.log('═══════════════════════════════════════════════════════\n');
  
  console.log(`📊 Current Budget: ${budget.percentage.toFixed(1)}%`);
  console.log(`   Cost: $${budget.cost.toFixed(2)} / $${budget.budget}`);
  console.log(`   Remaining: $${budget.remaining.toFixed(2)}\n`);
  
  console.log(`🎯 Current Profile: ${current.current.toUpperCase()}`);
  console.log(`   Mode: ${current.mode}\n`);
  
  console.log('─────────────────────────────────────────────────────────');
  console.log('  PROFILES\n');
  
  for (const [name, profile] of Object.entries(PROFILES)) {
    const isActive = current.current === name;
    const threshold = (profile.budget_threshold * 100).toFixed(0);
    
    console.log(`  ${profile.icons.emoji} ${name.toUpperCase()} ${isActive ? '[ACTIVE]' : ''}`);
    console.log(`     Budget threshold: >${threshold}%`);
    console.log(`     Components: ${Object.values(profile.components).filter(v => v).length}/13`);
    console.log(`     SSA target: ${(profile.ssa.efficiency_target * 100).toFixed(0)}%`);
    console.log(`     Circuit: ${profile.circuit.default_length} nodes`);
    console.log(`     ${profile.description}`);
    console.log('');
  }
  
  console.log('─────────────────────────────────────────────────────────');
  console.log('  AUTO-SWITCH RULES\n');
  console.log('  >90% budget → ssa-max (emergency)');
  console.log('  >75% budget → lite (conservative)');
  console.log('  <75% budget → full (balanced)');
  console.log('═══════════════════════════════════════════════════════\n');
  
  return { current: current.current, budget, profiles: PROFILES };
}

// ── Get profile config ───────────────────────────────────────────────────────
function getProfileConfig(name = null) {
  const current = loadCurrentProfile();
  const profileName = name || current.current;
  const profile = PROFILES[profileName];
  
  if (!profile) return null;
  
  return {
    ...profile,
    active: current.current === profileName,
    budget: getBudgetUsage()
  };
}

// ── CLI Interface ───────────────────────────────────────────────────────────
function main() {
  const args = process.argv.slice(2);
  
  if (!args.length) {
    showStatus();
    process.exit(0);
  }
  
  const cmd = args[0];
  
  switch(cmd) {
    case 'current':
      const curr = loadCurrentProfile();
      console.log(`Current profile: ${curr.current}`);
      console.log(JSON.stringify(PROFILES[curr.current], null, 2));
      break;
      
    case 'switch':
      if (args.length < 2) {
        console.log('Usage: auto-profile.cjs switch <lite|full|ssa-max>');
        process.exit(1);
      }
      const target = args[1];
      if (!PROFILES[target]) {
        console.log(`❌ Unknown profile: ${target}`);
        console.log('Available:', Object.keys(PROFILES).join(', '));
        process.exit(1);
      }
      saveProfile(target);
      break;
      
    case 'auto':
      autoSwitch();
      break;
      
    case 'status':
      showStatus();
      break;
      
    case 'config':
      const name = args[1] || loadCurrentProfile().current;
      const config = getProfileConfig(name);
      console.log(JSON.stringify(config, null, 2));
      break;
      
    default:
      console.log('Usage:');
      console.log('  node auto-profile.cjs          - Show status');
      console.log('  node auto-profile.cjs current   - Show current profile');
      console.log('  node auto-profile.cjs switch <mode> - Switch mode');
      console.log('  node auto-profile.cjs auto     - Auto-switch based on budget');
      console.log('  node auto-profile.cjs status    - Show all profiles');
      console.log('  node auto-profile.cjs config [name] - Show profile config');
      process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = { 
  PROFILES, 
  getProfileConfig, 
  saveProfile, 
  autoSwitch, 
  getBudgetUsage,
  showStatus 
};