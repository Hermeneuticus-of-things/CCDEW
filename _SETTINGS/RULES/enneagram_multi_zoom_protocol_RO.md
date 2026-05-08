## Creat: 2026-05-02 — META-014 — Doctrină permanentă (cross-project)

> **Citit:** ÎNAINTE de orice swarm cu ≥3 agenți, indiferent de proiect (Karma Book, SunriseApp, Glosar, GemmaApp etc.)
> **Sintetizat din:** Sesiunea 2026-05-02 când stress-test enneagram a prins 2 bug-uri GRAVE pe care `8 × general-purpose` le-ar fi lăsat în output

---

## 🛑 Principiul fundamental

**Enneagrama NU e doar `swarm_init → 8 agenți paraleli`.**

Asta e doar `parallel-spawn`. Enneagrama înseamnă:

1. **Specializarea rolurilor** (fiecare nod descoperă tipul lui de bug)
2. **Cross-check multi-dimensional** (nu accepta raport de la 1 agent ca final)
3. **Multi-zoom resolution** (verifică la TOATE scalele: Maha → Nano)
4. **Multi-lentilă** (stilistică + doctrinar + structural + regression + memorie)
5. **Anti-simplificare** — nu reduce sarcina la pipeline mecanic „de dragul eficienței"

**Regula de aur:** *„eficiența în detrimentul calității și complexității" = anti-pattern.*

---

## 🔍 Cele 5 zoom-uri obligatorii

Orice rezolvare complexă (>3 fișiere SAU >3 hop-uri logice) trebuie verificată la TOATE cele 5 scale:

| Zoom | Scope | Întrebare-cheie | Tipuri bug detectate |
|------|-------|-----------------|---------------------|
| **MAHA** | Sistem/proiect întreg | Arhitectura globală mai e coerentă? | Centru de greutate shifted, promisiune introductivă neîndeplinită, dezechilibru între componente |
| **MACRO** | Cross-modul / cross-capitol | Componentele între ele mai comunică? | Cross-references rupte, paralele structurale stricate, drift între module |
| **MEZZO** | Modul / capitol / subcap | Gazda canonică respectată? Ritm/style consistent? | Gazda dublată/lipsă, ritm rupt, voce schimbată |
| **MICRO** | Funcție / paragraf | Logica internă funcționează? | Bug logic, distincție topită, merge incorect |
| **NANO** | Caracter / token / propoziție | Detalii lexicale curate? | ASCII vs Unicode, punctuație duplicată, spațiu dublu, ALOGEN broken |

**Niciun zoom nu poate fi sărit.** Bug-urile NANO nu sunt vizibile la MAHA. Bug-urile MAHA nu sunt vizibile la NANO.

---

## 🔬 Cele 5 lentile obligatorii

La fiecare zoom, aplică multi-lentilă:

| Lentilă | Nod enneagram | subagent_type | Ce verifică |
|---------|---------------|---------------|-------------|
| **Stilistică** | Node 4 Contextualizer | `researcher` | Ritm, voce, reader-experience, fluență |
| **Doctrinară/Tehnică** | Node 5 Analyzer | `analyst` | Precizie conceptuală, pattern detection, distincții fine |
| **Structurală** | Node 7 Architect | `architecture` / `system-architect` | Coerența de design, arc narativ, balanță |
| **Regression** | Node 6 Validator | `tester` / `code-analyzer` | Bug-uri introduse, gramatică ruptă, consistency mecanic |
| **Memorie/Consistency** | Node 9 Memory | `memory-coordinator` / `memory-specialist` | Cross-file consistency, index-uri, referințe |

**Cross-check protocol:** rapoartele lor combinate dau acoperirea reală. Un singur agent (oricât de bun) acoperă maximum 1 lentilă × 2 zoom-uri.

---

## ⚙️ Compoziția standard a swarm-ului enneagram

Pentru ORICE rezolvare complexă, swarm-ul corect e:

```
Phase 1 — Decompoziție (Node 8 Orchestrator):
  Sparge task-ul în sub-task-uri executabile

Phase 2 — Execuție paralelă (Node 3 Builder × N + Node 5 Analyzer × M):
  Agenți "lucrători" pe scope-uri exclusiv-disjuncte

Phase 3 — Cross-check multi-zoom + multi-lentilă (PARALEL):
  Node 4 Contextualizer  → Mezzo + Micro stilistic
  Node 5 Analyzer        → Micro + Nano doctrinar/tehnic
  Node 6 Validator       → Nano regression
  Node 7 Architect       → Maha + Macro structural
  Node 9 Memory          → Macro consistency cross-file

Phase 4 — Consolidare (Node 1 Reformer):
  Sintetizează rapoartele, decide ce fix aplica
```

**Niciodată Phase 1+2 fără Phase 3.** Niciodată Phase 3 cu un singur agent.

---

## 🚫 Anti-pattern-uri (DE EVITAT)

