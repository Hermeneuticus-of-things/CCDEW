'use strict';
/**
 * Remote backup advisor — checks that critical state has off-machine copy.
 * Doesn't push automatically (user owns the remote); just warns.
 */

const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

const WORK = process.cwd();
const ARCHIVE = path.join(WORK, '_ARCHIVE');

function gitInfo() {
  const r = spawnSync('git', ['remote', '-v'], {
    cwd: WORK, encoding: 'utf-8', timeout: 3000, stdio: ['ignore', 'pipe', 'ignore'],
  });
  if (r.status !== 0) return { has_git: false };
  const remotes = (r.stdout || '').trim().split('\n').filter(Boolean);
  if (remotes.length === 0) return { has_git: true, has_remote: false };
  return { has_git: true, has_remote: true, remotes };
}

function lastCommit() {
  const r = spawnSync('git', ['log', '-1', '--format=%H|%ai|%s'], {
    cwd: WORK, encoding: 'utf-8', timeout: 3000, stdio: ['ignore', 'pipe', 'ignore'],
  });
  if (r.status !== 0) return null;
  const [hash, date, ...rest] = (r.stdout || '').trim().split('|');
  return { hash: (hash || '').slice(0, 8), date, subject: rest.join('|') };
}

function archiveSize() {
  if (!fs.existsSync(ARCHIVE)) return { exists: false, bytes: 0 };
  let bytes = 0, files = 0;
  function walk(d) {
    for (const f of fs.readdirSync(d)) {
      const full = path.join(d, f);
      const stat = fs.statSync(full);
      if (stat.isDirectory()) walk(full);
      else { bytes += stat.size; files++; }
    }
  }
  try { walk(ARCHIVE); } catch {}
  return { exists: true, bytes, files };
}

function check() {
  const git = gitInfo();
  const arch = archiveSize();
  const issues = [];
  if (!git.has_git) {
    issues.push({ severity: 'WARN', msg: 'No git repo — workspace state is not version-controlled' });
  } else if (!git.has_remote) {
    issues.push({ severity: 'HIGH', msg: 'Git repo has no remote — disk failure = total loss', suggestion: 'git remote add origin <your-repo-url>' });
  }
  if (arch.exists && arch.files > 100) {
    issues.push({ severity: 'INFO', msg: `_ARCHIVE/ has ${arch.files} files / ${(arch.bytes / 1024 / 1024).toFixed(1)}MB — consider periodic prune` });
  }
  return { git, archive: arch, issues, last_commit: lastCommit() };
}

module.exports = { check, gitInfo, archiveSize, lastCommit };
