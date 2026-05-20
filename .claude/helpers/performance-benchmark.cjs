#!/usr/bin/env node
/**
 * performance-benchmark.cjs — CCDEW Performance Testing
 * 
 * Tests:
 * - SSA efficiency (target <25% ratio)
 * - Hook handler load time
 * - Cache hit rate
 * - Memory usage
 * - API response times
 */

'use strict';

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const CCDEW_PATH = '/home/think/CCDEW';
const DATA_DIR = path.join(CCDEW_PATH, '.claude-flow/data');

console.log('═══════════════════════════════════════════════════════');
console.log('  CCDEW PERFORMANCE BENCHMARK');
console.log('═══════════════════════════════════════════════════════\n');

const results = {};

// ── SSA Performance ───────────────────────────────────────────────────────
function benchmarkSSA() {
  console.log('📊 SSA Performance');
  console.log('─────────────────────────────────────────────────────');
  
  const ssaStatsPath = path.join(DATA_DIR, 'ssa-stats.json');
  if (fs.existsSync(ssaStatsPath)) {
    const stats = JSON.parse(fs.readFileSync(ssaStatsPath, 'utf-8'));
    const ratio = stats.entries_total > 0 
      ? Math.round((stats.entries_saved / stats.entries_total) * 100) 
      : 0;
    
    results.ssa = {
      calls: stats.calls,
      ratio: ratio,
      target: 25,
      status: ratio <= 25 ? '✓ OK' : '⚠️ HIGH',
      entries_saved: stats.entries_saved,
      entries_total: stats.entries_total,
      chars_saved: stats.chars_saved,
      tokens_saved: stats.tokens_saved
    };
    
    console.log(`   Calls: ${stats.calls}`);
    console.log(`   Entries: ${stats.entries_saved}/${stats.entries_total} (${ratio}%)`);
    console.log(`   Target: <25% → Status: ${results.ssa.status}`);
    console.log(`   Chars saved: ${stats.chars_saved.toLocaleString()}`);
    console.log(`   Tokens saved: ${stats.tokens_saved.toLocaleString()}`);
  } else {
    console.log('   ⚠️  No SSA stats found');
    results.ssa = { status: 'NO_DATA', ratio: 0 };
  }
  
  console.log('');
}

// ── Hook Handler Performance ──────────────────────────────────────────────
function benchmarkHookHandler() {
  console.log('⚙️  Hook Handler Performance');
  console.log('─────────────────────────────────────────────────────');
  
  const hookPath = path.join(CCDEW_PATH, '.claude/helpers/hook-handler.cjs');
  const lines = fs.readFileSync(hookPath, 'utf-8').split('\n').length;
  
  // Test load time
  const start = Date.now();
  try {
    require(hookPath);
    const loadTime = Date.now() - start;
    
    results.hookHandler = {
      lines: lines,
      loadTime_ms: loadTime,
      status: loadTime < 100 ? '✓ FAST' : loadTime < 500 ? '⚠️ SLOW' : '❌ TOO SLOW'
    };
    
    console.log(`   Lines: ${lines}`);
    console.log(`   Load time: ${loadTime}ms → ${results.hookHandler.status}`);
  } catch(e) {
    console.log(`   ❌ Load failed: ${e.message}`);
    results.hookHandler = { lines, loadTime: -1, status: 'ERROR' };
  }
  
  console.log('');
}

// ── Cache Performance ─────────────────────────────────────────────────────
function benchmarkCache() {
  console.log('💾 Cache Performance');
  console.log('─────────────────────────────────────────────────────');
  
  const cacheFiles = [
    'codeburn-cache.json',
    'safla.json',
    'circuit9.json',
    'ssa-stats.json',
    'session-critical-index.json'
  ];
  
  let hits = 0, misses = 0, totalSize = 0;
  
  for (const file of cacheFiles) {
    const p = path.join(DATA_DIR, file);
    if (fs.existsSync(p)) {
      hits++;
      const size = fs.statSync(p).size;
      totalSize += size;
      console.log(`   ✓ ${file}: ${(size/1024).toFixed(1)}KB`);
    } else {
      misses++;
      console.log(`   ✗ ${file}: MISSING`);
    }
  }
  
  results.cache = {
    hits, misses, totalSize,
    hitRate: (hits / (hits + misses) * 100).toFixed(0) + '%',
    totalSize_KB: (totalSize / 1024).toFixed(1)
  };
  
  console.log(`   \n   Hit rate: ${results.cache.hitRate}`);
  console.log(`   Total size: ${results.cache.totalSize_KB}KB`);
  console.log('');
}

