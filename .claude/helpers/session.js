#!/usr/bin/env node
/**
 * Claude Flow Session Manager
 * Handles session lifecycle: start, restore, end
 */

const fs = require('fs');
const path = require('path');

const SESSION_DIR = path.join(process.cwd(), '.claude-flow', 'sessions');
const SESSION_FILE = path.join(SESSION_DIR, 'current.json');

const commands = {
  start: () => {
    const sessionId = `session-${Date.now()}`;
    const session = {
      id: sessionId,
      startedAt: new Date().toISOString(),
      cwd: process.cwd(),
      context: {},
      metrics: {
        edits: 0,
        commands: 0,
        tasks: 0,
        errors: 0,
      },
    };

    fs.mkdirSync(SESSION_DIR, { recursive: true });
    fs.writeFileSync(SESSION_FILE, JSON.stringify(session, null, 2));

    console.log(`Session started: ${sessionId}`);
    return session;
  },

  restore: () => {
    if (!fs.existsSync(SESSION_FILE)) {
      console.log('No session to restore');
      return null;
    }

    let session;
    try { session = JSON.parse(fs.readFileSync(SESSION_FILE, 'utf-8')); }
    catch { console.log('[WARN] Corrupt session file — ignoring'); return null; }
    session.restoredAt = new Date().toISOString();
    fs.writeFileSync(SESSION_FILE, JSON.stringify(session, null, 2));

    console.log(`Session restored: ${session.id}`);
    return session;
  },

  end: () => {
    if (!fs.existsSync(SESSION_FILE)) {
      console.log('No active session');
      return null;
    }

    let session;
    try { session = JSON.parse(fs.readFileSync(SESSION_FILE, 'utf-8')); }
    catch { console.log('[WARN] Corrupt session file — ignoring'); return null; }
    session.endedAt = new Date().toISOString();
    session.duration = Date.now() - new Date(session.startedAt).getTime();

    // Archive session
    const archivePath = path.join(SESSION_DIR, `${session.id}.json`);
    fs.writeFileSync(archivePath, JSON.stringify(session, null, 2));
    fs.unlinkSync(SESSION_FILE);

    console.log(`Session ended: ${session.id}`);
    console.log(`Duration: ${Math.round(session.duration / 1000 / 60)} minutes`);
    console.log(`Metrics: ${JSON.stringify(session.metrics)}`);

    return session;
  },

  status: () => {
    if (!fs.existsSync(SESSION_FILE)) {
      console.log('No active session');
      return null;
    }

    let session;
    try { session = JSON.parse(fs.readFileSync(SESSION_FILE, 'utf-8')); }
    catch { console.log('[WARN] Corrupt session file — ignoring'); return null; }
    const duration = Date.now() - new Date(session.startedAt).getTime();

    console.log(`Session: ${session.id}`);
    console.log(`Started: ${session.startedAt}`);
    console.log(`Duration: ${Math.round(duration / 1000 / 60)} minutes`);
    console.log(`Metrics: ${JSON.stringify(session.metrics)}`);

    return session;
  },

  update: (key, value) => {
    if (!fs.existsSync(SESSION_FILE)) {
      console.log('No active session');
      return null;
    }

    let session;
    try { session = JSON.parse(fs.readFileSync(SESSION_FILE, 'utf-8')); }
    catch { console.log('[WARN] Corrupt session file — ignoring'); return null; }
    session.context[key] = value;
    session.updatedAt = new Date().toISOString();
    fs.writeFileSync(SESSION_FILE, JSON.stringify(session, null, 2));

    return session;
  },

  get: (key) => {
    if (!fs.existsSync(SESSION_FILE)) return null;
    try {
      let session;
    try { session = JSON.parse(fs.readFileSync(SESSION_FILE, 'utf-8')); }
    catch { console.log('[WARN] Corrupt session file — ignoring'); return null; }
      return key ? (session.context || {})[key] : session.context;
    } catch { return null; }
  },

  metric: (name) => {
    if (!fs.existsSync(SESSION_FILE)) {
      return null;
    }

    let session;
    try { session = JSON.parse(fs.readFileSync(SESSION_FILE, 'utf-8')); }
    catch { console.log('[WARN] Corrupt session file — ignoring'); return null; }
    if (session.metrics[name] !== undefined) {
      session.metrics[name]++;
      fs.writeFileSync(SESSION_FILE, JSON.stringify(session, null, 2));
    }

    return session;
  },
};

// CLI
const [,, command, ...args] = process.argv;

if (command && commands[command]) {
  commands[command](...args);
} else {
  console.log('Usage: session.js <start|restore|end|status|update|metric> [args]');
}

module.exports = commands;
