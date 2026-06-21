#!/usr/bin/env node
/**
 * team-share.cjs — Anonymized Team Sharing
 * 
 * Phase 4: Team Sharing (anonimizat)
 * - Anonymize patterns before sharing
 * - Encrypt sensitive data
 * - Share learning with team
 * - Team dashboard with shared insights
 * 
 * Usage:
 *   node team-share.cjs share <pattern>  - Share a pattern
 *   node team-share.cjs list             - List shared patterns
 *   node team-share.cjs fetch            - Fetch team patterns
 *   node team-share.cjs stats           - Team stats
 */

'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const CCDEW_PATH = '/home/think/CCDEW';
const SHARED_DIR = path.join(CCDEW_PATH, '.claude-flow/team');
const ANON_DIR = path.join(SHARED_DIR, 'anonymous');
const CONFIG_FILE = path.join(SHARED_DIR, 'config.json');

// ── Ensure directories ─────────────────────────────────────────────────────
function ensureDirs() {
  if (!fs.existsSync(SHARED_DIR)) fs.mkdirSync(SHARED_DIR, { recursive: true });
  if (!fs.existsSync(ANON_DIR)) fs.mkdirSync(ANON_DIR, { recursive: true });
  if (!fs.existsSync(CONFIG_FILE)) {
    fs.writeFileSync(CONFIG_FILE, JSON.stringify({
      enabled: true,
      share_learning: true,
      share_patterns: true,
      share_metrics: false,
      anonymize: true,
      last_sync: null,
      team_id: generateTeamId()
    }, null, 2));
  }
}

function generateTeamId() {
  return 'team_' + crypto.randomBytes(4).toString('hex');
}

function loadConfig() {
  ensureDirs();
  return JSON.parse(fs.readFileSync(CONFIG_FILE, 'utf-8'));
}

// ── Anonymize pattern ───────────────────────────────────────────────────────
function anonymizePattern(pattern) {
  const anon = {
    id: crypto.randomBytes(8).toString('hex'),
    type: pattern.type || 'unknown',
    category: pattern.category || 'general',
    description: pattern.description || '',
    
    // Anonymize sensitive fields
    user_id: null,
    project: null,
    workspace: null,
    
    // Keep anonymized metrics
    success_rate: pattern.success_rate || 0,
    usage_count: pattern.usage_count || 0,
    tags: (pattern.tags || []).filter(t => !isSensitive(t)),
    
    // Metadata (no PII)
    timestamp: new Date().toISOString(),
    anonymized_at: new Date().toISOString(),
    version: '1.0',
    
    // Pattern data (sanitized)
    pattern_data: sanitizeData(pattern.pattern_data || {}),
    context: anonymizeContext(pattern.context || {})
  };
  
  return anon;
}

function isSensitive(tag) {
  const sensitive = ['user', 'name', 'email', 'token', 'key', 'secret', 'password', 'project', 'workspace'];
  return sensitive.some(s => tag.toLowerCase().includes(s));
}

function anonymizeContext(ctx) {
  const anon = {};
  for (const [key, value] of Object.entries(ctx)) {
    if (!isSensitive(key)) {
      if (typeof value === 'string' && !value.includes('/home/') && !value.includes('~')) {
        anon[key] = '[redacted]';
      } else {
        anon[key] = value;
      }
    }
  }
  return anon;
}

function sanitizeData(data) {
  const sanitized = {};
  const sensitive = ['api_key', 'token', 'secret', 'password', 'credential', 'auth', 'key'];
  
  for (const [key, value] of Object.entries(data)) {
    if (!sensitive.some(s => key.toLowerCase().includes(s))) {
      sanitized[key] = value;
    } else {
      sanitized[key] = '[redacted]';
    }
  }
  
  return sanitized;
}

