# Cerinte Tehnice Standard — Aplicabile la ORICE proiect

Acest fisier contine regulile si preferintele mele tehnice. Se aplica automat.
Claude le citeste si le respecta fara sa mai intrebe.

**REGULA ZERO — O MODIFICARE PE RAND:**
O singura modificare → build → install → test pe telefon → confirmare → urmatoarea.
NU batchui. NU presupune ca merge. Verifica PE TELEFON.

**REGULA UNU — NU UITA:**
Aceste reguli se executa AUTOMAT, fara sa ti se spuna, fara sa ti se reaminteasca.
Daca uiti una si userul trebuie sa iti spuna — inseamna ca ai gresit.
Citeste acest fisier la inceputul fiecarei sesiuni.

---

## 1. CHANGELOG obligatoriu

- Fiecare proiect are `CHANGELOG.md` la root
- La fiecare cerinta noua → scrie-o in CHANGELOG.md **IMEDIAT**, inainte de implementare
- Dupa implementare → marcheaza ce s-a facut
- Nu amana, nu batchui — fiecare cerinta se noteaza individual
- Include: cerinta, ce s-a modificat, buguri gasite, versiuni

## 2. Preview / UI Map

- Fiecare proiect cu UI are un preview server definit in `.claude/launch.json` **al proiectului** (nu in root)
- Preview-ul se porneste DOAR cand lucrezi pe acel proiect
- La fiecare modificare vizuala + build, actualizeaza preview-ul automat (HTML UI Map)
- Preview-ul trebuie sincronizat cu codul — nu ramane cu varianta veche
- NU folosi HTML preview sau SVG pentru proportii exacte pe Android — sunt inexacte

## 3. Build & Install (Android)

### Checklist inainte de build:
1. Verifica/actualiza UI si UX (layout-uri, culori, margini, responsive)
2. Verifica code lint si erori de cod
3. Verifica/actualiza versionName + versionCode in build.gradle.kts
4. Confirma versiunea cu userul inainte de build
5. Ruleaza testele
6. Build
7. Uninstall versiune veche (`adb uninstall`)
8. Install curat (`adb install -t`)
9. Actualizeaza preview-ul UI Map
10. Screenshot live de pe telefon pentru verificare

### Detalii tehnice:
- JAVA_HOME: `C:/Program Files/Android/Android Studio/jbr`
- ADB: `$LOCALAPPDATA/Android/Sdk/platform-tools/adb.exe`
- Gradle heap: 1536m (nu 4096m — crashuie)
- Flag `-t` obligatoriu pe Oppo la `adb install`
- APK-ul include versiunea in nume (ex: `Sunrise-v4.1-debug.apk`)
- Instalare curata = uninstall + install (nu `-r` replace)

## 4. Verificare pe telefon

- Cand telefonul e conectat: screenshot REAL (`adb exec-out screencap -p`)
- Cand NU e conectat: arbore cod complet (ID-uri, dp, culori, margini, fonturi, tap actions)
- NU folosi HTML preview ca substitut pentru telefon
- Dupa install, verifica live pe telefon — nu presupune ca merge

## 5. Servere preview — reguli

- launch.json se pune in `.claude/launch.json` **al proiectului**, nu in root
- Fiecare server are: name, port, scop documentat in CLAUDE.md al proiectului
- NU porni servere din alt proiect
- Procese Python vechi pe porturi se termina cu `taskkill`

## 6. Nu modifica fara confirmare

- Propune intai, executa dupa confirmare
- Valabil pentru orice editare de continut
- La cod/UI tehnic se poate lucra direct, dar la continut (text, structura) — confirma

## 7. Versiunare — Schema obligatorie

**Format versionName:** `V [stadiu] Major.Minor.Build`
- **Major** — versiune majora (schimbari mari de arhitectura/features)
- **Minor** — versiune minora (features noi, imbunatatiri)
- **Build** — numarul de build, creste cu **FIECARE** compilare, fara exceptie
- **Stadiu** — `alfa` | `beta` | `rc` | `release`

**Exemple:** `V alfa 1.0.1`, `V beta 4.5.12`, `V release 5.0.1`

**versionCode:** numar intreg, creste cu 1 la FIECARE compilare

**Reguli:**
- La FIECARE `./gradlew assembleDebug` → creste Build (+1) si versionCode (+1)
- versionName + versionCode vizibile in app (ecranul About)
- Exporturile au versiunea in nume (ex: `Sunrise-V-beta-4.5.12-debug.apk`)
- Se aplica la TOATE proiectele (Android, desktop, web, orice)

## 8. Oppo / ColorOS specifice

- "Enhanced installation protection" dezactivat via ADB: `adb shell settings put secure enhanced_installation_protection 0`
- `TextClock` NU functioneaza in widget pe Oppo — foloseste `AnalogClock` + `ImageView`
- `LocationManager.isLocationEnabled` returneaza gresit pe Oppo — foloseste `Settings.Secure.LOCATION_MODE`
- La install, Oppo poate cere confirmare vizuala — flag `-t` ajuta
- PendingIntent-uri pe Oppo: explicit intent, unique request code, re-set la fiecare update

