---
name: Skills-propose — search GitHub mature, NO code import
severity: HIGH
version: v3.6
date: 2026-05-10
status: applied
tags: [skills, github, ecosystem, license, intellectual-property]
---

# Skills-propose — search GitHub mature, NO code import

## Context
The user requested: "don't accidentally pick up bad skills — only meritorious ones". I.e.: when CCDEW detects a gap in a skill, search GitHub for a similar mature project and propose it — but without accidentally copy-pasting code that would violate licenses.

## Options

**A. Auto-clone repo + extract automatically**
- Pro: skill ready-to-use
- Contra: license violation at scale, attribution issue, security risk (compromised code)

**B. Search only + manual user decision**
- Pro: user has full control
- Contra: friction, user must do everything manually

**C. Search + scaffold metadata-only (NO code copy)**
- Pro: balance — automation for attribution, NO code import
- Contra: scaffold = placeholder, user must fill

## Decision
**C — search GitHub + scaffold with metadata only (description, topics, license, stars, URL).**

## Implementation
- `lib/skills-propose.cjs::propose(keyword)` — GitHub Search API, 4 query variants, 1h cache
- `filterMature()` strict by default:
  - ≥10 stars
  - License in {MIT, Apache-2.0, ISC, BSD-3, BSD-2, MPL-2.0}
  - Push within last 365 days
  - !archived, !disabled
  - License "unknown" → drop (opt-in via `--allow-unknown`)
- `generateScaffold(candidate, localName, gap)`:
  - Creates `.claude/skills/<localName>/SKILL.md`
  - Frontmatter: `inspired_by`, `inspired_url`, `inspired_stars`, `inspired_license`, `triggers`
  - Body: placeholder with "fill in implementation" instructions
  - **NEVER copies code**

## License attribution
- Top-of-SKILL.md explicitly written: `Inspired by: [<name>](<url>) — ⭐ N · <license>`
- Note: "If you adapt content from upstream, follow its license"

## Rationale
- User ownership: skill becomes the user's own, not a hidden fork
- Compliance: mandatory attribution, license respected
- Quality control: mature filter removes abandoned/junk projects

## Consequences
- 11 regression tests (filterMature, summarize, scaffold, fromInferFindings, redact PII from description)
- Live smoke: searching "code review" → 5 real candidates (8.6k★ → 444★)
- `--scaffold <name>` opt-in (default is listing only, no side-effect)

## PII concern
GitHub description may contain emails ("contact alice@x for support"). Solution: `summarize()` runs description through `redactString()` before output.
