#!/usr/bin/env node
/**
 * CCDEW Memory Engine — Universal Markdown Format
 * 
 * Toate intrările de memorie sunt stocate ca fișiere .md cu YAML frontmatter.
 * Avantaje:
 *   - Citibile de orice LLM (Claude, GPT, Qwen, etc.)
 *   - Compatibile cu orice platformă (OpenCode, Claude Code, Cursor, etc.)
 *   - Editabile manual în orice editor
 *   - Versionabile cu git
 *   - Portable între sisteme
 * 
 * Format:
 *   ---
 *   uid: <unic-id>
 *   project: <slug>
 *   layer: <L0|L1|L2|L3|L4>
 *   type: <sensory|working|episodic|semantic|identity>
 *   created_at: <ISO-8601>
 *   tags: [tag1, tag2]
 *   confidence: <0-1>
 *   ---
 *   
 *   <conținut markdown>
 */

'use strict';
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const os = require('os');

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// UTILITARE YAML/MARKDOWN
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function generateUID() {
  const ts = new Date().toISOString().replace(/[-:T.Z]/g, '').slice(0, 14);
  const rand = crypto.randomBytes(4).toString('hex');
  return `ccdew-${ts}-${rand}`;
}

function parseYAML(frontmatter) {
  const result = {};
  let currentKey = null;
  let currentArray = null;
  
  frontmatter.split('\n').forEach(line => {
    line = line.trim();
    if (!line) return;
    
    // Array item
    if (line.startsWith('- ')) {
      if (currentArray) {
        currentArray.push(line.slice(2).trim());
      }
      return;
    }
    
    // Key: value
    const match = line.match(/^([a-zA-Z_][a-zA-Z0-9_]*):\s*(.*)$/);
    if (match) {
      const [, key, val] = match;
      const trimmed = val.trim();
      
      if (trimmed === '') {
        // Probabil array următor
        currentArray = [];
        result[key] = currentArray;
        currentKey = key;
      } else if (trimmed.startsWith('[') && trimmed.endsWith(']')) {
        // Inline array
        result[key] = trimmed.slice(1, -1).split(',').map(s => s.trim());
      } else if (trimmed === 'true') {
        result[key] = true;
      } else if (trimmed === 'false') {
        result[key] = false;
      } else if (!isNaN(Number(trimmed))) {
        result[key] = Number(trimmed);
      } else {
        result[key] = trimmed;
      }
      currentArray = null;
    }
  });
  
  return result;
}

function stringifyYAML(obj) {
  const lines = [];
  for (const [key, val] of Object.entries(obj)) {
    if (Array.isArray(val)) {
      lines.push(`${key}:`);
      val.forEach(item => lines.push(`  - ${item}`));
    } else if (typeof val === 'object' && val !== null) {
      lines.push(`${key}:`);
      for (const [k, v] of Object.entries(val)) {
        lines.push(`  ${k}: ${v}`);
      }
    } else {
      lines.push(`${key}: ${val}`);
    }
  }
  return lines.join('\n');
}

function parseMarkdownEntry(content) {
  const match = content.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
  if (!match) return null;
  
  const [, frontmatter, body] = match;
  const meta = parseYAML(frontmatter);
  
  return {
    ...meta,
    _body: body.trim(),
    _raw: content
  };
}