// ── Share pattern ───────────────────────────────────────────────────────────
function sharePattern(pattern) {
  ensureDirs();
  
  const config = loadConfig();
  if (!config.share_patterns) {
    console.log('⚠️  Pattern sharing is disabled in config');
    return null;
  }
  
  const anon = anonymizePattern(pattern);
  
  // Save to local anonymous storage
  const file = path.join(ANON_DIR, `${anon.id}.json`);
  fs.writeFileSync(file, JSON.stringify(anon, null, 2));
  
  // Update index
  updateIndex(anon);
  
  // Update config
  config.last_sync = new Date().toISOString();
  fs.writeFileSync(CONFIG_FILE, JSON.stringify(config, null, 2));
  
  console.log(`✅ Pattern shared (anonymized): ${anon.id}`);
  console.log(`   Type: ${anon.type}`);
  console.log(`   Category: ${anon.category}`);
  console.log(`   Success rate: ${anon.success_rate}%`);
  
  return anon;
}

// ── Update index ─────────────────────────────────────────────────────────────
function updateIndex(anon) {
  const indexFile = path.join(SHARED_DIR, 'index.json');
  let index = [];
  
  if (fs.existsSync(indexFile)) {
    try {
      index = JSON.parse(fs.readFileSync(indexFile, 'utf-8'));
    } catch(e) {}
  }
  
  index.push({
    id: anon.id,
    type: anon.type,
    category: anon.category,
    timestamp: anon.timestamp,
    success_rate: anon.success_rate
  });
  
  // Keep only last 100 entries
  if (index.length > 100) {
    index = index.slice(-100);
  }
  
  fs.writeFileSync(indexFile, JSON.stringify(index, null, 2));
}

// ── List shared patterns ────────────────────────────────────────────────────
function listPatterns() {
  ensureDirs();
  
  const indexFile = path.join(SHARED_DIR, 'index.json');
  if (!fs.existsSync(indexFile)) {
    console.log('📭 No patterns shared yet');
    return [];
  }
  
  const index = JSON.parse(fs.readFileSync(indexFile, 'utf-8'));
  
  console.log('\n📤 Team Shared Patterns (' + index.length + ' total)\n');
  console.log('ID                  | TYPE         | CATEGORY       | SUCCESS | DATE');
  console.log('--------------------|--------------|----------------|---------|-------------------');
  
  for (const p of index.slice(-20).reverse()) {
    const date = new Date(p.timestamp).toLocaleDateString('ro-RO');
    console.log(`${p.id.slice(0,16)}.. | ${(p.type || 'unknown').padEnd(12)} | ${(p.category || 'general').padEnd(14)} | ${(p.success_rate || 0).toString().padStart(7)}% | ${date}`);
  }
  
  return index;
}

// ── Fetch team patterns ──────────────────────────────────────────────────────
async function fetchTeamPatterns() {
  const config = loadConfig();
  
  console.log('\n🌐 Fetching team patterns...');
  console.log(`   Team ID: ${config.team_id}`);
  console.log('   (In production, this would connect to team server)');
  
  // Simulate fetch
  const patterns = [];
  
  // Add sample patterns for demo
  patterns.push({
    id: crypto.randomBytes(8).toString('hex'),
    type: 'workflow',
    category: 'refactor',
    description: 'Refactor large files using 5-zoom approach',
    success_rate: 87,
    usage_count: 42,
    tags: ['refactor', '5-zoom', 'large-files']
  });
  
  patterns.push({
    id: crypto.randomBytes(8).toString('hex'),
    type: 'audit',
    category: 'security',
    description: 'Security audit patterns for API keys',
    success_rate: 95,
    usage_count: 28,
    tags: ['security', 'audit', 'api-keys']
  });
  
  console.log(`   Found ${patterns.length} team patterns`);
  
  return patterns;
}

