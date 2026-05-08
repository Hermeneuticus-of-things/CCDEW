# claude-code-eficient-workspace v2.0

**Workspace ultra-eficient pentru Claude Code** cu routing Enneagram, optimizare token automată, cost tracking real și feedback loop adaptiv.

> Bazat pe: [Hermeneuticus-of-things/claude-code-eficient-workspace](https://github.com/Hermeneuticus-of-things/claude-code-eficient-workspace)  
> Extins cu: v6.1 Micro — SSA + CodeBurn + SAFLA + Graphify + LangGraph Micro

---

## De ce acest workspace? — Ce economisești și cum

### Problema

Claude Code consumă tokeni la fiecare interacțiune. Fără optimizare:
- **La fiecare SessionStart** se injectează toată memoria disponibilă (130+ fișiere), chiar dacă 90% e irelevant pentru task-ul curent.
- **La fiecare prompt** contextul crește incremental — Claude "uită" ce a funcționat și ce nu.
- **Fără vizibilitate de cost** — nu știi ce task-uri costă cel mai mult sau unde e waste-ul.
- **Fără routing inteligent** — Claude tratează `"fix bug"` și `"redesign arhitectura"` la fel.

### Soluția — 5 mecanisme care lucrează împreună

#### 1. SSA — Filtrare context (−76% tokeni injectați)
La fiecare prompt, în loc să injectezi toată memoria, SSA calculează **similaritatea Jaccard trigram** între prompt și fiecare entry de memorie. Rezultat: din 50 entries, injectezi doar 12 — cele mai relevante. Obsidian index este inclus automat.

```
Fără SSA:  50 entries × ~200 tokeni = ~10.000 tokeni context
Cu SSA:    12 entries × ~200 tokeni =  ~2.400 tokeni context
Economie:  ~7.600 tokeni per prompt
```

#### 2. Enneagram Routing — Agentul potrivit pentru task-ul potrivit
Sistemul clasifică automat fiecare prompt în unul din 9 tipuri de task și alege agentul specializat. Un bug fix merge la `tester` (Node 6), nu la `sparc-orchestrator` (Node 8). Agentul potrivit → răspuns mai scurt și mai precis → mai puțini tokeni.

```
Task simplu  → TRIANGLE (3 agenți): coder → tester → memory-specialist
Task complex → HEXAD (6 agenți):   reviewer → researcher → ... → analyst
```

#### 3. CodeBurn — Vizibilitate completă a costurilor
Citește direct din `~/.claude/projects/` și afișează în statusline:

```
🔥 $3.81 azi  |  $230.82 luna aceasta  |  112 calls
```

La SessionEnd generează automat `_METRICS/codeburn-optimize-latest.md` cu sugestii concrete: "152 calls azi → grupează task-uri mici".

#### 4. SAFLA — Sistem care învață din experiență
Urmărește ce agent a funcționat sau nu pentru fiecare tip de task. Dacă Node 3 (coder) a eșuat de 3 ori pe task-uri de arhitectură, sistemul penalizează acest routing cu −0.30 și favorizează Node 7 (architecture). Se sincronizează cu CodeBurn: nodurile cu cost/call ridicat sunt penalizate automat.

#### 5. Red Hat Evaluator — Previne over-engineering
Înainte de orice task de arhitectură, injectează 2-3 întrebări critice:
- *"Ce presupuneri tacite conține această soluție?"*
- *"Există o abordare mai simplă cu ≤50% din complexitate?"*

Previne construirea unor soluții complexe care apoi necesită refactoring (= tokeni dubli).

### Rezultate măsurate

| Metric | Valoare |
|--------|---------|
| Reducere context per prompt | **76%** (SSA) |
| Overhead per hook event | **93–185ms** |
| session-end overhead | **117ms** (optimizat de la 8.5s) |
| Vizibilitate cost | **real-time** via codeburn CLI |

---

## Ce face

La fiecare prompt, sistemul:

1. **Filtrează contextul** — SSA reduce memoria injectată cu ~76% (Jaccard trigram, top-12 entries relevante)
2. **Evaluează critic** — Red Hat pune 2-3 întrebări înainte de arhitecturi complexe
3. **Rutează inteligent** — Enneagram trimite task-ul spre agentul optim (9 noduri, hexad/triangle)
4. **Urmărește costul** — CodeBurn afișează `$X.XX azi / $X.XX luna` în statusline
5. **Învață** — SAFLA ajustează weights per nod în funcție de succese/eșecuri
6. **Raportează** — Graphify generează raport la sfârșitul sesiunii

---

## Instalare rapidă

### 1. Cerințe

- Node.js ≥ 18
- Python 3.x
- Claude Code CLI

### 2. Clonează workspace-ul

```bash
git clone https://github.com/Hermeneuticus-of-things/claude-code-eficient-workspace.git workspace
cd workspace
```

### 3. Instalează CodeBurn (singurul pachet extern)

```bash
npm install -g codeburn
```

### 4. Pornește Claude Code

```bash
claude
```

La primul prompt, sistemul se auto-inițializează. Verifică:

```bash
node .claude/helpers/hook-handler.cjs flags
```

---

## Structura workspace

```
workspace/
├── .claude/
│   ├── settings.json          ← 13 hook-uri active
│   ├── helpers/               ← 40+ module (JS + Python)
│   │   ├── hook-handler.cjs   ← dispatcher central
│   │   ├── feature-flags.json ← toggle componente
│   │   ├── codeburn.cjs       ← cost tracking real
│   │   ├── ssa.cjs            ← filtrare context
│   │   ├── safla.cjs          ← feedback adaptiv
│   │   ├── graphify.cjs       ← rapoarte sesiune
│   │   ├── langgraph-micro.cjs← workflow state machine
│   │   ├── red-hat-evaluator.cjs ← evaluare critică
│   │   ├── auto-optimize.cjs  ← detectare prompt verbos
│   │   ├── metrics-update.cjs ← dashboard + metrics
│   │   ├── enneagram_router.py← routing 9 noduri
│   │   ├── intelligence.cjs   ← PageRank memory graph
│   │   └── obsidian-session-context.py ← context Obsidian
│   └── commands/
│       └── cost.md            ← /cost command
├── PROJECTS/                  ← proiectele tale
├── _BEST_PRACTICES/           ← wisdom per tip proiect
├── _TEMPLATES/                ← scaffolding (android/carte/generic)
├── _SETTINGS/RULES/           ← protocoale workspace
├── _MEMORY/                   ← vault Obsidian
├── _METRICS/                  ← snapshots codeburn + optimize
├── _DASHBOARD.md              ← actualizat automat la SessionEnd
└── BEST_PRACTICES.md          ← încărcat la fiecare session start
```

---

## Componente și feature flags

Editează `.claude/helpers/feature-flags.json` pentru a activa/dezactiva:

```json
{
  "components": {
    "enneagram": true,   // routing inteligent
    "ssa":       true,   // filtrare context -76%
    "codeburn":  true,   // cost tracking real
    "red_hat":   true,   // evaluare critică
    "safla":     true,   // feedback adaptiv
    "graphify":  true,   // rapoarte sesiune
    "langraph":  true,   // workflow tracking
    "crewai":    false   // dezactivat permanent
  }
}
```

---

## Comenzi CLI

```bash
# Status sistem
node .claude/helpers/hook-handler.cjs flags

# Cost real (citeşte din ~/.claude/projects/)
node .claude/helpers/hook-handler.cjs burn

# Performance per agent Enneagram
node .claude/helpers/hook-handler.cjs safla

# Raport sesiune ASCII
node .claude/helpers/hook-handler.cjs graphify

# Workflow activ
node .claude/helpers/hook-handler.cjs lg

# Diagnostice intelligence/memory
node .claude/helpers/hook-handler.cjs stats
```

## Slash commands în Claude Code

```
/cost           → codeburn status (azi + luna)
/cost today     → detalii ziua curentă
/cost month     → detalii luna curentă
/cost report    → dashboard TUI interactiv
/cost optimize  → sugestii reducere waste
```

---

## Enneagram — routingul inteligent

9 noduri specializate, 2 cicluri de lucru:

| Nod | Agent | Rol | Ciclu |
|-----|-------|-----|-------|
| 1 | reviewer | QA, code review | hexad |
| 2 | backend-dev | integrare, API | hexad |
| 3 | coder | implementare directă | triangle |
| 4 | researcher | context, documentare | hexad |
| 5 | analyst | analiză, debugging | hexad |
| 6 | tester | validare, testare | triangle |
| 7 | architecture | design sistem | hexad |
| 8 | sparc-orchestrator | orchestrare complexă | hexad |
| 9 | memory-specialist | memorie, consolidare | triangle |

**HEXAD** (1→4→2→8→5→7): task-uri complexe, cross-project, ≥6 agenți  
**TRIANGLE** (3→6→9): task-uri rapide, implementare directă, 3 agenți

---

## SSA — Sparse/Selective Attention

Reduce contextul injectat la fiecare prompt:

- **Input:** toate entries din memoria Intelligence graph + Obsidian index
- **Algoritm:** Jaccard trigram similarity între prompt și fiecare entry
- **Output:** top-12 entries cele mai relevante + pinned (prioritate `critical`)
- **Rezultat tipic:** 50 entries → 12 entries (76% reducere)

**SSA Zoom levels** (detectate automat din lungimea promptului):
- `NANO` — prompt scurt (<15 cuvinte): context minim
- `MICRO` — prompt mediu (15-30 cuvinte): context moderat
- `MAHA` — prompt lung (>30 cuvinte): context maxim

---

## SAFLA — Feedback adaptiv

Urmărește ce funcționează pentru fiecare agent:

- **+0.05** weight adjustment la task reușit
- **-0.10** weight adjustment la task eșuat (asimetric — penalizare mai mare)
- **Sync cu CodeBurn:** la cost/call > $0.05 → penalizare automată pe noduri active
- **Range:** [-0.5, +0.5] per nod

---

## Dashboard automat

La fiecare SessionEnd, sistemul actualizează automat:

- **`_DASHBOARD.md`** — metrici CodeBurn live (cost azi/luna, calls, cost/call)
- **`_METRICS/codeburn-optimize-latest.md`** — sugestii waste reduction
- **`_METRICS/codeburn-<timestamp>.json`** — snapshot complet (background)
- **`.claude-flow/reports/session-<timestamp>.md`** — raport Graphify complet

---

## Performanță

| Hook | Overhead |
|------|----------|
| UserPromptSubmit | ~104ms |
| PreToolUse | ~95ms |
| PostToolUse | ~100ms |
| SessionStart | ~185ms |
| SessionEnd | ~117ms |

---

## Arhitectură conexiuni

```
UserPromptSubmit
    ├── SSA.filterContext(intelligence + Obsidian)
    ├── AutoOptimize.analyze(prompt)
    ├── RedHat.evaluate(prompt)
    ├── LangGraph.startWorkflow(prompt)
    ├── SAFLA.hint(node)
    └── Enneagram.routeTask(prompt)

SessionStart
    ├── SAFLA.sessionStart()
    └── obsidian-session-context.py → session-critical-index.json

SessionEnd
    ├── CodeBurn.totals() [cache-first]
    ├── SAFLA.syncWithCodeBurn(burnTotals)
    ├── Graphify.generateReport()
    ├── MetricsUpdate → _DASHBOARD.md + _METRICS/
    └── LangGraph.clearActive()
```

---

## Adaugă un proiect nou

```bash
# Copiază template-ul potrivit
cp -r _TEMPLATES/generic/ PROJECTS/NumeProiect/

# Editează CLAUDE.md al proiectului
nano PROJECTS/NumeProiect/CLAUDE.md

# Adaugă în tabelul de proiecte din CLAUDE.md root
```

---

## Credite

- **Workspace original:** [Hermeneuticus-of-things](https://github.com/Hermeneuticus-of-things/claude-code-eficient-workspace)
- **Ruflo/claude-flow:** [ruvnet](https://github.com/ruvnet/ruflo)
- **CodeBurn:** [getagentseal](https://github.com/getagentseal/codeburn)
- **v6.1 Micro extensions:** implementate în sesiunea 2026-05-08
