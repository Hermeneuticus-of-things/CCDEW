#!/usr/bin/env node
'use strict';
const fs = require('fs');
const path = require('path');
const { writeAtomicJson } = require('./lib/atomic-write.cjs');

const DATA_DIR = path.join(process.cwd(), '.claude-flow', 'data');
const STORE = path.join(DATA_DIR, 'auto-memory-store.json');
const GRAPH = path.join(DATA_DIR, 'graph-state.json');
const RANKED = path.join(DATA_DIR, 'ranked-context.json');
const PENDING = path.join(DATA_DIR, 'pending-insights.jsonl');
const SESSION_DIR = path.join(process.cwd(), '.claude-flow', 'sessions');
const SESSION_FILE = path.join(SESSION_DIR, 'current.json');

const MAX_SIZE = 10 * 1024 * 1024;
const MAX_NODES = 5000;
const STOP = new Set(['the','a','an','is','are','was','were','be','been','have','has','had','do','does','did','will','would','could','should','to','of','in','for','on','with','at','by','from','as','into','and','but','or','if','when','which','who','this','that','it']);

const dirs = [path.join(require('os').homedir(), '.claude', 'projects'), path.join(process.cwd(), '.claude-flow', 'memory'), path.join(process.cwd(), '.claude', 'memory')];

function ensureDir() { if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true }); }
function readJSON(p) { try { const s = fs.statSync(p); if (s.size > MAX_SIZE) return null; } catch {} return fs.existsSync(p) ? JSON.parse(fs.readFileSync(p, 'utf8')) : null; }
function writeJSON(p, d) { ensureDir(); writeAtomicJson(p, d); }
function tok(text) { if (!text) return []; return text.toLowerCase().replace(/[^a-z0-9\s-]/g, ' ').split(/\s+/).filter(w => w.length > 2 && !STOP.has(w)); }
function trigrams(words) { const t = new Set(); for (const w of words) for (let i = 0; i <= w.length - 3; i++) t.add(w.slice(i, i + 3)); return t; }
function jaccard(a, b) { if (!a.size && !b.size) return 0; let inter = 0; for (const x of a) if (b.has(x)) inter++; return inter / (a.size + b.size - inter); }
function dedup(entries) { if (!entries || !Array.isArray(entries)) return entries; const seen = new Map(); for (const e of entries) seen.set(e.id || e.key || ('__' + seen.size), e); return Array.from(seen.values()); }
function sessionGet(key) { try { if (!fs.existsSync(SESSION_FILE)) return null; const s = JSON.parse(fs.readFileSync(SESSION_FILE, 'utf8')); return key ? (s.context || {})[key] : s.context; } catch { return null; } }
function sessionSet(key, val) { try { if (!fs.existsSync(SESSION_DIR)) fs.mkdirSync(SESSION_DIR, { recursive: true }); let s = fs.existsSync(SESSION_FILE) ? JSON.parse(fs.readFileSync(SESSION_FILE, 'utf8')) : {}; if (!s.context) s.context = {}; s.context[key] = val; s.updatedAt = new Date().toISOString(); fs.writeFileSync(SESSION_FILE, JSON.stringify(s, null, 2), 'utf8'); } catch {} }

function pagerank(nodes, edges, d, maxI) {
  d = d || 0.85; maxI = maxI || 30;
  const ids = Object.keys(nodes), n = ids.length;
  if (!n) return {};
  const outL = {}, inL = {};
  for (const id of ids) { outL[id] = []; inL[id] = []; }
  for (const e of edges) { if (outL[e.sourceId]) outL[e.sourceId].push(e.targetId); if (inL[e.targetId]) inL[e.targetId].push(e.sourceId); }
  const ranks = {}; for (const id of ids) ranks[id] = 1/n;
  for (let iter = 0; iter < maxI; iter++) {
    let dangling = 0; for (const id of ids) if (!outL[id].length) dangling += ranks[id];
    const newR = {}; let diff = 0;
    for (const id of ids) {
      let sum = 0; for (const src of inL[id]) { const cnt = outL[src].length; if (cnt > 0) sum += ranks[src] / cnt; }
      newR[id] = (1 - d) / n + d * (sum + dangling / n);
      diff += Math.abs(newR[id] - ranks[id]);
    }
    for (const id of ids) ranks[id] = newR[id];
    if (diff < 1e-6) break;
  }
  return ranks;
}

