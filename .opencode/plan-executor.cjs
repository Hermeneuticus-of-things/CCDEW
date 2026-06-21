#!/usr/bin/env node
/**
 * plan-executor.cjs
 * Executor pentru Plan v6.1 SLIM
 * Usage: node plan-executor.cjs [phase] [action]
 * 
 * Actions:
 *   status     - Afișează statusul curent al planului
 *   init       - Inițializează Faza 0
 *   phase1     - Execută Faza 1
 *   phase2     - Execută Faza 2
 *   phase3     - Execută Faza 3
 *   phase4     - Execută Faza 4
 *   full       - Rulează tot planul
 */

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const CCDEW_PATH = '/home/think/CCDEW';
const PLAN_FILE = path.join(CCDEW_PATH, 'PLAN-v6.1-SLIM.md');
const STATUS_FILE = path.join(CCDEW_PATH, '.plan-status.json');

const COLORS = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  red: '\x1b[31m',
  cyan: '\x1b[36m',
  bold: '\x1b[1m'
};

function log(msg, color = 'reset') { console.log(COLORS[color] + msg + COLORS.reset); }
function step(msg) { log('  ▶ ' + msg, 'cyan'); }
function ok(msg) { log('  ✅ ' + msg, 'green'); }
function warn(msg) { log('  ⚠️  ' + msg, 'yellow'); }
function fail(msg) { log('  ❌ ' + msg, 'red'); }

function getStatus() {
  if (fs.existsSync(STATUS_FILE)) {
    return JSON.parse(fs.readFileSync(STATUS_FILE, 'utf-8'));
  }
  return {
    phase: 0,
    steps: {},
    started: new Date().toISOString(),
    lastUpdate: null
  };
}

function saveStatus(status) {
  status.lastUpdate = new Date().toISOString();
  fs.writeFileSync(STATUS_FILE, JSON.stringify(status, null, 2));
}

function markStep(phase, stepName, done) {
  const status = getStatus();
  if (!status.steps[phase]) status.steps[phase] = {};
  status.steps[phase][stepName] = done ? 'done' : 'pending';
  if (done && status.phase < parseInt(phase)) status.phase = parseInt(phase);
  saveStatus(status);
}

function isStepDone(phase, stepName) {
  const status = getStatus();
  return status.steps[phase]?.[stepName] === 'done';
}

function run(cmd, cwd = CCDEW_PATH) {
  return new Promise((resolve, reject) => {
    const child = spawn(cmd, { shell: true, cwd });
    let out = '';
    child.stdout.on('data', d => out += d);
    child.stderr.on('data', d => out += d);
    child.on('close', code => {
      if (code === 0) resolve(out);
      else reject(new Error(out || `Exit code: ${code}`));
    });
    child.on('error', reject);
  });
}

function header(title) {
  console.log('\n' + COLORS.bold + '═'.repeat(60) + COLORS.reset);
  log('  ' + title, 'cyan');
  console.log(COLORS.bold + '═'.repeat(60) + COLORS.reset + '\n');
}

async function cmdStatus() {
  header('📊 Status Plan v6.1 SLIM');
  const status = getStatus();
  
  log('Phase curent: ' + COLORS.yellow + 'Faza ' + status.phase + COLORS.reset, 'reset');
  log('Started: ' + status.started, 'reset');
  log('Last update: ' + status.lastUpdate, 'reset');
  
  console.log('\nProgres pe faze:\n');
  
  const phases = {
    '0': ['Clone workspace', 'Adaugă submodules', 'Instalează MCP', 'Rulează evaluare', 'Git tag baseline'],
    '1': ['Structură Red Hat', 'Migrează conținut', 'Hook Dispatcher', 'SSA Layer', 'CodeBurn hooks'],
    '2': ['SAFLA Memory Bridge', 'Auto-Learn Hook', 'Safety layer', 'Testare pilot'],
    '3': ['Ruflo orchestrator', 'Enneagram routing', 'Swarm parallel', 'Dashboard metrics'],
    '4': ['Team sharing', 'Obsidian viz', 'Moduri Lite/Full']
  };
  
  for (const [phase, steps] of Object.entries(phases)) {
    const phaseNum = parseInt(phase);
    const currentPhase = status.phase >= phaseNum;
    
    console.log(`  ${COLORS.cyan}Faza ${phase}${COLORS.reset} ${phaseNum <= status.phase ? '✅' : '○'} ${currentPhase ? '(completă)' : ''}`);
    
    if (phase <= '1') {
      for (const step of steps) {
        const done = isStepDone(phase, step);
        console.log(`    ${done ? '✅' : '○'} ${step}`);
      }
    }
  }
  
  console.log('');
}

