'use strict';

const ENNEAGRAM_NODE_RE = /^[1-9]$/;

function isValidNodeId(nodeId) {
  return ENNEAGRAM_NODE_RE.test(String(nodeId));
}

function asString(v, max = 80) {
  if (v == null) return '';
  const s = typeof v === 'string' ? v : (typeof v === 'number' ? String(v) : '');
  return s.substring(0, max);
}

function clampNumber(v, min, max) {
  const n = Number(v);
  if (!Number.isFinite(n)) return min;
  return Math.max(min, Math.min(max, n));
}

module.exports = { isValidNodeId, asString, clampNumber };
