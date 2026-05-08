# Workspace CHANGELOG — <WORKSPACE_DIR>

Jurnal cerinte si modificari **la nivel workspace** (nu per-proiect).
Per-proiect: vezi `PROJECTS/<Nume>/CHANGELOG.md`.

---

## 2026-04-09 — Sistem Holografic de Scurtaturi (restructurare CLAUDE.md)

### Cerinta user (citat aproximativ):
> "ca sa nu consumi din tokeni tai mereu incepind cu root (CLAUDE.md), sa facem la fel si holografica la toate fisierele (CLAUDE.md) da si altele, creaza reguli pentru celelalte reguli pana la nivel de detalii proiect, si asa sa includa sa consumi corect si deja scurtaturi ca sa nu mai cauti tu la tine in memorie"

**Traducere:** Restructureaza toate fisierele `CLAUDE.md` + reguli intr-un sistem **holografic fractal** unde:
1. Fiecare fisier CLAUDE.md e un **index minimal** (nu detaliu)
2. Detaliile se citesc **on-demand** pe baza task-ului
3. "Reguli despre reguli" — meta-index care trimite la reguli granulare
4. Scurtaturi explicite — nu mai caut in memorie, urmez index-ul

### Problema rezolvata
**Inainte:** La fiecare session start se incarcau automat:
- `<WORKSPACE_DIR>\CLAUDE.md` — 7.6 KB
- `PROJECTS/MyAndroidApp/CLAUDE.md` — 35.9 KB
- `PROJECTS/MyBook/CLAUDE.md` — 8.6 KB (cand lucrez pe carte)
- `PROJECTS/MyResearch/CLAUDE.md` — 4.9 KB (cand lucrez pe glosar)
- **Total auto-load: ~57 KB = ~14000 tokeni inutili**

Multe reguli erau duplicate intre root si proiect. Detalii arhitecturale (TatwaWheel, TattvaSystem, Astro Module, widget layouts) erau incarcate chiar si cand task-ul nu le cerea.

### Structura noua — 3 nivele

**Nivel 0 — `<WORKSPACE_DIR>\CLAUDE.md`** (slim ~3 KB, auto-loaded):
- 3 reguli necondiționate inline (CHANGELOG, TODO, EPILOG)
- Tabel-index catre `_SETTINGS/RULES/`
- Lista proiecte active
- Restrictii root

**Nivel 1 — `_SETTINGS/RULES/`** (cross-project, on-demand):
- `INDEX.md` — master map "cand citesc ce"
- `session_start.md` — 3 reguli critice detaliate
- `changelog.md` — format CHANGELOG + scope detaliat per versiune
- `bug_log.md` — format BUG_LOG + cand creez intrare
- `cerinta_noua.md` — salvare cerinta mid-task in TODO.md
- `versioning.md` — schema generica V [stadiu] Major.Minor.Build

**Nivel 2 — `PROJECTS/<Nume>/CLAUDE.md`** (slim, auto-loaded pt proiect activ):
- Versiune curenta + stack minim
- Tabel-index catre `doc/` al proiectului
- Pointer la `_SETTINGS/RULES/` pt reguli generale

**Nivel 3 — `PROJECTS/<Nume>/doc/`** (on-demand, detalii granulare):
- **MyAndroidApp** (7 fisiere): ARCHITECTURE, TATTVA_WHEEL, HOME_SCREENS, ASTRO, WIDGETS, BUILD_TEST, FEATURES
- **MyBook** (3 fisiere): BOOK_STRUCTURE, EXPORT, TOOLS
- **MyResearch** (3 fisiere): FORMAT, SCRIPTS, STATE

### Fisiere noi create

**`_SETTINGS/RULES/`** (6 fisiere):
- INDEX.md
- session_start.md
- changelog.md
- bug_log.md
- cerinta_noua.md
- versioning.md

**`PROJECTS/MyAndroidApp/doc/`** (7 fisiere):
- INDEX.md
- ARCHITECTURE.md — package structure, services, persistence
- TATTVA_WHEEL.md — Tattva system + TatwaWheel components + Container/Continut rule
- HOME_SCREENS.md — Home layout + gesture schema + UI patterns
- ASTRO.md — 14 bodies, transits, PoF, TZ, Room v4, interpretations
- WIDGETS.md — TatwaWidget 4x2 complete
- BUILD_TEST.md — Android build + install + stress test 10 steps + preview servers

