'use strict';
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const BASE = path.join(process.cwd(), '.claude-flow');
const DATA = path.join(BASE, 'data');
const MEM  = path.join(BASE, '..', '_MEMORY');

const PATHS = {
  L4: path.join(MEM, 'identity'),           // permanent
  L3: path.join(MEM, 'semantic'),            // slow decay
  L2: path.join(BASE, 'sessions'),           // moderate decay
  L1: path.join(DATA, 'working.json'),       // fast decay
  L0: path.join(DATA, 'sensory.jsonl'),      // immediate
};

const DECAY = { L4: 0, L3: 30, L2: 14, L1: 3, L0: 0.04 }; // days
const MAX_L0 = 5 * 1024 * 1024; // 5MB

// ── Encryption Key (derived from workspace) ──────────────────────────────────
// Key changes per workspace — protects against cross-project leaks
const ENC_KEY = crypto.createHash('sha256').update(process.cwd() + '-ccdew-v3.9.8').digest().slice(0, 32);
const ENC_IV = crypto.createHash('sha256').update(process.cwd() + '-iv').digest().slice(0, 16);

function ensureDir(p) { if (!fs.existsSync(p)) fs.mkdirSync(p, { recursive: true }); }
function readJSON(p) { return fs.existsSync(p) ? JSON.parse(fs.readFileSync(p, 'utf8')) : null; }
function writeJSON(p, d) { ensureDir(path.dirname(p)); fs.writeFileSync(p, JSON.stringify(d, null, 2), 'utf8'); }

// ── Security: Encrypt/Decrypt (AES-256-GCM) ───────────────────────────────────
function encrypt(plaintext) {
  if (!plaintext) return '';
  try {
    const cipher = crypto.createCipheriv('aes-256-gcm', ENC_KEY, ENC_IV);
    let enc = cipher.update(String(plaintext), 'utf8', 'hex');
    enc += cipher.final('hex');
    const auth = cipher.getAuthTag().toString('hex');
    return enc + ':' + auth;
  } catch { return plaintext; }
}

function decrypt(ciphertext) {
  if (!ciphertext || !ciphertext.includes(':')) return ciphertext;
  try {
    const [enc, auth] = ciphertext.split(':');
    const decipher = crypto.createDecipheriv('aes-256-gcm', ENC_KEY, ENC_IV);
    decipher.setAuthTag(Buffer.from(auth, 'hex'));
    let dec = decipher.update(enc, 'hex', 'utf8');
    dec += decipher.final('utf8');
    return dec;
  } catch { return ciphertext; }
}

function mask(value, showLast = 4) {
  if (!value) return '';
  const s = String(value);
  if (s.length <= showLast) return '******';
  return s.slice(0, 3) + '***' + s.slice(-showLast);
}

function isSensitive(key) {
  const patterns = ['key', 'token', 'secret', 'password', 'pass', 'api', 'auth', 'private', 'credential', 'access'];
  return patterns.some(p => key.toLowerCase().includes(p));
}

function autoProtect(obj) {
  if (typeof obj === 'string') return isSensitive(obj) ? '[PROTECTED]' : obj;
  if (Array.isArray(obj)) return obj.map(autoProtect);
  if (obj && typeof obj === 'object') {
    const result = {};
    for (const [k, v] of Object.entries(obj)) {
      result[k] = isSensitive(k) ? '[ENCRYPTED:' + encrypt(String(v)).slice(0, 32) + '...]' : autoProtect(v);
    }
    return result;
  }
  return obj;
}

function secureRead(obj, key) {
  if (!obj || typeof obj !== 'object') return obj;
  const val = obj[key];
  if (isSensitive(key) && val && typeof val === 'string' && val.startsWith('[ENCRYPTED:')) {
    const enc = val.replace('[ENCRYPTED:', '').replace('...]', '');
    return decrypt(enc);
  }
  return val;
}