// ── Memory Usage ──────────────────────────────────────────────────────────
function benchmarkMemory() {
  console.log('🧠 Memory Usage');
  console.log('─────────────────────────────────────────────────────');
  
  const mem = process.memoryUsage();
  const heapUsed = (mem.heapUsed / 1024 / 1024).toFixed(1);
  const heapTotal = (mem.heapTotal / 1024 / 1024).toFixed(1);
  const rss = (mem.rss / 1024 / 1024).toFixed(1);
  
  results.memory = {
    heapUsed_MB: heapUsed,
    heapTotal_MB: heapTotal,
    rss_MB: rss,
    status: heapUsed < 100 ? '✓ OK' : '⚠️ HIGH'
  };
  
  console.log(`   Heap: ${heapUsed}/${heapTotal}MB`);
  console.log(`   RSS: ${rss}MB`);
  console.log(`   Status: ${results.memory.status}`);
  console.log('');
}

// ── API Response Times ─────────────────────────────────────────────────────
function benchmarkAPI() {
  console.log('🌐 API Response Times');
  console.log('─────────────────────────────────────────────────────');
  
  const endpoints = [
    '/api/health',
    '/api/ccdew-stats',
    '/api/circuit9-status',
    '/api/workflow-status',
    '/api/profile-status'
  ];
  
  results.api = {};
  
  for (const ep of endpoints) {
    const start = Date.now();
    try {
      const child = spawn('curl', ['-s', '-o', '/dev/null', '-w', '%{time_total}', 
        `http://localhost:8765${ep}`], { timeout: 5000 });
      
      let time = 0;
      child.stdout.on('data', d => { time = parseFloat(d.toString()) || 0; });
      
      child.on('close', () => {
        const ms = Math.round(time * 1000);
        results.api[ep] = { time_ms: ms, status: ms < 100 ? '✓' : ms < 500 ? '⚠️' : '❌' };
        console.log(`   ${ep.padEnd(30)} ${ms.toString().padStart(4)}ms ${results.api[ep].status}`);
      });
    } catch(e) {
      results.api[ep] = { time_ms: -1, status: 'ERROR' };
      console.log(`   ${ep.padEnd(30)} ERROR`);
    }
  }
  
  console.log('');
}

// ── Module Sizes ──────────────────────────────────────────────────────────
function benchmarkModules() {
  console.log('📦 Module Sizes');
  console.log('─────────────────────────────────────────────────────');
  
  const modules = fs.readdirSync(path.join(CCDEW_PATH, '.claude/helpers'))
    .filter(f => f.endsWith('.cjs') && !f.includes('lib/'));
  
  const sizes = modules.map(m => {
    const p = path.join(CCDEW_PATH, '.claude/helpers', m);
    return { name: m, lines: fs.readFileSync(p, 'utf-8').split('\n').length };
  }).sort((a, b) => b.lines - a.lines);
  
  results.modules = {
    total: sizes.length,
    oversized: sizes.filter(m => m.lines > 500).length,
    small: sizes.filter(m => m.lines < 100).length
  };
  
  console.log(`   Total modules: ${sizes.length}`);
  console.log(`   Oversized (>500L): ${results.modules.oversized}`);
  console.log(`   Small (<100L): ${results.modules.small}`);
  console.log('   Top 5 largest:');
  
  for (const m of sizes.slice(0, 5)) {
    const flag = m.lines > 500 ? '⚠️' : '  ';
    console.log(`   ${flag} ${m.name}: ${m.lines}L`);
  }
  
  console.log('');
}

// ── Run All Benchmarks ────────────────────────────────────────────────────
console.log('Running benchmarks...\n');

benchmarkSSA();
benchmarkHookHandler();
benchmarkCache();
benchmarkMemory();
benchmarkModules();

setTimeout(() => {
  console.log('═══════════════════════════════════════════════════════');
  console.log('  SUMMARY');
  console.log('═══════════════════════════════════════════════════════\n');
  
  console.log(`SSA Efficiency: ${results.ssa?.ratio || 0}% (target <25%)`);
  console.log(`Hook Handler: ${results.hookHandler?.lines || '?'} lines, ${results.hookHandler?.loadTime_ms || '?'}ms`);
  console.log(`Cache: ${results.cache?.hitRate || '?'} hit rate, ${results.cache?.totalSize_KB || '?'}KB`);
  console.log(`Memory: ${results.memory?.heapUsed_MB || '?'}MB heap`);
  console.log(`Modules: ${results.modules?.total || '?'} total, ${results.modules?.oversized || '?'} oversized`);
  
  // Overall score
  let score = 100;
  if (results.ssa?.ratio > 25) score -= 10;
  if (results.hookHandler?.loadTime_ms > 500) score -= 20;
  if (results.cache?.hitRate !== '100%') score -= 5;
  if (results.memory?.status !== '✓ OK') score -= 15;
  if (results.modules?.oversized > 0) score -= 5;
  
  console.log(`\n📊 Overall Score: ${score}/100`);
  
  if (score >= 90) console.log('✅ EXCELLENT - System optimized');
  else if (score >= 70) console.log('⚠️  GOOD - Minor improvements possible');
  else console.log('❌ NEEDS WORK - Significant optimizations required');
  
  console.log('\n═══════════════════════════════════════════════════════\n');
  
  process.exit(0);
}, 2000);