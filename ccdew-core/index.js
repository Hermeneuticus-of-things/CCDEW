#!/usr/bin/env node
/**
 * ccdew-core — Entry point for external projects
 * Usage: const ccdew = require('ccdew-core');
 */
'use strict';
const path = require('path');

// Find ccdew-core location (could be in various places)
function findCCDEWCore() {
  const dirs = [
    __dirname,                                      // local
    path.join(process.env.HOME, 'CCDEW/ccdew-core'),
    path.join(process.env.HOME, 'ccdew-core'),
    '/usr/local/lib/node_modules/ccdew-core',
  ];
  
  for (const dir of dirs) {
    if (require('fs').existsSync(path.join(dir, 'lib', 'ssa.cjs'))) {
      return dir;
    }
  }
  return __dirname; // fallback to local
}

const CORE_DIR = findCCDEWCore();
const lib = path.join(CORE_DIR, 'lib');

function load(name) {
  try { return require(path.join(lib, name + '.cjs')); }
  catch { return null; }
}

module.exports = {
  version: '3.9.7',
  path: CORE_DIR,
  
  // Core modules
  ssa: load('ssa'),
  safla: load('safla'),
  codeburn: load('codeburn'),
  intelligence: load('intelligence'),
  instincts: load('instincts'),
  autoProfile: load('auto-profile'),
  teamShare: load('team-share'),
  hookHandler: load('hook-handler'),
  autoOptimize: load('auto-optimize'),
  redHat: load('red-hat-evaluator'),
  secretScan: load('secret-scan'),
  
  // Libraries
  sharedUtils: load('shared-utils'),
  atomicWrite: load('atomic-write'),
  flags: load('flags'),
  errorLog: load('error-log'),
  fileLock: load('file-lock'),
  platform: load('platform'),
  pricing: load('pricing'),
  strings: load('strings'),
  i18n: load('i18n'),
  
  // Helper: filter context using SSA
  filterContext: (prompt, entries) => {
    if (!module.exports.ssa) return entries;
    return module.exports.ssa.filterContext(prompt, entries);
  },
  
  // Helper: get stats
  getStats: () => {
    const stats = { ssa: null, safla: null, budget: 0 };
    if (module.exports.ssa) {
      const s = module.exports.ssa.getSSAEfficiency();
      stats.ssa = { ratio: s.ratio, entries: s.entries, status: s.status };
    }
    return stats;
  }
};