**`PROJECTS/MyBook/doc/`** (3 fisiere):
- INDEX.md
- BOOK_STRUCTURE.md — folders, ierarhie surse, protocoale, stare curenta
- EXPORT_TOOLS.md — Scrivener scripts/teme + preview LIVE + NotebookLM

**`PROJECTS/MyResearch/doc/`** (3 fisiere):
- INDEX.md
- FORMAT.md — termen alogen / romanesc / atribut
- SCRIPTS_STATE.md — scripturi import/enrich + stare curenta + NotebookLM

### Fisiere modificate (rescrise slim)

| Fisier | Inainte | Dupa | Reducere |
|---|---|---|---|
| `<WORKSPACE_DIR>\CLAUDE.md` | 7.6 KB | ~3 KB | -61% |
| `PROJECTS/MyAndroidApp/CLAUDE.md` | 35.9 KB | ~5 KB | -86% |
| `PROJECTS/MyBook/CLAUDE.md` | 8.6 KB | ~3 KB | -65% |
| `PROJECTS/MyResearch/CLAUDE.md` | 4.9 KB | ~3 KB | -39% |
| **TOTAL auto-load** | **57 KB** | **~14 KB** | **-75%** |

### Backup
`_ARCHIVE/pre_holografic_2026-04-09/` contine copii integrale:
- ROOT_CLAUDE.md (7616 bytes)
- MyAndroidApp_CLAUDE.md (35889 bytes)
- MyBook_CLAUDE.md (8627 bytes)
- MyResearch_CLAUDE.md (4857 bytes)

Rollback: copy back la locatiile originale daca apar probleme.

### Verificare post-task
- Toate CLAUDE.md slim contin index valid spre fisiere care EXISTA
- Toate fisierele din `_SETTINGS/RULES/` si `doc/` au continut migrat din original
- Nicio informatie pierduta (audit spot-check)
- Sizes masurate si raportate

### De ce aceasta restructurare
- **Token economy:** -75% la session start (de la ~14K la ~3.5K tokeni auto-load)
- **Claritate:** fiecare regula traieste intr-un singur loc (not duplicated)
- **Scalabilitate:** proiecte noi urmeaza acelasi pattern (template slim + doc/)
- **Discoverability:** index-urile au tabel "task → fisier" explicit
- **Holografic:** fiecare nivel reflecta structura intregului (fractal)

---

## 2026-04-09 — BEST_PRACTICES.md fractal + reguli per-template

### Cerinta user (citat aproximativ):
> "trebuie sa ai si un root un fisier (BEST_PRACTICES) unde pui ce si deprinzi bun si te va ajuta pe viitor. Si la nivel specific de proiect un (BEST_PRACTICES) pentru ca fiecare proiect este diferit si are cerinte de intelegeri specifice. Ca root si la alte nivele comunica fractal intre ele si sa te dezvolte rapid pe tine (Claude) si te face mai eficient si mai rapid cu mai putin consum de tokeni — prin aceste tu te dezvolti si cresti ca (inteligenta). Generic template creeaza reguli pentru ca fiecare template sa se adapteze pe genul (tipul) de proiect sau scopul proiectului, nu conteaza despre ce va fi acel proiect."

**Traducere:** Creeaza fisiere `BEST_PRACTICES.md` la fiecare nivel (root + per-proiect + template stubs), comunicate fractal, prin care Claude **creste ca inteligenta** persistenta peste sesiuni. Fiecare template trebuie sa aiba reguli specifice tipului sau (android / carte / research); generic are reguli **universale** care se aplica oricarui proiect indiferent de scop.

### Mecanism: BEST_PRACTICES.md ca inteligenta persistenta

**Problema:** Memoria Claude e volatila (context window). Lectiile invatate intr-o sesiune se pierd in urmatoarea. Solutia memoriilor `<USER_HOME>.claude\projects\.../memory/` functioneaza, dar nu calatoresc cu proiectul si nu sunt fractale.

