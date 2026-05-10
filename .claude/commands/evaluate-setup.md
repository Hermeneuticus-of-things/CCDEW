---
description: Run a full health-check of the Claude Code workspace — config, hooks, modules, state, costs, security
allowed-tools: Bash, Read, Glob
---

# /evaluate-setup

Run a comprehensive workspace audit. Inspired by Red Hat's `claude-code-setup-evaluator`.

## What it checks

1. **Config** — `settings.json` valid, all hooks wired, all referenced modules exist
2. **Feature flags** — what's enabled vs available
3. **Hot-path performance** — measures every hook (in-process median)
4. **Module API surface** — each helper exports the expected functions
5. **State integrity** — `.claude-flow/data/safla.json` has only valid Enneagram nodes (1–9), no `[object Object]` corruption
6. **Cost tracking** — codeburn CLI reachable, today/month totals fresh
7. **Security** — secret-scan + project-scope active, sensitive paths protected
8. **Cross-platform** — `findExecutable` resolves binaries with proper extensions

## How to run

```bash
node .claude/helpers/evaluate-setup.cjs
```

Or directly via the hook handler:

```bash
node .claude/helpers/hook-handler.cjs evaluate-setup
```

## Output

A table-style report with PASS/WARN/FAIL per check, plus a JSON dump at `.claude-flow/reports/evaluate-<timestamp>.json` for diffing across runs.

## Exit codes

- `0` — all PASS
- `1` — at least one FAIL
- `0` (with WARN) — only warnings, non-blocking

## Auto-fix suggestions

For each WARN/FAIL, the report links to the smallest possible fix:
- Missing `codeburn` → `npm install -g codeburn`
- Corrupt SAFLA key → `node .claude/helpers/hook-handler.cjs safla-clean`
- MCP server config wrong (no `mcp start` arg) → suggests global `.claude.json` patch
