# _SETTINGS/RULES/enneagram_multi_zoom_protocol.md — Multi-Zoom + Multi-Lens Doctrine

## Created: 2026-05-02 — META-014 — Permanent doctrine (cross-project)

> **Read:** BEFORE any swarm with ≥3 agents, regardless of project
> **Synthesized from:** stress-test session 2026-05-02 where enneagram caught 2 GRAVE bugs that `8 × general-purpose` would have missed

---

## 🛑 Fundamental principle

**The Enneagram is NOT just `swarm_init → 8 parallel agents`.**

That is merely `parallel-spawn`. The Enneagram means:

1. **Role specialization** (each node detects its own type of bug)
2. **Multi-dimensional cross-check** (never accept single-agent report as final)
3. **Multi-zoom resolution** (verify at ALL scales: Maha → Nano)
4. **Multi-lens** (stylistic + doctrinal/technical + structural + regression + memory)
5. **Anti-simplification** — do not reduce the task to a mechanical pipeline "for efficiency's sake"

**Golden rule:** *"efficiency at the expense of quality and complexity" = anti-pattern.*

---

## 🔍 The 5 mandatory zoom levels

Any complex resolution (>3 files OR >3 logical hops) must be verified at ALL 5 scales:

| Zoom | Scope | Key question | Bug types detected |
|------|-------|--------------|--------------------|
| **MAHA** | Whole system/project | Is the global architecture still coherent? | Center of gravity shifted, broken introductory promise, component imbalance |
| **MACRO** | Cross-module / cross-chapter | Do components still communicate? | Broken cross-references, broken structural parallels, drift |
| **MEZZO** | Module / chapter / subsection | Canonical host respected? Rhythm/style consistent? | Duplicated/missing host, broken rhythm, voice shift |
| **MICRO** | Function / paragraph | Internal logic intact? | Logic bug, fine distinction lost, incorrect merge |
| **NANO** | Character / token / sentence | Lexical details clean? | ASCII vs Unicode, doubled punctuation, double space, broken markup |

**No zoom can be skipped.** NANO bugs are invisible at MAHA. MAHA bugs are invisible at NANO.

---

## 🔬 The 5 mandatory lenses

At each zoom, apply multi-lens:

| Lens | Enneagram node | subagent_type | What it checks |
|------|----------------|---------------|----------------|
| **Stylistic** | Node 4 Contextualizer | `researcher` | Rhythm, voice, reader-experience, fluency |
| **Doctrinal/Technical** | Node 5 Analyzer | `analyst` | Conceptual precision, pattern detection, fine distinctions |
| **Structural** | Node 7 Architect | `architecture` / `system-architect` | Design coherence, narrative arc, balance |
| **Regression** | Node 6 Validator | `tester` / `code-analyzer` | Introduced bugs, broken grammar, mechanical consistency |
| **Memory/Consistency** | Node 9 Memory | `memory-coordinator` / `memory-specialist` | Cross-file consistency, indexes, references |

**Cross-check protocol:** their combined reports give real coverage. A single agent (no matter how good) covers at most 1 lens × 2 zoom levels.

---

## ⚙️ Standard enneagram swarm composition

For ANY complex resolution, the correct swarm is:

```
Phase 1 — Decomposition (Node 8 Orchestrator):
  Break task into executable sub-tasks

Phase 2 — Parallel execution (Node 3 Builder × N + Node 5 Analyzer × M):
  "Worker" agents on exclusively-disjoint scopes

Phase 3 — Multi-zoom + multi-lens cross-check (PARALLEL):
  Node 4 Contextualizer  → Mezzo + Micro stylistic
  Node 5 Analyzer        → Micro + Nano doctrinal/technical
  Node 6 Validator       → Nano regression
  Node 7 Architect       → Maha + Macro structural
  Node 9 Memory          → Macro consistency cross-file

Phase 4 — Consolidation (Node 1 Reformer):
  Synthesize reports, decide which fixes to apply
```

