# {{NUME_PROIECT}}/doc/INDEX.md — Master Index Detalii Proiect

> **Scop:** Router detalii {{NUME_PROIECT}}. Citit on-demand pe baza task-ului.
> **Parent:** `../CLAUDE.md` (slim)

## Cand citesc ce

| Task | Fisier | Continut principal |
|---|---|---|
| Inteleg package-urile si arhitectura | `ARCHITECTURE.md` | Package → rol, servicii, persistenta |
| Lucrez pe ecrane / UI / gesturi | `SCREENS.md` | Layout, gesture schema, UI patterns |
| Build / install / stress test | `BUILD_TEST.md` | Gradle, adb, 10 pasi stress test |

<!-- Adauga fisiere doc pe masura ce proiectul creste. Exemple:
- WIDGETS.md — daca ai widget-uri home screen
- NOTIFICATIONS.md — daca ai canal-uri si foreground services complexe
- DATA_LAYER.md — daca Room + DataStore + SharedPrefs sunt complexe
- THEMES.md — daca ai multiple teme / dark mode
-->

## Reguli cross-project (nu duplicate aici)

| Categorie | Locatie |
|---|---|
| Session start / 3 reguli critice | `_SETTINGS/RULES/session_start.md` |
| Format CHANGELOG | `_SETTINGS/RULES/changelog.md` |
| Format BUG_LOG | `_SETTINGS/RULES/bug_log.md` |
| Cerinta noua mid-task | `_SETTINGS/RULES/cerinta_noua.md` |
| Schema versionare | `_SETTINGS/RULES/versioning.md` |
| Best practices cross-project | `<WORKSPACE_DIR>\BEST_PRACTICES.md` |
| Best practices Android mature (MyAndroidApp) | `PROJECTS/MyAndroidApp/BEST_PRACTICES.md` |
| Best practices {{NUME_PROIECT}} | `../BEST_PRACTICES.md` |

## Fisiere operationale in root proiect

| Fisier | Scop |
|---|---|
| `CLAUDE.md` | Quick-context slim |
| `BEST_PRACTICES.md` | Lectii invatate specific proiect |
| `CHANGELOG.md` | Jurnal cerinte + modificari + versiuni |
| `TODO.md` | Task-uri active |
| `BUG_LOG.md` | Bug-uri (simptom → cauza → fix) |
| `SESSION_STATUS.md` | Status ultima sesiune |
