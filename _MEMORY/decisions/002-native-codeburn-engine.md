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
`codeburn` CLI (npm package, AgentSeal) e singura dependență externă. Dacă userul rulează `npm install -g codeburn` greșit (sau pe alt machine), tot sistemul de cost-tracking pică. Output: `[CODEBURN] CLI unavailable`.

## Opțiuni

**A. Hard-require codeburn (status quo v3.0)**
- Pro: pricing canonical, latency 150ms
- Contra: SPOF dacă CLI lipsește; utilizator novice se blochează

**B. Fallback la engine nativ (parser direct `~/.claude/projects/**/*.jsonl`)**
- Pro: zero dependențe externe; funcționează imediat
- Contra: pricing differă (modele/multipliers nu sunt 1:1 cu CLI); latency ~2.7s pe 79 fișiere

**C. Doar engine nativ (drop CLI complet)**
- Pro: simplicitate
- Contra: pierdere precizie pricing canonical

## Decizie
**B — CLI preferred when present, native fallback otherwise.**

## Motiv
- CLI dă cifre canonical când existent (cea mai bună sursă)
- Native asigură că sistemul **nu se blochează** când CLI lipsește
- User vede sursa explicit (`source: 'real'` vs `source: 'native'`) → e clar ce numere are

## Consecințe
- `lib/codeburn-engine.cjs` 123 linii noi (parser pricing per model tier opus/sonnet/haiku)
- Disclaimer în README: native pricing e estimate, CLI e canonical
- 8 teste pentru engine (modelTier, costForLine, totals, isAvailable)

## Verificare
- Live test cu CLI absent: returnează cifre native ($1398/zi vs $235 CLI — pricing diferit, dar magnitudine ok)
- 8/8 tests PASS