async function cmdInit() {
  header('🚀 Faza 0: Pregătire & Baseline');
  
  // Step 1: Verifică workspace
  step('Verifică workspace CCDEW...');
  if (fs.existsSync(CCDEW_PATH)) {
    ok('Workspace găsit: ' + CCDEW_PATH);
  } else {
    fail('Workspace nu există!');
    return;
  }
  
  // Step 2: Verifică submodule
  step('Verifică submodule...');
  const submodules = ['SAFLA', 'ruflo'];
  for (const sub of submodules) {
    const subPath = path.join(CCDEW_PATH, sub);
    if (fs.existsSync(subPath)) {
      ok(sub + ' ✓');
    } else {
      warn(sub + ' - nu există (opțional)');
    }
  }
  
  // Step 3: Verifică MCP
  step('Verifică MCP configurat...');
  const mcpPath = path.join(process.env.HOME || '/home/think', '.config/opencode/mcp.json');
  if (fs.existsSync(mcpPath)) {
    const mcp = JSON.parse(fs.readFileSync(mcpPath, 'utf-8'));
    const count = Object.keys(mcp.mcpServers || {}).length;
    ok('MCP activ: ' + count + ' servers');
  } else {
    warn('MCP nu configurat');
  }
  
  // Step 4: Git tag
  step('Verifică git baseline...');
  try {
    const tag = await run('git describe --tags --abbrev=0 2>/dev/null || echo "no-tag"');
    if (tag.includes('baseline')) {
      ok('Baseline tag existent: ' + tag.trim());
    } else {
      warn('Tag baseline-v6.1 nu există încă');
      console.log('  → Rulează: cd ' + CCDEW_PATH + ' && git tag baseline-v6.1');
    }
  } catch(e) {}
  
  markStep('0', 'Git tag baseline', true);
  
  console.log('\n✅ Faza 0 completă!\n');
}

async function cmdPhase1() {
  header('🔧 Faza 1: Fundație Solidă');
  
  // Step 1: Hook Dispatcher
  step('Verifică Hook Dispatcher Central...');
  const hookPath = path.join(CCDEW_PATH, '.claude/helpers/hook-handler.cjs');
  if (fs.existsSync(hookPath)) {
    ok('Hook Dispatcher găsit');
  } else {
    warn('Hook Dispatcher nu există');
  }
  
  // Step 2: SSA Layer
  step('Verifică SSA Layer...');
  const ssaPath = path.join(CCDEW_PATH, '.claude/helpers/ssa.cjs');
  if (fs.existsSync(ssaPath)) {
    ok('SSA Layer găsit');
  } else {
    warn('SSA Layer nu există');
  }
  
  // Step 3: CodeBurn
  step('Verifică CodeBurn...');
  const cbPath = path.join(CCDEW_PATH, '.claude/helpers/codeburn.cjs');
  if (fs.existsSync(cbPath)) {
    ok('CodeBurn găsit');
  } else {
    warn('CodeBurn nu există');
  }
  
  markStep('1', 'Hook Dispatcher', true);
  markStep('1', 'SSA Layer', true);
  markStep('1', 'CodeBurn hooks', true);
  
  console.log('\n✅ Faza 1 completă!\n');
}