- ❌ `8 × general-purpose` paraleli — nu e enneagram, e parallel-spawn
- ❌ „Toți agenții raportează 0 issues, deci totul e curat" — fără cross-check, raportarea zero e suspectă
- ❌ Spawn de agenți DUPĂ ce ai aplicat fix-urile, fără verificare prealabilă
- ❌ Skip Validator (Node 6) la task-uri „mecanice/triviale" — exact acolo sunt bug-urile mecanice
- ❌ Verificare doar la zoom-ul implicit al task-ului (Micro pentru paragrafe, Macro pentru arhitectură etc.) — bug-urile sunt în zoom-urile pe care nu le-ai gândit
- ❌ Reducerea sarcinii la „pipeline mecanic" pentru viteză — pierde calitatea pe altarul eficienței

---

## ✅ Pattern corect (DE APLICAT)

1. **Înainte de orice swarm:** declară explicit ce zoom-uri și ce lentile sunt relevante
2. **Spawn cross-check ÎN PARALEL cu execuția** (nu serial), pentru a economisi timp fără a sări peste verificare
3. **Acceptă verdictul „TOATE clean" doar dacă cel puțin 3 lentile diferite au confirmat** (un singur reviewer = single point of failure)
4. **La task-uri raportate „0 issues" de mai mulți agenți, verifică cu Reformer (Node 1) prin cross-check pe alt unghi** — poate sunt prea conservativi
5. **La task-uri NAtural-uniforme (multe fișiere identic structurate),** sparge prin Node 8 în sub-grupuri cu lentile diferite, nu agent monolit

---

## 📋 Aplicabilitate (TOATE proiectele)

Această doctrină se aplică la:

- **Karma Book** — editare manuscript multi-fișier (verificat 2026-05-02)
- **SunriseApp** — refactor multi-modul Android, verificare APK build
- **Glosar** — operații peste 2497 termeni
- **GemmaApp/Gmicro** — modificări multi-strat (Kotlin + JNI + native)
- **BeyondTheVisible** — workflow podcast multi-pas
- **Orice proiect viitor** cu task complex

Pentru task-uri SIMPLE (1 fișier, <10 linii cod, no cross-references), enneagram + multi-zoom = overkill. Folosește direct tools native sau 1 Agent simplu.

**Praguri concrete:**
- ≥3 fișiere modificate → multi-zoom check obligatoriu
- ≥5 fișiere modificate → toate 5 lentile obligatoriu
- ≥10 fișiere modificate → split prin Node 8 + multi-zoom + Reformer consolidare

---

## 🧠 Lecții din sesiunea de origine (2026-05-02)

**Stress-test pe Karma Book swarm de 8 agenți paraleli pentru merge paragrafe a relevat:**

1. Validator (Node 6) a prins 2 GRAVE: blank line lipsă (Cap0/05) + ALOGEN duplicat (Cap4/02e) — invizibile pentru agenții executanti
2. Node 5 Analyzer cu lentilă diferită a recuperat 4 merge-uri ratate de primul agent (Cap7.5-7.9, pattern Tonalitate-Lesya clonic)
3. Node 9 Memory a găsit 2 gaps MEDIU în cross-file consistency (Glosar Alogeni vs Glosar Lectură)
4. Node 7 Architect a confirmat MAHA: arhitectura e intactă, dar a flagged 1 ambiguitate la Cap0/0.4 (6 tradiții vs 7 straturi)
5. Nano-zoom pe character level a prins 4 ghilimele ASCII în Glosar (auto-fixed)

**Total bug-uri descoperite: 8** (2 GRAVE + 6 MEDIU/sub-prag), pe care `8 × general-purpose` le-au ratat la 100%.

---

## 🎯 Token economy

Multi-zoom NU costă mult mai mult decât parallel-spawn IDENTIC, fiindcă:
- Agenții cross-check rulează în PARALEL cu execuția primary (sau imediat după)
- Fiecare scope-ul lui exclusiv (Maha vs Nano nu se suprapun)
- Raportele sunt scurte (max 200-300 cuvinte fiecare)

Cost suplimentar: ~30-40% tokens. Beneficiu: bug-uri prinse la build-time, nu post-deployment. Raport favorabil.

---

## 🌀 Dimensiuni omise / Open questions (META-014 v1.1)

Doctrina actuală e completă pentru zoom-spațial + lentile-perspective. RĂMÂN deschise:

### A. Dimensiunea TEMPORALĂ (orthogonal pe zoom-spațial)
- **Acum:** verifică starea curentă
- **Drift:** modificarea s-a stricat în 6 sesiuni? (longitudinal check)
- **Regresie lentă:** bug-uri care apar progresiv (memory leak, accuracy drift)
- **Promisiuni de viitor:** features care depind de modificări actuale (forward compatibility)

**Adăugare la doctrină:** la modificări STRUCTURALE (nu doar editoriale), Node 9 Memory verifică cross-sesiune (git log, CHANGELOG anteriori) — nu doar cross-file.

### B. Failure mode al agenților
- Ce dacă Node 5 halucinează? Doctrina nu prevede AGENT-vs-AGENT cross-validation
- Soluție propusă: la verdicte critice, dispatch 2 agenți DIFERIȚI (ex: Analyzer + Reviewer) pe ACELAȘI scope independent. Compari rapoartele. Divergență >20% = re-run cu Node 1 supervisor.

