'use strict';
/**
 * Path safety — mitigates shell injection when execFileSync uses `shell:true`.
 * Validates a binary path doesn't contain shell metacharacters.
 *
 * Why: Node 22 blocks .cmd/.bat without shell:true (CVE-2024-27980), so we
 * had to opt back into shell mode. That re-opens injection if the path
 * itself contains `& ; | $ \` etc. — possible if PATH is attacker-controlled.
 */

const SHELL_METACHARS = /[&;|`$<>()'"!\r\n*?]/;

function isSafeBinaryPath(p) {
  if (!p || typeof p !== 'string') return false;
  if (p.length > 1024) return false;
  if (SHELL_METACHARS.test(p)) return false;
  return true;
}

function assertSafeBinaryPath(p) {
  if (!isSafeBinaryPath(p)) {
    const err = new Error(`Unsafe binary path (shell metachar detected): ${p}`);
    err.code = 'EUNSAFE_PATH';
    throw err;
  }
}

module.exports = { isSafeBinaryPath, assertSafeBinaryPath };