// ── L4: Identity (permanent, zero decay) — AUTO-ENCRYPT sensitive ──────────────
function l4Get(key) {
  const p = path.join(PATHS.L4, key + '.json');
  const data = readJSON(p);
  if (!data) return null;
  if (data.protected && data.value) return decrypt(data.value);
  return data;
}
function l4Set(key, value, protect = null) {
  ensureDir(PATHS.L4);
  const p = path.join(PATHS.L4, key + '.json');
  const doProtect = protect !== null ? protect : isSensitive(key);
  const entry = {
    key,
    createdAt: Date.now(),
    updatedAt: Date.now(),
    layer: 'L4',
    protected: doProtect,
    value: doProtect ? encrypt(String(value)) : String(value),
  };
  fs.writeFileSync(p, JSON.stringify(entry, null, 2), 'utf8');
}
function l4List() {
  if (!fs.existsSync(PATHS.L4)) return [];
  return fs.readdirSync(PATHS.L4).filter(f => f.endsWith('.json')).map(f => f.replace('.json', ''));
}
function l4Delete(key) {
  const p = path.join(PATHS.L4, key + '.json');
  if (fs.existsSync(p)) fs.unlinkSync(p);
}

// ── L3: Semantic (slow decay ~30 days) — AUTO-ENCRYPT sensitive ────────────────
function l3Get(key) {
  const p = path.join(PATHS.L3, key + '.json');
  const data = readJSON(p);
  if (!data) return null;
  if (data.protected && data.value) return decrypt(data.value);
  return data;
}
function l3Set(key, value, decayDays = 30) {
  ensureDir(PATHS.L3);
  const p = path.join(PATHS.L3, key + '.json');
  const doProtect = isSensitive(key);
  const entry = {
    key,
    createdAt: Date.now(),
    expiresAt: Date.now() + decayDays * 86400000,
    layer: 'L3',
    protected: doProtect,
    value: doProtect ? encrypt(String(value)) : String(value),
  };
  fs.writeFileSync(p, JSON.stringify(entry, null, 2), 'utf8');
}
function l3List() {
  if (!fs.existsSync(PATHS.L3)) return [];
  return fs.readdirSync(PATHS.L3).filter(f => f.endsWith('.json')).map(f => f.replace('.json', ''));
}
function l3GC() {
  if (!fs.existsSync(PATHS.L3)) return 0;
  const now = Date.now();
  let removed = 0;
  for (const f of fs.readdirSync(PATHS.L3)) {
    if (!f.endsWith('.json')) continue;
    const data = readJSON(path.join(PATHS.L3, f));
    if (data && data.expiresAt && data.expiresAt < now) {
      fs.unlinkSync(path.join(PATHS.L3, f));
      removed++;
    }
  }
  return removed;
}

// ── L2: Episodic (moderate decay ~14 days) ─────────────────────────────────────
function l2Get(sessionId) {
  const p = path.join(PATHS.L2, sessionId + '.json');
  return readJSON(p);
}
function l2Save(sessionId, summary) {
  ensureDir(PATHS.L2);
  const p = path.join(PATHS.L2, sessionId + '.json');
  const entry = { sessionId, summary, createdAt: Date.now(), layer: 'L2' };
  fs.writeFileSync(p, JSON.stringify(entry, null, 2), 'utf8');
}
function l2List() {
  if (!fs.existsSync(PATHS.L2)) return [];
  return fs.readdirSync(PATHS.L2).filter(f => f.endsWith('.json')).map(f => f.replace('.json', ''));
}
function l2GC() {
  if (!fs.existsSync(PATHS.L2)) return 0;
  const now = Date.now();
  let removed = 0;
  for (const f of fs.readdirSync(PATHS.L2)) {
    if (!f.endsWith('.json')) continue;
    const data = readJSON(path.join(PATHS.L2, f));
    if (data && data.createdAt && (now - data.createdAt) > DECAY.L2 * 86400000) {
      fs.unlinkSync(path.join(PATHS.L2, f));
      removed++;
    }
  }
  return removed;
}

