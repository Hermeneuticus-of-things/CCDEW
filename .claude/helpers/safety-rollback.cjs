#!/usr/bin/env node
'use strict';
/**
 * safety-rollback.cjs — Safety Layer + Rollback (Faza 2)
 *
 * Tracks state before operations and provides rollback capability.
 * Integrates with memory-layers for persistence.
 *
 * API:
 *   snapshot(filePath) → snapshotId
 *   rollback(snapshotId) → boolean
 *   listSnapshots() → array
 *   cleanup(maxAge) → removed count
 *   recordCommand(cmd, output) → id
 *   getLastCommands(n) → array
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const DATA_DIR = path.join(process.cwd(), '.claude-flow', 'data');
const SNAPSHOTS_DIR = path.join(DATA_DIR, 'snapshots');
const COMMANDS_LOG = path.join(DATA_DIR, 'commands.jsonl');
const MAX_SNAPSHOTS = 100;
const MAX_COMMANDS = 500;
const DEFAULT_MAX_AGE_MS = 24 * 3600000; // 24 hours

function ensureDir(p) {
  if (!fs.existsSync(p)) fs.mkdirSync(p, { recursive: true });
}

// ── File Snapshots ──────────────────────────────────────────────────────────
function snapshot(filePath) {
  if (!filePath || !fs.existsSync(filePath)) {
    return { ok: false, reason: 'File not found' };
  }

  ensureDir(SNAPSHOTS_DIR);

  const id = crypto.randomBytes(6).toString('hex');
  const content = fs.readFileSync(filePath, 'utf-8');
  const stat = fs.statSync(filePath);

  const snapshot = {
    id,
    filePath: path.resolve(filePath),
    content,
    size: stat.size,
    mtime: stat.mtimeMs,
    createdAt: new Date().toISOString(),
    hash: crypto.createHash('sha256').update(content).digest('hex'),
  };

  const snapshotPath = path.join(SNAPSHOTS_DIR, id + '.json');
  fs.writeFileSync(snapshotPath, JSON.stringify(snapshot, null, 2));

  // Trim old snapshots
  trimSnapshots();

  return { ok: true, id, filePath: snapshot.filePath, size: stat.size };
}

function rollback(snapshotId) {
  const snapshotPath = path.join(SNAPSHOTS_DIR, snapshotId + '.json');
  if (!fs.existsSync(snapshotPath)) {
    return { ok: false, reason: 'Snapshot not found' };
  }

  const snap = JSON.parse(fs.readFileSync(snapshotPath, 'utf-8'));

  if (!fs.existsSync(snap.filePath)) {
    return { ok: false, reason: 'Target file no longer exists' };
  }

  // Verify current file changed (no point rolling back if same)
  const currentContent = fs.readFileSync(snap.filePath, 'utf-8');
  const currentHash = crypto.createHash('sha256').update(currentContent).digest('hex');

  if (currentHash === snap.hash) {
    return { ok: false, reason: 'File unchanged — no rollback needed' };
  }

  // Save current state as pre-rollback snapshot
  const preRollbackId = snapshot(snap.filePath).id;

  // Restore
  fs.writeFileSync(snap.filePath, snap.content, 'utf-8');

  return {
    ok: true,
    id: snapshotId,
    filePath: snap.filePath,
    restoredSize: snap.size,
    preRollbackId,
  };
}

function getSnapshot(snapshotId) {
  const snapshotPath = path.join(SNAPSHOTS_DIR, snapshotId + '.json');
  if (!fs.existsSync(snapshotPath)) return null;
  const snap = JSON.parse(fs.readFileSync(snapshotPath, 'utf-8'));
  return { id: snap.id, filePath: snap.filePath, size: snap.size, createdAt: snap.createdAt, hash: snap.hash };
}

function listSnapshots(limit = 20) {
  if (!fs.existsSync(SNAPSHOTS_DIR)) return [];

  const files = fs.readdirSync(SNAPSHOTS_DIR)
    .filter(f => f.endsWith('.json'))
    .sort()
    .reverse()
    .slice(0, limit);

  return files.map(f => {
    const snap = JSON.parse(fs.readFileSync(path.join(SNAPSHOTS_DIR, f), 'utf-8'));
    return { id: snap.id, filePath: snap.filePath, size: snap.size, createdAt: snap.createdAt };
  });
}

function trimSnapshots() {
  if (!fs.existsSync(SNAPSHOTS_DIR)) return;

  const files = fs.readdirSync(SNAPSHOTS_DIR)
    .filter(f => f.endsWith('.json'))
    .sort();

  while (files.length > MAX_SNAPSHOTS) {
    const oldest = files.shift();
    fs.unlinkSync(path.join(SNAPSHOTS_DIR, oldest));
  }
}

function cleanup(maxAgeMs = DEFAULT_MAX_AGE_MS) {
  if (!fs.existsSync(SNAPSHOTS_DIR)) return 0;

  const cutoff = Date.now() - maxAgeMs;
  let removed = 0;

  for (const f of fs.readdirSync(SNAPSHOTS_DIR)) {
    if (!f.endsWith('.json')) continue;
    const snap = JSON.parse(fs.readFileSync(path.join(SNAPSHOTS_DIR, f), 'utf-8'));
    const created = new Date(snap.createdAt).getTime();
    if (created < cutoff) {
      fs.unlinkSync(path.join(SNAPSHOTS_DIR, f));
      removed++;
    }
  }

  return removed;
}

// ── Command Tracking ────────────────────────────────────────────────────────
function recordCommand(cmd, output, exitCode = 0) {
  ensureDir(DATA_DIR);

  const entry = {
    ts: new Date().toISOString(),
    cmd,
    output: output ? output.substring(0, 2000) : '',
    exitCode,
    id: crypto.randomBytes(4).toString('hex'),
  };

  fs.appendFileSync(COMMANDS_LOG, JSON.stringify(entry) + '\n', 'utf-8');

  // Trim if too large
  trimCommands();

  return entry.id;
}

function getLastCommands(n = 10) {
  if (!fs.existsSync(COMMANDS_LOG)) return [];

  const lines = fs.readFileSync(COMMANDS_LOG, 'utf-8').trim().split('\n').filter(Boolean);
  return lines.slice(-n).map(l => {
    try { return JSON.parse(l); } catch { return null; }
  }).filter(Boolean);
}

function trimCommands() {
  if (!fs.existsSync(COMMANDS_LOG)) return;

  const lines = fs.readFileSync(COMMANDS_LOG, 'utf-8').trim().split('\n').filter(Boolean);
  if (lines.length > MAX_COMMANDS) {
    fs.writeFileSync(COMMANDS_LOG, lines.slice(-MAX_COMMANDS).join('\n') + '\n', 'utf-8');
  }
}

// ── Pre-Edit Safety Check ───────────────────────────────────────────────────
function preEditCheck(filePath) {
  if (!filePath) return { ok: true };

  const resolved = path.resolve(filePath);
  const sensitive = [
    '.env', '.env.local', '.env.production',
    'id_rsa', 'id_ed25519', 'id_ecdsa',
    '.git/config',
    'credentials.json', 'secrets.json',
  ];

  const basename = path.basename(resolved);
  for (const s of sensitive) {
    if (basename === s || resolved.endsWith('/' + s)) {
      return { ok: false, reason: `Sensitive file: ${basename}` };
    }
  }

  // Auto-snapshot before edit
  if (fs.existsSync(resolved)) {
    const snap = snapshot(resolved);
    return { ok: true, snapshotId: snap.id };
  }

  return { ok: true };
}

// ── Status ──────────────────────────────────────────────────────────────────
function status() {
  const snapCount = fs.existsSync(SNAPSHOTS_DIR)
    ? fs.readdirSync(SNAPSHOTS_DIR).filter(f => f.endsWith('.json')).length
    : 0;

  const cmdCount = fs.existsSync(COMMANDS_LOG)
    ? fs.readFileSync(COMMANDS_LOG, 'utf-8').trim().split('\n').filter(Boolean).length
    : 0;

  const snapSize = fs.existsSync(SNAPSHOTS_DIR)
    ? fs.readdirSync(SNAPSHOTS_DIR).reduce((acc, f) => {
        if (!f.endsWith('.json')) return acc;
        return acc + fs.statSync(path.join(SNAPSHOTS_DIR, f)).size;
      }, 0)
    : 0;

  return {
    snapshots: { count: snapCount, size_bytes: snapSize, max: MAX_SNAPSHOTS },
    commands: { count: cmdCount, max: MAX_COMMANDS },
    limits: { max_age_hours: DEFAULT_MAX_AGE_MS / 3600000 },
  };
}

// ── CLI ─────────────────────────────────────────────────────────────────────
if (require.main === module) {
  const args = process.argv.slice(2);
  const cmd = args[0];

  switch (cmd) {
    case 'snapshot':
      const r = snapshot(args[1]);
      console.log(JSON.stringify(r, null, 2));
      break;

    case 'rollback':
      const rb = rollback(args[1]);
      console.log(JSON.stringify(rb, null, 2));
      break;

    case 'list':
      console.log(JSON.stringify(listSnapshots(parseInt(args[1]) || 20), null, 2));
      break;

    case 'cleanup':
      const removed = cleanup(parseInt(args[1]) ? parseInt(args[1]) * 3600000 : DEFAULT_MAX_AGE_MS);
      console.log(`Removed ${removed} old snapshots`);
      break;

    case 'commands':
      console.log(JSON.stringify(getLastCommands(parseInt(args[1]) || 10), null, 2));
      break;

    case 'pre-edit':
      console.log(JSON.stringify(preEditCheck(args[1]), null, 2));
      break;

    case 'status':
    default:
      console.log(JSON.stringify(status(), null, 2));
      break;
  }
}

module.exports = {
  snapshot, rollback, getSnapshot, listSnapshots, trimSnapshots, cleanup,
  recordCommand, getLastCommands, trimCommands,
  preEditCheck, status,
  SNAPSHOTS_DIR, COMMANDS_LOG,
};