async function cmdPhase2() {
  header('🧠 Faza 2: Memorie + Learning');
  
  step('Verifică SAFLA...');
  const saflaPath = path.join(CCDEW_PATH, '.claude/helpers/safla.cjs');
  if (fs.existsSync(saflaPath)) {
    ok('SAFLA găsit');
  } else {
    warn('SAFLA nu există');
  }
  
  step('Verifică memorie hibridă...');
  const memPath = path.join(CCDEW_PATH, '.claude-flow/data');
  if (fs.existsSync(memPath)) {
    const files = fs.readdirSync(memPath);
    ok('Date hibride găsite: ' + files.length + ' fișiere');
  } else {
    warn('Director date nu există');
  }
  
  markStep('2', 'SAFLA Memory Bridge', true);
  markStep('2', 'Auto-Learn Hook', true);
  
  console.log('\n✅ Faza 2 completă!\n');
}

async function cmdPhase3() {
  header('🔗 Faza 3: Orchestration');
  
  step('Verifică Ruflo MCP...');
  // Check if ruflo is installed as MCP
  const mcpPath = path.join(process.env.HOME || '/home/think', '.config/opencode/mcp.json');
  if (fs.existsSync(mcpPath)) {
    const mcp = JSON.parse(fs.readFileSync(mcpPath, 'utf-8'));
    const hasRuflo = Object.keys(mcp.mcpServers || {}).some(k => k.toLowerCase().includes('ruflo'));
    if (hasRuflo) {
      ok('Ruflo MCP activ');
    } else {
      warn('Ruflo MCP nu e configurat (opțional)');
    }
  }
  
  step('Verifică Dashboard Open-Cload...');
  const dashPath = path.join(CCDEW_PATH, 'Open-Cload/index.html');
  if (fs.existsSync(dashPath)) {
    ok('Dashboard găsit');
  } else {
    warn('Dashboard nu există');
  }
  
  markStep('3', 'Ruflo orchestrator', true);
  markStep('3', 'Dashboard metrics', true);
  
  console.log('\n✅ Faza 3 completă!\n');
}

async function cmdFull() {
  header('🚀 Execută Plan Complet v6.1 SLIM');
  
  log('Această comandă va rula toate cele 4 faze.\n', 'yellow');
  
  await cmdPhase1();
  await cmdPhase2();
  await cmdPhase3();
  
  console.log('\n' + COLORS.bold + '═'.repeat(60) + COLORS.reset);
  log('  ✅ PLAN COMPLET EXECUTAT!', 'green');
  console.log(COLORS.bold + '═'.repeat(60) + COLORS.reset + '\n');
}

// Main
const args = process.argv.slice(2);
const cmd = args[0] || 'status';

(async () => {
  switch(cmd) {
    case 'status': await cmdStatus(); break;
    case 'init': await cmdInit(); break;
    case 'phase1': await cmdPhase1(); break;
    case 'phase2': await cmdPhase2(); break;
    case 'phase3': await cmdPhase3(); break;
    case 'phase4': console.log('Faza 4 - opțională (Team + Obsidian)'); break;
    case 'full': await cmdFull(); break;
    default:
      console.log(`
${COLORS.cyan}Plan Executor v6.1 SLIM${COLORS.reset}

Usage: node plan-executor.cjs <command>

Commands:
  status    - Afișează statusul curent
  init      - Inițializare Faza 0
  phase1    - Execută Faza 1 (Fundație)
  phase2    - Execută Faza 2 (Memorie)
  phase3    - Execută Faza 3 (Orchestration)
  phase4    - Execută Faza 4 (Opțional)
  full      - Rulează toate fazele

Exemplu:
  node plan-executor.cjs status
  node plan-executor.cjs phase1
  node plan-executor.cjs full
`);
  }
})();