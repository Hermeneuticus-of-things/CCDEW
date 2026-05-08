'use strict';
/**
 * Standalone test for project-scope.cjs (no test framework, Node built-ins only).
 * Run: node _test_project-scope.cjs
 */

const fs   = require('fs');
const path = require('path');

// WORKSPACE_DIR must be set BEFORE requiring the module (read at load time).
const WORKSPACE = path.resolve(__dirname, '..', '..');
process.env.WORKSPACE_DIR = WORKSPACE;
delete process.env.CLAUDE_PROJECT;

const scope = require('./project-scope.cjs');

const STATE_PATH = path.join(WORKSPACE, '.claude-flow', 'data', 'active-project.json');

let passed = 0;
let total = 0;

function record(name, ok, expected, got) {
  total++;
  if (ok) {
    passed++;
    console.log('[PASS] ' + name);
  } else {
    console.log('[FAIL] ' + name + ': expected ' + JSON.stringify(expected) + ', got ' + JSON.stringify(got));
  }
}

function clearState() {
  try { if (fs.existsSync(STATE_PATH)) fs.unlinkSync(STATE_PATH); } catch (e) {}
}

// 1. listProjects() includes Consiliu
{
  const projects = scope.listProjects();
  const ok = Array.isArray(projects) && projects.includes('Consiliu');
  record('listProjects() returns Consiliu', ok, 'array containing "Consiliu"', projects);
}

// 2. detect() with prompt mention
{
  const tmpCwd = path.join(WORKSPACE, '.claude', 'helpers');
  const result = scope.detect('work on Consiliu', { cwd: tmpCwd });
  const ok = result && result.name === 'Consiliu' && result.detected_from === 'prompt';
  record('detect("work on Consiliu") => name=Consiliu, detected_from=prompt',
    ok, { name: 'Consiliu', detected_from: 'prompt' }, result);
}

// 3. detect() empty prompt outside PROJECTS/
{
  const tmpCwd = path.join(WORKSPACE, '.claude', 'helpers');
  const result = scope.detect('', { cwd: tmpCwd });
  const ok = result === null || (result && result.detected_from === 'recent-edit');
  record('detect("", cwd outside PROJECTS) => null or recent-edit',
    ok, 'null or recent-edit', result);
}

// 4. setActive('Consiliu') then getActive()
{
  clearState();
  const set = scope.setActive('Consiliu');
  const got = scope.getActive('', { cwd: path.join(WORKSPACE, '.claude') });
  const ok = set && set.name === 'Consiliu' && got && got.name === 'Consiliu';
  record('setActive("Consiliu") + getActive() returns Consiliu',
    ok, { name: 'Consiliu' }, { set: set, got: got });
}

// 5. setActive('NonExistent')
{
  const result = scope.setActive('NonExistent');
  const ok = result === null;
  record('setActive("NonExistent") returns null', ok, null, result);
}

// 6. isFileInScope in-scope
{
  const active = { name: 'Consiliu', path: 'PROJECTS/Consiliu', detected_from: 'manual' };
  const result = scope.isFileInScope('PROJECTS/Consiliu/CLAUDE.md', active);
  record('isFileInScope("PROJECTS/Consiliu/CLAUDE.md") => true',
    result === true, true, result);
}

// 7. isFileInScope out-of-scope
{
  const active = { name: 'Consiliu', path: 'PROJECTS/Consiliu', detected_from: 'manual' };
  const result = scope.isFileInScope('README.md', active);
  record('isFileInScope("README.md") => false',
    result === false, false, result);
}

// 8. classifyEdit other-project
{
  const active = { name: 'Consiliu', path: 'PROJECTS/Consiliu', detected_from: 'manual' };
  const result = scope.classifyEdit('PROJECTS/OtherProj/x.md', active);
  record('classifyEdit("PROJECTS/OtherProj/x.md") => "other-project:OtherProj"',
    result === 'other-project:OtherProj', 'other-project:OtherProj', result);
}

// 9. classifyEdit workspace-root
{
  const active = { name: 'Consiliu', path: 'PROJECTS/Consiliu', detected_from: 'manual' };
  const result = scope.classifyEdit('README.md', active);
  record('classifyEdit("README.md") => "workspace-root"',
    result === 'workspace-root', 'workspace-root', result);
}

// 10. preEditWarning in-scope is empty
{
  const active = { name: 'Consiliu', path: 'PROJECTS/Consiliu', detected_from: 'manual' };
  const result = scope.preEditWarning('PROJECTS/Consiliu/CLAUDE.md', active);
  record('preEditWarning(in-scope) => ""', result === '', '', result);
}

// 11. preEditWarning cross-project includes phrase
{
  const active = { name: 'Consiliu', path: 'PROJECTS/Consiliu', detected_from: 'manual' };
  const result = scope.preEditWarning('PROJECTS/OtherProj/x.md', active);
  const ok = typeof result === 'string' && result.includes('Cross-project edit');
  record('preEditWarning(cross-project) includes "Cross-project edit"',
    ok, 'string containing "Cross-project edit"', result);
}

// 12. hintLine(null)
{
  const result = scope.hintLine(null);
  record('hintLine(null) => ""', result === '', '', result);
}

// 13. hintLine(active) includes 'PROJECTS/' and detection source
{
  const active = {
    name: 'Consiliu',
    path: 'PROJECTS/Consiliu',
    detected_from: 'manual',
    structure: ['CLAUDE.md', 'TODO.md', 'src/']
  };
  const result = scope.hintLine(active);
  const ok = typeof result === 'string'
    && result.includes('PROJECTS/')
    && result.includes('manual');
  record('hintLine(active) includes "PROJECTS/" and detection source',
    ok, 'string containing "PROJECTS/" and "manual"', result);
}

console.log('\n' + passed + '/' + total + ' passed');
process.exit(passed === total ? 0 : 1);
