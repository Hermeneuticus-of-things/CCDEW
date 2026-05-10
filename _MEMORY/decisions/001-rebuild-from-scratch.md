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
v2.0 al `claude-code-eficient-workspace` avea 5 fix-uri identificate într-un audit anterior:
1. SAFLA `[object Object]` silent corruption
2. Codeburn Windows ENOENT (no `.cmd` ext)
3. Atomic rename EPERM concurrent
4. hook-handler eager-require 12 modules
5. Node 22 refuză `.cmd` la `execFileSync`

## Opțiuni considerate

**A. Incremental patch (5 fix-uri minore)**
- Pro: minimal change, low risk regresie
- Contra: state învățat SAFLA rămâne corupt; arhitectura veche cu eager-require persistă; testabilitate slabă

**B. Rebuild from scratch cu best practices**
- Pro: arhitectură curată (lib/ + helpers/); lazy require; full test suite; documented decisions
- Contra: HIGH risk regresie; pierdere temporară state învățat; 1 zi de muncă

## Decizie
**B — rebuild from scratch.**

## Motiv
- Workspace-ul era deja "experimental, ne-testat pe scară largă" (recunoscut)
- 5 fix-uri = 5 puncte de fragility; un rebuild rezolvă cauzele structurale
- Backup snapshot la `_ARCHIVE/pre-rebuild-2026-05-10/` permite rollback total instant

## Consecințe
- ✅ 4 module `lib/` reutilizabile (`atomic-write`, `platform`, `flags`, `validate`)
- ✅ Lazy require redus latency hot-path 146ms cold-load → ~5ms warm
- ✅ 4 test suite regression cu 24 verificări (era 0)
- ⚠️ State SAFLA pierdut (133 feedback → 45 valid restaurate din backup)

## Verificare
- v3.0.0 audit: 38/38 PASS, 0 WARN, 0 FAIL
- v3.0.0 tests: 24/24 PASS

## Referințe
- Backup: `_ARCHIVE/pre-rebuild-2026-05-10/`
- CHANGELOG: `## [3.0.0]`
