# {{NUME_CERCETARE}} — Proiect Cercetare
## Actualizat: {{DATA}}

> **Parent:** `D:\Cloude Code\CLAUDE.md` (reguli workspace)
> **Reguli cross-project:** `_SETTINGS/RULES/INDEX.md`
> **Patterns + anti-patterns:** `D:\Cloude Code\BEST_PRACTICES.md` + `./BEST_PRACTICES.md`
> **Ruflo:** `_SETTINGS/RULES/ruflo_integration.md`
> **Detalii proiect:** `./doc/INDEX.md`

## Quick context

**Tip proiect:** Cercetare / Analiza
**Format:** Notite Markdown + date brute (CSV/JSON) + rapoarte
**Stare:** {{Colectare / Analiza / Redactare / Finalizat}}

## 🗺️ Index proiect

| Task | Fisier |
|---|---|
| Metodologie si design | `doc/METHODOLOGY.md` |
| Surse si bibliografie | `doc/SOURCES.md` |
| Stare analiza + concluzii | `doc/FINDINGS.md` |
| Best practices specifice | `BEST_PRACTICES.md` |
| Cerinte + versiuni | `CHANGELOG.md` |
| Task-uri active | `TODO.md` |

## Reguli specifice Cercetare

1. **Citare exacta cu context** — nu parafraza fara atribuire (plagiat accidental)
2. **Triangulare surse** — minim 2 surse independente pentru orice claim
3. **Snapshot data inainte de modificari** — cu timestamp in nume (`data_YYYY-MM-DD.csv`)
4. **Separare stricta data bruta / analiza / interpretare** — nu amesteca in acelasi fisier
5. **Jurnal decizii metodologice** — de ce am ales X (in `doc/METHODOLOGY.md`)
6. **Lipsuri in date = "missing"**, nu "absenta" — marcheaza explicit
7. **Fisiere noi in `inbox/`** — trecute prin review inainte de sortare
8. **Anti confirmation bias** — cauta activ surse care contrazic ipoteza
9. **Fara cherry-picking citate** — foloseste citate reprezentative, nu doar cele care confirma
10. **Nu modifica data bruta** — doar snapshots si derivate

## Ruflo tools relevante

| Tool | Cand | Restrictie |
|---|---|---|
| `memory_search` | Cautare semantic cross-surse ("unde am mai intalnit claim-ul X?") | Triangulare surse ramane manuala |
| `swarm_init` | Procesare batch date (≥50 fisiere), analiza paralela pe surse independente | Nu modifica data bruta |
| `intelligence_patterns` | Identificare pattern-uri in date, sugestii metodologice | Nu inlocuieste analiza critica |

**Regula:** Workflow-ul de cercetare (colectare → analiza → redactare) NU se schimba. Ruflo e complementar. Detalii: `_SETTINGS/RULES/ruflo_integration.md`.

## Structura foldere

```
notes/         ← notite, analize, concluzii
data/          ← date brute si procesate (cu snapshots)
references/    ← surse externe, articole, papers
screenshots/   ← capturi de ecran
exports/       ← rapoarte finale
archive/       ← versiuni vechi + snapshots data
inbox/         ← fisiere noi, neorganizate (review inainte de sortare)
doc/           ← detalii tehnice on-demand (METHODOLOGY, SOURCES, FINDINGS)
```

## Despre

{{Descrie tema, intrebarea de cercetare, scopul, publicul tinta, durata estimata}}
