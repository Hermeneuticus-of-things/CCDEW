#!/usr/bin/env node
'use strict';
/**
 * NLM Session Hook — Auto-check NLM auth at session start
 *
 * Implements anti-suspicion rules from _SETTINGS/RULES/nlm_anti_suspicion.md:
 *   - Check auth MAXIMUM once per session (NOT on every query)
 *   - NO --refresh or --keep-alive (triggers detection)
 *   - Throttle: ≥3s between queries
 *   - Single channel: one method per session
 *
 * Integration: Runs at SessionStart via hook-handler.cjs
 *
 * Usage:
 *   node nlm-session-hook.cjs        # Check + warn if invalid
 *   node nlm-session-hook.cjs --force # Force refresh auth
 *   node nlm-session-hook.cjs --check # Silent check, exit code only
 */

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const STATE_FILE = path.join(process.env.HERMES_MEMORY_DIR || '/home/think/.hermes/memories', 'nlm-session-state.json');

function readState() {
  try { return JSON.parse(fs.readFileSync(STATE_FILE, 'utf-8')); } catch { return null; }
}

function writeState(state) {
  fs.writeFileSync(STATE_FILE, JSON.stringify(state));
}

function isNewSession() {
  const state = readState();
  if (!state) return true;
  // New session if last check was >6h ago
  return (Date.now() - (state.last_check || 0)) > 6 * 60 * 60 * 1000;
}

function checkAuth() {
  try {
    const r = execSync('python3 .claude/scripts/nlm_auto_login.py --check --silent 2>&1', {
      encoding: 'utf-8',
      timeout: 15000,
      cwd: path.join(__dirname, '..'),
    });
    return { ok: true, output: r.trim() };
  } catch (e) {
    const msg = e.stderr?.trim() || e.message;
    // Exit code != 0 means auth invalid
    return { ok: false, output: msg };
  }
}

function forceLogin() {
  try {
    const r = execSync('python3 .claude/scripts/nlm_auto_login.py --force 2>&1', {
      encoding: 'utf-8',
      timeout: 60000,
      cwd: path.join(__dirname, '..'),
    });
    return { ok: r.includes('AUTH_REFRESHED_OK'), output: r.trim() };
  } catch (e) {
    return { ok: false, output: e.stderr?.trim() || e.message };
  }
}

function main() {
  const args = process.argv.slice(2);
  const isForce = args.includes('--force');
  const isCheck = args.includes('--check');

  // Anti-suspicion: check auth MAXIMUM once per session
  if (!isForce && !isNewSession()) {
    if (!isCheck) {
      console.log('[NLM Hook] Skipping auth check — already checked this session (anti-suspicion)');
    }
    process.exit(0);
  }

  const auth = isForce ? forceLogin() : checkAuth();

  // Update state
  writeState({
    last_check: Date.now(),
    session_id: process.env.HERMES_SESSION_ID || Date.now().toString(),
    ok: auth.ok,
  });

  if (!auth.ok && !isCheck) {
    console.warn(`[NLM Hook] ⚠ Auth invalid. Run manually: python3 .claude/scripts/nlm_auto_login.py --force`);
    console.warn(`[NLM Hook] Output: ${auth.output.slice(0, 200)}`);
    process.exit(1);
  }

  if (!isCheck) {
    console.log(`[NLM Hook] ✅ Auth ${auth.ok ? 'valid' : 'invalid'} — anti-suspicion pattern respected`);
    console.log(`[NLM Hook] Not checking again this session (max 1× per session)`);
  }

  process.exit(auth.ok ? 0 : 1);
}

main();
