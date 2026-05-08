# _SETTINGS/RULES/bug_log.md — Format BUG_LOG.md

> **Citit:** La fiecare bug descoperit (raportat de user sau identificat in testare).
> **Scop:** Jurnal focalizat DOAR pe bug-uri. CHANGELOG creste mult si devine dificil sa gasesti istoricul unui bug specific.

## Regula centrala

La FIECARE bug descoperit:

1. **Creeaza intrare in `BUG_LOG.md` INAINTE de a aplica fix** cu header:
   `## BUG #N — YYYY-MM-DD HH:MM — [Titlu] — Status: ACTIVE`

2. Inregistreaza simptomul exact (citat user), versiune afectata, logcat, screenshot, pasi de reproducere.

3. Listeaza teorii investigate (respinse cu motiv) + cauza reala (root cause) — fisier + linie.

4. Dupa fix: actualizeaza la `Status: FIXED`, adauga fix aplicat (before/after) + verificare (build + install + stress test + screenshot).

5. In `CHANGELOG.md` scrii cu referinta `BUG #N` (nu duplica continutul complet, doar rezumat + link).

## Aceasta regula NU are exceptii

Fix de 1 linie sau bug critic — **TOATE** merg in BUG_LOG.md.

## Format intrare complet

```markdown
## BUG #N — 2026-MM-DD HH:MM — [Titlu descriptiv] — Status: ACTIVE

### Simptom (citat user):
> "exact ce a zis user-ul despre bug"

### Versiune afectata
V beta 4.17.X (versionCode XXX)

### Reproducere
1. Pas 1 concret
2. Pas 2
3. Observa: [comportamentul gresit]

### Logcat (relevanta)
```
[pastes din adb logcat -d | grep relevant]
```

### Screenshot
`bug_[descriere]_YYYYMMDD_HHMMSS.png`

### Teorii investigate (respinse)

**Teorie 1:** [ce credeam ca e cauza]
- **Respinsa:** [motiv concret — ce am verificat si de ce nu e asta]

**Teorie 2:** [...]
- **Respinsa:** [...]

### Cauza reala (root cause)
[Fisier:linie] — [explicatie concreta]

Exemplu:
> `HomeScreen.kt:325` — `remember { }` fara key, state-ul pill-ului nu se invalideaza la schimbarea orei

### Fix aplicat
**Before:**
```kotlin
val pill = remember { calculatePill() }
```
**After:**
```kotlin
val pill = remember(currentHour) { calculatePill() }
```

### Verificare
- [x] Build gradle assembleDebug SUCCESSFUL
- [x] adb install -r succes
- [x] Stress test: 5 cicluri nav + 300 monkey events PASS
- [x] Logcat verify: FATAL=0, ANR=0, NPE=0, crash buffer empty
- [x] Screenshot dovada: `fix_bug_N_YYYYMMDD.png`

### Lessons learned
[Ce am invatat — ca sa nu repet greseala si sa gasesc pattern-uri similare in alta parte]

### Status: FIXED in V beta 4.17.X (versionCode YYY)
```

## Ce NU fac

- ❌ Nu scriu direct fix-ul fara header "BUG #N ACTIVE"
- ❌ Nu sar peste sectiunea "Teorii respinse" (utila pt pattern-recognition viitor)
- ❌ Nu zic "fixed" fara stress test + screenshot
- ❌ Nu omit cauza reala — mereu fisier + linie concrete
- ❌ Nu duplic continut in CHANGELOG — doar referinta scurta `BUG #N`

## Zero fix-uri de suprafata

Cauza reala > fix rapid. Daca un try-catch face ca eroarea sa dispara dar cauza adevarata e alta → NU e fix acceptabil. Caut root cause, fix la origine.

## Integrare cu CHANGELOG

**In CHANGELOG.md:**
```markdown
### Bug fix:
- BUG #12 — weather pill highlight state stale la schimbarea orei
  Fix: `remember(currentHour)` in HomeScreen.kt:325
  Detalii complete: BUG_LOG.md#bug-12
```

**In BUG_LOG.md:** intrarea completa cu toate sectiunile.