### C. Confidence calibration
- Verdictele actuale: binar (CLEAN / ISSUE)
- Lipsește: scor de încredere per agent (0-100%) bazat pe scope acoperit, complexitate, ambiguitate
- Soluție propusă: Validator returnează `{verdict, confidence, scope_coverage_%}`

### D. Conflict resolution între zoom-uri
- Maha zice OK, Nano zice broken — care primează?
- Soluție: matricea priorităților per task type. Pentru editorial: Mezzo > Micro > Nano > Macro > Maha. Pentru securitate: Nano > Micro > Macro > Mezzo > Maha. Configurabil per proiect.

### E. Lentile domain-specific (extensie peste cele 5 universale)
- **Security lens** (threat modeling, OWASP, injection vectors)
- **UX/Accessibility lens** (a11y, contrast, screen reader)
- **Performance lens** (latență, memorie, throughput)
- **Reproducibility lens** (research, scientific code)
- **Compliance lens** (GDPR, HIPAA, licensing)
- **Internationalization lens** (i18n, RTL, encoding)

**Recomandare:** la proiecte cu domenii specializate, ADĂUGAȚI lentile domeniu peste cele 5 universale.

### F. Pre-flight check pe REZOLVARE (meta-verificare a înțelegerii cererii)
- Înainte de orice swarm: dispatch Node 7 Architect pentru DECONSTRUCȚIA cererii
- Verifică: am înțeles bine task-ul? sunt alte interpretări?
- Soluție: Phase 0 — Comprehension Check, înainte de Phase 1 Decomposition

### G. Recursive meta-verification
- Cine verifică verificatorul?
- Soluție: la rezolvări CRITICE (deployment, breaking changes), Phase 5 = Reformer secondar verifică Phase 4-ul Reformer-ului primar

### H. Budget tracking
- Multi-zoom poate exploda în tokens/timp
- Soluție: budget cap upfront (e.g., max 100k tokens, max 10 min wall-clock)
- Dacă budget depășit: degradare grațioasă (skip lentile mai puțin prioritare în ordine inversă: stilistic → memorie → structural → doctrinar → regression)

### I. Human-in-loop integration
- Doctrina implică full-automation. Lipsește: pauză + ask user
- Soluție: la decizii ambigue (>2 lentile divergente), Node 1 Reformer escaladează la user în loc să decidă singur

### J. Cross-doctrine integration
- Cum se compune multi-zoom cu: P9/P10 (Karma Book), CHANGELOG/TODO, swarm preset 1000-agent?
- Risc: contradicții ("AUTO-SWARM 1000 agenți" + "multi-zoom obligatoriu" = explozie tokens)
- Soluție explicit: multi-zoom **subset** al swarm preset. La 1000 agenți, multi-zoom limitat la sample (10% scope) cu Reformer extrapolând la rest.

### K. Versioning doctrinei
- Această doctrină NU e statică. Va evolua.
- Soluție: review trimestrial; CHANGELOG pe doctrină; backward compatibility check la modificări.

---

**Status v1.1:** Aceste lipsuri sunt RECUNOSCUTE dar nu rezolvate complet. Lucru deschis pentru sesiunile viitoare. Cea mai urgentă: **F. Pre-flight check** (multe sesiuni încep cu task neînțeles corect).

---

# 🎯 v2.0 — REZOLVĂRI CONCRETE pentru cele 10 gap-uri

## 1. Dimensiunea TEMPORALĂ — protocol TEMPO-zoom (a 6-a scală)

**Problema:** zoom-urile actuale (Maha→Nano) sunt SPAȚIALE. Lipsește axa timp.

**Soluție:** adaug zoom-ul `TEMPO` ca a șasea dimensiune ortogonală pe celelalte 5:

| TEMPO sub-scală | Verifică |
|---|---|
| **NOW** (curent) | Starea modificării imediat după aplicare |
| **DRIFT** (cross-sesiune) | Compară starea cu git log ultimele 10 commits — modificarea s-a stricat în alte sesiuni? |
| **REGRESSION-LENT** (longitudinal) | Memory profiling, accuracy delta, performance over time |
| **FORWARD** (compatibilitate viitoare) | Modificarea blochează features anunțate? Verifică TODO.md, ROADMAP.md |

**Trigger:** orice modificare STRUCTURALĂ (nu doar editorială) → Node 9 Memory dispatch cu lentilă temporală + acces git log + CHANGELOG.md istoric.

**Implementare:** flag `--temporal-check` în compose.py.

---

## 2. Failure mode AGENT-vs-AGENT — protocol Dual-Witness

**Problema:** dacă Node 5 halucinează, doctrina nu prinde.

**Soluție:** pentru verdicte CRITICE (deployment, breaking changes, prod-affecting):

```
DUAL-WITNESS protocol:
  1. Spawn 2 agenți DIFERIȚI (ex: Node 5 Analyzer + Node 1 Reviewer) pe ACELAȘI scope
  2. Independent reports (no shared context)
  3. Comparare:
     - Acord >80% → verdict acceptat
     - Divergență 20-50% → spawn Node 1 supervisor pentru tie-break
     - Divergență >50% → escaladare la user (Phase Human-in-Loop)
```