// ── L1: Working (fast decay ~3 days) ──────────────────────────────────────────
function l1Get() { return readJSON(PATHS.L1) || { tasks: [], goals: [], context: {} }; }
function l1Set(data) { writeJSON(PATHS.L1, data); }
function l1SetTask(task) {
  const d = l1Get();
  d.tasks = d.tasks || [];
  d.tasks.unshift({ task, createdAt: Date.now() });
  d.tasks = d.tasks.slice(0, 20); // max 20 tasks
  l1Set(d);
}
function l1SetGoal(goal) {
  const d = l1Get();
  d.goals = d.goals || [];
  d.goals.unshift({ goal, createdAt: Date.now() });
  d.goals = d.goals.slice(0, 10); // max 10 goals
  l1Set(d);
}
function l1Clear() { l1Set({ tasks: [], goals: [], context: {}, updatedAt: Date.now() }); }
function l1GC() {
  const now = Date.now();
  const d = l1Get();
  let changed = false;
  if (d.tasks) {
    const before = d.tasks.length;
    d.tasks = d.tasks.filter(t => (now - t.createdAt) < DECAY.L1 * 86400000);
    if (d.tasks.length !== before) changed = true;
  }
  if (d.goals) {
    const before = d.goals.length;
    d.goals = d.goals.filter(g => (now - g.createdAt) < DECAY.L1 * 86400000);
    if (d.goals.length !== before) changed = true;
  }
  if (changed) l1Set(d);
  return changed;
}

// ── L0: Sensory (immediate, ~1 hour) ──────────────────────────────────────────
function l0Append(entry) {
  ensureDir(path.dirname(PATHS.L0));
  try {
    if (fs.existsSync(PATHS.L0) && fs.statSync(PATHS.L0).size > MAX_L0) {
      fs.renameSync(PATHS.L0, PATHS.L0 + '.old');
    }
  } catch {}
  const line = JSON.stringify({ ...entry, ts: Date.now(), layer: 'L0' });
  fs.appendFileSync(PATHS.L0, line + '\n', 'utf8');
}
function l0Read(count = 50) {
  if (!fs.existsSync(PATHS.L0)) return [];
  const lines = fs.readFileSync(PATHS.L0, 'utf8').trim().split('\n').filter(Boolean);
  return lines.slice(-count).map(l => { try { return JSON.parse(l); } catch { return null; } }).filter(Boolean);
}
function l0Clear() {
  if (fs.existsSync(PATHS.L0)) fs.writeFileSync(PATHS.L0, '', 'utf8');
}
function l0GC() {
  if (!fs.existsSync(PATHS.L0)) return 0;
  const lines = fs.readFileSync(PATHS.L0, 'utf8').trim().split('\n').filter(Boolean);
  const cutoff = Date.now() - 3600000; // 1 hour
  const kept = lines.filter(l => { try { const e = JSON.parse(l); return !e.ts || e.ts > cutoff; } catch { return false; } });
  if (kept.length !== lines.length) { fs.writeFileSync(PATHS.L0, kept.join('\n') + '\n', 'utf8'); return lines.length - kept.length; }
  return 0;
}

// ── Unified GC ────────────────────────────────────────────────────────────────
function gc() {
  return { L3_removed: l3GC(), L2_removed: l2GC(), L1_removed: l1GC() ? 1 : 0, L0_removed: l0GC() };
}

// ── Status ────────────────────────────────────────────────────────────────────
function status() {
  const mk = (p) => fs.existsSync(p) ? fs.readdirSync(p).filter(f => f.endsWith('.json')).length : 0;
  const data = readJSON(PATHS.L1) || {};
  const l0Size = fs.existsSync(PATHS.L0) ? fs.statSync(PATHS.L0).size : 0;
  return {
    L4: { layer: 'Identity', decay: 'never', count: l4List().length, path: PATHS.L4 },
    L3: { layer: 'Semantic', decay: '30d', count: l3List().length, path: PATHS.L3 },
    L2: { layer: 'Episodic', decay: '14d', count: l2List().length, path: PATHS.L2 },
    L1: { layer: 'Working', decay: '3d', tasks: (data.tasks || []).length, goals: (data.goals || []).length },
    L0: { layer: 'Sensory', decay: '1h', size_bytes: l0Size, recent: l0Read(5).length },
  };
}

