# _SETTINGS/RULES/ruflo_integration.md — Cand si cum folosesc ruflo
## Actualizat: 2026-05-01 (META-011 — secțiunile 1+3 mutate în enneagram_topology.md)

> **Citit:** On-demand, când task-ul depășește capacitatea tool-urilor native.
> **Routing agent / swarm triggers:** → `enneagram_topology.md`. Live hook routing: `.claude/helpers/router.js` (JS, folosit de `hook-handler.cjs`). Explorare interactivă: `enneagram_router.py` (CLI utilitar).

## Regula principala: ruflo complementeaza, nu inlocuieste

Workflow-ul existent (CHANGELOG → TODO → cod → epilog) ramane identic.

---

## 1. Swarm

**Routing agent și când activezi swarm** → `_SETTINGS/RULES/enneagram_topology.md`
- Live (auto, hook chain): `.claude/helpers/router.js` (JS port `bfsPath`/`nextNode`, apelat de `hook-handler.cjs`)
- CLI utilitar (explorare manuală): `python .claude/helpers/enneagram_router.py route <task_type>`
- Swarm preset (topologie + parametri) → `_SETTINGS/RULES/swarm_preset.md`

---

## 2. Memory search (`memory_search`)

**Cand:** Caut ceva SEMANTIC, nu text exact.
- "Unde am mai avut un bug similar?" (cauza, nu string)
- "Ce pattern am folosit ultima data pentru X?"
- Cross-project: info care traverseaza MyAndroidApp ↔ MyBook ↔ MyResearch

**Cand NU:**
- Caut un string/funcție/fișier precis → Grep/Glob (mai rapid)
- Caut decizie recentă → `CHANGELOG.md` al proiectului (sursa canonică)

**Alternativa preferata:** `python .claude/helpers/obs.py search "<query>"` — cauta semantic in vault Obsidian, fara ruflo memory.

---

## 3. Intelligence patterns (`intelligence_patterns`)

**Cand:** Vreau sugestii de optimizare pe baza pattern-urilor invatate din sesiuni anterioare.
**Cand NU:** Task standard cu soluție clară.

---

## Ce NU face ruflo in acest workspace

- **NU inlocuieste MEMORY.md** — ruflo memory e pe sesiune, MEMORY.md e cross-sesiune
- **NU inlocuieste CHANGELOG/TODO** — fisierele filesystem sunt sursa canonica
- **NU inlocuieste BEST_PRACTICES** — lectiile stau in 3-tier fractal, nu in ruflo
- **NU ruleaza automat fara confirmare** — PATTERN-001 se aplica si la ruflo
