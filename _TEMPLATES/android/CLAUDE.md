# {{NUME_PROIECT}} — Android App
## Actualizat: {{DATA}}

> **Parent:** `D:\Cloude Code\CLAUDE.md` (reguli workspace)
> **Reguli cross-project:** `_SETTINGS/RULES/INDEX.md`
> **Patterns + anti-patterns:** `D:\Cloude Code\BEST_PRACTICES.md` + `./BEST_PRACTICES.md`
> **Ruflo:** `_SETTINGS/RULES/ruflo_integration.md`
> **Detalii proiect:** `./doc/INDEX.md`

## Quick context

**Tip proiect:** Android app
**Stack:** Kotlin + Jetpack Compose + Gradle (Kotlin DSL)
**Package:** `com.{{dev}}.{{nume}}`
**SDK:** compileSdk X, minSdk Y, targetSdk Z
**Versiune curenta:** V alpha 0.1.0
**Stare:** {{In curs / Stabil}}

## 🗺️ Index proiect

| Task | Fisier |
|---|---|
| Arhitectura, packages, servicii | `doc/ARCHITECTURE.md` |
| Ecrane si UI patterns | `doc/SCREENS.md` |
| Build + stress test + install | `doc/BUILD_TEST.md` |
| Best practices specifice | `BEST_PRACTICES.md` |
| Cerinte + versiuni | `CHANGELOG.md` |
| Task-uri active | `TODO.md` |
| Bug-uri | `BUG_LOG.md` |

## Reguli specifice Android

- **O modificare pe rand** → build → install → test pe telefon → confirmare
- **Stress test obligatoriu** dupa fiecare install (vezi `doc/BUILD_TEST.md`)
- **Version bump** la FIECARE build (vezi `_SETTINGS/RULES/versioning.md`)
- **Help + Tooltip** pe ORICE element UI nou — nu adaugat dupa
- **APK rename + baseline** in `exports/` inainte de versiune noua

## Graphify — Knowledge Graph

La primul build al proiectului, construieste graful:
```
/graphify app/src
```

Dupa primul build, git hook-ul reconstruieste automat graful la fiecare `git commit`:
```
graphify hook install
```

Graf stocat in `graphify-out/graph.json`. Interogare: `/graphify query "intrebare"`.

## Ruflo tools relevante

| Tool | Cand | Restrictie |
|---|---|---|
| `memory_search` | Cautare semantic in bug history, pattern-uri anterioare | Nu inlocuieste `BUG_LOG.md` |
| `swarm_init` | Refactors mari ≥5 fisiere independente (migrare API, rename cross-screen) | NU la task-uri normale — "o modificare pe rand" prevaleza |
| `hooks_route` | Nu stiu ce agent e potrivit | Rar — majoritatea task-urilor Android sunt directe |

**Regula:** Workflow-ul Android (CHANGELOG → build → install → stress test) NU se schimba. Ruflo e complementar. Detalii: `_SETTINGS/RULES/ruflo_integration.md`.

## Phone Mirror (Preview live)

Mirroring live al telefonului in Preview panel. Setup:
1. Conecteaza telefonul USB cu debugging activ
2. Ruleaza `adb devices` si copiaza device ID in `screenshots/mirror_server.py` (sau lasa gol pt auto-detect)
3. Adauga in `.claude/launch.json`:
```json
{
  "version": "0.0.1",
  "configurations": [
    {
      "name": "phone-mirror",
      "runtimeExecutable": "python",
      "runtimeArgs": ["PROJECTS/{{NUME_PROIECT}}/screenshots/mirror_server.py"],
      "port": 8777
    }
  ]
}
```
4. In Claude Code: Preview panel se deschide automat cu `preview_start("phone-mirror")`

## Structura foldere

```
app/              ← cod sursa Android (Gradle root)
assets/           ← resurse directe (imagini, sunete, fonturi, date)
references/      ← documente externe (specificatii, mockups, API docs)
screenshots/     ← capturi ecran telefon/emulator + mirror_server.py
skills/          ← skills Claude specifice proiectului
inbox/           ← fisiere noi, neorganizate
exports/         ← APK-uri (cu versiune in nume)
archive/         ← versiuni vechi
notes/           ← idei, planuri, todo-uri
doc/             ← detalii tehnice on-demand
```

## Despre

{{Descrie aici ce face aplicatia, pentru cine e, ce platforma targeteaza}}
