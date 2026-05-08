'use strict';
/**
 * Project Scope Guard (v6.1 Micro)
 * --------------------------------
 * Detects which project under PROJECTS/<Name>/ the user is actively working
 * on, then:
 *   1. Surfaces the project's structure summary at UserPromptSubmit so Claude
 *      knows the layout without re-reading files.
 *   2. Warns at pre-edit when an edit lands OUTSIDE the active project
 *      (root or another project) so cross-project leakage is visible.
 *
 * Persistence: .claude-flow/data/active-project.json
 *   {
 *     "name":      "Karma",
 *     "path":      "PROJECTS/Karma",
 *     "detected_from": "cwd"|"recent-edit"|"manual",
 *     "ts":        "2026-05-08T21:00:00Z",
 *     "structure": ["CLAUDE.md", "TODO.md", "src/", ...]
 *   }
 *
 * Detection priority (first match wins):
 *   1. CLAUDE_PROJECT env var (manual override)
 *   2. cwd contains PROJECTS/<Name>/
 *   3. Most recently edited file under PROJECTS/<Name>/ in last 2h
 *   4. Project name mentioned literally in the prompt
 */

const fs   = require('fs');
const path = require('path');

const FLAGS_PATH   = path.join(__dirname, 'feature-flags.json');
const WORKSPACE    = process.env.WORKSPACE_DIR || process.cwd();
const PROJECTS_DIR = path.join(WORKSPACE, 'PROJECTS');
const STATE_PATH   = path.join(WORKSPACE, '.claude-flow', 'data', 'active-project.json');
const RECENT_TTL   = 2 * 60 * 60 * 1000; // 2 hours

function loadFlags() {
  try { return JSON.parse(fs.readFileSync(FLAGS_PATH, 'utf-8')); } catch { return {}; }
}

function listProjects() {
  if (!fs.existsSync(PROJECTS_DIR)) return [];
  try {
    return fs.readdirSync(PROJECTS_DIR, { withFileTypes: true })
      .filter(e => e.isDirectory() && !e.name.startsWith('.'))
      .map(e => e.name);
  } catch { return []; }
}

function projectStructure(name) {
  const root = path.join(PROJECTS_DIR, name);
  if (!fs.existsSync(root)) return [];
  try {
    return fs.readdirSync(root, { withFileTypes: true })
      .filter(e => !e.name.startsWith('.'))
      .map(e => e.isDirectory() ? e.name + '/' : e.name)
      .slice(0, 20);
  } catch { return []; }
}

/**
 * Detect the active project. Returns { name, path, detected_from } or null.
 */
function detect(prompt, options = {}) {
  const projects = listProjects();
  if (projects.length === 0) return null;

  // 1. Manual env override
  const envProj = (process.env.CLAUDE_PROJECT || '').trim();
  if (envProj) {
    const match = projects.find(p => p.toLowerCase() === envProj.toLowerCase());
    if (match) return { name: match, path: `PROJECTS/${match}`, detected_from: 'env' };
  }

  // 2. cwd inside PROJECTS/<Name>/
  const cwd = (options.cwd || process.cwd()).replace(/\\/g, '/');
  const m = cwd.match(/PROJECTS\/([^/]+)/i);
  if (m) {
    const match = projects.find(p => p.toLowerCase() === m[1].toLowerCase());
    if (match) return { name: match, path: `PROJECTS/${match}`, detected_from: 'cwd' };
  }

  // 3. Most recently modified file under any PROJECTS/<Name>/ in last 2h
  const now = Date.now();
  let bestProj = null, bestMtime = 0;
  for (const proj of projects) {
    const projPath = path.join(PROJECTS_DIR, proj);
    try {
      // Sample top-level + one level deep — bounded scan
      const stack = [{ dir: projPath, depth: 0 }];
      while (stack.length) {
        const { dir, depth } = stack.pop();
        if (depth > 2) continue;
        let entries;
        try { entries = fs.readdirSync(dir, { withFileTypes: true }); }
        catch { continue; }
        for (const e of entries) {
          if (e.name.startsWith('.')) continue;
          const full = path.join(dir, e.name);
          if (e.isDirectory()) {
            if (depth < 2) stack.push({ dir: full, depth: depth + 1 });
            continue;
          }
          try {
            const mtime = fs.statSync(full).mtimeMs;
            if (now - mtime < RECENT_TTL && mtime > bestMtime) {
              bestMtime = mtime; bestProj = proj;
            }
          } catch { /* skip */ }
        }
      }
    } catch { /* skip */ }
  }
  if (bestProj) return { name: bestProj, path: `PROJECTS/${bestProj}`, detected_from: 'recent-edit' };

  // 4. Project name mentioned in prompt — word-boundary match so "auth" in
  // "authenticate" doesn't accidentally match a project named "Auth".
  if (prompt) {
    for (const proj of projects) {
      const re = new RegExp('\\b' + escapeRegExp(proj) + '\\b', 'i');
      if (re.test(prompt)) {
        return { name: proj, path: `PROJECTS/${proj}`, detected_from: 'prompt' };
      }
    }
  }

  return null;
}

