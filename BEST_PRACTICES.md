# BEST_PRACTICES.md — Workspace Root (Universal Wisdom)

> **Scop:** Fisier LIVING care contine DOAR lectii **universale** — aplicabile la ORICE tip de proiect (Android, carte, glosar, research, web, etc.), indiferent de stack sau domeniu.
>
> **Citit:** La inceputul FIECAREI sesiuni (parte din session start). Auto-load via CLAUDE.md pointer.
> **Scris:** De Claude, doar pentru lectii cu adevarat universale. Specificity-first — pattern-urile incep la proiect, urca doar cu dovada.
>
> **De ce exista:** Memoria Claude (`<USER_HOME>.claude\...memory\`) e per-user, volatila, si nu calatoreste cu proiectul. BEST_PRACTICES.md traieste in filesystem, survive restart-urilor, si e partajat cu proiectul. Acesta e mecanismul prin care Claude dezvolta **inteligenta persistenta** in timp.

---

## 🧭 Principiu fundamental: Specificity-first

**Lectiile nu incep la root. Incep la nivelul CEL MAI SPECIFIC posibil si urca doar cu dovada.**

```
DESCOPAR LECTIE NOUA
        ↓
Scrie la PROIECT (default — PROJECTS/<Nume>/BEST_PRACTICES.md)
        ↓
Se aplica si la alt proiect de acelasi tip?
   NU → stay at project
   DA → promoveaza la INTERMEDIAT (_BEST_PRACTICES/<tip>/BEST_PRACTICES.md)
        ↓
Se aplica si la proiecte de alt tip?
   NU → stay at intermediat
   DA → promoveaza la ROOT (acest fisier)
```

**Root e gatekept.** O lectie intra aici DOAR daca:
1. Exista evidenta ca se aplica la ≥2 tipuri diferite de proiect (ex: Android + carte, sau glosar + research)
2. NU depinde de un tool, framework, sau domeniu specific
3. NU e deja reprezentata la un nivel inferior

**De ce:** Root citit la fiecare session start. Daca umplem root cu lectii type-specific, sesiunile pierd tokeni inutili si user-ul pierde focus.

---

## 📐 Arhitectura pe 3 niveluri + loading on-demand (META-003)

```
🌐 ROOT (acest fisier)                           ← SESSION START
   Lectii UNIVERSALE                              (citit automat)
        ↓ refera
🔧 INTERMEDIAT (_BEST_PRACTICES/<tip>/)           ← ON-DEMAND
   Lectii PER TIP (android, carte, generic)       (citit cand incep task)
   Fiecare folder = 4 fisiere:
   - BEST_PRACTICES.md (slim index, ~2 KB)
   - details.md        (Cand/Ce fac/Refs per ID)
   - growth_log.md     (rules + rationale + istorie — audit only)
   - skills.md         (Skills docs — doar cand invoc skill)
        ↓ refera
🎯 PROIECT (PROJECTS/<Nume>/BEST_PRACTICES.md)    ← ON-DEMAND
   Lectii SPECIFICE                               (citit cand incep task)
```

**Reading order la BOOT (session start):**
1. `<WORKSPACE_DIR>\BEST_PRACTICES.md` (acest fisier — universal) — **ACESTA E SINGURUL BP CITIT LA BOOT**
2. `MEMORY.md` + memorii relevante
3. `CLAUDE.md` root + workspace index

**Reading order cand user da task pe proiect:**
1. `PROJECTS/<proiect>/CLAUDE.md` (context proiect)
2. `_BEST_PRACTICES/<tip>/BEST_PRACTICES.md` (slim index intermediat — quick scan IDs)
3. `_BEST_PRACTICES/<tip>/details.md` — DOAR sectiunea `## AND-NNN` care se aplica la task-ul curent (nu tot fisierul)
4. `PROJECTS/<proiect>/BEST_PRACTICES.md` (lectii specifice proiect)

**Cand citesc `growth_log.md`:** DOAR la audit (promovare/demovare pattern, review periodic, decizie arhitecturala). Niciodata la task normal.

**Cand citesc `skills.md`:** DOAR cand decid sa invoc un skill din nivel intermediat.

**Escalation la mode C (verbose, citesc tot intermediat-ul):** DOAR daca user cere explicit review de arhitectura, decizie cross-pattern, sau context complet. Altfel ramane slim + on-demand per ID.

**Motiv:** META-002 a dublat costul session start (~17 KB → ~36 KB) pentru ca am citit intermediat eager la fiecare boot. META-003 il aduce inapoi sub 20 KB cu economie reala per task si load la cerere.

---

## 🎯 Patterns universale

### PATTERN-001 — Propune inainte, executa dupa confirmare
**Cand:** Orice modificare non-triviala de cod, fisiere, arhitectura, sau structura.
**Ce fac:** Expun planul in text (fisiere afectate, motivatie, trade-offs) si astept OK.
**De ce:** User verifica de 3 ori, nu vrea surprize, valoriza controlul.
**Refs:** Regula #2 root CLAUDE.md; memorie `feedback_workflow.md`.

### PATTERN-002 — CHANGELOG inainte de cod
**Cand:** La orice cerinta primita de la user.
**Ce fac:** Scriu cerinta + scope + fisiere tinta in `PROJECTS/<Nume>/CHANGELOG.md` **INAINTE de prima linie de cod**.
**De ce:** Daca sesiunea se intrerupe sau user intreaba mai tarziu, istoricul exista. Fara asta, munca se pierde si user pierde incredere.
**Refs:** `_SETTINGS/RULES/changelog.md`, `_SETTINGS/RULES/session_start.md`.

### PATTERN-003 — TODO.md persistent (anti-crash)
**Cand:** Orice task multi-pas.
**Ce fac:** Scriu task-urile in `PROJECTS/<Nume>/TODO.md` cu checkbox-uri `[ ]`/`[~]`/`[x]`. Actualizez pe masura ce avansez, nu la sfarsit.
**De ce:** TodoWrite in memorie = ephemeral, dispare la restart. TODO.md in filesystem = supravietuieste crash.
**Refs:** `_SETTINGS/RULES/session_start.md`.

### PATTERN-004 — Background agents: output pe disc înainte de return (anti-compaction-loss)
**Cand:** Orice agent lansat cu `run_in_background: true`.
**Problema:** La compactarea sesiunii, task ID-urile devin invalide. Output-ul din sistemul de task-uri Claude se pierde permanent — fișierele `.output` rămân goale.
**Ce fac:**
1. În promptul oricărui agent background includ **obligatoriu**: `"Write your COMPLETE output to <file_path> before returning. This is your PRIMARY output — the task system is unreliable across session compaction."`
2. Path-ul e: `doc/agent_outputs/YYYY-MM-DD_<agent_name>.md` (relativ la proiect)
3. La reluarea sesiunii: citesc `doc/agent_outputs/` pentru a recupera orice output anterior — NU mă bazez pe task output.
**De ce:** TaskOutput tool depinde de sesiunea activă. Fișierele pe disc supraviețuiesc compactărilor, restart-urilor, și crash-urilor de sesiune.
**Anti-pattern:** A lansa agents background și a citi rezultatele DOAR prin TaskOutput — garantat pierdere de date la compaction.

### PATTERN-004 — BUG_LOG.md separat de CHANGELOG
**Cand:** La fiecare bug descoperit (orice tip de proiect care are bugs — cod, continut, date).
**Ce fac:** Creez intrare in `BUG_LOG.md` cu status ACTIVE INAINTE de fix. Dupa fix: Status FIXED + root cause + verificare. In CHANGELOG pun doar referinta `BUG #N`, nu continut duplicat.
**De ce:** CHANGELOG creste mult, greu sa gasesti un bug specific. BUG_LOG e focusat, searchable.
**Refs:** `_SETTINGS/RULES/bug_log.md`.

### PATTERN-005 — Holografic / fractal — fiecare nivel e un index
**Cand:** Organizez documentatie, reguli, sau orice sistem cu multe fisiere.
**Ce fac:** Fiecare nivel (root, proiect, doc/) are un INDEX.md care trimite la detalii. Citesc doar ce imi trebuie pentru task-ul curent.
**De ce:** Economie de tokeni brutala (75% in cazul nostru). User valorifica performanta.
**Refs:** META-001 (2026-04-09 refactor fractal), META-002 (2026-04-09 3-tier BEST_PRACTICES).

### PATTERN-006 — Cerinta noua mid-task → TODO.md imediat
**Cand:** User trimite cerinta in timp ce lucrez la alt task.
**Ce fac:** Deschid `PROJECTS/<Nume>/TODO.md`, scriu cerinta noua in sectiune `## 📌 CERINTA NOUA [timestamp]` cu citat exact + interpretare. Abia apoi continui task-ul curent.
**De ce:** Daca sesiunea crapa, cerinta se pierde. TodoWrite nu e suficient (ephemeral).
**Refs:** `_SETTINGS/RULES/cerinta_noua.md`.

### PATTERN-007 — Epilog la completare (actualizare imediata)
**Cand:** La fiecare ducere la capat a unei cerinte.
**Ce fac:** Actualizez IMEDIAT CHANGELOG.md (rezultat complet, fisiere, versiune) + TODO.md (checkbox `[x]` + sumar).
**De ce:** User observa cand lucruri implementate "dispar" — inseamna n-am actualizat la timp. Regula asta previne.
**Refs:** `_SETTINGS/RULES/session_start.md` Regula 3/3.

### PATTERN-008 — Export cu timestamp in folder dedicat
**Cand:** Orice output care reprezinta o versiune publicabila/livrabila (APK, Scrivener .scrivx, PDF, bundle).
**Ce fac:** Salvez in `export/` (sau `exports/`) cu timestamp in nume: `<NumeProiect>_YYYY-MM-DD_HHMM.<ext>`.
**De ce:** Versionare naturala fara git blame. Rollback instant. Vechile versiuni nu se pierd, polueaza structura canonica a proiectului.
**Refs:** Cross-tip — aplicabil la toate 3 tipuri (`_BEST_PRACTICES/android/AND-005`, `carte/KRT-002`, `generic/GEN-007`).
**Istorie promovare:** 2026-04-09 promovat din intermediat (triplu-evidenta: Android, carte, generic).

---

## 🚫 Anti-patterns universale

### ANTI-001 — Try-catch ca fix pentru bug
**Gresit:** Bug-ul crapa → il inconjur cu try-catch ca sa nu mai crape.
**Corect:** Cauza reala, fix la radacina. Try-catch doar pentru errori asteptate (network, file I/O).
**Refs:** `_SETTINGS/RULES/bug_log.md` "Zero fix-uri de suprafata"; memorie `feedback_no_surface_fixes.md`.

### ANTI-002 — Preview server din alt proiect
**Gresit:** Lucrez pe MyAndroidApp, dar las pornit `my-book-viewer`.
**Corect:** Opresc servere irelevante. Port + nume = clar pentru ce proiect. Un proiect activ = servere doar ale lui.
**Refs:** Memorie `feedback_preview_servers.md`.

### ANTI-003 — Adaug efecte fara cerere
**Gresit:** "Uite, am pus si un gradient aici pentru ca e frumos."
**Corect:** Nu adaug gradient / glow / shadow / animatii / efecte pe elemente existente fara cerere explicita user. Aplicabil la orice tip de UI (Compose, HTML, PDF, carte layout).
**Refs:** Memorie `feedback_no_unrequested_effects.md`.

### ANTI-004 — Documentez ce-am facut la sfarsit
**Gresit:** "Fac totul, apoi scriu CHANGELOG si TODO la sfarsitul sesiunii."
**Corect:** CHANGELOG inainte de cod (`PATTERN-002`), TODO actualizat in timpul lucrului (`PATTERN-003`).
**Refs:** `_SETTINGS/RULES/session_start.md`.

### ANTI-005 — Incep task fara sa citesc SESSION_STATUS / TODO
**Gresit:** User zice "continua de unde ai ramas" dar sar direct pe cod.
**Corect:** Citesc `TODO.md` + ultimul entry din `CHANGELOG.md` al proiectului activ pentru continuity.
**Refs:** CLAUDE.md root session start checklist.

### ANTI-006 — Pun lectie type-specific in root
**Gresit:** "Stress test obligatoriu dupa install" e o regula Android, dar o scriu in root BEST_PRACTICES.
**Corect:** Root = DOAR universal. Daca e Android-only → `_BEST_PRACTICES/android/`. Daca e carte-only → `_BEST_PRACTICES/carte/`. Principiu specificity-first.
**Refs:** Sectiunea "Principiu fundamental: Specificity-first" de mai sus.

---

## 🛠️ Skills universale (aplicabile la orice tip de proiect)

### `Skill tool` (built-in) — invocare skills
- **Unde:** Orice task care se mapeaza pe un skill disponibil.
- **Cum:** Tool `Skill` cu `skill: "<nume>"`.
- **Cand:** Inainte de a implementa manual ceva pentru care exista skill dedicat.

### `Agent tool` (built-in) — delegare catre subagenti
- **Unde:** Task-uri complexe multi-pas, cercetare deep, task-uri independente care pot rula in paralel.
- **Cum:** Tool `Agent` cu `subagent_type`.
- **Agenti universali utili:**
  - `general-purpose` — research multi-step
  - `Explore` — explorare codebase (quick/medium/very thorough)
  - `Plan` — software architect pentru planuri de implementare
- **Cand NU:** Task-uri simple care se rezolva in 1-3 tool calls directe.

### `TodoWrite` (built-in) — task tracking in-session
- **Unde:** Task-uri cu ≥3 pasi. Complementeaza `TODO.md` (persistent) cu tracking live.
- **Cand NU:** Task-uri simple (<3 pasi).

### `Preview tools` (MCP `Claude_Preview`) — dev server + verification
- **Unde:** Orice proiect cu output vizual (Android WebView, carte .md, web app).
- **Cum:** `preview_start` → `preview_screenshot` / `preview_snapshot` / `preview_logs`.
- **Cand NU:** Proiecte pure backend / data fara output vizual.

### `notebooklm-mcp` — RAG pe corpus mare
- **Unde:** Orice proiect cu >50 documente (carte, glosar, research, legal).
- **Cum:** `nlm query notebook "<id>" "<intrebare>"`, `source_add`, `notebook_create`.
- **Cand NU:** Corpus mic (<10 fisiere) — grep/search directe sunt suficiente.

### `engineering:documentation` — documentatie tehnica structurata
- **Unde:** Orice proiect care are componenta tehnica documentabila (cod, pipeline, API, format spec).
- **Cand NU:** Texte pur editoriale / literatura.

### `skill-creator` — meta skill pentru crearea de skills noi
- **Unde:** Cand identific un pattern recurent care merita skill dedicat.
- **Cand NU:** Functionalitate one-shot.

---

> **Navigare, Growth rules, Growth log, How-to:** → [`_BEST_PRACTICES/GROWTH_LOG.md`](_BEST_PRACTICES/GROWTH_LOG.md) — citit DOAR la audit, nu la task normal.