**Solutia:** `BEST_PRACTICES.md` ca fisiere vii la fiecare nivel:
- **Fractal:** Root ↔ Proiect ↔ Template, cu cross-references Parent/Related/Sibling
- **Persistent in filesystem:** supravietuiesc crash-urilor, migrari, sesiuni noi
- **Growth log:** fiecare sesiune adauga patterns/anti-patterns noi (cresc cu proiectul)
- **Token-efficient:** doar patterns relevante pentru proiectul activ se incarca

### Fisiere noi create — BEST_PRACTICES.md

**Root workspace** (1 fisier):
- `<WORKSPACE_DIR>\BEST_PRACTICES.md` — **PATTERN-001..008** (propune inainte, CHANGELOG inainte de cod, TODO persistent, BUG_LOG separat, o modificare pe rand, holografic fractal, cerinta noua mid-task, epilog la completare) + **ANTI-001..008** (try-catch ca fix, batch modificari, preview server alt proiect, defaultMinSize, skip version bump, efecte fara cerere, document la sfarsit, incep fara SESSION_STATUS). Growth log 2026-04-09.

**Per-proiect** (3 fisiere):
- `PROJECTS/MyAndroidApp/BEST_PRACTICES.md` — **SAP-001..009** (TatwaColors single source, Container/Continut, StandardGestures, AstroCache, TZ getOffset, Help+Tooltip, APK rename baseline, stress test 300 monkey, return to Home) + **SAP-ANTI-001..005** (defaultMinSize, swipe Tranzite, FAB fara drag, hardcode colors, AndroidViewBinding legacy)
- `PROJECTS/MyBook/BEST_PRACTICES.md` — **KB-001..008** (Index Master canonic, skill activat, Exemple vs Ilustratii, Constructor Afirmativ P4, anti-teleologic, build_scrivener.py, preview LIVE, NotebookLM queries) + **KB-ANTI-001..005** (edit 01_INDEX, duplicare concept, ilustratii, export in structura canonica, Cap.0 ca tratat)
- `PROJECTS/MyResearch/BEST_PRACTICES.md` — **GL-001..007** (format strict, trimiteri holografice bidirectionale, import fidel, deduplicare cu definitia lunga, Devanagari+IAST, fisier per litera, NotebookLM upload) + **GL-ANTI-001..005** (modific text sursa, definitie contextuala, merge variante, trimiteri unidirectionale, .indd fara InDesign)

**Template stubs** (4 fisiere, pentru proiecte viitoare):
- `_TEMPLATES/generic/BEST_PRACTICES.md` — stub cu PROJ-001/PROJ-ANTI-001 template
- `_TEMPLATES/android/BEST_PRACTICES.md` — stub + referinta la MyAndroidApp ca sibling mature
- `_TEMPLATES/carte/BEST_PRACTICES.md` — stub + referinta la MyBook ca sibling mature
- `_TEMPLATES/research/BEST_PRACTICES.md` — stub cu exemple patterns cercetare

### Cross-linking fractal

Fiecare `BEST_PRACTICES.md` are sectiunea `🌳 Cross-links fractal`:
- **Parent:** trimite la nivel superior (root sau cross-project)
- **Sibling reference:** trimite la proiect mature de acelasi tip (MyBook pt carti, MyAndroidApp pt android)
- **Related doc:** trimite la detalii tehnice locale (`doc/`)
- **Operational:** trimite la CHANGELOG/TODO/BUG_LOG

Astfel, cand Claude lucreaza pe orice fisier din proiect, poate naviga fractal: pattern local → pattern proiect → pattern workspace → template sibling.

### Reguli per-template (tip-specifice)

**Conform cerintei user:** "Generic template creeaza reguli pentru ca fiecare template sa se adapteze pe genul de proiect sau scopul proiectului."

Fiecare template `CLAUDE.md` are acum sectiunea `Reguli specifice [tip]` cu reguli adaptate tipului:

| Template | Nr. reguli specifice | Focus |
|---|---|---|
| `generic/` | **10 reguli universale** | Propune inainte, CHANGELOG inainte, TODO persistent, epilog, o modificare pe rand, cauza reala, snapshot, onestitate, nu sterge, cerinta noua |
| `android/` | **5+ reguli Android** | O modificare → build → test telefon, stress test, version bump, Help+Tooltip, APK baseline |
| `carte/` | **10 reguli editoriale** | Un capitol per fisier, Index canonic, Exemple vs Ilustratii, P4, anti-teleologic, skill activat, preview LIVE, export timestamp |
| `research/` | **10 reguli metodologice** | Citare exacta, triangulare surse, snapshot data, separare data/analiza/interpretare, jurnal decizii, anti confirmation bias |

### Fisiere template slim actualizate

Toate 4 template-urile au acum:
- `CLAUDE.md` slim cu referinte la `_SETTINGS/RULES/`, `BEST_PRACTICES.md`, `doc/INDEX.md`
- `BEST_PRACTICES.md` stub cu PROJ-001 / PROJ-ANTI-001 templates
- `doc/INDEX.md` stub cu "cand citesc ce" per tip proiect

| Template | CLAUDE.md | BEST_PRACTICES.md | doc/INDEX.md |
|---|---|---|---|
| `generic/` | Slim + 10 reguli universale | Stub PROJ | Stub generic |
| `android/` | Slim + reguli Android | Stub + ref MyAndroidApp | ARCHITECTURE, SCREENS, BUILD_TEST |
| `carte/` | Slim + 10 reguli carte | Stub + ref MyBook | BOOK_STRUCTURE, EXPORT_TOOLS |
| `research/` | Slim + 10 reguli research | Stub | METHODOLOGY, SOURCES, FINDINGS |

### Final: CLAUDE.md slim actual

Dupa acest refactor, **toate** fisierele CLAUDE.md reale (workspace + 3 proiecte active) au fost rescrise slim:

| Fisier | Stare finala | Contine |
|---|---|---|
| `<WORKSPACE_DIR>\CLAUDE.md` | ~5 KB | 3 reguli, memorie, index workspace, proiecte, templates, structura |
| `PROJECTS/MyAndroidApp/CLAUDE.md` | ~6 KB | Quick context, index `doc/`, 15 reguli critice, structura, despre |
| `PROJECTS/MyBook/CLAUDE.md` | ~4 KB | Quick context, index `doc/`, skill activ, 10 reguli, NotebookLM, structura |
| `PROJECTS/MyResearch/CLAUDE.md` | ~4 KB | Quick context, stare numerica, index `doc/`, 10 reguli, surse, NotebookLM |

### De ce BEST_PRACTICES.md este mecanismul de crestere a inteligentei

Cand Claude:
1. **Descopera** un pattern nou (ex: "TatwaColors.kt ca single source e critic pentru UI consistency")
2. **Il verbalizeaza** in `BEST_PRACTICES.md` al proiectului cu `ID`, `Cand`, `Ce fac`, `De ce`, `Refs`
3. **Sesiunea urmatoare** il poate gasi fara sa-l rediscover-uiasca (evita re-munca)
4. **Patterns comune** pot migra in sus: proiect → root (daca e universal) → template stub
5. **Anti-patterns** blocheaza regresii viitoare (ex: "NU defaultMinSize pe randuri compacte")

Astfel, `BEST_PRACTICES.md` functioneaza ca **memorie persistenta** care creste cu proiectul si face fiecare sesiune mai eficienta decat precedenta (mai putin consum tokeni, mai putin re-gandit, mai putine regresii).

### Verificare post-task

- ✅ 4 `BEST_PRACTICES.md` reale (root + 3 proiecte) cu patterns + anti-patterns + growth log
- ✅ 4 `BEST_PRACTICES.md` stub in template-uri cu cross-links fractali
- ✅ 4 template `CLAUDE.md` slim cu reguli specifice tipului
- ✅ 4 CLAUDE.md reale (workspace + 3 proiecte) rescrise slim
- ✅ Cross-links Parent/Related/Sibling functionale la fiecare nivel
- ✅ Growth log in fiecare `BEST_PRACTICES.md` cu data 2026-04-09
