'use strict';
/**
 * Secret-leak scanner — checks file content + path before Write/Edit.
 * Inspired by Red Hat's claude-code-setup-evaluator hooks.
 * Returns { safe: true } or { safe: false, reason, matches }.
 */

const path = require('path');

const SENSITIVE_PATHS = [
  /\.env(\.|$)/i,
  /credentials?\.(json|ya?ml)$/i,
  /secrets?\.(json|ya?ml|env)$/i,
  /private[_-]?key/i,
  /id_rsa$/,
  /\.pem$/i,
  /\.pfx$/i,
  /\.p12$/i,
];

const SECRET_PATTERNS = [
  { name: 'AWS Access Key',          re: /AKIA[0-9A-Z]{16}/ },
  { name: 'AWS Secret Key',          re: /aws_secret_access_key\s*=\s*['"]?[A-Za-z0-9/+=]{40}['"]?/i },
  { name: 'Anthropic API Key',       re: /sk-ant-[a-zA-Z0-9_-]{20,}/ },
  { name: 'OpenAI API Key',          re: /sk-(?!ant-)[a-zA-Z0-9]{20,}/ },
  { name: 'GitHub PAT',              re: /(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}/ },
  { name: 'Google API Key',          re: /AIza[0-9A-Za-z_-]{35}/ },
  { name: 'Stripe Live Key',         re: /sk_live_[0-9a-zA-Z]{24,}/ },
  { name: 'Slack Bot Token',         re: /xox[baprs]-[0-9]{10,}-[0-9]{10,}-[a-zA-Z0-9]{24,}/ },
  { name: 'Generic Bearer Token',    re: /bearer\s+[a-zA-Z0-9._-]{32,}/i },
  { name: 'Private Key Block',       re: /-----BEGIN (RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----/ },
  { name: 'Password Assignment',     re: /(?:^|\s)(password|passwd|pwd)\s*[:=]\s*['"][^'"\s]{8,}['"]/i },
];

function isSensitivePath(filePath) {
  if (!filePath) return false;
  const base = path.basename(filePath);
  return SENSITIVE_PATHS.some(re => re.test(base));
}

function scanContent(content) {
  if (!content || typeof content !== 'string') return [];
  const matches = [];
  for (const { name, re } of SECRET_PATTERNS) {
    const m = content.match(re);
    if (m) matches.push({ pattern: name, sample: m[0].slice(0, 20) + (m[0].length > 20 ? '...' : '') });
  }
  return matches;
}

function check({ filePath, content }) {
  const reasons = [];
  if (filePath && isSensitivePath(filePath)) {
    reasons.push(`sensitive filename: ${path.basename(filePath)}`);
  }
  const matches = scanContent(content);
  if (matches.length > 0) {
    reasons.push(`${matches.length} secret pattern(s) detected: ${matches.map(m => m.pattern).join(', ')}`);
  }
  return reasons.length > 0
    ? { safe: false, reason: reasons.join(' | '), matches }
    : { safe: true };
}

module.exports = { check, isSensitivePath, scanContent };
