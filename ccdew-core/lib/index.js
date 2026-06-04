#!/usr/bin/env node
/**
 * ccdew-core/index.js — Main export
 * Load all modules from this single entry point
 */
'use strict';
const path = require('path');

const CORE_PATH = __dirname;

function load(name) {
  try { return require(path.join(CORE_PATH, 'lib', name + '.cjs')); }
  catch { return null; }
}

module.exports = {
  ssa: load('ssa'),
  safla: load('safla'),
  codeburn: load('codeburn'),
  intelligence: load('intelligence'),
  instincts: load('instincts'),
  autoProfile: load('auto-profile'),
  teamShare: load('team-share'),
  hookHandler: load('hook-handler'),
  
  // Libraries
  sharedUtils: load('shared-utils'),
  atomicWrite: load('atomic-write'),
  flags: load('flags'),
  errorLog: load('error-log'),
  fileLock: load('file-lock'),
  platform: load('platform'),
  pricing: load('pricing'),
};