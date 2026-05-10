---
name: Native codeburn engine (CLI-independent fallback)
severity: MED
version: v3.0.1
date: 2026-05-10
status: applied
tags: [reliability, dependencies, codeburn, fallback]
---

# Native codeburn engine (CLI-independent fallback)

## Context
The `codeburn` CLI (npm package, AgentSeal) is the only external dependency. If the user runs `npm install -g codeburn` incorrectly (or on a different machine), the entire cost-tracking system breaks. Output: `[CODEBURN] CLI unavailable`.

## Options

**A. Hard-require codeburn (status quo v3.0)**
- Pro: canonical pricing, ~150ms latency
- Contra: SPOF if CLI is missing; novice user gets stuck

**B. Fallback to native engine (parser directly on `~/.claude/projects/**/*.jsonl`)**
- Pro: zero external dependencies; works immediately
- Contra: pricing differs (models/multipliers not 1:1 with CLI); ~2.7s latency on 79 files

**C. Native engine only (drop CLI completely)**
- Pro: simplicity
- Contra: loss of canonical pricing precision

## Decision
**B — CLI preferred when present, native fallback otherwise.**

## Rationale
- CLI returns canonical numbers when available (best source)
- Native ensures the system **never blocks** when CLI is missing
- User sees the source explicitly (`source: 'real'` vs `source: 'native'`) → it's clear which numbers they have

## Consequences
- `lib/codeburn-engine.cjs` 123 new lines (per-model-tier pricing parser opus/sonnet/haiku)
- README disclaimer: native pricing is an estimate, CLI is canonical
- 8 tests for the engine (modelTier, costForLine, totals, isAvailable)

## Verification
- Live test with CLI absent: returns native numbers ($1398/d vs $235 CLI — different pricing, but magnitude OK)
- 8/8 tests PASS