function loadState() {
  try {
    if (fs.existsSync(STATE_PATH)) return JSON.parse(fs.readFileSync(STATE_PATH, 'utf-8'));
  } catch { /* ignore */ }
  return null;
}

function saveState(state) {
  try {
    fs.mkdirSync(path.dirname(STATE_PATH), { recursive: true });
    // Per-pid+timestamp tmp suffix avoids tmp clobbering when concurrent
    // hooks (post-edit + pre-edit) both call saveState().
    const tmp = STATE_PATH + '.' + process.pid + '.' + Date.now() + '.tmp';
    fs.writeFileSync(tmp, JSON.stringify(state, null, 2), 'utf-8');
    fs.renameSync(tmp, STATE_PATH);
  } catch { /* non-fatal */ }
}

function escapeRegExp(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }

/**
 * Get currently active project, refreshing detection if stale.
 * @param {string} prompt — current user prompt (helps name-mention detection)
 * @param {object} opts   — { force: boolean }
 */
function getActive(prompt, opts = {}) {
  const flags = loadFlags();
  if (flags.components && flags.components.project_scope === false) return null;

  const cached = loadState();
  // Cache valid for 5 minutes unless forced
  if (cached && !opts.force) {
    const age = Date.now() - new Date(cached.ts || 0).getTime();
    if (age < 5 * 60 * 1000) return cached;
  }

  const detected = detect(prompt, opts);
  if (!detected) return null;
  const state = {
    ...detected,
    ts: new Date().toISOString(),
    structure: projectStructure(detected.name),
  };
  saveState(state);
  return state;
}

/**
 * Force-set active project (CLI: hook-handler.cjs scope-set <name>).
 */
function setActive(name) {
  const projects = listProjects();
  const match = projects.find(p => p.toLowerCase() === name.toLowerCase());
  if (!match) return null;
  const state = {
    name: match,
    path: `PROJECTS/${match}`,
    detected_from: 'manual',
    ts: new Date().toISOString(),
    structure: projectStructure(match),
  };
  saveState(state);
  return state;
}

/**
 * Returns true if filePath is inside the active project's directory.
 * Returns true also when no project is active (no scope to enforce).
 */
function isFileInScope(filePath, activeProject) {
  if (!filePath || !activeProject) return true;
  // Use path.relative to handle cross-platform separator mismatch and any
  // mixed-slash inputs from hookInput.toolInput.file_path on Windows.
  const abs = path.resolve(path.isAbsolute(filePath) ? filePath : path.join(WORKSPACE, filePath));
  const projAbs = path.resolve(path.join(WORKSPACE, activeProject.path));
  if (abs === projAbs) return true;
  const rel = path.relative(projAbs, abs);
  if (rel && !rel.startsWith('..') && !path.isAbsolute(rel)) return true;
  // Allowed: workspace meta files (root CLAUDE.md, README, etc.) the user
  // might genuinely need to update — these are explicit, never accidental.
  // We'll WARN on root edits but not classify them as out-of-scope-rejection.
  return false;
}

/**
 * Determine where filePath lives, for a clearer warning.
 */
function classifyEdit(filePath, activeProject) {
  if (!filePath || !activeProject) return 'in-scope';
  const abs = path.isAbsolute(filePath) ? filePath : path.join(WORKSPACE, filePath);
  const projAbs = path.join(WORKSPACE, activeProject.path);
  if (abs === projAbs || abs.startsWith(projAbs + path.sep)) return 'in-scope';

  const otherMatch = abs.match(new RegExp(`PROJECTS[/\\\\]([^/\\\\]+)`));
  if (otherMatch) return `other-project:${otherMatch[1]}`;

  if (abs.startsWith(WORKSPACE + path.sep) || abs === WORKSPACE) {
    const rel = path.relative(WORKSPACE, abs);
    if (!rel.includes(path.sep)) return 'workspace-root';
    return 'workspace-meta';
  }
  return 'external';
}

/**
 * One-line hint string for inject-workflow.
 */
function hintLine(active) {
  if (!active) return '';
  const struct = (active.structure || []).slice(0, 6).join(', ');
  return `[SCOPE] Active: ${active.path} (${active.detected_from}) | top: ${struct || '(empty)'}`;
}

/**
 * Warning string for pre-edit when out of scope. Returns '' if in-scope.
 */
function preEditWarning(filePath, active) {
  if (!active) return '';
  const cls = classifyEdit(filePath, active);
  if (cls === 'in-scope') return '';
  if (cls === 'workspace-meta' || cls === 'workspace-root') {
    return `[SCOPE WARN] Editing workspace file '${path.basename(filePath)}' while active project is ${active.path}. Confirm this is intentional.`;
  }
  if (cls.startsWith('other-project:')) {
    const other = cls.split(':')[1];
    return `[SCOPE WARN] Editing PROJECTS/${other}/ but active project is ${active.path}. Cross-project edit — confirm before proceeding.`;
  }
  return `[SCOPE WARN] Editing path outside ${active.path}: ${filePath}`;
}

module.exports = {
  detect, getActive, setActive,
  isFileInScope, classifyEdit,
  hintLine, preEditWarning,
  listProjects, projectStructure,
};
