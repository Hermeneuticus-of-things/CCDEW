'use strict';
/**
 * Ruflo Integration — MCP Tools Wrapper v6.1 SLIM
 * Wraps Ruflo MCP tools for Claude Code integration.
 * 
 * API:
 *   memoryStore(key, value, ttl?) → boolean
 *   memorySearch(query, limit?)  → results[]
 *   swarmInit(options?)          → swarmId
 *   agentSpawn(name, task, swarmId?) → result
 *   hooksRoute(prompt, context?) → routing info
 *   status()                    → system status
 */

const { spawnSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const RUFLO_BIN = process.env.RUFLO_BIN || 'ruflo';

function execRuflo(args, opts = {}) {
  try {
    const r = spawnSync(RUFLO_BIN, args, {
      encoding: 'utf-8',
      timeout: opts.timeout || 30_000,
      stdio: ['pipe', 'pipe', 'pipe'],
      ...opts,
    });
    return {
      stdout: r.stdout || '',
      stderr: r.stderr || '',
      status: r.status,
      ok: r.status === 0,
    };
  } catch (e) {
    return { stdout: '', stderr: e.message, status: 1, ok: false, error: e.message };
  }
}

function memoryStore(key, value, ttl = 3600) {
  const result = execRuflo(['mcp', 'call', 'ruflo_memory_store', '--key', key, '--value', value, '--ttl', String(ttl)]);
  return result.ok;
}

function memorySearch(query, limit = 10) {
  const result = execRuflo(['mcp', 'call', 'ruflo_memory_search', '--query', query, '--limit', String(limit)]);
  if (result.ok) {
    try {
      return JSON.parse(result.stdout);
    } catch {
      return [];
    }
  }
  return [];
}

function swarmInit(options = {}) {
  const { topology = 'hierarchical', maxAgents = 6, strategy = 'specialized', agents = [] } = options;
  const agentList = agents.join(',');
  const args = [
    'swarm', 'init',
    '--topology', topology,
    '--max-agents', String(maxAgents),
    '--strategy', strategy,
    ...(agentList ? ['--agents', agentList] : []),
  ];
  
  const result = execRuflo(args);
  
  if (result.ok) {
    try {
      const parsed = JSON.parse(result.stdout);
      return { ok: true, swarmId: parsed.swarm_id || parsed.id || 'swarm-' + Date.now(), ...parsed };
    } catch {
      return { ok: true, swarmId: result.stdout.trim() || 'swarm-' + Date.now() };
    }
  }
  return { ok: false, error: result.stderr || result.error || 'swarm init failed' };
}

function agentSpawn(agentName, task, swarmId = null) {
  const args = [
    'agent', 'spawn',
    '--name', agentName,
    '--task', task.substring(0, 500),
    ...(swarmId ? ['--swarm', swarmId] : []),
  ];
  
  const result = execRuflo(args);
  
  if (result.ok) {
    try {
      return { ok: true, result: JSON.parse(result.stdout) };
    } catch {
      return { ok: true, result: result.stdout.trim() };
    }
  }
  return { ok: false, error: result.stderr || result.error || 'agent spawn failed' };
}

function status() {
  const result = execRuflo(['status']);
  if (result.ok) {
    try {
      return JSON.parse(result.stdout);
    } catch {
      return { status: 'unknown', raw: result.stdout };
    }
  }
  return { status: 'unavailable', error: result.stderr || 'ruflo not available' };
}

function health() {
  const result = execRuflo(['health']);
  if (result.ok) {
    try {
      return JSON.parse(result.stdout);
    } catch {
      return { status: 'unknown' };
    }
  }
  return { status: 'unavailable' };
}

function hooksRoute(prompt, context = {}) {
  const result = execRuflo(['hooks', 'route', '--prompt', prompt.substring(0, 1000)]);
  if (result.ok) {
    try {
      return JSON.parse(result.stdout);
    } catch {
      return {};
    }
  }
  return {};
}

function federationInit() {
  const result = execRuflo(['federation', 'init']);
  return result.ok;
}

function federationSend(to, message, type = 'task-request') {
  const result = execRuflo(['federation', 'send', '--to', to, '--type', type, '--message', message]);
  return result.ok;
}

function federationStatus() {
  const result = execRuflo(['federation', 'status']);
  if (result.ok) {
    try {
      return JSON.parse(result.stdout);
    } catch {
      return {};
    }
  }
  return { error: result.stderr };
}

module.exports = {
  memoryStore,
  memorySearch,
  swarmInit,
  agentSpawn,
  status,
  health,
  hooksRoute,
  federationInit,
  federationSend,
  federationStatus,
  execRuflo,
};