'use strict';
/**
 * Lightweight version-migration framework for JSON state files.
 *
 * Usage:
 *   const { migrate } = require('./migrate.cjs');
 *   const data = migrate(rawObject, 'safla', [
 *     { from: '1.0', to: '2.0', up: (d) => ({...d, version:'2.0', sessions: d.sessions || 0}) },
 *   ]);
 *
 * Each step's `up()` MUST set d.version to its `to` value and return the new object.
 */

function migrate(data, schemaName, steps) {
  if (!data || typeof data !== 'object') return data;
  if (!Array.isArray(steps)) return data;

  let current = data;
  let safety = 32;
  while (safety-- > 0) {
    const v = current.version || '0.0';
    const step = steps.find(s => s.from === v);
    if (!step) break;
    try {
      current = step.up(current);
      if (!current || current.version !== step.to) {
        throw new Error(`migration ${schemaName} ${step.from}→${step.to} did not set version`);
      }
    } catch (e) {
      try { require('./error-log.cjs').logError(`migrate.${schemaName}`, e); } catch {}
      break;
    }
  }
  return current;
}

function isCurrentVersion(data, version) {
  return data && data.version === version;
}

module.exports = { migrate, isCurrentVersion };