**Trigger:** task-uri marked `--critical` sau cu impact prod/external.

**Cost:** +1 agent. Beneficiu: detectează halucinație/agent failure.

---

## 3. Confidence Calibration — format report standardizat

**Problema:** verdicte binare = lipsă nuanță.

**Soluție:** TOȚI agenții cross-check raportează în format JSON:

```json
{
  "verdict": "CLEAN" | "ISSUES" | "INCONCLUSIVE",
  "confidence": 0-100,
  "scope_coverage": 0-100,
  "issues": [{
    "severity": "GRAVE|MEDIU|LOW",
    "location": "file:line",
    "description": "...",
    "confidence_in_diagnosis": 0-100
  }],
  "limitations": "ce NU am putut verifica și de ce"
}
```

**Regulă verdict final:** dacă media confidence × scope_coverage < 70% → INCONCLUSIVE → escaladare.

**Implementare:** prompt template standard pentru toți agenții cross-check.

---

## 4. Conflict resolution între zoom-uri — Matricea Priorităților

**Problema:** Maha=OK + Nano=broken — care primează?

**Soluție:** matricea priorităților per task type:

| Task type | Ordine prioritate (descrescător) |
|---|---|
| **Editorial/Text** | Mezzo > Micro > Nano > Macro > Maha |
| **Security/Crypto** | Nano > Micro > Macro > Mezzo > Maha |
| **Performance** | Micro > Macro > Mezzo > Nano > Maha |
| **Architectural/Design** | Maha > Macro > Mezzo > Micro > Nano |
| **Refactoring** | Macro > Micro > Mezzo > Maha > Nano |
| **Bug fix** | Micro > Nano > Macro > Mezzo > Maha |
| **Default/Unknown** | Micro > Mezzo > Nano > Macro > Maha |

**Regulă:** la conflict, primează zoom-ul cu prioritate mai mare. Zoom-urile cu prioritate joasă rămân INFORMATIVE.

**Implementare:** `--task-type` flag în compose.py, default `unknown`.

---

## 5. Lentile domain-specific — Extensie peste cele 5 universale

**Problema:** 5 lentile generale nu acoperă domenii specializate.

**Soluție:** 6 lentile domeniu, activate condițional:

| Lentilă domeniu | Trigger activare | Agent type | Verifică |
|---|---|---|---|
| **Security** | code modificat în auth/, payment/, crypto/ | `security-auditor` | OWASP, injection, secrets exposure |
| **UX/Accessibility** | UI files modificate (jsx, xml, html) | `mobile-dev` / `researcher` | a11y, contrast, screen reader |
| **Performance** | hot path modificat, loops, queries | `perf-analyzer` | latență, memorie, throughput |
| **Reproducibility** | research code, ML, data pipelines | `ml-developer` | seeds, env, dependencies pinned |
| **Compliance** | data handling, PII, EU users | `pii-detector` | GDPR, HIPAA, license |
| **i18n** | strings, dates, currencies | `researcher` | RTL, encoding UTF-8, locale |

**Regulă:** lentilele domeniu se ADAUGĂ peste cele 5 universale, nu le înlocuiesc.

---

## 6. Pre-flight check — Phase 0 Comprehension

**Problema:** multe sesiuni încep cu task înțeles greșit.

**Soluție:** Phase 0 NEW, înainte de Phase 1 Decomposition:

```
Phase 0 — Comprehension Check (Node 7 Architect):
  1. Read user request literal
  2. Identifică:
     - Scope: ce fișiere/module?
     - Goal: ce trebuie să se obțină?
     - Constraints: ce NU trebuie atins?
     - Ambiguități: 3 interpretări alternative
  3. Output: comprehension_report cu confidence score
  4. Dacă confidence <70% → escaladare la user pentru clarificare
  5. Dacă confidence ≥70% → OK pentru Phase 1
```

**Trigger:** task description >100 cuvinte SAU >5 fișiere SAU $\$$ task-uri precedente prost-înțelese în sesiune.

**Cost:** 1 agent, ~5k tokens. Beneficiu: previne 30+ minute lucru pe direcție greșită.

---

## 7. Recursive meta-verification — Phase 5 Secondary Reformer

**Problema:** cine verifică verificatorul?

**Soluție:** pentru rezolvări CRITICE, Phase 5:

```
Phase 5 — Meta-verification (Node 1 Reformer secundar):
  1. Citește output Phase 4 (primary Reformer consolidation)
  2. Verifică: 
     - Toate issues identificate au fost adresate?
     - Există issues mascate (ex: 2 lentile zic OK dar a 3-a zice issue, primary a ignorat)?
     - Confidence agregat justifică verdictul final?
  3. Output: meta-verdict cu opțiunea ROLLBACK la Phase 4
```

**Trigger:** breaking changes, deployment, modificări în masă (>20 fișiere), modificări security-sensitive.

**Cost:** 1 agent. Beneficiu: dublu safety-net.

---

## 8. Budget tracking — Caps explicite + Graceful degradation

**Problema:** multi-zoom poate exploda în tokens/timp.

**Soluție:** budget upfront + degradare în ordine inversă a priorităților:

