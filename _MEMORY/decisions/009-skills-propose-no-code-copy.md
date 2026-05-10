---
name: Skills-propose — search GitHub maturi, NU import cod
severity: HIGH
version: v3.6
date: 2026-05-10
status: applied
tags: [skills, github, ecosystem, license, intellectual-property]
---

# Skills-propose — search GitHub maturi, NU import cod

## Context
Userul a cerut: "să nu preluăm din greșeală în skills meritorios". Adică: când CCDEW detectează gap într-un skill, să caute pe GitHub un proiect mature similar și să-l propună — DAR fără să facem accidental copy-paste de cod care să violeze licențe.

## Opțiuni

**A. Auto-clone repo + extract automat**
- Pro: skill ready-to-use
- Contra: violare license la scale, attribution issue, security risk (kompromitat code)

**B. Doar search + manual user decision**
- Pro: user has full control
- Contra: friction, user trebuie să facă tot manual

**C. Search + scaffold metadata-only (NO code copy)**
- Pro: balance — automation pentru attribution, NO code import
- Contra: scaffold = placeholder, user trebuie să umple

## Decizie
**C — search GitHub + scaffold cu metadata only (description, topics, license, stars, URL).**

## Implementare
- `lib/skills-propose.cjs::propose(keyword)` — GitHub Search API, 4 query variants, cache 1h
- `filterMature()` strict implicit:
  - ≥10 stars
  - License în {MIT, Apache-2.0, ISC, BSD-3, BSD-2, MPL-2.0}
  - Push în ultimele 365 zile
  - !archived, !disabled
  - License "unknown" → drop (opt-in cu `--allow-unknown`)
- `generateScaffold(candidate, localName, gap)`:
  - Creează `.claude/skills/<localName>/SKILL.md`
  - Frontmatter: `inspired_by`, `inspired_url`, `inspired_stars`, `inspired_license`, `triggers`
  - Body: placeholder cu instrucțiuni "fill in implementation"
  - **NICIODATĂ copiază cod**

## License attribution
- Top-of-SKILL.md scris explicit: `Inspired by: [<name>](<url>) — ⭐ N · <license>`
- Notă: "If you adapt content from upstream, follow its license"

## Motiv
- User ownership: skill devine al userului, nu fork ascuns
- Compliance: attribution obligatorie, license respectată
- Quality control: filter mature scoate proiecte abandoned/junk

## Consecințe
- 11 teste regression (filterMature, summarize, scaffold, fromInferFindings, redact PII din descriere)
- Smoke live: caut "code review" → 5 candidates real (8.6k★ → 444★)
- `--scaffold <name>` opt-in (default e doar listing, nu side-effect)

## PII concern
Description GitHub poate conține emails ("contact alice@x for support"). Soluție: `summarize()` trece description prin `redactString()` înainte de output.
