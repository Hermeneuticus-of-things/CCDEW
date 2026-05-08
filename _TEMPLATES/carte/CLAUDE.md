# {{NUME_CARTE}} — Proiect Carte
## Actualizat: {{DATA}}

> **Parent:** `D:\Cloude Code\CLAUDE.md` (reguli workspace)
> **Reguli cross-project:** `_SETTINGS/RULES/INDEX.md`
> **Patterns + anti-patterns:** `D:\Cloude Code\BEST_PRACTICES.md` + `./BEST_PRACTICES.md`
> **Ruflo:** `_SETTINGS/RULES/ruflo_integration.md`
> **Inspiratie mature:** `PROJECTS/Karma Book/BEST_PRACTICES.md`
> **Detalii proiect:** `./doc/INDEX.md`

## Quick context

**Tip proiect:** Carte / Manuscris
**Format sursa:** Markdown (.md per capitol/subcapitol)
**Export principal:** Scrivener (.scrivx) + PDF
**Preview:** Markdown LIVE (port 8766)
**Stare:** {{In curs / Editare / Finalizat}}

## 🗺️ Index proiect

| Task | Fisier |
|---|---|
| Structura capitole, protocoale editoriale | `doc/BOOK_STRUCTURE.md` |
| Export Scrivener, preview, tools | `doc/EXPORT_TOOLS.md` |
| Best practices specifice | `BEST_PRACTICES.md` |
| Cerinte + versiuni | `CHANGELOG.md` |
| Task-uri active | `TODO.md` |

## Reguli specifice Carte

1. **Un capitol/subcapitol = un fisier .md** — nu amesteca sectiuni in acelasi fisier
2. **Index canonic = sursa macro pentru structura** — edit doar cu confirmare explicita
3. **Exemple vs Ilustratii** — distinctie stricta: Exemple concrete in text; Ilustratii doar daca cerute explicit
4. **Constructor afirmativ (P4)** — evita formulari "nu X, ci Y", scrie afirmativ
5. **Anti-teleologic** (daca relevant pentru tema) — evita "scopul vietii este X"
6. **Skill activat inainte de editare** — citeste skill-ul relevant din `notes/skills/` daca exista
7. **Preview LIVE la editari vizuale** — `preview_start("md-viewer")` sau `python serve_md.py`
8. **Export cu timestamp** — `Carte_YYYY-MM-DD_HHMM.scriv`, vechile in `archive/`
9. **Nu modifica continut fara confirmare** — propune intai, executa dupa
10. **Fara edit direct in structura canonica** — confirmare obligatorie pentru orice modificare

## Ruflo tools relevante

| Tool | Cand | Restrictie |
|---|---|---|
| `memory_search` | Cross-referinte intre capitole ("unde mai apare conceptul X?") | NotebookLM e mai bun pentru cautare in corpus complet |
| `intelligence_patterns` | Sugestii de consistenta editoriala | Nu inlocuieste protocoalele editoriale |

**Regula:** Editing-ul e secvential, nu paralel. NU swarm pe task-uri editoriale — riscul de inconsistenta e prea mare. Detalii: `_SETTINGS/RULES/ruflo_integration.md`.

## Structura foldere

```
manuscript/      ← textul cartii (fisiere .md per capitol/subcapitol)
notes/           ← idei, planuri, schite, skills Claude
references/      ← surse externe, materiale colectate
assets/          ← imagini, diagrame folosite in carte
export/          ← rezultate finale (.scrivx, .pdf, .docx)
  build_scrivener.py     ← genereaza .scrivx cu timestamp
  prepare_scrivener.py   ← genereaza .txt curate pentru import manual
archive/         ← versiuni vechi
doc/             ← detalii tehnice on-demand (BOOK_STRUCTURE, EXPORT_TOOLS)
serve_md.py      ← Preview LIVE auto-refresh (port 8766)
```

## Despre

{{Descrie subiectul cartii, publicul tinta, tonul dorit, volumul planificat, limba}}

## launch.json (pentru Preview LIVE)

Pune in `.claude/launch.json` al workspace-ului (NU in root proiect):
```json
{
  "version": "0.0.1",
  "configurations": [
    {
      "name": "md-viewer",
      "runtimeExecutable": "python",
      "runtimeArgs": ["PROJECTS/{{NUME_PROIECT}}/serve_md.py"],
      "port": 8766
    }
  ]
}
```