**Never Phase 1+2 without Phase 3.** Never Phase 3 with a single agent.

---

## 🚫 Anti-patterns (TO AVOID)

- ❌ `8 × general-purpose` parallel — that is not enneagram, it is parallel-spawn
- ❌ "All agents report 0 issues, so everything is clean" — without cross-check, the zero-report is suspicious
- ❌ Spawning agents AFTER applying fixes, without prior verification
- ❌ Skipping Validator (Node 6) for "mechanical/trivial" tasks — that's exactly where the mechanical bugs live
- ❌ Verifying only at the implicit zoom of the task (Micro for paragraphs, Macro for architecture, etc.) — bugs hide in the zooms you didn't think of
- ❌ Reducing the task to a "mechanical pipeline" for speed — loses quality on the altar of efficiency

---

## ✅ Correct pattern (TO APPLY)

1. **Before any swarm:** explicitly declare which zooms and which lenses are relevant
2. **Spawn cross-check IN PARALLEL with execution** (not serial), to save time without skipping verification
3. **Accept "ALL clean" verdict only if at least 3 different lenses confirmed it** (single reviewer = single point of failure)
4. **For tasks reported "0 issues" by multiple agents, verify with Reformer (Node 1) cross-checking from a different angle** — they may be over-conservative
5. **For NATURALLY-uniform tasks (many identically-structured files),** split via Node 8 into sub-groups with different lenses, not a monolithic agent

---

## 📋 Applicability (ALL projects)

This doctrine applies to:

- Multi-file manuscript editing (writing projects)
- Android refactoring across multiple modules
- Glossary / large reference data operations
- Multi-layer modifications (Kotlin + JNI + native, etc.)
- Multi-step automation workflows
- **Any future project** with complex tasks

For SIMPLE tasks (1 file, <10 LOC, no cross-references), enneagram + multi-zoom = overkill. Use native tools or 1 simple Agent.

**Concrete thresholds:**
- ≥3 modified files → multi-zoom check mandatory
- ≥5 modified files → all 5 lenses mandatory
- ≥10 modified files → Node 8 split + multi-zoom + Reformer consolidation

---

## 🛠 Helper script

`python .claude/helpers/enneagram_compose.py "<task description>" --files N`

Returns the correct swarm composition (which nodes, which zooms, which lenses) for any task.

Examples:
```bash
python .claude/helpers/enneagram_compose.py "merge paragraphs in 115 files" --files 115
python .claude/helpers/enneagram_compose.py "refactor 8 components" --files 8
python .claude/helpers/enneagram_compose.py "fix 1 typo" --files 1
```

---

## 🧠 Lessons from the origin session (2026-05-02)

**Stress-test on a manuscript-editing swarm of 8 parallel agents revealed:**

1. Validator (Node 6) caught 2 GRAVE bugs: missing blank line + duplicated technical-term markup — invisible to the executing agents
2. Node 5 Analyzer with a different lens recovered 4 missed candidates (clonal pattern across similar files)
3. Node 9 Memory found 2 MEDIUM gaps in cross-file consistency between parallel reference documents
4. Node 7 Architect confirmed MAHA: architecture intact, flagged 1 ambiguity at intro level
5. Nano-zoom at character level caught 4 ASCII-quote artifacts (auto-fixed)

**Total bugs discovered: 8** (2 GRAVE + 6 MEDIUM/sub-threshold), which `8 × general-purpose` missed at 100% rate.

---

## 🎯 Token economy

Multi-zoom does NOT cost much more than IDENTICAL parallel-spawn, because:
- Cross-check agents run IN PARALLEL with primary execution (or immediately after)
- Each has exclusive scope (Maha vs Nano do not overlap)
- Reports are short (max 200-300 words each)

Extra cost: ~30-40% tokens. Benefit: bugs caught at build-time, not post-deployment. Favorable ratio.

---

