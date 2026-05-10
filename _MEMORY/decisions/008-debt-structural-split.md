---
name: DEBT structural — NU split intelligence + hook-handler
severity: HIGH
version: v3.5+
date: 2026-05-10
status: deferred (debt documented, not yet executed)
tags: [debt, refactor, split, architecture, decision-not-to-act]
---

# DEBT structural — NU split intelligence.cjs + hook-handler.cjs

## Context
`auto-infer` (5-zoom audit) flagează în mod constant 2 fișiere ca **HIGH** (>500 lines hard cap):

```
intelligence.cjs   979 lines
hook-handler.cjs  1024 lines
```

Recomandare automată: "Split into 3 modules by responsibility".

## Opțiuni

**A. Split immediate (urmează recomandarea)**
- intelligence.cjs → `intel-graph.cjs` + `intel-init.cjs` + `intel-consolidate.cjs`
- hook-handler.cjs → `lib/handlers/{lifecycle,audit,tools}.cjs`
- Timp estimat: 2-3 ore
- Risc: HIGH regresie (modificări în 30+ comenzi handler, în init/consolidate cu logic complex)

**B. Defer ca DEBT documented**
- Mențin status quo
- Risc: 0 (nimic nu se schimbă)
- Cost: audit va flag-a în continuare ca HIGH (cosmetic, nu funcțional)

**C. Extract minimal (mut 1-2 funcții în submodule)**
- 30-50% reducere LOC fără to refactor major
- Risc: LOW
- Beneficiu: parțial — încă peste 500 lines

## Decizie
**B — defer ca DEBT documented.**

## Motiv
1. **HIGH risk regresie** — refactor masiv = șansă mare bug în comenzi care funcționează acum
2. **0 user-visible benefit** — userul nu vede LOC, doar comportamentul
3. **Nicio cerere funcțională activă** care să trigger split (când vom integra alt project care folosește graph functions, atunci facem extract)
4. **Best practice "stable + performant final"** — split adăugat acum aduce instabilitate
5. **Audit warning ≠ bug** — e signal pentru viitor, nu blocker pentru acum

## Trigger pentru re-evaluare
Re-evaluăm split-ul când:
- Apare bug specific în zone neacoperite de tests în `intelligence.cjs::consolidate()` (most complex)
- Vrem să share `intelligence` cu alt project (atunci scoatem ca lib separat)
- LOC-ul depășește 1500 (atunci e impractical pentru navigare)

## Consecințe
- /infer va arăta în continuare 2 HIGH findings → asta e expected, nu trebuie ignorat ci INTERPRETAT
- /optimize macro raport: "proposal-only, decizie umană"
- DEBT vizibil în `_MEMORY/_DASHBOARD.md::Pending Corrections`
