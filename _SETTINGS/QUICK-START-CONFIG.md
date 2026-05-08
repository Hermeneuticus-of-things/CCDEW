# Quick Start Config — Workspace <WORKSPACE_DIR>\

> **Scop:** Reguli rapide de baza (naming, plasare fisiere, workflow, prompts) — un singur fisier on-demand.
> **Parent:** [`../CLAUDE.md`](../CLAUDE.md)
> **Consolidat din:** NAMING-CONVENTIONS.md + WHERE-TO-PUT-FILES.md + WORKFLOW.md + PROMPT-TEMPLATES.md (META-005, 2026-04-30)

## 1. Naming conventions

### Pentru proiecte

Foloseste nume scurte si clare:
- MyAndroidApp
- CarteaKarma
- ResearchTopic01

### Pentru fisiere

Foloseste preferabil:
- litere
- cifre
- liniuta minus sau underscore

Exemple bune:
- outline-v1.md
- notes-2026-03-31.md
- screenshot-home-screen-01.png
- source-list.md

Evita nume de tipul:
- final-final-bun2.zip
- nou cel mai bun versiune ultima.docx

## 2. Where to put files

### Capturi de ecran

- ale proiectului curent -> `screenshots/`
- generale, utile si pentru alte proiecte -> `_REFERENCE_LIBRARY/images/`

### PDF-uri, documente, note primite

- pentru un proiect anume -> `references/docs/`
- generale -> `_REFERENCE_LIBRARY/docs/`

### Imagini pentru design sau UI

- specifice proiectului -> `assets/images/`
- reutilizabile -> `_GLOBAL_ASSETS/images/`

### Sunete

- specifice proiectului -> `assets/sounds/`
- reutilizabile -> `_GLOBAL_ASSETS/sounds/`

### Date JSON, CSV, text, mock data

- pentru proiect -> `assets/data/`

### Arhive zip noi

- pune-le mai intai in `_INBOX_ZIPS/`
- extrage ce merita
- muta apoi continutul unde trebuie

### Referinte web salvate manual

- capturi sau exporturi web -> `references/web/` sau `_REFERENCE_LIBRARY/web-captures/`

## 3. Workflow

### Principiul de baza

Nu amesteci skill-urile, template-urile, proiectele si arhivele.
Fiecare lucru are locul lui.

### Ordinea buna de lucru

1. Pastrezi skill-urile in `_GLOBAL_SKILLS`.
2. Cand incepi ceva nou, copiezi un template din `_TEMPLATES` in `PROJECTS`.
3. Redenumesti proiectul.
4. Pui in proiect doar skill-urile de care ai nevoie, in folderul `skills/`.
5. Adaugi materiale noi in `inbox/`.
6. Muti materialele validate in `references/`, `assets/` sau `notes/`.
7. Pastrezi ce livrezi in `exports/`.

### Regula foarte importanta

In Claude Code deschizi doar folderul proiectului activ.
Nu deschizi tot `<WORKSPACE_DIR>`.

### Ce inseamna fiecare tip de folder intr-un proiect

- `skills/` = skill-urile folosite de proiect
- `notes/` = idei, planuri, instructiuni locale
- `references/` = documente si surse de lucru
- `screenshots/` = imagini de referinta sau capturi de UI
- `assets/` = imagini, sunete, date, fonturi
- `src/` sau `app/` = continutul principal al proiectului
- `exports/` = ce livrezi sau trimiti mai departe
- `archive/` = versiuni vechi din interiorul proiectului

## 4. Prompt templates (optional)

### Pentru Android

Use android-master.
Turn this starter into a real Android app in Kotlin with Jetpack Compose.
Keep the existing project structure, improve navigation, create production-ready screens, and use adaptive layouts and clean resources.

### Pentru widget

Use android-master.
Add a Jetpack Glance home screen widget to this project.

### Pentru Android Auto

Use android-master.
Extend this project with Android Auto support where appropriate.

### Pentru scriere de carte

Use the skills from this project.
Organize the existing notes into a coherent book structure.
Keep all references, create a clean outline, and write in a style consistent with the notes in this project.

### Pentru cercetare

Use the skills from this project.
Organize the materials from inbox, references, and screenshots.
Create a research summary, open questions, working notes, and a clean export.
