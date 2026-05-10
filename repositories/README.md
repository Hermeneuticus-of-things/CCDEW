# repositories/

This folder follows the Red Hat `claude-code-setup-evaluator` meta-workspace pattern.

## Purpose
A single CCDEW workspace can host multiple **independent repositories** here, each with its own `.git/` and clean separation. CCDEW's hooks, skills, and audit tools apply to all of them; their git history stays separate.

## How to use
```bash
cd repositories/
git clone <your-repo-url>
# Now `/verify`, `/review`, `/quality-gate`, secret-scan all work inside that repo's diffs.
```

## Active vs CCDEW root
- **CCDEW root** (`<workspace>/CCDEW/`) — the workspace itself: helpers, skills, settings.
- **Sub-projects** under `PROJECTS/` — owned by you, integrated into CCDEW (CHANGELOG.md, TODO.md per project).
- **External repos under `repositories/`** — third-party or standalone repos you want to work on with CCDEW tooling but **not commit into CCDEW's history**.

The `/scope-status` command auto-detects which mode applies.