function buildEdges(entries) {
  const edges = [], byCat = {}, byFile = {};
  for (const e of entries) { const c = e.category || e.namespace || 'default'; if (!byCat[c]) byCat[c] = []; byCat[c].push(e); }
  for (const e of entries) { const f = e.metadata && e.metadata.sourceFile; if (f) { if (!byFile[f]) byFile[f] = []; byFile[f].push(e); } }
  for (const f of Object.keys(byFile)) { const g = byFile[f]; for (let i = 0; i < g.length - 1; i++) edges.push({ sourceId: g[i].id, targetId: g[i+1].id, type: 'temporal', weight: 0.5 }); }
  for (const c of Object.keys(byCat)) { const g = byCat[c]; for (let i = 0; i < g.length; i++) { const ta = trigrams(tok(g[i].content || g[i].summary || '')); for (let j = i+1; j < g.length; j++) { const tb = trigrams(tok(g[j].content || g[j].summary || '')); const sim = jaccard(ta, tb); if (sim > 0.3) edges.push({ sourceId: g[i].id, targetId: g[j].id, type: 'similar', weight: sim }); } } }
  return edges;
}

function bootstrap() {
  const entries = [];
  const cwd = process.cwd();
  for (const base of dirs) {
    if (!fs.existsSync(base)) continue;
    try {
      if (base.endsWith('projects')) {
        const slug = cwd.replace(/^\//, '').replace(/\//g, '-');
        const memDir = path.join(base, slug, 'memory');
        if (fs.existsSync(memDir)) { const files = fs.readdirSync(memDir).filter(f => f.endsWith('.md')); for (const file of files) { const content = fs.readFileSync(path.join(memDir, file), 'utf8'); if (!content.trim()) continue; const sections = content.split(/^##?\s+/m).filter(Boolean); for (let si = 0; si < sections.length; si++) { const lines = sections[si].trim().split('\n'); const title = lines[0].trim(); const body = lines.slice(1).join('\n').trim(); if (!body || body.length < 10) continue; const id = 'mem-' + file.replace('.md','') + '-' + title.replace(/[^a-z0-9]/gi,'-').toLowerCase().slice(0,30) + '-' + si; entries.push({ id, key: title.toLowerCase().replace(/[^a-z0-9]+/g,'-').slice(0,50), content: body.slice(0,500), summary: title, namespace: file === 'MEMORY.md' ? 'core' : file.replace('.md',''), type: 'semantic', metadata: { sourceFile: file, bootstrapped: true }, createdAt: Date.now() }); } } }
      } else {
        const files = fs.readdirSync(base).filter(f => f.endsWith('.md')); for (const file of files) { const content = fs.readFileSync(path.join(base, file), 'utf8'); if (!content.trim()) continue; const sections = content.split(/^##?\s+/m).filter(Boolean); for (let si = 0; si < sections.length; si++) { const lines = sections[si].trim().split('\n'); const title = lines[0].trim(); const body = lines.slice(1).join('\n').trim(); if (!body || body.length < 10) continue; const id = 'mem-' + file.replace('.md','') + '-' + title.replace(/[^a-z0-9]/gi,'-').toLowerCase().slice(0,30) + '-' + si; entries.push({ id, key: title.toLowerCase().replace(/[^a-z0-9]+/g,'-').slice(0,50), content: body.slice(0,500), summary: title, namespace: file === 'MEMORY.md' ? 'core' : file.replace('.md',''), type: 'semantic', metadata: { sourceFile: file, bootstrapped: true }, createdAt: Date.now() }); } }
      }
    } catch {}
  }
  return entries;
}

function buildGraph(store) {
  const nodes = {}; for (const e of store) { const id = e.id || e.key || 'entry-' + Math.random().toString(36).slice(2,8); e.id = id; nodes[id] = { id, category: e.namespace || e.type || 'default', confidence: (e.metadata && e.metadata.confidence) || 0.5, accessCount: (e.metadata && e.metadata.accessCount) || 0, createdAt: e.createdAt || Date.now() }; }
  const edges = buildEdges(store);
  const nodeCount = Object.keys(nodes).length;
  const pageRanks = nodeCount > MAX_NODES ? Object.fromEntries(Object.keys(nodes).map(id => [id, 1/nodeCount])) : pagerank(nodes, edges, 0.85, 30);
  return { version: 1, updatedAt: Date.now(), nodeCount: Object.keys(nodes).length, nodes, edges, pageRanks };
}

function buildRanked(store, graph) {
  const rankedEntries = store.map(e => { const id = e.id; const content = e.content || e.value || ''; const summary = e.summary || e.key || ''; const words = tok(content + ' ' + summary); return { id, content, summary, category: e.namespace || e.type || 'default', confidence: graph.nodes[id] ? graph.nodes[id].confidence : 0.5, pageRank: graph.pageRanks[id] || 0, accessCount: graph.nodes[id] ? graph.nodes[id].accessCount : 0, words }; }).sort((a, b) => (0.6 * a.pageRank + 0.4 * a.confidence) - (0.6 * b.pageRank + 0.4 * b.confidence));
  return { version: 1, computedAt: Date.now(), entries: rankedEntries };
}

function boost(ids, amount) {
  const ranked = readJSON(RANKED);
  if (!ranked || !ranked.entries) return;
  let changed = false;
  for (const e of ranked.entries) { if (ids.includes(e.id)) { e.confidence = Math.max(0, Math.min(1, (e.confidence || 0.5) + amount)); e.accessCount = (e.accessCount || 0) + 1; changed = true; } }
  if (changed) writeJSON(RANKED, ranked);
  const graph = readJSON(GRAPH);
  if (graph && graph.nodes) { for (const id of ids) { if (graph.nodes[id]) { graph.nodes[id].confidence = Math.max(0, Math.min(1, (graph.nodes[id].confidence || 0.5) + amount)); graph.nodes[id].accessCount = (graph.nodes[id].accessCount || 0) + 1; } } writeJSON(GRAPH, graph); }
}

function init() {
  ensureDir();
  const graphState = readJSON(GRAPH);
  let store = readJSON(STORE);
  if (!store || !Array.isArray(store) || !store.length) { const bootstrapped = bootstrap(); if (bootstrapped.length) { store = bootstrapped; writeJSON(STORE, store); } else return { nodes: 0, edges: 0, message: 'No memory entries' }; }
  const deduped = dedup(store);
  if (deduped.length < store.length) { writeJSON(STORE, deduped); store = deduped; }
  if (graphState && graphState.nodeCount === deduped.length && Date.now() - (graphState.updatedAt || 0) < 60000) return { nodes: graphState.nodeCount, edges: (graphState.edges || []).length, message: 'Cache hit' };
  const graph = buildGraph(store);
  const ranked = buildRanked(store, graph);
  writeJSON(GRAPH, graph);
  writeJSON(RANKED, ranked);
  return { nodes: Object.keys(graph.nodes).length, edges: graph.edges.length, message: 'Graph built' };
}

function getContext(prompt) {
  if (!prompt) return null;
  const ranked = readJSON(RANKED);
  if (!ranked || !ranked.entries || !ranked.entries.length) return null;
  const promptWords = tok(prompt);
  if (!promptWords.length) return null;
  const promptTrigrams = trigrams(promptWords);
  const scored = [];
  for (const e of ranked.entries) { const sim = jaccard(promptTrigrams, trigrams(e.words || [])); const score = 0.6 * sim + 0.4 * (e.pageRank || 0); if (score >= 0.05) scored.push({ ...e, score }); }
  if (!scored.length) return null;
  scored.sort((a, b) => b.score - a.score);
  const top = scored.slice(0, 5);
  const matchedIds = top.map(e => e.id);
  const prev = sessionGet('lastMatchedPatterns');
  sessionSet('lastMatchedPatterns', matchedIds);
  if (prev && Array.isArray(prev)) { const newSet = new Set(matchedIds); const toBoost = prev.filter(id => !newSet.has(id)); if (toBoost.length) boost(toBoost, 0.03); }
  const lines = ['[INTELLIGENCE] Relevant patterns:'];
  for (let i = 0; i < top.length; i++) lines.push('  * (' + top[i].score.toFixed(2) + ') ' + (top[i].summary || top[i].content || '').slice(0, 80) + ' [rank #' + (i+1) + ']');
  return lines.join('\n');
}

function recordEdit(file) {
  ensureDir();
  try { if (fs.existsSync(PENDING) && fs.statSync(PENDING).size > 2 * 1024 * 1024) fs.renameSync(PENDING, PENDING + '.old'); } catch {}
  const entry = JSON.stringify({ type: 'edit', file: file || 'unknown', timestamp: Date.now(), sessionId: sessionGet('sessionId') });
  fs.appendFileSync(PENDING, entry + '\n', 'utf8');
}

function feedback(success) {
  const matched = sessionGet('lastMatchedPatterns');
  if (matched && Array.isArray(matched)) boost(matched, success ? 0.05 : -0.02);
}

function consolidate() {
  ensureDir();
  let store = readJSON(STORE);
  if (!store || !Array.isArray(store)) return { entries: 0, edges: 0, message: 'No store' };
  store = dedup(store);
  let newEntries = 0;
  if (fs.existsSync(PENDING)) {
    const lines = fs.readFileSync(PENDING, 'utf8').trim().split('\n').filter(Boolean);
    const counts = {};
    for (const line of lines) { try { const i = JSON.parse(line); if (i.file) counts[i.file] = (counts[i.file] || 0) + 1; } catch {} }
    for (const [file, count] of Object.entries(counts)) {
      if (count >= 3 && !store.some(e => e.metadata && e.metadata.sourceFile === file && e.metadata.autoGenerated)) {
        store.push({ id: 'insight-' + Date.now() + '-' + Math.random().toString(36).slice(2,6), key: 'frequent-edit-' + path.basename(file), content: 'File ' + file + ' edited ' + count + ' times this session.', summary: 'Frequently edited: ' + path.basename(file) + ' (' + count + 'x)', namespace: 'insights', type: 'procedural', metadata: { sourceFile: file, editCount: count, autoGenerated: true }, createdAt: Date.now() });
        newEntries++;
      }
    }
    fs.writeFileSync(PENDING, '', 'utf8');
  }
  const graph = readJSON(GRAPH);
  if (graph && graph.nodes) { const now = Date.now(); for (const id of Object.keys(graph.nodes)) { const n = graph.nodes[id]; const hrs = (now - (n.createdAt || now)) / 3600000; if (!n.accessCount && hrs > 24) n.confidence = Math.max(0.05, (n.confidence || 0.5) - 0.005 * Math.floor(hrs / 24)); } }
  for (const e of store) { if (!e.id) e.id = 'entry-' + Math.random().toString(36).slice(2,8); }
  const newGraph = buildGraph(store);
  const ranked = buildRanked(store, newGraph);
  writeJSON(GRAPH, newGraph);
  writeJSON(RANKED, ranked);
  if (newEntries) writeJSON(STORE, store);
  return { entries: store.length, edges: newGraph.edges.length, newEntries, message: 'Consolidated' };
}

function stats(json) {
  const graph = readJSON(GRAPH) || {};
  const ranked = readJSON(RANKED) || {};
  const nodes = graph.nodes ? Object.keys(graph.nodes).length : 0;
  const edges = (graph.edges || []).length;
  const confs = graph.nodes ? Object.values(graph.nodes).map(n => n.confidence || 0.5) : [];
  confs.sort((a, b) => a - b);
  const pr = graph.pageRanks || {};
  const prSum = Object.values(pr).reduce((s, v) => s + v, 0);
  const top = (ranked.entries || []).slice(0, 10).map((e, i) => ({ rank: i+1, summary: (e.summary || '').slice(0, 60), score: (0.6 * (e.pageRank || 0) + 0.4 * (e.confidence || 0.5)).toFixed(4) }));
  if (json) { console.log(JSON.stringify({ nodes, edges, confMean: confs.length ? (confs.reduce((s, c) => s + c, 0) / confs.length).toFixed(4) : 0, prSum: prSum.toFixed(4), topPatterns: top }, null, 2)); return; }
  console.log('+--------------------------------------------------------------+');
  console.log('|  Intelligence Diagnostics (ADR-050)                           |');
  console.log('+--------------------------------------------------------------+');
  console.log('  Nodes: ' + nodes + ' | Edges: ' + edges + ' | PR sum: ' + prSum.toFixed(4));
  if (confs.length) console.log('  Confidence: min=' + confs[0].toFixed(3) + ' max=' + confs[confs.length-1].toFixed(3) + ' mean=' + (confs.reduce((s, c) => s + c, 0) / confs.length).toFixed(3));
  if (top.length) { console.log(''); console.log('  Top Patterns:'); for (const p of top) console.log('    #' + p.rank + ' ' + p.summary + ' [' + p.score + ']'); }
  console.log('+--------------------------------------------------------------+');
}

module.exports = { init, getContext, recordEdit, feedback, consolidate, stats };

if (require.main === module) {
  const cmd = process.argv[2];
  if (cmd === 'init') { const r = init(); console.log(JSON.stringify(r)); }
  else if (cmd === 'stats') stats(process.argv.includes('--json'));
  else if (cmd === 'consolidate') { const r = consolidate(); console.log(JSON.stringify(r)); }
  else console.log('Usage: intelligence.cjs <stats|init|consolidate> [--json]');
}