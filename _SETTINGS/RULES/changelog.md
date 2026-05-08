# _SETTINGS/RULES/changelog.md — Format CHANGELOG

> **Citit:** Inainte de a scrie in `PROJECTS/<Proiect>/CHANGELOG.md`.
> **Frecventa:** La fiecare cerinta noua sau sub-cerinta.

## Cand scriu in CHANGELOG

- **INAINTE de orice linie de cod** (per session_start REGULA 1)
- Orice cerinta, chiar fix de 1 linie / typo / change de culoare
- Bug fix (cu referinta la `BUG #N` din BUG_LOG.md)
- Feature nou, refactor, optimizare, documentatie

## Format intrare obligatoriu

```markdown
## 2026-MM-DD — [Titlu scurt] — V beta X.Y.Z

### Cerinta user (citat exact):
> "textul exact trimis de user"

### Interpretare (daca cerinta e neclara):
[Traducere + ce inteleg sa fac]

### Scope planificat:

**N1 — [FisierTinta.kt] L[linie sau functie]:**
- **Before:** [starea actuala concreta]
- **After:** [modificarea]
- **De ce:** [motivul — bug, feature, user request, refactor]

**N2 — [AltFisier.kt] L[linie]:**
- Before / After / De ce

### Versionare:
- versionCode X → Y
- versionName "V beta A.B.C" → "V beta A.B.D"

### Fisiere modificate (lista finala):
- `path/to/File1.kt`
- `path/to/File2.xml`
- `build.gradle.kts`

### ✅ BUILD SUCCESSFUL + stress test PASS (dupa build+install):
- **APK size:** 27,805,923 bytes (27.8 MB)
- **Diferenta fata de precedent:** +15 KB
- **Stress test breakdown:**
  - Logcat clear + force-stop + launch
  - Multi-nav 5 cicluri, 300 monkey events (5787ms)
  - Cold restart la mijloc si sfarsit
- **Logcat verify (4 grep-uri):**
  - FATAL = 0
  - ANR = 0
  - NPE = 0
  - Crash buffer empty
- **Screenshot:** `v4_17_37_tatwa_combo_shapes.png`
```

## Ce NU e acceptabil

- ❌ "minor fixes" (fara detalii)
- ❌ "refactor code" (fara fisiere)
- ❌ "V X.Y.Z bump" (fara motivatie)
- ❌ Omit versiune sau APK size
- ❌ Omit stress test rezultat
- ❌ Sari peste "De ce"

## Cerinte speciale

### Bump versiune obligatoriu la FIECARE build
`versionCode` si `versionName` cresc la **fiecare** modificare de cod care ajunge pe telefon. Schema detaliata: `versioning.md`.

### Bug fixes
Daca fix-ul e pentru un bug raportat → referinta scurta `BUG #N` in CHANGELOG, **continutul complet** in `BUG_LOG.md` (format in `bug_log.md`).

Scop: CHANGELOG nu duplica BUG_LOG, ramane sumar.

### Workspace-level tasks
Cand task-ul nu e specific unui proiect (ex: restructurare workspace, modificari `_SETTINGS/`, `_TEMPLATES/`) → scrie in `_SETTINGS/CHANGELOG-FORMAT.md` in loc de `PROJECTS/<Nume>/CHANGELOG.md`.

## Exemplu minim valid

```markdown
## 2026-04-09 — N1 weather pills highlight — V beta 4.17.6

### Cerinta user: "vremea din Home ora actuala cu vremea sa fie pe centru pill evidentiat"

**N1 — HomeScreen.kt L314-380 (weather pills row):**
- Before: forEach fara highlighting
- After: forEachIndexed, idx=0 = ora curenta, aplic border 1.dp tertiary RoundedCornerShape(6.dp) + background tertiary.alpha=0.10f pe pill curent
- De ce: user vrea sa vada instant vremea actuala

**Versionare:** versionCode 165 → 166, versionName "V beta 4.17.5" → "V beta 4.17.6"

**Fisiere modificate:** HomeScreen.kt, build.gradle.kts
```