function createMarkdownEntry(meta, body) {
  return `---\n${stringifyYAML(meta)}\n---\n\n${body.trim()}\n`;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// UNIVERSAL MEMORY ENGINE
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class UniversalMemory {
  constructor(projectPath) {
    this.projectPath = path.resolve(projectPath);
    this.slug = this.projectPath.replace(/^\//, '').replace(/\//g, '-');
    this.baseDir = path.join(this.projectPath, '.claude-flow');
    this.memDir = path.join(this.projectPath, '_MEMORY');
    
    // Structura pe layere — toate sunt .md
    this.layers = {
      L0: path.join(this.memDir, 'L0-sensory'),
      L1: path.join(this.memDir, 'L1-working'),
      L2: path.join(this.memDir, 'L2-episodic'),
      L3: path.join(this.memDir, 'L3-semantic'),
      L4: path.join(this.memDir, 'L4-identity')
    };
    
    // Index global (JSON pentru performanță)
    this.indexPath = path.join(this.baseDir, 'memory-index.json');
    
    this.ensureDirs();
  }
  
  ensureDirs() {
    Object.values(this.layers).forEach(dir => {
      fs.mkdirSync(dir, { recursive: true });
    });
    fs.mkdirSync(this.baseDir, { recursive: true });
  }
  
  // ── Scriere intrare în orice layer ────────────────────────────────────
  write(layer, data) {
    if (!this.layers[layer]) throw new Error(`Layer necunoscut: ${layer}`);
    
    const uid = data.uid || generateUID();
    const timestamp = new Date().toISOString();
    
    const meta = {
      uid,
      project: this.slug,
      layer,
      type: data.type || this.getTypeForLayer(layer),
      created_at: timestamp,
      updated_at: timestamp,
      tags: data.tags || [],
      confidence: data.confidence !== undefined ? data.confidence : 0.5,
      source: data.source || 'manual',
      llm: data.llm || 'universal',
      platform: data.platform || 'cross-platform',
      ...data.meta
    };
    
    const body = this.formatBody(data);
    const content = createMarkdownEntry(meta, body);
    
    const filename = `${timestamp.slice(0, 10)}-${uid}.md`;
    const filepath = path.join(this.layers[layer], filename);
    
    fs.writeFileSync(filepath, content, 'utf8');
    this.updateIndex(meta, filepath);
    
    return { uid, filepath, meta };
  }
  
  // ── Citire intrare după UID ────────────────────────────────────────────
  read(uid) {
    const index = this.readIndex();
    const entry = index[uid];
    if (!entry) return null;
    
    const content = fs.readFileSync(entry.path, 'utf8');
    return parseMarkdownEntry(content);
  }
  
  // ── Căutare în toate layerele ──────────────────────────────────────────
  search(keywords, options = {}) {
    const { layers = ['L1', 'L2', 'L3', 'L4'], limit = 20 } = options;
    const kws = Array.isArray(keywords) ? keywords : [keywords];
    const results = [];
    
    for (const layer of layers) {
      const dir = this.layers[layer];
      if (!fs.existsSync(dir)) continue;
      
      const files = fs.readdirSync(dir).filter(f => f.endsWith('.md'));
      for (const f of files) {
        const content = fs.readFileSync(path.join(dir, f), 'utf8');
        const entry = parseMarkdownEntry(content);
        if (!entry) continue;
        
        let score = 0;
        const searchText = `${entry._body} ${entry.tags?.join(' ') || ''}`.toLowerCase();
        
        kws.forEach(kw => {
          if (searchText.includes(kw.toLowerCase())) score++;
        });
        
        if (score > 0) {
          results.push({ ...entry, _score: score, _file: f });
        }
      }
    }
    
    results.sort((a, b) => b._score - a._score);
    return results.slice(0, limit);
  }
  
  // ── Listare layer ──────────────────────────────────────────────────────
  list(layer, limit = 50) {
    const dir = this.layers[layer];
    if (!fs.existsSync(dir)) return [];
    
    const files = fs.readdirSync(dir)
      .filter(f => f.endsWith('.md'))
      .sort().reverse()
      .slice(0, limit);
    
    return files.map(f => {
      const content = fs.readFileSync(path.join(dir, f), 'utf8');
      return parseMarkdownEntry(content);
    }).filter(Boolean);
  }
  
  // ── Garbage Collection per layer ───────────────────────────────────────
  gc(layer) {
    const decay = { L0: 1/24, L1: 3, L2: 14, L3: 30, L4: Infinity }[layer];
    if (!decay || decay === Infinity) return 0;
    
    const dir = this.layers[layer];
    if (!fs.existsSync(dir)) return 0;
    
    const cutoff = Date.now() - (decay * 24 * 60 * 60 * 1000);
    let removed = 0;
    
    fs.readdirSync(dir).forEach(f => {
      if (!f.endsWith('.md')) return;
      const stat = fs.statSync(path.join(dir, f));
      if (stat.mtimeMs < cutoff) {
        fs.unlinkSync(path.join(dir, f));
        removed++;
      }
    });
    
    return removed;
  }
  
  // ── Promovare între layere ────────────────────────────────────────────
  promote(fromLayer, toLayer, uid) {
    const entry = this.read(uid);
    if (!entry) throw new Error(`Entry ${uid} not found`);
    
    const newMeta = {
      ...entry,
      uid: generateUID(),
      layer: toLayer,
      type: this.getTypeForLayer(toLayer),
      promoted_from: uid,
      promoted_at: new Date().toISOString(),
      confidence: Math.min(1, (entry.confidence || 0.5) + 0.1)
    };
    
    delete newMeta._body;
    delete newMeta._raw;
    delete newMeta._score;
    delete newMeta._file;
    
    const body = entry._body;
    return this.write(toLayer, { ...newMeta, body });
  }
  
  // ── Agregare către OS-Level (propagare) ───────────────────────────────
  propagateToOS(uid) {
    const entry = this.read(uid);
    if (!entry) return null;
    
    const osDir = path.join(os.homedir(), '.config', 'opencode', 'ccdew-os', 'propagated');
    fs.mkdirSync(osDir, { recursive: true });
    
    const osPath = path.join(osDir, `${entry.uid}.md`);
    const osContent = createMarkdownEntry(
      { ...entry, propagated_at: new Date().toISOString(), source_project: this.slug },
      entry._body
    );
    
    fs.writeFileSync(osPath, osContent, 'utf8');
    return osPath;
  }
  
  // ── Index management ──────────────────────────────────────────────────
  readIndex() {
    try {
      const data = fs.readFileSync(this.indexPath, 'utf8');
      return JSON.parse(data);
    } catch {
      return {};
    }
  }

  updateIndex(meta, filepath) {
    let index = {};
    try {
      if (fs.existsSync(this.indexPath)) {
        index = JSON.parse(fs.readFileSync(this.indexPath, 'utf8'));
      }
    } catch {}
    
    index[meta.uid] = {
      uid: meta.uid,
      layer: meta.layer,
      type: meta.type,
      created_at: meta.created_at,
      tags: meta.tags,
      path: filepath
    };
    
    fs.mkdirSync(path.dirname(this.indexPath), { recursive: true });
    fs.writeFileSync(this.indexPath, JSON.stringify(index, null, 2), 'utf8');
  }
  
  // ── Helpers ────────────────────────────────────────────────────────────
  getTypeForLayer(layer) {
    const map = { L0: 'sensory', L1: 'working', L2: 'episodic', L3: 'semantic', L4: 'identity' };
    return map[layer] || 'unknown';
  }
  
  formatBody(data) {
    if (data.body) {
      // Ensure body is a string and return as-is
      return typeof data.body === 'string' ? data.body : JSON.stringify(data.body, null, 2);
    }
    
    const parts = [];
    if (data.title) parts.push(`# ${data.title}`);
    if (data.description) parts.push(`\n${data.description}`);
    if (data.context) parts.push(`\n## Context\n\n${data.context}`);
    if (data.details) parts.push(`\n## Detalii\n\n${data.details}`);
    if (data.result) parts.push(`\n## Rezultat\n\n${data.result}`);
    if (data.action_items) parts.push(`\n## Acțiuni\n\n${data.action_items.map(a => `- [ ] ${a}`).join('\n')}`);
    
    parts.push(`\n---\n\n*Generat de CCDEW Universal Memory — ${new Date().toISOString()}*`);
    
    return parts.join('\n');
  }
  
  // ── Status ──────────────────────────────────────────────────────────────
  status() {
    const result = {};
    for (const [layer, dir] of Object.entries(this.layers)) {
      if (fs.existsSync(dir)) {
        const files = fs.readdirSync(dir).filter(f => f.endsWith('.md'));
        result[layer] = files.length;
      } else {
        result[layer] = 0;
      }
    }
    return result;
  }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// OS-LEVEL MEMORY AGGREGATOR (lucrează cu .md)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function aggregateFromMarkdown(projectPath) {
  const mem = new UniversalMemory(projectPath);
  const osDir = path.join(os.homedir(), '.config', 'opencode', 'ccdew-os', 'propagated');
  fs.mkdirSync(osDir, { recursive: true });
  
  const propagated = [];
  
  // Propagă L3 și L4 către OS
  ['L3', 'L4'].forEach(layer => {
    const entries = mem.list(layer);
    entries.forEach(entry => {
      if (entry.confidence >= 0.7) {
        const osPath = mem.propagateToOS(entry.uid);
        propagated.push({ layer, uid: entry.uid, osPath });
      }
    });
  });
  
  return propagated;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// CLI
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function main() {
  const cmd = process.argv[2];
  const projectPath = process.argv[3] || process.cwd();
  const mem = new UniversalMemory(projectPath);
  
  switch(cmd) {
    case 'init':
      console.log('✅ Memorie universală inițializată pentru:', projectPath);
      console.log(JSON.stringify(mem.status(), null, 2));
      break;
      
    case 'write': {
      const layer = process.argv[4];
      const title = process.argv[5];
      const content = process.argv.slice(6).join(' ');
      const result = mem.write(layer, { title, body: content, tags: ['manual'] });
      console.log('✅ Scris în', layer, ':', result.uid);
      break;
    }
    
    case 'search': {
      const query = process.argv[4];
      const results = mem.search(query);
      console.log(`🔍 ${results.length} rezultate pentru "${query}":`);
      results.forEach(r => {
        console.log(`  [${r.layer}] ${r._file} — score: ${r._score}`);
      });
      break;
    }
    
    case 'list': {
      const layer = process.argv[4];
      const entries = mem.list(layer);
      console.log(`📂 ${entries.length} intrări în ${layer}:`);
      entries.forEach(e => {
        console.log(`  ${e.uid} — ${e.tags?.join(', ')}`);
      });
      break;
    }
    
    case 'propagate': {
      const propagated = aggregateFromMarkdown(projectPath);
      console.log(`🚀 ${propagated.length} intrări propagate către OS:`);
      propagated.forEach(p => console.log(`  ${p.layer}: ${p.uid}`));
      break;
    }
    
    case 'status':
      console.log(JSON.stringify(mem.status(), null, 2));
      break;
      
    default:
      console.log(`
CCDew Universal Memory Engine v2.0
Format: Markdown (.md) pentru compatibilitate universală

Usage:
  universal-memory.cjs init [project-path]           Inițializează structura
  universal-memory.cjs write <layer> <title> <text>  Scrie în layer
  universal-memory.cjs search <query>                Caută în memorie
  universal-memory.cjs list <layer>                  Listează intrări
  universal-memory.cjs propagate [project-path]      Propagă către OS
  universal-memory.cjs status                        Arată status

Layere:
  L0 — Sensory (input imediat, 1 oră)
  L1 — Working (task-uri, goal-uri, 3 zile)
  L2 — Episodic (sesiuni, 14 zile)
  L3 — Semantic (concepte, patterns, 30 zile)
  L4 — Identity (cunoștințe permanente)

Exemplu:
  universal-memory.cjs write L1 "Task important" "Detalii task..."
      `);
  }
}

module.exports = { UniversalMemory, aggregateFromMarkdown };
if (require.main === module) main();