// ── Query (search across layers) — decrypts for display ───────────────────────
function query(keyword) {
  const results = [];
  const kw = keyword.toLowerCase();
  // L4
  for (const k of l4List()) {
    const raw = readJSON(path.join(PATHS.L4, k + '.json'));
    if (!raw) continue;
    const val = raw.protected ? '[ENCRYPTED]' : (raw.value || '');
    if (val.toLowerCase().includes(kw) || k.toLowerCase().includes(kw)) {
      results.push({ layer: 'L4', key: k, encrypted: raw.protected || false, match: raw.protected ? '[ENCRYPTED: ' + k + ']' : val.slice(0, 100) });
    }
  }
  // L3
  for (const k of l3List()) {
    const raw = readJSON(path.join(PATHS.L3, k + '.json'));
    if (!raw) continue;
    const val = raw.protected ? '[ENCRYPTED]' : (raw.value || '');
    if (val.toLowerCase().includes(kw) || k.toLowerCase().includes(kw)) {
      results.push({ layer: 'L3', key: k, encrypted: raw.protected || false, match: raw.protected ? '[ENCRYPTED: ' + k + ']' : val.slice(0, 100) });
    }
  }
  // L2
  for (const s of l2List()) { const d = l2Get(s); if (d && d.summary && JSON.stringify(d.summary).toLowerCase().includes(kw)) results.push({ layer: 'L2', sessionId: s, match: (d.summary || '').slice(0, 100) }); }
  // L1
  const wd = l1Get();
  const matchTasks = (wd.tasks || []).filter(t => (t.task || '').toLowerCase().includes(kw));
  const matchGoals = (wd.goals || []).filter(g => (g.goal || '').toLowerCase().includes(kw));
  if (matchTasks.length) results.push({ layer: 'L1', type: 'tasks', matches: matchTasks.map(t => t.task.slice(0, 80)) });
  if (matchGoals.length) results.push({ layer: 'L1', type: 'goals', matches: matchGoals.map(g => g.goal.slice(0, 80)) });
  return results;
}

// ── Promote: L0 → L1 → L2 → L3 ───────────────────────────────────────────────
function promote(id, from, to, value) {
  if (from === 'L0' && to === 'L1') l1SetTask(value);
  else if (from === 'L1' && to === 'L2') l2Save(id, value);
  else if (from === 'L2' && to === 'L3') l3Set(id, value, 30);
  else if (from === 'L3' && to === 'L4') l4Set(id, value);
}

// ── API for hook-handler ───────────────────────────────────────────────────────
const HANDLERS = {
  'memory-l4-get': (args) => { const r = l4Get(args[0]); console.log(r ? JSON.stringify(r, null, 2) : 'null'); },
  'memory-l4-set': (args) => { l4Set(args[0], args[1] || args.slice(1).join(' ')); console.log('[OK] L4 set: ' + args[0] + (isSensitive(args[0]) ? ' [ENCRYPTED]' : '')); },
  'memory-l3-set': (args) => { l3Set(args[0], args[1] || args.slice(1).join(' ')); console.log('[OK] L3 set: ' + args[0] + (isSensitive(args[0]) ? ' [ENCRYPTED]' : '')); },
  'memory-l1-task': (args) => { l1SetTask(args.join(' ')); console.log('[OK] L1 task added'); },
  'memory-l1-goal': (args) => { l1SetGoal(args.join(' ')); console.log('[OK] L1 goal added'); },
  'memory-l0': (args) => { l0Append({ msg: args.join(' ') }); console.log('[OK] L0 logged'); },
  'memory-query': (args) => { const r = query(args[0] || ''); console.log(JSON.stringify(r, null, 2)); },
  'memory-status': () => { const s = status(); console.log(JSON.stringify(s, null, 2)); },
  'memory-gc': () => { const r = gc(); console.log(JSON.stringify(r, null, 2)); },
  'memory-secure': (args) => { const val = args.slice(1).join(' '); console.log('Original: ' + val); console.log('Masked: ' + mask(val)); console.log('Encrypted: ' + encrypt(val)); },
};

function dispatch(cmd, args) {
  if (HANDLERS[cmd]) { HANDLERS[cmd](args); return; }
  console.log('Usage: memory-layers.cjs <' + Object.keys(HANDLERS).join('|') + '> [args]');
}

// ── CLI / Export ──────────────────────────────────────────────────────────────
module.exports = {
  // Core layers
  l4Get, l4Set, l4List, l3Get, l3Set, l3List,
  l2Get, l2Save, l2List, l1Get, l1Set, l1SetTask, l1SetGoal, l1Clear,
  l0Append, l0Read, l0Clear,
  // Operations
  promote, gc, status, query, dispatch,
  // Security
  encrypt, decrypt, mask, isSensitive, autoProtect, secureRead,
  // Constants
  PATHS, DECAY,
};

if (process.argv[1] && (process.argv[1] === __filename || process.argv[1].endsWith('memory-layers.cjs'))) {
  const [,, command, ...args] = process.argv;
  if (command) dispatch(command, args);
}