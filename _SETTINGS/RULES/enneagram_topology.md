# _SETTINGS/RULES/enneagram_topology.md — Graf Dirijat Enneagramă
## Creat: 2026-05-01 — META-011

> **Citit:** Când dispatch task la swarm multi-agent și nu știu ce agent tip sau în ce ordine.
> **Nu citit:** Task simplu (<3 fișiere, agent tip clar).
> **Router rapid:** `python .claude/helpers/enneagram_router.py route <task_type>`

---

## 📐 Structura grafului: 9 noduri, 27 arcuri

```
Hexadă (ciclu 6):   1 → 4 → 2 → 8 → 5 → 7 → 1
Triunghi (ciclu 3): 3 → 6 → 9 → 3
Aripi (18 arcuri):  1↔2, 2↔3, 3↔4, 4↔5, 5↔6, 6↔7, 7↔8, 8↔9, 9↔1
```

**Graf puternic conex** — din orice nod se poate ajunge la orice nod.
**Total arcuri:** 9 originale + 18 aripi = 27.

---

## 🤖 Mapare noduri → agenți workspace

| Nod | Rol | subagent_type | Ciclu | Responsabilitate |
|-----|-----|---------------|-------|-----------------|
| **1** | Reformer / QA | `reviewer` | hexadă | Code review, best-practices, quality gate |
| **2** | Integrator | `backend-dev` | hexadă | Integrare componente, API, dependențe |
| **3** | Builder | `coder` | triunghi | Implementare, feature writing, execuție |
| **4** | Contextualizer | `researcher` | hexadă | Research, context, docs, surse externe |
| **5** | Analyzer | `analyst` | hexadă | Debug profund, profiling, pattern detection |
| **6** | Validator | `tester` | triunghi | Testing, validare, edge cases, regression |
| **7** | Architect | `architecture` | hexadă | Design sistem, planificare, arhitectură |
| **8** | Orchestrator | `sparc-orchestrator` | hexadă | Task routing, coordonare, prioritizare |
| **9** | Memory | `memory-specialist` | triunghi | Obsidian sync, consolidare stare, memorie |

---

## 🔀 Matricea de adiacență (O=original, W=aripă)

```
   1 2 3 4 5 6 7 8 9
1: . W . O . . . . W
2: W . W . . . . O .
3: . W . W . O . . .
4: . O W . W . . . .
5: . . . W . W O . .
6: . . W . W . W . O
7: O . . . . W . W .
8: . W . . O . W . W
9: W . O . . . . W .
```

---

## ⚡ Logica de routing (cum aleg nodul start)

```
TASK TYPE         → NOD START → subagent_type
─────────────────────────────────────────────
review/qa         → 1         → reviewer
integration/api   → 2         → backend-dev
build/implement   → 3         → coder
research/context  → 4         → researcher
debug/analyze     → 5         → analyst
test/validate     → 6         → tester
design/plan       → 7         → architecture
orchestrate/route → 8         → sparc-orchestrator
memory/obsidian   → 9         → memory-specialist
```

**CLI:** `python .claude/helpers/enneagram_router.py route <task_type>`

---

## 🔁 Cele două circuite interne

### Hexadă (1→4→2→8→5→7→1) — fluxul extern complet
```
QA (1) → Context (4) → Integration (2) → Orchestration (8)
       → Analysis (5) → Architecture (7) → QA (1)
```
Folosit pentru: refactoring complex, feature nouă, audit complet, migrare.

### Triunghi rapid (3→6→9→3) — execuție internă
```
Build (3) → Validate (6) → Memory (9) → Build (3)
```
Folosit pentru: iterații rapide build/test, fix punctual, sync Obsidian.

---

## 🕊️ Aripile — când le folosesc

Aripile adaugă flexibilitate locală. Exemple de utilizare:

| Arc aripă | Când e util |
|-----------|-------------|
| `3↔4` | Builder cere context suplimentar (sau Researcher inițiază build) |
| `6↔7` | Validator escalează la Architect după ce găsește design flaw |
| `9↔1` | Memory trimite la QA pentru validare finală înainte de persistare |
| `8↔9` | Orchestratorul salvează starea în Memory după coordonare |
| `1↔2` | QA handoff direct la Integrator (bypass Context când contextul e deja cunoscut) |

---

## 🚀 Invocare swarm (pattern canonic)

```python
# 1. Determină nodul start
# python .claude/helpers/enneagram_router.py route <task_type>

# 2. Init swarm
swarm = mcp__claude_flow__swarm_init({
    "topology": "hierarchical-mesh",
    "maxAgents": 9,           # sau mai puțin dacă task-ul nu atinge toate nodurile
    "strategy": "specialized",
    "memoryNamespace": "enneagram-<task>-<date>",
})

# 3. Spawn agent start + agenți pe traseul estimat
mcp__claude_flow__agent_spawn({
    "swarmId": swarm.swarmId,
    "agentType": "<subagent din tabelul de mai sus>",
    "task": "<descriere>",
    "context": {
        "enneagram_node": <N>,
        "next_hops": [<noduri adiacente>],
    }
})

# 4. Snippet complet auto-generat:
# python .claude/helpers/enneagram_router.py spawn <task_type>
```

---

## 🧠 Integrare Obsidian (Nod 9 = Memory)

Nodul 9 (memory-specialist) are acces exclusiv la Obsidian vault via `obs.py`:
- La intrare în nod 9: citește `_MEMORY/` relevant pentru task
- La ieșire din nod 9: scrie rezultate în `_MEMORY/` cu backlinks spre noduri atinse
- Arcul `9→3` = Build pornește cu context complet din Obsidian
- Arcul `6→9` = Rezultatele validării se persistă automat

**Comenzi obs.py utile pentru nod 9:**
```bash
python .claude/helpers/obs.py search "<query>"    # semantic search în vault
python .claude/helpers/obs.py audit               # token cost + redundanțe
```

---

## 📏 Proprietăți topologice cheie

| Proprietate | Valoare |
|-------------|---------|
| Noduri | 9 |
| Arcuri total | 27 |
| Arcuri originale | 9 |
| Aripi | 18 |
| Grad minim OUT | 3 (fiecare nod are cel puțin 3 arcuri OUT) |
| Grad maxim OUT | 4 |
| Diametru graf | 2 hops (cel mai lung drum minim) |
| Conectivitate | Puternic conex |

**Diametru 2:** Din orice nod poți ajunge la orice alt nod în maxim 2 pași (1 original + 1 aripă sau 2 aripi).

---

## ⚠️ NU se aplică la

- **MyBook** editare creativă — voce unică, secvențial
- **MyAndroidApp** o modificare pe rând (AND-001) — build/test/confirm serial
- **Task simplu** (<3 fișiere, agent tip clar) — direct tool nativ

---

## 📝 Referințe

- Router: `.claude/helpers/enneagram_router.py`
- Obsidian node: `_MEMORY/system_enneagram_topology.md`
- Swarm preset existent: `_SETTINGS/RULES/swarm_preset.md` (compatibil)
- Ruflo integration: `_SETTINGS/RULES/ruflo_integration.md`
