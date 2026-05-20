#!/usr/bin/env node
/**
 * team-share.cjs — Anonymized Team Sharing (SLIM)
 * Usage: node team-share.cjs [share|learn|list|fetch|stats]
 */
'use strict';
const fs = require('fs'), path = require('path'), crypto = require('crypto');
const CCDEW_PATH = '/home/think/CCDEW';
const SHARED_DIR = path.join(CCDEW_PATH, '.claude-flow/team');
const ANON_DIR = path.join(SHARED_DIR, 'anonymous');
const CONFIG_FILE = path.join(SHARED_DIR, 'config.json');

function ensureDirs() {
  if (!fs.existsSync(SHARED_DIR)) fs.mkdirSync(SHARED_DIR, { recursive: true });
  if (!fs.existsSync(ANON_DIR)) fs.mkdirSync(ANON_DIR, { recursive: true });
  if (!fs.existsSync(CONFIG_FILE)) {
    fs.writeFileSync(CONFIG_FILE, JSON.stringify({
      enabled: true, share_learning: true, share_patterns: true, anonymize: true, team_id: 'team_' + crypto.randomBytes(4).toString('hex')
    }, null, 2));
  }
}

function anonymize(pattern) {
  return { id: crypto.randomBytes(8).toString('hex'), type: pattern.type || 'unknown', category: pattern.category || 'general', success_rate: pattern.success_rate || 0, tags: (pattern.tags || []).filter(t => !['user','name','email','token','key','secret','password','project','workspace'].some(s => t.toLowerCase().includes(s))), timestamp: new Date().toISOString() };
}

function sharePattern(pattern) {
  ensureDirs();
  const anon = anonymize(pattern);
  fs.writeFileSync(path.join(ANON_DIR, anon.id + '.json'), JSON.stringify(anon, null, 2));
  const idx = path.join(SHARED_DIR, 'index.json');
  let index = [];
  try { if (fs.existsSync(idx)) index = JSON.parse(fs.readFileSync(idx, 'utf-8')); } catch {}
  index.push({ id: anon.id, type: anon.type, category: anon.category, timestamp: anon.timestamp, success_rate: anon.success_rate });
  if (index.length > 100) index = index.slice(-100);
  fs.writeFileSync(idx, JSON.stringify(index, null, 2));
  console.log('Shared: ' + anon.id + ' (' + anon.type + ')');
}

function listPatterns() {
  ensureDirs();
  const idx = path.join(SHARED_DIR, 'index.json');
  let index = [];
  try { if (fs.existsSync(idx)) index = JSON.parse(fs.readFileSync(idx, 'utf-8')); } catch {}
  if (index.length === 0) { console.log('No patterns shared'); return; }
  console.log('\n' + index.length + ' patterns:\n');
  index.slice(-20).reverse().forEach(p => console.log(p.id.slice(0,16) + '.. | ' + p.type + ' | ' + p.category + ' | ' + (p.success_rate || 0) + '%'));
}

function shareFromLearning() {
  const f = path.join(CCDEW_PATH, '.claude-flow/data/learning.jsonl');
  if (!fs.existsSync(f)) { console.log('No learning entries'); return; }
  const lines = fs.readFileSync(f, 'utf-8').trim().split('\n').filter(l => l.trim());
  if (lines.length === 0) { console.log('No learning'); return; }
  const last = JSON.parse(lines[lines.length - 1]);
  sharePattern({ type: 'workflow', category: last.workflow || 'general', description: 'Workflow pattern', success_rate: 80, tags: ['workflow','learning'] });
}

function stats() {
  ensureDirs();
  const idx = path.join(SHARED_DIR, 'index.json');
  let index = [];
  try { if (fs.existsSync(idx)) index = JSON.parse(fs.readFileSync(idx, 'utf-8')); } catch {}
  const cfg = JSON.parse(fs.readFileSync(CONFIG_FILE, 'utf-8'));
  console.log('\nTeam ID: ' + cfg.team_id);
  console.log('Total shared: ' + index.length);
  console.log('By type:', Object.entries(index.reduce((acc, p) => { acc[p.type] = (acc[p.type] || 0) + 1; return acc; }, {})).map(([k,v]) => k + ':' + v).join(', '));
}

function main() {
  const args = process.argv.slice(2), cmd = args[0];
  if (!cmd) { console.log('share|learn|list|fetch|stats'); return; }
  if (cmd === 'share') { try { sharePattern(JSON.parse(args.slice(1).join(' '))); } catch(e) { console.log('Invalid JSON: ' + e.message); } }
  else if (cmd === 'learn') shareFromLearning();
  else if (cmd === 'list') listPatterns();
  else if (cmd === 'fetch') console.log('Simulated fetch (needs team server)');
  else if (cmd === 'stats') stats();
  else console.log('Unknown: ' + cmd);
}

if (require.main === module) main();
module.exports = { anonymize, sharePattern, listPatterns, shareFromLearning, stats };