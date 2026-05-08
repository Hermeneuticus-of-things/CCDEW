# _SETTINGS/RULES/swarm_preset.md — Default Swarm Preset (Holografic-Mesh)
## Creat: 2026-04-19 · User request: persistenta cross-sesiune

> **Citit:** Automat cand user cere "swarm", "agenti paraleli", "mesh", "holografic", sau task multi-file (>=5 fisiere).
> **Nu citit:** Task simplu (<3 fisiere, directie clara).
> **Routing agent (ce tip de agent pentru ce task):** → `enneagram_topology.md` + `python .claude/helpers/enneagram_router.py route <task_type>`

---

## ⚡ DEFAULT PRESET — 1000-AGENT HOLOGRAFIC-MESH

**Cand user spune "swarm", "mesh", "holografic", "pine N agenti", "paraleli":**
Aplica AUTOMAT acest preset, fara sa intreb.

```
topology:      hierarchical-mesh
maxAgents:     1000  (symbolic — MCP capeaza real la 50/100; preset-ul declara intentia)
strategy:      specialized
protocol:      message-bus
coordination:  V3 (Flash Attention + AgentDB + SONA learning)
```

**Invocare canonica (copy-paste in cod):**
```js
mcp__claude-flow__swarm_init({
  topology: "hierarchical-mesh",
  maxAgents: 1000,           // declarative; MCP va scala la max suportat
  strategy: "specialized",
  memoryNamespace: "<project>-<date>",
  flashAttention: true,
  agentDbIntegration: true,
  sonaLearning: true,
})
```

**De ce "1000 symbolic":**
- User a cerut explicit "pine 100afent mash" si apoi "1000 symbolic".
- MCP schema current cap = 50 reali (pool).
- "1000" = intent declarativ = "scale up la max pe care-l poate sustine hardware-ul / MCP-ul curent".
- Hook-ul V3 (`hierarchical-mesh topology with 15-agent coordination`) porneste deja 15 agenti la boot — preset-ul cere scalare dincolo de asta cand task-ul cere.

---

## 🕸️ HOLOGRAFIC = fiecare agent vede intregul context

**Principiu holografic (din sistemul 3-tier fractal workspace):**
- Fiecare agent primeste upfront contextul COMPLET al task-ului (scope, fisiere atinse, reguli proiect, BP relevante, deliverables).
- Fiecare agent lucreaza pe scope EXCLUSIV (zero overlap pe fisiere editate).
- Memorie COMUNA via `agentDB` namespace + `memory_store` pentru cross-agent learnings.
- La finalizare, agentii raporteaza concis (sub 200 cuvinte / agent) + fisiere atinse + status.

**Workflow obligatoriu (din `feedback_parallel_agents_methodology.md`):**
1. **Tu** (orchestratorul) citesti upfront toate fisierele-cheie.
2. **Tu** decupezi task-ul in N sub-task-uri disjuncte (scope exclusiv/agent).
3. **Tu** transmiti explicit in prompt: context + fisiere permise + fisiere interzise + deliverable.
4. **Tu** lansezi agentii in SINGUR `<function_calls>` block (paralel real, nu serial).
5. Agentii ruleaza `run_in_background: true` pentru taskuri lungi.
6. **Tu** consolidezi outputs + faci edit-urile critice care cer context complet.

---

## 📋 CAND ACTIVEZ PRESET-UL

### ✅ Activeaza MESH automat:
- **Refactor multi-file** (>=5 fisiere independente)
- **Gap audit** ("ce am uitat?", "verifica ce lipseste", "agenti sa verifece si sa cera ce am omis")
- **Batch migration** (rename cross-codebase, format update 50+ files)
- **Verificare paralela read-only** (lint + security + UI + i18n + docs simultan)
- **Research paralel** (surse diferite per agent: Jainism / Vedanta / NotebookLM etc.)
- **Gap-audit gen "ship-readiness"** — ex: pre-release audit, completeness check
- **User spune explicit**: "swarm", "mesh", "pine N agenti", "paraleli", "holografic"

### ❌ NU activa mesh:
- **Editare text literar** (MyBook) — secvential, o voce unica
- **O modificare pe rand** (MyAndroidApp AND-001) — build/test/confirm inainte de urmatoarea
- **Task pe 1-3 fisiere** → Agent tool nativ singur
- **Task cu dependente seriale stricte** (A → B → C) — nu paralelizabil

---

## 🧬 ADN PRESET — 5 trasaturi invariante

1. **Topology = hierarchical-mesh** (nu `star`, nu `ring` — doar mesh permite peer-to-peer plus coordinator delegation)
2. **Strategy = specialized** (fiecare agent are subagent_type dedicat: `coder`, `tester`, `reviewer`, `researcher`, `security-auditor`, etc.)
3. **Scope exclusiv per agent** — zero merge-conflict pe fisiere editate
4. **Background = default** pentru taskuri > 3 min (`run_in_background: true`)
5. **Raport concis** — sub 200 cuvinte / agent + fisiere atinse + status pass/fail/partial

---

## 🔁 TRIGGER AUTOMAT LA SESSION START

Hook-ul `SessionStart:compact` porneste deja un swarm V3 de 15 agenti (`swarm-<ID>-<random>`, `hierarchical-mesh`). Acest fisier declara ca **daca task-ul userului cere scalare, extinde la preset-ul 1000** fara sa mai intrebi.

**Comanda quick re-init (daca hook-ul nu e activ):**
```bash
# In Claude Code runtime:
mcp__claude-flow__swarm_init {"topology":"hierarchical-mesh","maxAgents":1000,"strategy":"specialized"}
```

---

## 📝 LOG PER UTILIZARE

La fiecare invocare a preset-ului, scrie in:
- `PROJECTS/<Proiect>/CHANGELOG.md`: `### Swarm mesh 1000 lansat — <data> — <N agenti reali> — task: <descriere>`
- `memory_store` cu namespace `swarm-history` + summary

---

## 🎯 REFERINTE WORKSPACE

- `CLAUDE.md` root → pointer la acest fisier
- `_SETTINGS/RULES/ruflo_integration.md` → cand folosesc ruflo in general
- `feedback_parallel_agents_methodology.md` (MEMORY.md) → metodologia scope exclusiv + memorie comuna
- `feedback_always_use_agents_preload_context.md` (MEMORY.md) → regula: agenti paraleli AUTOMAT, nu optional
- `feedback_agents_efficiency_confirmed.md` (MEMORY.md) → user a confirmat ca paralel = mai eficient

---

## ⚠️ NOTA CRITICA

Acest preset **NU** se aplica la:
- **MyBook** editare creativa (voce unica)
- **MyAndroidApp** build/edit normal (o modificare pe rand)
- **Orice task cu dependente seriale stricte**

Dar se aplica IMPLICIT la:
- **MyLLMApp / any rooted Android** gap audits, ship-readiness, refactor multi-module
- **Orice "ce am omis?" / "verifica ce lipseste"** pe orice proiect
- **Orice request cu cuvantul "paraleli" / "mesh" / "swarm" / "pine N agenti"**