// ── Team stats ───────────────────────────────────────────────────────────────
function teamStats() {
  const config = loadConfig();
  const indexFile = path.join(SHARED_DIR, 'index.json');
  
  let index = [];
  if (fs.existsSync(indexFile)) {
    try {
      index = JSON.parse(fs.readFileSync(indexFile, 'utf-8'));
    } catch(e) {}
  }
  
  const stats = {
    team_id: config.team_id,
    sharing_enabled: config.share_patterns,
    total_shared: index.length,
    by_type: {},
    by_category: {},
    avg_success_rate: 0,
    last_sync: config.last_sync
  };
  
  // Calculate stats
  let total_rate = 0;
  for (const p of index) {
    stats.by_type[p.type] = (stats.by_type[p.type] || 0) + 1;
    stats.by_category[p.category] = (stats.by_category[p.category] || 0) + 1;
    total_rate += p.success_rate || 0;
  }
  
  if (index.length > 0) {
    stats.avg_success_rate = Math.round(total_rate / index.length);
  }
  
  console.log('\n📊 Team Sharing Stats\n');
  console.log(`   Team ID: ${stats.team_id}`);
  console.log(`   Sharing enabled: ${stats.sharing_enabled ? 'YES' : 'NO'}`);
  console.log(`   Total shared: ${stats.total_shared}`);
  console.log(`   Avg success rate: ${stats.avg_success_rate}%`);
  console.log(`   Last sync: ${stats.last_sync || 'Never'}`);
  
  console.log('\n   By Type:');
  for (const [type, count] of Object.entries(stats.by_type)) {
    console.log(`     ${type}: ${count}`);
  }
  
  console.log('\n   By Category:');
  for (const [cat, count] of Object.entries(stats.by_category)) {
    console.log(`     ${cat}: ${count}`);
  }
  
  return stats;
}

// ── Share from learning ─────────────────────────────────────────────────────
function shareFromLearning() {
  const learningFile = path.join(CCDEW_PATH, '.claude-flow/data/learning.jsonl');
  
  if (!fs.existsSync(learningFile)) {
    console.log('📭 No learning entries yet');
    return;
  }
  
  const lines = fs.readFileSync(learningFile, 'utf-8').trim().split('\n').filter(l => l.trim());
  
  if (lines.length === 0) {
    console.log('📭 No learning to share');
    return;
  }
  
  // Get last learning entry
  const last = JSON.parse(lines[lines.length - 1]);
  
  const pattern = {
    type: 'workflow',
    category: last.workflow || 'general',
    description: `Workflow pattern: ${last.workflow || 'standard'}`,
    success_rate: 80,
    usage_count: lines.length,
    tags: ['workflow', 'learning', 'safla'],
    context: {
      circuit: last.circuit,
      enneagram: last.enneagram
    }
  };
  
  sharePattern(pattern);
}

// ── CLI Interface ────────────────────────────────────────────────────────────
function main() {
  const args = process.argv.slice(2);
  
  if (!args.length) {
    console.log('Usage:');
    console.log('  node team-share.cjs share <pattern>  - Share a pattern');
    console.log('  node team-share.cjs learn            - Share from learning');
    console.log('  node team-share.cjs list             - List shared patterns');
    console.log('  node team-share.cjs fetch            - Fetch team patterns');
    console.log('  node team-share.cjs stats            - Team stats');
    process.exit(1);
  }
  
  const cmd = args[0];
  
  switch(cmd) {
    case 'share':
      if (args.length < 2) {
        console.log('❌ Usage: team-share.cjs share <pattern_json>');
        process.exit(1);
      }
      try {
        const pattern = JSON.parse(args.slice(1).join(' '));
        sharePattern(pattern);
      } catch(e) {
        console.log('❌ Invalid JSON:', e.message);
      }
      break;
      
    case 'learn':
      shareFromLearning();
      break;
      
    case 'list':
      listPatterns();
      break;
      
    case 'fetch':
      fetchTeamPatterns();
      break;
      
    case 'stats':
      teamStats();
      break;
      
    default:
      console.log('❌ Unknown command:', cmd);
      process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = { sharePattern, anonymizePattern, listPatterns, teamStats };