## 🌀 Omitted dimensions / Open questions (META-014 v1.1)

The current doctrine is complete for spatial-zoom + perspective-lenses. The following remain OPEN:

### A. TEMPORAL dimension (orthogonal to spatial-zoom)
- **Now:** verify current state
- **Drift:** has the modification rotted across 6 sessions? (longitudinal check)
- **Slow regression:** bugs that surface progressively (memory leaks, accuracy drift)
- **Forward promises:** features that depend on current modifications (forward compatibility)

**Add to doctrine:** for STRUCTURAL changes (not just editorial), Node 9 Memory must verify cross-session (git log, prior CHANGELOG entries) — not just cross-file.

### B. Agent failure mode
- What if Node 5 hallucinates? Doctrine lacks AGENT-vs-AGENT cross-validation
- Proposed solution: for critical verdicts, dispatch 2 DIFFERENT agents (e.g., Analyzer + Reviewer) on the SAME scope independently. Compare reports. Divergence >20% = re-run with Node 1 supervisor.

### C. Confidence calibration
- Current verdicts: binary (CLEAN / ISSUE)
- Missing: confidence score per agent (0-100%) based on scope coverage, complexity, ambiguity
- Proposed: Validator returns `{verdict, confidence, scope_coverage_%}`

### D. Conflict resolution across zoom levels
- Maha says OK, Nano says broken — which wins?
- Solution: priority matrix per task type. For editorial: Mezzo > Micro > Nano > Macro > Maha. For security: Nano > Micro > Macro > Mezzo > Maha. Configurable per project.

### E. Domain-specific lenses (extension over the 5 universal)
- **Security lens** (threat modeling, OWASP, injection vectors)
- **UX/Accessibility lens** (a11y, contrast, screen reader)
- **Performance lens** (latency, memory, throughput)
- **Reproducibility lens** (research, scientific code)
- **Compliance lens** (GDPR, HIPAA, licensing)
- **Internationalization lens** (i18n, RTL, encoding)

**Recommendation:** for projects with specialized domains, ADD domain lenses on top of the 5 universal ones.

### F. Pre-flight check on the REQUEST (meta-verification of comprehension)
- Before any swarm: dispatch Node 7 Architect to DECONSTRUCT the request
- Verify: did I understand the task? are there alternative interpretations?
- Solution: Phase 0 — Comprehension Check, before Phase 1 Decomposition

### G. Recursive meta-verification
- Who verifies the verifier?
- Solution: for CRITICAL resolutions (deployments, breaking changes), Phase 5 = secondary Reformer verifies Phase 4 of primary Reformer

### H. Budget tracking
- Multi-zoom can blow up in tokens/time
- Solution: explicit upfront budget cap (e.g., max 100k tokens, max 10 min wall-clock)
- If budget exceeded: graceful degradation (skip lower-priority lenses in reverse order: stylistic → memory → structural → doctrinal → regression)

### I. Human-in-loop integration
- Doctrine implies full automation. Missing: pause + ask user
- Solution: for ambiguous decisions (>2 lenses divergent), Node 1 Reformer escalates to user instead of deciding alone

### J. Cross-doctrine integration
- How does multi-zoom compose with: P9/P10 (project protocols), CHANGELOG/TODO rules, 1000-agent swarm preset?
- Risk: contradictions ("AUTO-SWARM 1000 agents" + "multi-zoom mandatory" = token explosion)
- Solution: multi-zoom is a **subset** of the swarm preset. At 1000 agents, multi-zoom is limited to a sample (10% scope) with Reformer extrapolating to the rest.

### K. Doctrine versioning
- This doctrine is NOT static. It will evolve.
- Solution: quarterly review; doctrine CHANGELOG; backward-compatibility check on modifications.

---

**Status v1.1:** these gaps are ACKNOWLEDGED but not fully resolved. Open work for future sessions. Most urgent: **F. Pre-flight check** (many sessions begin with mis-understood task).
