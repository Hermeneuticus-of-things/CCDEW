# {{NUME_PROIECT}}
## Actualizat: {{DATA}}

> **Parent:** `D:\Cloude Code\CLAUDE.md` (reguli workspace)
> **Reguli cross-project:** `_SETTINGS/RULES/INDEX.md`
> **Patterns + anti-patterns:** `D:\Cloude Code\BEST_PRACTICES.md` + `./BEST_PRACTICES.md`
> **Ruflo:** `_SETTINGS/RULES/ruflo_integration.md`
> **Detalii proiect:** `./doc/INDEX.md`

## Quick context

**Tip proiect:** Generic (oricare alt tip care nu se incadreaza in android/carte/research)
**Stack:** {{Tehnologii folosite}}
**Stare:** {{In curs / Stabil / Archived}}

## 🗺️ Index proiect

| Task | Fisier |
|---|---|
| Detalii arhitectura si continut | `doc/INDEX.md` |
| Best practices specifice proiectului | `BEST_PRACTICES.md` |
| Cerinte + versiuni | `CHANGELOG.md` |
| Task-uri active | `TODO.md` |
| Bug-uri (daca aplicabil) | `BUG_LOG.md` |

## 🌐 Reguli universale (se aplica ORICE tip de proiect)

> Astea sunt regulile care **NU depind de tipul proiectului** — se aplica intotdeauna, indiferent ce faci aici.
> Pentru reguli specifice unui tip (android/carte/research), vezi template-ul dedicat.

1. **Propune inainte, executa dupa** — nu modifica continut/cod fara confirmare explicita de la user
2. **CHANGELOG.md inainte de cod** — scrie cerinta in CHANGELOG IMEDIAT, nu la sfarsit (vezi `_SETTINGS/RULES/session_start.md`)
3. **TODO.md persistent** — scrie task-urile in TODO.md INAINTE de lucru (anti-crash, vezi `_SETTINGS/RULES/session_start.md`)
4. **Epilog la completare** — dupa fiecare cerinta dusa la capat: update CHANGELOG + TODO imediat
5. **O modificare pe rand** — modificare → verifica → confirmare → urmatoarea; nu batch
6. **Cauza reala, nu fix la suprafata** — niciodata try-catch ca fix, niciodata patch peste simptom
7. **Snapshot inainte de modificari majore** — backup in `archive/` cu timestamp inainte de refactor mare
8. **Onestitate in status** — nu zice "gata" cand nu e gata; "in lucru" e acceptabil, minciuna nu
9. **Nu sterge fara confirmare explicita** — fisierele pot avea valoare nevisibila (istoric, work-in-progress al user-ului)
10. **Cerinta noua mid-task** → save to TODO.md imediat, nu uita (vezi `_SETTINGS/RULES/cerinta_noua.md`)

## Ruflo tools relevante

| Tool | Cand | Restrictie |
|---|---|---|
| `memory_search` | Cautare semantic cross-project, pattern-uri anterioare | Grep e mai rapid pentru text exact |
| `swarm_init` | Operatii batch pe ≥50 fisiere independente | Nu modifica fara confirmare |
| `hooks_route` | Rutare automata la agentul potrivit | Doar cand task-ul e ambiguu |

**Regula:** Workflow-ul standard (CHANGELOG → TODO → cod → epilog) NU se schimba. Ruflo e complementar. Detalii: `_SETTINGS/RULES/ruflo_integration.md`.

## Reguli specifice proiect

{{Completeaza reguli care NU sunt in regulile universale de mai sus — doar ce e special aici si nu acopera un template dedicat}}

## Structura foldere sugerata

```
src/ sau content/    ← continut principal (cod, texte, date)
assets/              ← resurse (imagini, sunete, date)
references/          ← surse externe, documentatie
notes/               ← idei, planuri, instructiuni locale
archive/             ← versiuni vechi
exports/             ← rezultate finale
doc/                 ← detalii tehnice on-demand
```

## Despre

{{Descrie proiectul, scopul, contextul, publicul, constraints}}