## 9. Organizare fisiere

- Nu crea fisiere in root workspace — doar in `PROJECTS/` sau `_TEMPLATES/`
- Nu modifica `_TEMPLATES/` — doar copiaza
- Resurse partajate in `_GLOBAL_ASSETS/`
- Versiunile vechi merg in `archive/`
- Exporturile in `exports/` cu timestamp

## 10. Limba si comunicare

- Limba de lucru: romana
- Termeni tehnici: pot ramane in engleza
- Raspunsuri scurte, la obiect
- Onestitate — daca nu stii, spune ca nu stii

---

# PARTEA II — Cerinte specifice per TIP DE PROIECT

---

## TIP: Aplicatie Android / Kotlin

### Setup initial
- Template: copiaza `_TEMPLATES/android/` in `PROJECTS/<Nume>/`
- Structura: `app/` = proiect Gradle complet, `exports/` = APK-uri, `screenshots/` = capturi telefon
- `CLAUDE.md` obligatoriu cu: package, versiune, SDK, dependinte, structura sursa
- `.claude/launch.json` cu preview servers (ui-map, mockup)

### UI/UX
- UI Map HTML (`ui_map/`) pentru fiecare ecran/widget major — sincronizat cu codul
- Forme, culori, dimensiuni (dp/sp) documentate in CLAUDE.md
- Responsive breakpoints documentate (compact, small, normal)
- Tap zones cu intent-uri documentate
- Screenshot real de pe telefon dupa fiecare modificare vizuala

### Build & Deploy
- Checklist complet (vezi sectiunea 3 de mai sus)
- Gradle Kotlin DSL, AGP, Kotlin, Compose BOM — versiuni documentate in CLAUDE.md
- `gradle.properties`: Xmx1536m, parallel=true, caching=true
- Debug APK in `exports/` cu versiune in nume
- Instalare curata: uninstall + install -t

### Widget-uri
- RemoteViews: NU suporta `layout_weight`, `TextClock` pe Oppo, view-uri custom
- Foloseste: `FrameLayout` + `ImageView` (bitmap) + `AnalogClock` + `TextView`
- Bitmap-uri generate programatic (tick marks, forme, text 3D)
- AlarmManager 60s pentru update text/tatwa, ace AnalogClock sunt live
- Testare pe telefon real obligatorie — emulatorul nu reflecta Oppo

### Oppo/ColorOS
- Vezi sectiunea 8 de mai sus
- Testare pe dispozitiv real Android 14+ (SDK 34+, ColorOS recomandat pentru quirks)

---

## TIP: Carte / Manuscris

### Setup initial
- Template: copiaza `_TEMPLATES/carte/` in `PROJECTS/<Nume>/`
- Structura: `01_INDEX/` = schelet canonic, `04_CARTE/` = continut scris, `02_REFERINTE/` = glosare
- `CLAUDE.md` obligatoriu cu: titlu, numar capitole/fisiere, limba, surse

### Editare
- Skill editorial activ (ex: karma-book-engine) — se activeaza inainte de orice interventie
- NU modifica continut fara confirmare explicita — propune intai
- Fiecare concept are o singura gazda canonica — nu duplica intre capitole
- Index Master = referinta canonica, nu se modifica fara confirmare

### Preview LIVE
- `serve_md.py` in folderul continutului (ex: `04_CARTE/`)
- Preview server in `.claude/launch.json` al proiectului
- Auto-refresh la 2s, navigare pe capitole cu sageti
- Verificare vizuala la fiecare editare

### Export
- Scrivener: `python export/build_scrivener.py` → .scrivx cu timestamp
- Tema Scrivener: `tema-cititor.scrtheme` din `_SETTINGS/`
- Formate: PDF, DOCX, EPUB, RTF, HTML, TXT (din Scrivener Compile)
- Exporturile in `export/` cu timestamp in nume

### Calitate text
- Protocoale editoriale (P0-P13) daca exista skill activ
- Grile de testare pentru exemple noi
- Verificare anti-teleologica, constructor afirmativ
- Exemple vs ilustratii: exemplele se pastreaza, ilustratiile se scot

---

## TIP: Glosar / Research / Enciclopedie

### Setup initial
- Structura: un fisier mare sau fisiere per litera/categorie
- CLAUDE.md cu: numar termeni, procent completare, surse

### Editare
- Fiecare termen: definitie + etimologie + context
- Nu duplica termeni
- Verificare ortografie termeni sanscriti/alogeni

### Export
- NotebookLM: upload surse via `nlm` CLI
- Format: Markdown structurat

---

## TIP: Cercetare / Analiza

### Setup initial
- Template: copiaza `_TEMPLATES/research/` in `PROJECTS/<Nume>/`
- Structura: `notes/` = idei, `references/` = surse, `conclusions/` = rezultate

### Lucru
- Surse documentate cu link/referinta
- Note structurate pe teme
- Concluzii separate de note brute

---

## TIP: Generic

### Setup initial
- Template: copiaza `_TEMPLATES/generic/` in `PROJECTS/<Nume>/`
- CLAUDE.md minimal cu: scopul proiectului, structura
- Adapteaza structura la nevoie
