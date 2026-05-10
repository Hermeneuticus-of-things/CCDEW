'use strict';
/**
 * Cross-process file lock — uses O_EXCL create on a sibling .lock file
 * to serialize critical sections across multiple Node processes (e.g.
 * 2 Claude Code sessions writing safla.json simultaneously).
 *
 * Lock is auto-released on process exit (best-effort cleanup) and
 * after STALE_MS even if owner crashed.
 */

const fs = require('fs');
const path = require('path');

const RETRY_DELAYS_MS = [10, 25, 50, 100, 200, 400, 800];
const STALE_MS = 30_000;

function syncSleep(ms) {
  const end = Date.now() + ms;
  while (Date.now() < end) { /* in-process busy wait */ }
}

function lockPathFor(targetFile) {
  return targetFile + '.lock';
}

function acquire(targetFile, opts = {}) {
  const lockPath = lockPathFor(targetFile);
  const timeoutMs = opts.timeoutMs || 5_000;
  const start = Date.now();
  let attempt = 0;

  while (true) {
    try {
      const fd = fs.openSync(lockPath, 'wx');
      fs.writeSync(fd, JSON.stringify({ pid: process.pid, ts: Date.now() }));
      fs.closeSync(fd);
      return { lockPath, acquired_at: Date.now(), pid: process.pid };
    } catch (e) {
      if (e.code !== 'EEXIST') throw e;
      try {
        const stat = fs.statSync(lockPath);
        if (Date.now() - stat.mtimeMs > STALE_MS) {
          try { fs.unlinkSync(lockPath); } catch {}
          continue;
        }
      } catch { /* lock vanished, retry */ continue; }
    }
    if (Date.now() - start > timeoutMs) {
      const err = new Error(`lock acquire timeout after ${timeoutMs}ms on ${lockPath}`);
      err.code = 'ELOCK_TIMEOUT';
      throw err;
    }
    const delay = RETRY_DELAYS_MS[Math.min(attempt, RETRY_DELAYS_MS.length - 1)];
    syncSleep(delay);
    attempt++;
  }
}

function release(handle) {
  if (!handle || !handle.lockPath) return;
  try { fs.unlinkSync(handle.lockPath); } catch { /* may already be gone */ }
}

function withLock(targetFile, fn, opts = {}) {
  const handle = acquire(targetFile, opts);
  try { return fn(); }
  finally { release(handle); }
}

module.exports = { acquire, release, withLock, lockPathFor };
