'use strict';
/**
 * Multi-platform detection — Claude Code, Cursor, Codex, Gemini, OpenCode.
 * Inspired by everything-claude-code (ECC).
 *
 * Returns an object describing the host AI tool, so hooks can adapt.
 *
 * Detection order (env vars first, then markers on disk):
 *   CLAUDE_CODE_*  → claude-code
 *   CURSOR_*       → cursor
 *   CODEX_*        → codex
 *   GEMINI_*       → gemini
 *   OPENCODE_*     → opencode
 */

const fs = require('fs');
const path = require('path');

function detectPlatform() {
  const env = process.env;

  if (env.CLAUDE_CODE_VERSION || env.CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS) {
    return { name: 'claude-code', version: env.CLAUDE_CODE_VERSION || 'unknown', source: 'env' };
  }
  if (env.CURSOR_AI_VERSION || env.CURSOR_TRACE_ID) {
    return { name: 'cursor', version: env.CURSOR_AI_VERSION || 'unknown', source: 'env' };
  }
  if (env.CODEX_API_KEY || env.OPENAI_API_KEY && env.CODEX_MODE) {
    return { name: 'codex', source: 'env' };
  }
  if (env.GEMINI_API_KEY || env.GOOGLE_GEMINI_VERSION) {
    return { name: 'gemini', version: env.GOOGLE_GEMINI_VERSION || 'unknown', source: 'env' };
  }
  if (env.OPENCODE_VERSION) {
    return { name: 'opencode', version: env.OPENCODE_VERSION, source: 'env' };
  }

  // Disk markers
  const cwd = process.cwd();
  if (fs.existsSync(path.join(cwd, '.cursor'))) {
    return { name: 'cursor', source: 'disk' };
  }
  if (fs.existsSync(path.join(cwd, '.claude'))) {
    return { name: 'claude-code', source: 'disk' };
  }
  return { name: 'unknown', source: 'fallback' };
}

function getCapabilities() {
  const p = detectPlatform();
  const caps = {
    'claude-code': { hooks: true, slashCommands: true, mcpServers: true, subAgents: true },
    'cursor':      { hooks: false, slashCommands: false, mcpServers: true, subAgents: false },
    'codex':       { hooks: false, slashCommands: false, mcpServers: false, subAgents: false },
    'gemini':      { hooks: false, slashCommands: false, mcpServers: false, subAgents: false },
    'opencode':    { hooks: true, slashCommands: true, mcpServers: false, subAgents: false },
    'unknown':     { hooks: false, slashCommands: false, mcpServers: false, subAgents: false },
  };
  return { platform: p, capabilities: caps[p.name] };
}

module.exports = { detectPlatform, getCapabilities };
