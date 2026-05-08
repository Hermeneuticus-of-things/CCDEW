# _SETTINGS/RULES/versioning.md — Schema Versionare

> **Citit:** La fiecare bump versiune (orice modificare care ajunge pe telefon sau in export).
> **Scop:** Schema uniforma cross-project.

## Schema generica

```
V [stadiu] Major.Minor.Build
```

- **stadiu:** `alpha` / `beta` / `rc` / (omite = stable)
- **Major:** crestere la schimbari arhitecturale mari sau breaking
- **Minor:** crestere la features noi
- **Build:** crestere la fiecare modificare, inclusiv fix-uri mici

## Exemple

| Versiune | Interpretare |
|---|---|
| `V beta 4.17.37` | Beta, major 4, minor 17, build 37 |
| `V alpha 1.0.5` | Alpha, prima versiune major, fara features noi, 5 iteratii |
| `V rc 2.3.12` | Release candidate, major 2, minor 3, build 12 |
| `V 3.0.0` | Stable, major 3, minor 0, primul build stable |

## Regula #1 — Bump la FIECARE build

**Niciodata nu reinstalezi acelasi versionCode.** La FIECARE build care ajunge pe telefon:
- `versionCode` creste (mereu, fara exceptii)
- `versionName` creste (Build component mereu, Minor/Major dupa context)

### De ce
- Permite rollback clar (fiecare APK are identitate unica)
- Debugging: `adb logcat | grep VersionName` identifica exact ce ruleaza
- Install replace: `adb install -r` cere versionCode > celui existent
- Nu se confunda build-urile in exports/

## Regula #2 — APK name contine versiunea

Format nume APK:
```
<NumeApp>-V-beta-<Major>.<Minor>.<Build>-debug.apk
```

Exemplu: `Sunrise-V-beta-4.17.37-debug.apk`

## Regula #3 — Afisare in app

App-ul trebuie sa afiseze versiunea **vizibil** (Settings > About sau header):
```
V beta 4.17.37 (build 197)
```

Asta ajuta user-ul sa raporteze bug-uri cu versiune exacta.

## Bump decision tree

```
Modificare cod?
├── Fix bug / typo / 1 linie → Build++
├── Refactor intern (nicio schimbare vizibila) → Build++
├── Feature mic (ex: nou toggle, label) → Build++
├── Feature mediu (ex: nou screen, nou tab) → Minor++ Build=0
├── Feature mare (ex: module nou) → Minor++ Build=0
├── Breaking change UI / schimbare fundamentala → Major++ Minor=0 Build=0
└── Schimbare stadiu (alpha→beta→rc→stable) → stadiu++ (altul ramane)
```

## Per-proiect overrides

**MyAndroidApp (Android):**
- `versionCode` in `app/app/build.gradle.kts`
- `versionName` in `app/app/build.gradle.kts`
- Tagged in APK via Gradle

**MyBook (carte/manuscript):**
- Versiunea e data si revizia manuscris (`YYYY-MM-DD_revN`)
- Tracked in `CHANGELOG.md` header

**MyResearch (glosar/enciclopedie):**
- Tracked in `INDEX_MASTER.md` header cu numar total termeni + data

## Integrare cu CHANGELOG

Intrarea CHANGELOG contine sectiunea:
```markdown
### Versionare:
- versionCode X → Y
- versionName "V beta A.B.C" → "V beta A.B.D"
```

Fara aceasta sectiune, CHANGELOG e invalid (per `changelog.md`).
