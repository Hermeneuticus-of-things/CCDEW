# {{NUME_PROIECT}}/doc/INDEX.md — Master Index Detalii Proiect

> **Scop:** Router detalii {{NUME_PROIECT}}. Citit on-demand pe baza task-ului.
> **Parent:** `../CLAUDE.md` (slim, contine doar quick-context + pointer aici)

## Cand citesc ce

| Task | Fisier | Continut principal |
|---|---|---|
| {{Task type 1}} | `{{FILE1}}.md` | {{Descriere}} |
| {{Task type 2}} | `{{FILE2}}.md` | {{Descriere}} |

<!-- Adauga fisiere doc pe masura ce proiectul creste. Regula: daca ai > 10 KB detalii care nu intra in CLAUDE.md slim, creezi un fisier doc nou. -->

## Reguli cross-project (nu duplicate aici)

| Categorie | Locatie |
|---|---|
| Session start / 3 reguli critice | `_SETTINGS/RULES/session_start.md` |
| Format CHANGELOG | `_SETTINGS/RULES/changelog.md` |
| Format BUG_LOG | `_SETTINGS/RULES/bug_log.md` |
| Cerinta noua mid-task | `_SETTINGS/RULES/cerinta_noua.md` |
| Schema versionare | `_SETTINGS/RULES/versioning.md` |
| Best practices cross-project | `<WORKSPACE_DIR>/BEST_PRACTICES.md` |
| Best practices {{NUME_PROIECT}} | `../BEST_PRACTICES.md` |

## Fisiere operationale in root proiect

| Fisier | Scop |
|---|---|
| `CLAUDE.md` | Quick-context slim |
| `BEST_PRACTICES.md` | Lectii invatate specific proiect |
| `CHANGELOG.md` | Jurnal cerinte + modificari |
| `TODO.md` | Task-uri active |
| `BUG_LOG.md` | Bug-uri (daca aplicabil) |