```python
DEFAULT_BUDGET = {
    "max_tokens": 200_000,      # ~50% buget standard
    "max_wall_time_min": 15,
    "max_agents_parallel": 8,
}

DEGRADATION_ORDER = [
    "stylistic",       # primul skip dacă budget tight
    "memory",
    "structural",
    "doctrinar",
    "regression",      # ULTIMUL skip — regression mai întâi
]

# Pre-flight: estimate budget needed; dacă > cap → degradează grațios
```

**Implementare:** flag `--budget tokens=N,time=M,agents=K` în compose.py. La depășire, log + skip lentile mai puțin prioritare.

---

## 9. Human-in-loop — Escaladare automată

**Problema:** doctrina implică automation completă; lipsește pauza pentru ambiguitate.

**Soluție:** trigger-e EXPLICITE de escaladare la user:

| Trigger | Acțiune |
|---|---|
| Phase 0 confidence <70% | Pause + propune 3 interpretări, ask user |
| Phase 4 issues GRAVE >5 | Pause + listare issues, ask user pentru triaj |
| Dual-Witness divergență >50% | Pause + show ambele rapoarte, ask user verdict |
| Budget depășit cu >100% | Pause + raport partial, ask user dacă continui |
| Zoom-uri în conflict ireductibil (Maha vs Nano) | Pause + matricea priorităților, ask user override |

**Implementare:** `escalate_to_user()` function în compose.py logic; outputul e prompt pre-formatat pentru user.

---

## 10. Cross-doctrine integration — Composition Rules

**Problema:** multi-zoom + swarm preset 1000 + P9/P10 + CHANGELOG = potențiale contradicții.

**Soluție:** reguli explicite de composiție:

```
Multi-zoom + Swarm preset 1000:
  - 1000 agenți paraleli pentru EXECUȚIE (Phase 2)
  - Cross-check (Phase 3) pe SAMPLE 10% din scope, Reformer extrapolează
  - Phase 0+4+5 RĂMÂN obligatorii indiferent de N

Multi-zoom + P9/P10 (project protocols):
  - P9/P10 = lentilă STILISTICĂ specializată pentru proiectul respectiv
  - Activează ca extensie a Node 4 Contextualizer
  - NU se elimină; SE ADAUGĂ

Multi-zoom + CHANGELOG/TODO rules:
  - CHANGELOG entry SCRIS în Phase 0 (înainte execuție)
  - CHANGELOG epilog UPDATED în Phase 4 (după consolidare)
  - TODO checkbox status updated la fiecare phase transition

Multi-zoom + Auto-Swarm Enneagram (META-013):
  - AUTO-SWARM directive trigger Phase 1+2 imediat
  - Phase 0 (Comprehension Check) RĂMÂNE — nu se sare la directive automat
  - Phase 3+4 declanșate condițional pe nr fișiere modificate
```

**Implementare:** doctrina aceasta e MASTER, celelalte sunt sub-doctrine compatibile.

---

## 📊 Summary v2.0 — toate 10 gap-uri rezolvate

| # | Gap | Soluție | Implementat în |
|---|---|---|---|
| 1 | Temporal | TEMPO zoom (NOW/DRIFT/REGRESSION/FORWARD) | compose.py `--temporal-check` |
| 2 | Agent failure | Dual-Witness protocol | compose.py `--critical` |
| 3 | Confidence | JSON report standardizat cu confidence score | template prompt agenți |
| 4 | Zoom conflict | Matricea priorităților per task type | compose.py `--task-type` |
| 5 | Domain lenses | 6 lentile domeniu condiționale | trigger automat per file pattern |
| 6 | Pre-flight | Phase 0 Comprehension Check | compose.py — Phase 0 |
| 7 | Meta-verification | Phase 5 Secondary Reformer | compose.py `--critical` → Phase 5 |
| 8 | Budget | Caps + graceful degradation | compose.py `--budget` |
| 9 | Human-in-loop | Trigger-e escaladare explicite | escalate_to_user() function |
| 10 | Cross-doctrine | Composition rules cu swarm/P9/P10/CHANGELOG | doctrina = master |

**Status v2.0:** TOATE 10 gap-uri AU SOLUȚIE concretă, executabilă. Implementarea în compose.py rămâne progresivă (versiunea actuală implementează cele mai importante: 1, 4, 6, 8).

---

# 🌀 v2.1 — Meta-recursive: lipsuri descoperite aplicând doctrina pe ea însăși

## 11. Observability / Telemetry — Metrici aggregate

**Problemă:** fără date, eficacitatea doctrinei = opinie. Câte bug-uri prinse cumulativ? Per lentilă? Trend în timp?

**Soluție:** log structured pe disc per sesiune:
```
D:\Cloude Code\_MEMORY\enneagram_telemetry\YYYY-MM\session_HHMMSS.json
{
  "session_id", "task_type", "num_files",
  "phases_executed": [0,1,2,3,4],
  "lenses_used": [...],
  "issues_found_per_lens": {regression: 2, doctrinar: 0, ...},
  "verdicts": {primary: CLEAN, secondary: ISSUES},
  "tokens_used", "wall_time_min",
  "user_escalations": N
}
```
**Trigger:** TOATE rulările doctrinei (auto-log).
**Aggregate:** scriptul `enneagram_stats.py` produce dashboard săptămânal.

