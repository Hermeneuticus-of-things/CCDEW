# BEST_PRACTICES.md — {{NUME_PROIECT}} (Android)

> **Parent:** `<WORKSPACE_DIR>\BEST_PRACTICES.md` — patterns cross-project
> **Related:** `doc/INDEX.md` — detalii tehnice proiect
> **Scop:** Lectii specifice acestui proiect Android — Compose patterns, library quirks, debugging tricks.
> **Creste cu:** Fiecare bug rezolvat, feature, refactor.

> **Inspiratie:** `PROJECTS/MyAndroidApp/BEST_PRACTICES.md` — patterns Android mature. Copiaza si adapteaza cele relevante.

---

## 🎯 Project patterns

### PROJ-001 — {{Titlu pattern}}
**Cand:** {{Trigger-ul}}
**Ce fac:** {{Actiunea concreta}}
**De ce:** {{Motivatia}}
**Refs:** {{Fisiere relevante}}

<!--
Exemple pattern-uri Android din MyAndroidApp pe care le poti adapta:
- Single source of truth pentru culori (Kt file, NU theme duplicate)
- Component reutilizabil cu parametri default
- StandardGestures pentru uniform tap/double/long
- Cache pentru calcule scumpe (ex: Swiss Ephemeris, calendar queries)
- Help + Tooltip inline pe TOATE elementele noi
- APK rename + baseline pastrat inainte de versiune noua
- Stress test monkey 300 events + 4 greps logcat
-->

---

## 🚫 Project anti-patterns

### PROJ-ANTI-001 — {{Titlu anti-pattern}}
**Gresit:** {{Ce e tentant sa fac}}
**Corect:** {{Ce fac in schimb}}
**De ce:** {{Motivatia}}
**Refs:** {{Fisiere relevante}}

<!--
Exemple anti-patterns Android de evitat:
- defaultMinSize(minHeight) pe randuri de lista
- Hardcode culori in mai multe fisiere
- FAB fara drag support
- Batch modificari fara test intre ele
- Skip version bump
- try-catch ca fix pentru crash
- AndroidViewBinding pentru feature compose-first
-->

---

## 🌳 Cross-links fractal

- **Parent:** `<WORKSPACE_DIR>\BEST_PRACTICES.md` — patterns cross-project
- **Sibling reference:** `PROJECTS/MyAndroidApp/BEST_PRACTICES.md` — Android patterns mature
- **Related doc:** `doc/ARCHITECTURE.md`, `doc/SCREENS.md`, `doc/BUILD_TEST.md`
- **Operational:** `CHANGELOG.md`, `TODO.md`, `BUG_LOG.md`

## 📈 Growth log

### {{DATA}} — Initial creation
- Stub template creat din `_TEMPLATES/android/BEST_PRACTICES.md`
- De populat cu patterns/anti-patterns pe masura ce proiectul creste
