#!/usr/bin/env node
/**
 * Project-Level Memory System — 5 Layer Architecture
 * Each project/session has its own L0-L4 memory, isolated and project-specific
 * L0-L2 are ephemeral (short-term), L3-L4 persist and may propagate to OS-level
 */

'use strict';
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// PROJECT MEMORY MANAGER
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class ProjectMemory {
  constructor(projectPath) {
    this.projectPath = path.resolve(projectPath);
    this.slug = this.projectPath.replace(/^\//, '').replace(/\//g, '-');
    this.baseDir = path.join(this.projectPath, '.claude-flow');
    this.dataDir = path.join(this.baseDir, 'data');
    this.memDir = path.join(this.baseDir, 'memory');
    
    this.paths = {
      L0: path.join(this.dataDir, 'sensory.jsonl'),
      L1: path.join(this.dataDir, 'working.json'),
      L2: path.join(this.baseDir, 'sessions'),
      L3: path.join(this.memDir, 'semantic'),
      L4: path.join(this.memDir, 'identity')
    };
    
    this.decay = { L0: 0.04, L1: 3, L2: 14, L3: 30, L4: Infinity };
    
    // Encryption key derivat din calea proiectului (unic per proiect)
    this.encKey = crypto.createHash('sha256').update(this.projectPath + '-ccdew-proj-v1').digest().slice(0, 32);
    this.encIv = crypto.createHash('sha256').update(this.projectPath + '-iv').digest().slice(0, 16);
    
    this.ensureDirs();
  }
  
  ensureDirs() {
    Object.values(this.paths).forEach(p => {
      fs.mkdirSync(path.dirname(p) || p, { recursive: true });
    });
  }
  
  // ── LAYER 0: SENSORY — Immediate input (1 hour, ~1MB cap) ────────────────
  sensoryLog(entry) {
    if (!entry) return;
    const MAX_L0 = 1024 * 1024; // 1 MiB
    if (fs.existsSync(this.paths.L0) && fs.statSync(this.paths.L0).size > MAX_L0) {
      fs.renameSync(this.paths.L0, this.paths.L0 + '.old');
    }
    const line = JSON.stringify({ ...entry, _ts: Date.now(), _layer: 'L0' });
    fs.appendFileSync(this.paths.L0, line + '\n', 'utf8');
  }
  
  sensoryRead(count = 50) {
    if (!fs.existsSync(this.paths.L0)) return [];
    const lines = fs.readFileSync(this.paths.L0, 'utf8').trim().split('\n').filter(Boolean);
    return lines.slice(-count).map(l => { try { return JSON.parse(l); } catch { return null; } }).filter(Boolean);
  }
  
  sensoryClear() {
    if (fs.existsSync(this.paths.L0)) fs.writeFileSync(this.paths.L0, '', 'utf8');
  }
  
  // ── LAYER 1: WORKING — Active tasks/goals (3 days, max 20 tasks) ───────
  workingGet() {
    return readJSON(this.paths.L1) || { tasks: [], goals: [], insights: [], _layer: 'L1' };
  }
  
  workingSet(data) {
    writeJSON(this.paths.L1, { ...this.workingGet(), ...data });
  }
  
  workingAddTask(task, priority = 'normal') {
    const d = this.workingGet();
    d.tasks = d.tasks || [];
    d.tasks.unshift({ task, priority, createdAt: Date.now() });
    d.tasks = d.tasks.slice(0, 20);
    this.workingSet(d);
    return d;
  }
  
  workingAddGoal(goal, deadline = null) {
    const d = this.workingGet();
    d.goals = d.goals || [];
    d.goals.unshift({ goal, deadline, createdAt: Date.now() });
    d.goals = d.goals.slice(0, 10);
    this.workingSet(d);
    return d;
  }
  
  workingAddInsight(insight) {
    const d = this.workingGet();
    d.insights = d.insights || [];
    d.insights.unshift({ insight, createdAt: Date.now() });
    d.insights = d.insights.slice(0, 30); // max 30 insights per project
    this.workingSet(d);
    return d;
  }
  
  // ── LAYER 2: EPISODIC — Session snapshots (14 days) ────────────────────
  episodicSave(sessionId, summary) {
    const p = path.join(this.paths.L2, `session-${sessionId}.json`);
    writeJSON(p, { sessionId, summary, createdAt: Date.now(), _layer: 'L2' });
    return p;
  }
  
  episodicGet(sessionId) {
    return readJSON(path.join(this.paths.L2, `session-${sessionId}.json`));
  }
  
  episodicList() {
    if (!fs.existsSync(this.paths.L2)) return [];
    return fs.readdirSync(this.paths.L2).filter(f => f.endsWith('.json')).map(f => f.replace('.json', ''));
  }
  
  // ── LAYER 3: SEMANTIC — Concepts, patterns (30 days decay) ─────────────
  semanticSet(key, value, tags = [], confidence = 0.5) {
    const p = path.join(this.paths.L3, `${safeKey(key)}.json`);
    const doProtect = isSensitive(key);
    const entry = {
      key,
      value: doProtect ? this.encrypt(String(value)) : value,
      tags,
      confidence,
      createdAt: Date.now(),
      expiresAt: Date.now() + this.decay.L3 * 86400000,
      _layer: 'L3',
      protected: doProtect
    };
    fs.mkdirSync(this.paths.L3, { recursive: true });
    fs.writeFileSync(p, JSON.stringify(entry, null, 2), 'utf8');
    return entry;
  }
  
  semanticGet(key) {
    const p = path.join(this.paths.L3, `${safeKey(key)}.json`);
    const data = readJSON(p);
    if (!data) return null;
    if (data.protected && data.value) data.value = this.decrypt(data.value);
    return data;
  }
  
  semanticList() {
    if (!fs.existsSync(this.paths.L3)) return [];
    return fs.readdirSync(this.paths.L3).filter(f => f.endsWith('.json')).map(f => f.replace('.json', ''));
  }
  
  semanticGC() {
    if (!fs.existsSync(this.paths.L3)) return 0;
    const now = Date.now();
    let removed = 0;
    for (const f of fs.readdirSync(this.paths.L3)) {
      if (!f.endsWith('.json')) continue;
      const data = readJSON(path.join(this.paths.L3, f));
      if (data && data.expiresAt && data.expiresAt < now) {
        fs.unlinkSync(path.join(this.paths.L3, f));
        removed++;
      }
    }
    return removed;
  }
  
  // ── LAYER 4: IDENTITY — Permanent project-specific knowledge ────────────
  identitySet(key, value) {
    const p = path.join(this.paths.L4, `${safeKey(key)}.json`);
    const doProtect = isSensitive(key);
    const entry = {
      key,
      value: doProtect ? this.encrypt(String(value)) : value,
      createdAt: Date.now(),
      updatedAt: Date.now(),
      _layer: 'L4',
      protected: doProtect
    };
    fs.mkdirSync(this.paths.L4, { recursive: true });
    fs.writeFileSync(p, JSON.stringify(entry, null, 2), 'utf8');
    return entry;
  }
  
  identityGet(key) {
    const p = path.join(this.paths.L4, `${safeKey(key)}.json`);
    const data = readJSON(p);
    if (!data) return null;
    if (data.protected && data.value) data.value = this.decrypt(data.value);
    return data;
  }
  
  identityList() {
    if (!fs.existsSync(this.paths.L4)) return [];
    return fs.readdirSync(this.paths.L4).filter(f => f.endsWith('.json')).map(f => f.replace('.json', ''));
  }
  
  // ── PROMOTION: L0 → L1 → L2 → L3 → L4 → OS-Global ──────────────────────
  promote(entry, fromLayer, toLayer) {
    if (fromLayer === 'L0' && toLayer === 'L1') {
      return this.workingAddInsight(entry.msg || entry.insight || JSON.stringify(entry));
    }
    else if (fromLayer === 'L1' && toLayer === 'L2') {
      const sid = `auto-${Date.now()}`;
      return this.episodicSave(sid, entry);
    }
    else if (fromLayer === 'L2' && toLayer === 'L3') {
      const key = entry.key || entry.sessionId || `episodic-${Date.now()}`;
      return this.semanticSet(key, entry.summary || entry, ['promoted'], 0.6);
    }
    else if (fromLayer === 'L3' && toLayer === 'L4') {
      return this.identitySet(entry.key || `identity-${Date.now()}`, entry.value || entry);
    }
    else if (fromLayer === 'L4' && toLayer === 'OS') {
      // Propagate to OS-level global memory
      return propagateToOS(entry, this.projectPath, this.slug);
    }
  }
  
  // ── AUTO-PROPAGATION: decide what moves up ──────────────────────────────
  autoPropagate() {
    const promoted = [];
    
    // L1 → L2: Insights that appear multiple times
    const insights = this.workingGet().insights || [];
    const insightFreq = {};
    insights.forEach(i => {
      const hash = hashContent(i.insight);
      insightFreq[hash] = (insightFreq[hash] || 0) + 1;
    });
    Object.entries(insightFreq).forEach(([hash, count]) => {
      if (count >= 3) {
        const entry = insights.find(i => hashContent(i.insight) === hash);
        if (entry) {
          this.promote(entry, 'L1', 'L3');
          promoted.push({ layer: 'L1→L3', key: entry.insight.slice(0, 50) });
        }
      }
    });
    
    // L3 → L4: High confidence semantic entries
    this.semanticList().forEach(key => {
      const entry = this.semanticGet(key);
      if (entry && entry.confidence >= 0.85) {
        if (!fs.existsSync(path.join(this.paths.L4, `${safeKey(entry.key)}.json`))) {
          this.promote(entry, 'L3', 'L4');
          promoted.push({ layer: 'L3→L4', key: entry.key });
        }
      }
    });
    
    // L4 → OS: Stable project knowledge
    this.identityList().forEach(key => {
      const entry = this.identityGet(key);
      if (entry && (Date.now() - entry.createdAt) > 86400000) { // at least 1 day old
        this.promote(entry, 'L4', 'OS');
        promoted.push({ layer: 'L4→OS', key: entry.key });
      }
    });
    
    return promoted;
  }
  
  // ── Security helpers ────────────────────────────────────────────────────
  encrypt(plaintext) {
    if (!plaintext) return '';
    try {
      const cipher = crypto.createCipheriv('aes-256-gcm', this.encKey, this.encIv);
      let enc = cipher.update(String(plaintext), 'utf8', 'hex');
      enc += cipher.final('hex');
      const auth = cipher.getAuthTag().toString('hex');
      return enc + ':' + auth;
    } catch { return plaintext; }
  }
  
  decrypt(ciphertext) {
    if (!ciphertext || !ciphertext.includes(':')) return ciphertext;
    try {
      const [enc, auth] = ciphertext.split(':');
      const decipher = crypto.createDecipheriv('aes-256-gcm', this.encKey, this.encIv);
      decipher.setAuthTag(Buffer.from(auth, 'hex'));
      let dec = decipher.update(enc, 'hex', 'utf8');
      dec += decipher.final('utf8');
      return dec;
    } catch { return ciphertext; }
  }
  
  // ── Status ──────────────────────────────────────────────────────────────
  status() {
    return {
      project: this.slug,
      L0: { count: this.sensoryRead(9999).length, path: this.paths.L0 },
      L1: { tasks: this.workingGet().tasks?.length || 0, goals: this.workingGet().goals?.length || 0 },
      L2: { sessions: this.episodicList().length, path: this.paths.L2 },
      L3: { concepts: this.semanticList().length, path: this.paths.L3 },
      L4: { identities: this.identityList().length, path: this.paths.L4 }
    };
  }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// OS-LEVEL GLOBAL MEMORY (cross-project)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
const OS_BASE = path.join(require('os').homedir(), '.config', 'opencode', 'ccdew-os');
const OS_STATE = path.join(OS_BASE, 'global-state.json');
const OS_MEMORY = path.join(OS_BASE, 'memory.jsonl');
const OS_LEARNINGS = path.join(OS_BASE, 'learnings.json');
const OS_PATTERNS = path.join(OS_BASE, 'patterns.json');

function ensureOSDir() {
  fs.mkdirSync(OS_BASE, { recursive: true });
}

function getOSState() {
  ensureOSDir();
  return readJSON(OS_STATE, {
    version: '1.0',
    firstBoot: Date.now(),
    totalSessions: 0,
    projects: {},
    learnings: [],
    patterns: [],
    preferences: {}
  });
}

function saveOSState(state) {
  state.lastSync = new Date().toISOString();
  writeJSON(OS_STATE, state);
}

// Propagare automată de la proiect la OS
function propagateToOS(entry, projectPath, slug) {
  ensureOSDir();
  const state = getOSState();
  
  // Log propagation
  fs.appendFileSync(OS_MEMORY, JSON.stringify({
    type: 'propagation',
    fromProject: slug,
    fromPath: projectPath,
    entry,
    ts: Date.now()
  }) + '\n', 'utf8');
  
  // Index project
  if (!state.projects[projectPath]) {
    state.projects[projectPath] = {
      slug,
      firstSeen: Date.now(),
      propagations: 0
    };
  }
  state.projects[projectPath].propagations++;
  state.projects[projectPath].lastSync = Date.now();
  
  saveOSState(state);
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// HELPERS
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function readJSON(p, defaultVal = null) {
  try { return JSON.parse(fs.readFileSync(p, 'utf8')); } catch { return defaultVal; }
}

function writeJSON(p, d) {
  fs.mkdirSync(path.dirname(p), { recursive: true });
  fs.writeFileSync(p, JSON.stringify(d, null, 2), 'utf8');
}

function safeKey(key) {
  return String(key).replace(/[^a-z0-9_-]/gi, '-').slice(0, 80);
}

function isSensitive(key) {
  const patterns = ['key', 'token', 'secret', 'password', 'pass', 'api', 'auth', 'private', 'credential', 'access'];
  return patterns.some(p => key.toLowerCase().includes(p));
}

function hashContent(text) {
  return crypto.createHash('md5').update(String(text)).digest('hex').slice(0, 16);
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// CLI / Module
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function main() {
  const projectPath = process.argv[3] || process.cwd();
  const cmd = process.argv[2];
  const mem = new ProjectMemory(projectPath);
  
  switch(cmd) {
    case 'init':
      console.log(JSON.stringify(mem.status(), null, 2));
      break;
    case 'status':
      console.log(JSON.stringify(mem.status(), null, 2));
      break;
    case 'log':
      mem.sensoryLog({ msg: process.argv.slice(3).join(' ') });
      console.log('[OK] Logged to L0');
      break;
    case 'task':
      mem.workingAddTask(process.argv.slice(3).join(' '));
      console.log('[OK] Task added to L1');
      break;
    case 'goal':
      mem.workingAddGoal(process.argv.slice(3).join(' '));
      console.log('[OK] Goal added to L1');
      break;
    case 'insight':
      mem.workingAddInsight(process.argv.slice(3).join(' '));
      console.log('[OK] Insight added to L1');
      break;
    case 'remember': {
      const [k, ...v] = process.argv.slice(3);
      mem.semanticSet(k, v.join(' '));
      console.log('[OK] Saved to L3:', k);
      break;
    }
    case 'identity': {
      const [k, ...v] = process.argv.slice(3);
      mem.identitySet(k, v.join(' '));
      console.log('[OK] Saved to L4:', k);
      break;
    }
    case 'promote': {
      const promoted = mem.autoPropagate();
      console.log(`[OK] Auto-promoted ${promoted.length} items:`);
      promoted.forEach(p => console.log(`  ${p.layer}: ${p.key}`));
      break;
    }
    case 'os-status': {
      const os = getOSState();
      console.log('OS-Level Global State:');
      console.log(JSON.stringify(os, null, 2));
      break;
    }
    default:
      console.log(`
Usage: project-memory.cjs <command> [project-path]

Commands:
  init                  Initialize project memory structure
  status                Show all layers status
  log <msg>             Log to L0 (sensory)
  task <desc>           Add task to L1 (working)
  goal <desc>           Add goal to L1 (working)
  insight <text>        Add insight to L1 (working)
  remember <key> <val>  Save to L3 (semantic)
  identity <key> <val>  Save to L4 (identity)
  promote               Auto-promote between layers
  os-status             Show OS-level global state
      `);
  }
}

if (require.main === module) main();
module.exports = ProjectMemory;