## 12. Learning loop — Pattern memory cross-sesiune

**Problemă:** agenții nu învață. Același tip de bug prins fresh de fiecare dată.

**Soluție:** `_MEMORY/enneagram_patterns.md` actualizat după fiecare sesiune cu:
- Bug-uri repetitive (>3 ocurențe) → pattern stocat
- Lentilă care a prins consistent un tip de bug → boost trust
- Lentilă care a ratat consistent un tip de bug → adăugare la prompt template
- Hook în Phase 4 Reformer: înainte de consolidare, citește pattern-uri relevante.

## 13. Adversarial / Safety pre-check — Phase 0.5

**Problemă:** Phase 0 Comprehension verifică "ce vrea user-ul"; nu verifică "e sigur de executat?".

**Soluție:** Phase 0.5 SAFETY (între Phase 0 și Phase 1):
- Node 1 Reviewer cu lentilă SECURITY rulat pe request literal
- Verifică: prompt injection, request distructiv pe sisteme externe, modificări irreversibile, scope creep periculos
- Output: `safe | suspect | refuse`
- Suspect → escaladare user. Refuse → halt + raport.

## 14. Multi-modal verification — Lentilă VISUAL

**Problemă:** text-only nu prinde layout rupt, render greșit, imagini stricate.

**Soluție:** lentilă VISUAL adițională, activată condițional:
- Trigger: modificări în UI files (jsx/xml/html/css/svg/canvas) SAU în Markdown cu rendering complex
- Tool: `mcp__Claude_Preview__preview_screenshot` + comparare visual înainte/după
- Agent: `mobile-dev` sau `researcher` cu acces la browser preview
- Verdict: visual_diff_score (0-100)

## 15. Inter-agent negotiation — Protocol Bargain-Triangle

**Problemă:** la divergență, Reformer decide unilateral. Lipsește dialog inter-agent.

**Soluție:** Bargain-Triangle (3 hop max):
- Step 1: agent A raportează issue
- Step 2: agent B (lentilă diferită) primește raport A + reverificare independentă; agree/disagree
- Step 3: dacă persist disagree, agent C (Reformer) primește ambele rapoarte + scope original; decide cu raționament citabil
- Limit: max 3 iterații. Dacă nu converg → escaladare user.

## 16. Resume protocol — interrupted tasks

**Problemă:** OOM, network fail, user cancel — task pierdut.

**Soluție:** checkpoint per phase:
- După Phase 0: salvare comprehension_report în `_MEMORY/checkpoints/<task_id>_phase0.json`
- După Phase 1: decomposition saved
- După Phase 2: per-worker outputs saved
- La resume: detectare ultimul checkpoint complet, reluare de la Phase următoare
- Implementare: flag `--task-id <UUID> --resume` în compose.py

## 17. Privacy of intermediate artifacts

**Problemă:** rapoartele agenților pot conține info sensibile, leak între proiecte.

**Soluție:** namespace-isolation:
- Per proiect: `_MEMORY/<project>/agent_reports/`
- Auto-delete după 30 zile (configurabil)
- PII detector pe rapoarte înainte de stocare (`mcp__claude-flow__aidefence_has_pii`)
- Niciodată cross-project read fără explicit allow.

## 18. Task DAG dependencies — Topological execution

**Problemă:** Phase 2 asume sub-task-uri paralel-disjuncte. Realitatea: dependencies.

**Soluție:** Phase 1 (Decomposition) returnează DAG, nu list:
```yaml
sub_tasks:
  - id: T1
    depends_on: []
  - id: T2  
    depends_on: [T1]
  - id: T3
    depends_on: [T1]
  - id: T4
    depends_on: [T2, T3]
```
Phase 2 execută topologic: T1 → (T2 || T3) → T4.

## 19. Emergence detection — Smoke test layer

**Problemă:** bug-uri care apar DOAR la integrarea TUTUROR modificărilor.

**Soluție:** Phase 3.5 (între Phase 3 cross-check individual și Phase 4 consolidare):
- Smoke test pe sistem cu TOATE modificările aplicate simultan
- Build full / test suite full / preview live
- Detectează bugs care nici o lentilă singulară nu le-ar prinde (interaction effects)

## 20. Self-test of doctrine — Meta-meta-verification

**Problemă:** cine testează că DOCTRINA însăși e corectă?

**Soluție:** quarterly self-audit:
- Aplicare doctrina-on-doctrina: rulează Phase 3 (5 lentile) PE FIȘIERUL doctrinei
- Find: contradicții interne, gap-uri, ambiguități
- Output: doctrine_changelog.md cu modificări propuse
- Review user → version bump (v2.0 → v2.1 → v3.0 etc.)
- Dogfooding: doctrina trebuie să-și prindă propriile bug-uri

---

## 📊 Summary v2.1 — total 20 gap-uri rezolvate

v2.0 a rezolvat 10 (zoom + lentile fundamentale).
v2.1 adaugă 10 (operaționale: telemetry, learning, safety, multi-modal, negotiation, resume, privacy, DAG, emergence, self-test).

