---
name: Rebuild from scratch (vs incremental fixes)
severity: HIGH
version: v3.0
date: 2026-05-10
status: applied
tags: [architecture, refactor, foundational]
---

# Rebuild from scratch (vs incremental fixes)

## Context
v2.0 of `claude-code-eficient-workspace` had 5 fixes identified in a prior audit:
1. SAFLA `[object Object]` silent corruption
2. Codeburn Windows ENOENT (no `.cmd` ext)
3. Atomic rename EPERM under concurrency
4. hook-handler eager-require 12 modules
5. Node 22 refuses `.cmd` at `execFileSync`

## Options considered

**A. Incremental patch (5 minor fixes)**
- Pro: minimal change, low regression risk
- Contra: SAFLA learned state remains corrupt; old eager-require architecture persists; weak testability

**B. Rebuild from scratch with best practices**
- Pro: clean architecture (lib/ + helpers/); lazy require; full test suite; documented decisions
- Contra: HIGH regression risk; temporary loss of learned state; 1 day of work

## Decision
**B — rebuild from scratch.**

## Rationale
- The workspace was already "experimental, not widely tested" (acknowledged)
- 5 fixes = 5 fragility points; a rebuild addresses the structural causes
- Backup snapshot at `_ARCHIVE/pre-rebuild-2026-05-10/` allows instant total rollback

## Consequences
- ✅ 4 reusable `lib/` modules (`atomic-write`, `platform`, `flags`, `validate`)
- ✅ Lazy require reduced hot-path latency 146ms cold-load → ~5ms warm
- ✅ 4 regression test suites with 24 checks (was 0)
- ⚠️ SAFLA state lost (133 feedbacks → 45 valid restored from backup)

## Verification
- v3.0.0 audit: 38/38 PASS, 0 WARN, 0 FAIL
- v3.0.0 tests: 24/24 PASS

## References
- Backup: `_ARCHIVE/pre-rebuild-2026-05-10/`
- CHANGELOG: `## [3.0.0]`
