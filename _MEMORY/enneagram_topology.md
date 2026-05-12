# Enneagram Adaptive Topology — CCDEW

> Source: `_MEMORY/enneagram_adaptive_topology.json` (live config)
> Integrates with: `ssa.cjs` (5D scoring), `safla.cjs` (feedback loop), `hook-handler.cjs` (routing)

## The 9 Types

| # | Name | Core | Stress → | Growth ← |
|---|------|------|----------|-----------|
| 1 | Reformer | Perfection | 4 | 7 |
| 2 | Helper | Connection | 8 | 4 |
| 3 | Achiever | Status | 9 | 6 |
| 4 | Individualist | Authenticity | 2 | 1 |
| 5 | Investigator | Understanding | 7 | 8 |
| 6 | Loyalist | Security | 3 | 12→9 |
| 7 | Enthusiast | Freedom | 1 | 5 |
| 8 | Challenger | Power | 5 | 2 |
| 9 | Peacemaker | Harmony | 6 | 3 |

## Arc Topology (Default Weights)

All 72 arcs (9×8 source→target) start at weight `1.0`.

Higher weight = stronger path = higher probability of routing.

### Key Arcs (Stress/Growth Lines)

```json
{
  "1→4": 1.5,  "1→7": 1.5,
  "2→8": 1.5,  "2→4": 1.5,
  "3→9": 1.5,  "3→6": 1.5,
  "4→2": 1.5,  "4→1": 1.5,
  "5→7": 1.5,  "5→8": 1.5,
  "6→3": 1.5,  "6→9": 1.5,
  "7→1": 1.5,  "7→5": 1.5,
  "8→2": 1.5,  "8→5": 1.5,
  "9→6": 1.5,  "9→3": 1.5
}
```

### Active Learning

When SAFLA records feedback for type X on task Y:
1. Increment arc_weights[`X→Y`] by `feedback_delta`
2. Clamp to [0.5, 3.0]
3. Normalize row to sum 9

## SSA Integration (5D Scoring)

See `ssa.cjs::scoreEnneagramType()`:

```javascript
function scoreEnneagramType(node, query) {
  const weights = topology.arc_weights;
  return (
    weights[`${node}→${inferTarget(query)}`] * 0.4 +
    getStressArc(node, query) * 0.2 +
    getGrowthArc(node, query) * 0.2 +
    getWing(node) * 0.1 +
    recentSuccessRate(node) * 0.1
  );
}
```

## SAFLA Feedback Loop

When `safla.recordOutcome(nodeId, success, cost_delta)` is called:
1. Look up node type from `enneagram_adaptive_topology.json`
2. Apply cost-aware adjustment:
   - `cost_delta > 0.2` → penalize: `weight[node] *= 0.9`
   - `cost_delta < -0.1` → reward: `weight[node] *= 1.1`
   - `success === false` → extra penalty: `weight[node] *= 0.85`
3. Persist to JSON with atomic write

## JSON Schema

```json
{
  "default": {
    "1": 1.0,
    "2": 1.0,
    "3": 3.0,
    "4": 1.0,
    "5": 1.0,
    "6": 1.0,
    "7": 1.0,
    "8": 1.0,
    "9": 1.0,
    "arc_weights": {
      "1→2": 1.0,
      ...
    }
  }
}
```

## Key Functions

| Function | Location | Purpose |
|---|---|---|
| `scoreEnneagramType()` | `ssa.cjs:scoreEnneagramType` | 5D scoring with arc weights |
| `updateArcWeight()` | `safla.cjs` | Apply feedback to arcs |
| `getStressTarget()` | `safla.cjs` | Return stress arrow target |
| `getGrowthTarget()` | `safla.cjs` | Return growth arrow target |
| `loadTopology()` | `hook-handler.cjs` | Load JSON on init |

## Adaptive Behavior

- **Cold start:** All types weight 1.0, arcs weight 1.0
- **After 10 sessions:** SAFLA adjusts weights based on real cost/success data
- **Top performer:** Type 3 has weight 3.0 by default (Achievers optimize tokens)
- **Stress routing:** When user shows frustration, SSA boosts stress-target types
- **Growth routing:** When user asks "how could this be better", SSA boosts growth-target types

## Type-to-Task Mapping Heuristics

| Type | Best for | Avoid |
|------|---------|-------|
| 1 | Code review, refactor, polish | Ambiguous specs |
| 2 | Help docs, onboarding, empathy | Harsh criticism |
| 3 | Fast prototyping, benchmarks | Philosophical debates |
| 4 | Creative features, design | Repetitive boilerplate |
| 5 | Research, architecture, deep dives | Social features |
| 6 | Security, testing, compliance | Breaking changes |
| 7 | Prototypes, experiments, explore | Long-term maintenance |
| 8 | Infrastructure, CLI, power tools | UX polish |
| 9 | Integration, smoothing edges | High-stakes decisions |