# /profile — Switch between CCDEW v6.1 SLIM profiles

Switch between Lite/Full/SSA-Max operation modes.

## Usage

```
/profile                — Show current profile and available options
/profile lite          — Minimal overhead, core routing only
/profile full          — All components active (default)
/profile ssa-max       — Maximum token efficiency focus
/profile status        — Detailed component status by profile
```

## Profiles

### Lite
Minimal overhead — only core routing active.
- Enneagram: ✅
- CodeBurn: ✅  
- Secret Scan: ✅
- All others: ❌

### Full (default)
All CCDEW components active.
- Enneagram, SSA, SAFLA, CodeBurn, Red Hat Evaluator, Graphify, LangGraph, Project Scope, Intelligence, Auto-Optimize, Instincts, Secret Scan, Ruflo

### SSA-Max
Focus on maximum token efficiency.
- Enneagram: ✅
- SSA: ✅ (aggressive filtering)
- CodeBurn: ✅ (lower budget $50/day)
- Graphify, LangGraph, Instincts, Ruflo: ❌
- top_k: 6, min_score: 0.25

## Examples

```
/profile
/profile lite
/profile ssa-max
```

## Notes

- Changes apply immediately to new tasks
- Current session continues with previous config
- Profile stored in `feature-flags.json::mode`
- Run `/flags` to see current component state