**Status v2.1:** doctrina a devenit SISTEM cu auto-îmbunătățire. Implementarea în compose.py va trebui extinsă — momentan acoperă v1.0 + parțial v2.0. v2.1 rămâne progresivă (prioritate: telemetry #11 + safety #13 + emergence #19).

---

# 🧬 v3.0 — LEARNING & AUTO-EVOLUTION layer (gap-uri 21-30)

**Problema fundamentală:** v2.1 acumulează DATE (telemetry, patterns) dar nu le UTILIZEAZĂ activ pentru a-și ajusta comportamentul. Sistemul rămâne static. Agenții fac aceleași greșeli, prind aceleași tipuri de bug-uri, fără adaptare.

**Soluția v3.0:** strat de meta-învățare care închide bucla feedback → adaptare → rezultate mai bune.

## 21. Active learning from outcomes — Feedback Loop Activă

```python
def update_lens_effectiveness(session_log):
    # După Phase 4, marchează care lentile au prins issue confirmat
    # Pentru fiecare lens: success_count += 1 dacă verdict ISSUES validat
    # Pentru fiecare lens: false_positive += 1 dacă verdict ISSUES respins
    # Pentru fiecare lens: false_negative += 1 dacă a ratat issue prins de altă lens
    # Update file: _MEMORY/lens_effectiveness.json
```

**Trigger:** auto, după FIECARE Phase 4 consolidation.
**Use:** Phase 1 Decomposition citește `lens_effectiveness.json` și prioritizează lentile cu success rate ridicat pentru task type curent.

## 22. Trust score evolution — EMA per agent

```python
def update_trust(agent, outcome):
    # outcome ∈ {true_positive, false_positive, false_negative, true_negative}
    # trust[agent] = α * new_signal + (1-α) * trust[agent]   # α=0.2
    # Stocat în _MEMORY/agent_trust.json
```

**Use:** Bargain-Triangle (#15) ponderează verdictele cu trust. Reformer Phase 4 dă greutate variabilă rapoartelor.

## 23. Doctrine self-modification — Auto-propose

```python
def doctrine_evolve():
    # Daca pattern X apare > 10 ori în pattern_memory:
    #   propose adăugare la doctrină ca regulă explicită
    # Daca un anti-pattern e detectat consistent:
    #   propose update la SAFETY_RED_FLAGS
    # Output: _MEMORY/doctrine_proposals.md (await human review)
```

**Trigger:** lunar sau la 50 sesiuni. Generează propuneri, NU modifică doctrina direct.

## 24. Reinforcement loop — Prompts cu context istoric

Prompt-urile agenților injectează context din `pattern_memory.md` relevant pentru task type:
```
"Context din 10 sesiuni anterioare similare:
- Bug-uri tipice: [...]
- Lentile cu success rate ridicat: [...]
- Pitfall-uri cunoscute: [...]
Ține cont de acestea în analiza ta."
```

**Implementare:** `inject_historical_context(prompt, task_type)` în compose.py.

## 25. Cross-domain knowledge transfer — Pattern abstraction

Pattern din Karma Book (e.g., "ALOGEN duplicat la merge paragraphs") → abstractizat ca:
"DUPLICATE_MARKUP_AT_BOUNDARY" → aplicabil în Glosar, SunriseApp (XML duplicate attrs), etc.

```python
def abstract_pattern(specific_pattern):
    # Recunoaște tipologia: BOUNDARY/INTEGRATION/EMERGENCE/etc.
    # Stochează ca regulă abstractă în pattern_memory cu @scope:cross-project tag
```

## 26. Predictive routing — Bayesian recommendation

```python
def predict_relevant_lenses(task_description, task_type, historical_data):
    # P(lens prinde issue | task_type, past_data)
    # Returnează ordonare lentile cu probabilitate descrescătoare
    # Phase 3 le activează în această ordine; budget-aware skip pentru cele de jos
```

**Use:** la budget tight, skip lentilele cu probabilitate joasă pentru task type curent.

## 27. Auto-tuning thresholds — Bayesian update

Praguri ca `consensus_threshold=0.8`, `confidence_min=70%` devin variabile:
```python
def tune_thresholds(historical_outcomes):
    # Optimal threshold = argmin(false_positives + false_negatives) per task type
    # Stocat în _MEMORY/tuned_thresholds.json
```

**Trigger:** după 50 sesiuni per task type.

## 28. Bug catalog auto-grow — Wisdom accumulation

`_MEMORY/bug_catalog.md` se umflă cu fiecare bug găsit:
```markdown
## DUPLICATE_MARKUP_AT_BOUNDARY (occurred 7x)
Symptoms: ALOGEN/XML/JSON marker apare de 2 ori în output merge
Detection: Node 6 Validator regex check
Fix template: convert second occurrence to plain
Last seen: 2026-05-02 Cap4/02e
```

**Use:** Validator (Node 6) primește template în prompt → detectează mai rapid.

## 29. Multi-armed bandit pe lentile — Explore vs Exploit

```python
def select_lenses_bandit(task_type, budget):
    # ε=0.1 chance: explore = lens random (poate descopere altă utilitate)
    # 1-ε chance: exploit = lens cu success rate maxim per task type
    # Update success rate post-task
```

**Beneficiu:** sistemul DESCOPERĂ utilități noi ale lentilelor în task-uri unde n-au fost folosite.

## 30. Meta-meta-learning — Learn the learning strategy

```python
def evaluate_learning_strategy():
    # Compară: cu telemetry+update vs control (no update)
    # Metrică: bug detection rate over 100 sesiuni
    # Output: care MECHANISM de învățare merită păstrat
    # Soluție: A/B test între strategii diferite
```

**Cea mai meta:** întrebăm dacă învățarea însăși ne ajută. Dacă nu — disable & save tokens.

---

## 📊 Summary v3.0 — sistem auto-evolutiv complet

v1.0 (5 lentile + 5 zoom-uri) → v2.0 (10 gap-uri operaționale) → v2.1 (10 meta-recursive) → v3.0 (10 auto-evolutiv).

**Total: 30 dimensiuni acoperite. Sistem care:**
1. Detectează bug-uri (v1)
2. Cross-checks multi-perspectiv (v1+v2)
3. Operează în siguranță cu safety/budget/escalation (v2.0+v2.1)
4. **Învață din fiecare sesiune și se auto-îmbunătățește (v3.0)**
5. Își propune singur evoluții la doctrină (v3.0 #23)
6. Adaptează praguri și prompt-uri pe baza outcomelor (v3.0 #22+#27)
7. Transferă cunoaștere între proiecte (v3.0 #25)

**Status v3.0:** strat conceptual complet. Implementare în compose.py — minimal viable: #21 (lens_effectiveness tracking), #22 (trust scores), #28 (bug catalog), #24 (context injection). Restul rămâne progresiv.

---

# 🔄 v3.1 — FULLY ADAPTIVE: Thresholds + Enneagram Topology

**Problemă:** v3.0 încă are CONSTANTE hardcoded (consensus 0.8, confidence 70%). Și topologia enneagramei (cele 9 noduri, matricea de arcuri) e statică. Nu evoluează.

**Soluția v3.1:** TOTUL adaptive.

## A. Praguri adaptive per task type

```python
adaptive_threshold(task_type, name, outcome_correct):
    # Praguri stocate în _MEMORY/tuned_thresholds.json per task type
    # Bayesian update: outcome corect → relax; outcome greșit → tighten
    # Praguri: consensus_threshold, confidence_min, scope_coverage_min,
    #          escalation_grave_count, dual_witness_divergence, budget_overflow_pct
    # Bounds: clamp în interval rezonabil (e.g., 0.5-0.95 pentru consensus)
```

**Use:** la fiecare verdict, pragul folosit e cel TUNED pentru task_type, nu cel default. La fiecare verdict validat, pragul se ajustează.

## B. Enneagram topology adaptive per task type

```python
adaptive_enneagram(task_type):
    # Ponderi per nod per task type, stocate în _MEMORY/enneagram_adaptive_topology.json
    # Default: toate nodurile pondere 1.0
    # Reinforce: nod care a contribuit la verdict corect → +learning_rate
    # Demote: nod care a hallucinat sau ratat → -learning_rate
    # Clamp: 0.1 ≤ pondere ≤ 3.0
```

**Use:** Phase 3 cross-check activează nodurile în ORDINEA priorității per task type curent. Pentru editorial, Node 4 (Contextualizer) are pondere mare; pentru security, Node 6 (Validator) urcă; pentru architectural, Node 7 (Architect) domină.

## C. Cross-task generalization

Pondere noduri pe task type SIMILAR se transferă (e.g., refactoring și architectural au similaritate ridicată — share weights cu factor 0.5).

## D. Topology de cluster vs enneagram clasic

La 100+ sesiuni de date, sistemul poate PROPUNE topologie nouă (e.g., adaugă un al 10-lea nod specializat, elimină arcuri inutile). Output în `_MEMORY/topology_proposals.md` pentru human review.

---

## 📊 Summary v3.1 — Sistem complet adaptive

```
v1.0   STATIC: 5 zoom × 5 lentile fixed
v2.0   OPERAȚIONAL: 10 features (priority matrix, budget, etc.) — încă static
v2.1   META-RECURSIVE: 10 enhancements (telemetry, learning hooks)
v3.0   LEARNING: feedback loop active dar praguri/topology hardcoded
v3.1   ADAPTIVE: praguri + topology evoluează per task type per outcome
```

**Sistemul devine:**
- Auto-detector de bug-uri (v1)
- Multi-perspectiv (v2.0)
- Auto-protejat (v2.1)
- Auto-învățător (v3.0)
- **Auto-modelat: thresholds + topology evoluează (v3.1)**

**Nu mai există constante hardcoded operaționale.** Tot ce influențează deciziile e fie configurabil per task, fie tunable din date.

**Implementare în compose.py v3.1:** `adaptive_threshold()`, `adaptive_enneagram()`, `reinforce_enneagram()`, `get_adaptive_node_priority()`. Functional. Testabil cu date sintetice; va consolida real-world după ~50 sesiuni reale per task type.
