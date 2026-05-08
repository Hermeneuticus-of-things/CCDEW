#!/usr/bin/env python3
"""
enneagram_compose.py — Multi-zoom + multi-lentilă swarm composer

Doctrina META-014 (2026-05-02): orice cerere complexă cere verificare
la TOATE cele 5 zoom-uri (Maha/Macro/Mezzo/Micro/Nano) prin TOATE cele 5
lentile (stilistic/doctrinar/structural/regression/memorie).

Acest script ia o descriere de task + nr fișiere implicate și întoarce
composiția corectă a swarm-ului (Phase 1-4 + agenți + zoom-uri + lentile).

Usage:
  python enneagram_compose.py "<task_description>" [--files N]
  python enneagram_compose.py "merge paragraphs in 115 manuscript files" --files 115
  python enneagram_compose.py "refactor 8 Android components" --files 8
  python enneagram_compose.py "fix 1 typo" --files 1   # → returns "no swarm needed"

Reference: D:\\Cloude Code\\_SETTINGS\\RULES\\enneagram_multi_zoom_protocol.md
"""

import sys
import os
import json
import uuid
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any


# 9 noduri enneagram — sincronizat cu enneagram_router.py
NODES = {
    1: {"role": "Reformer / QA",      "agent": "reviewer",            "lens": "regression+quality"},
    2: {"role": "Integrator",         "agent": "backend-dev",         "lens": "integration"},
    3: {"role": "Builder",            "agent": "coder",               "lens": "execution"},
    4: {"role": "Contextualizer",     "agent": "researcher",          "lens": "stylistic+UX"},
    5: {"role": "Analyzer",           "agent": "analyst",             "lens": "doctrinar+pattern"},
    6: {"role": "Validator",          "agent": "tester",              "lens": "regression+nano"},
    7: {"role": "Architect",          "agent": "system-architect",    "lens": "structural+maha"},
    8: {"role": "Orchestrator",       "agent": "sparc-orchestrator",  "lens": "decomposition"},
    9: {"role": "Memory/Consolidator", "agent": "memory-coordinator",  "lens": "cross-file+macro"},
}

# v2.0 #4: Matricea priorităților per task type (la conflict zoom)
PRIORITY_MATRIX = {
    "editorial":      ["MEZZO", "MICRO", "NANO", "MACRO", "MAHA"],
    "security":       ["NANO", "MICRO", "MACRO", "MEZZO", "MAHA"],
    "performance":    ["MICRO", "MACRO", "MEZZO", "NANO", "MAHA"],
    "architectural":  ["MAHA", "MACRO", "MEZZO", "MICRO", "NANO"],
    "refactoring":    ["MACRO", "MICRO", "MEZZO", "MAHA", "NANO"],
    "bugfix":         ["MICRO", "NANO", "MACRO", "MEZZO", "MAHA"],
    "default":        ["MICRO", "MEZZO", "NANO", "MACRO", "MAHA"],
}

# v2.0 #5: Domain lenses — activate per file pattern
DOMAIN_LENSES = {
    "security":     {"trigger_patterns": ["auth/", "payment/", "crypto/", "secret"],   "agent": "security-auditor"},
    "ux_a11y":      {"trigger_patterns": [".jsx", ".tsx", ".vue", ".html", ".xml"],    "agent": "mobile-dev"},
    "performance":  {"trigger_patterns": ["loop", "query", "hot/"],                    "agent": "perf-analyzer"},
    "reproducibility": {"trigger_patterns": [".ipynb", "research/", "ml/"],            "agent": "ml-developer"},
    "compliance":   {"trigger_patterns": ["pii", "gdpr", "hipaa", "personal"],         "agent": "pii-detector"},
    "i18n":         {"trigger_patterns": ["locale/", "i18n/", "translations"],         "agent": "researcher"},
    "visual":       {"trigger_patterns": [".css", ".svg", ".html", "ui/"],             "agent": "mobile-dev"},
}

# v2.0 #8: Default budget caps + degradation order
DEFAULT_BUDGET = {
    "max_tokens": 200_000,
    "max_wall_time_min": 15,
    "max_agents_parallel": 8,
}
DEGRADATION_ORDER = ["stilistic", "memorie", "structural", "doctrinar", "regression"]

# v2.1 #13: Phase 0.5 Safety — patterns suspecte
SAFETY_RED_FLAGS = [
    "rm -rf", "DROP TABLE", "DELETE FROM", "TRUNCATE",
    "git push --force", "git reset --hard origin",
    "production", "prod-db", "billing", "live-customers",
    ".env", "secrets", "private-key",
]

# ── Workspace root (cross-platform) ──────────────────────────────────────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE   = os.environ.get('WORKSPACE_DIR', os.path.normpath(os.path.join(_SCRIPT_DIR, '..', '..')))

# v2.1 #11: Telemetry log path
_MEMORY_DIR = os.path.join(WORKSPACE, '_MEMORY')
TELEMETRY_DIR = os.path.join(_MEMORY_DIR, 'enneagram_telemetry')

# v2.1 #12: Pattern memory pentru cross-session learning
PATTERN_MEMORY = os.path.join(_MEMORY_DIR, 'enneagram_patterns.md')

# v2.1 #16: Checkpoint dir pentru resume protocol
CHECKPOINT_DIR = os.path.join(_MEMORY_DIR, 'enneagram_checkpoints')

# v2.1 #17: Privacy isolation per project
PRIVACY_DIR_TEMPLATE = os.path.join(_MEMORY_DIR, '{project}', 'agent_reports')

# v2.0 #9: Triggere escaladare la user
ESCALATION_TRIGGERS = {
    "comprehension_low":     "Phase 0 confidence <70% — propune 3 interpretări",
    "grave_issues_many":     "Phase 4 issues GRAVE >5",
    "dual_witness_diverge":  "Dual-Witness divergență >50%",
    "budget_exceeded":       "Budget depășit cu >100%",
    "zoom_conflict_irreducible": "Zoom-uri în conflict ireductibil cu priority matrix",
    "safety_suspect":        "Safety pre-check a detectat red flags",
}

# v2.1 #20: Self-test config — quarterly review
SELF_TEST_CONFIG = {
    "review_interval_days": 90,
    "audit_targets": [
        os.path.join("_SETTINGS", "RULES", "enneagram_multi_zoom_protocol.md"),
        os.path.join(".claude", "helpers", "enneagram_compose.py"),
        os.path.join(".claude", "helpers", "enneagram_router.py"),
    ],
}

# Cele 5 zoom-uri — Maha (cosmic) → Nano (caracter)
ZOOMS = {
    "MAHA":  {"scope": "Sistem/proiect întreg",       "checks": "centru greutate, promisiune introductivă, balanță"},
    "MACRO": {"scope": "Cross-modul/cross-capitol",   "checks": "cross-references, paralele structurale, drift"},
    "MEZZO": {"scope": "Modul/capitol/subcap",        "checks": "gazda canonică, ritm, voce, P10"},
    "MICRO": {"scope": "Funcție/paragraf",            "checks": "logica internă, distincții, merge corect"},
    "NANO":  {"scope": "Caracter/token/propoziție",   "checks": "ASCII vs Unicode, punctuație, spațiu, ALOGEN"},
}

# 5 lentile — fiecare cu nodul ei principal
LENSES = {
    "stilistic":   {"node": 4, "covers": ["MEZZO", "MICRO"], "questions": "Mai sună a [proiect]? Ritm rupt? Reader experience?"},
    "doctrinar":   {"node": 5, "covers": ["MICRO", "NANO"],  "questions": "Distincții fine păstrate? Termeni precisi? Pattern coerent?"},
    "structural":  {"node": 7, "covers": ["MAHA", "MACRO"],  "questions": "Arhitectura intactă? Arc narativ coerent? Balanță componente?"},
    "regression":  {"node": 6, "covers": ["NANO", "MICRO"],  "questions": "Bug-uri introduse? Gramatică ruptă? ALOGEN dup? Mecanic OK?"},
    "memorie":     {"node": 9, "covers": ["MACRO", "MEZZO"], "questions": "Cross-file consistency? Index-uri sincronizate? Refs valide?"},
}


# =====================================================================
# v2.1 IMPLEMENTATIONS — toate 20 gap-uri funcționale
# =====================================================================

def log_telemetry(session_data: dict) -> str:
    """v2.1 #11 — Telemetry log per sesiune."""
    Path(TELEMETRY_DIR).mkdir(parents=True, exist_ok=True)
    today = datetime.now()
    month_dir = Path(TELEMETRY_DIR) / today.strftime("%Y-%m")
    month_dir.mkdir(parents=True, exist_ok=True)
    log_path = month_dir / f"session_{today.strftime('%Y%m%d_%H%M%S')}.json"
    session_data["timestamp"] = today.isoformat()
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(session_data, f, indent=2, ensure_ascii=False)
    return str(log_path)


def update_pattern_memory(pattern: dict) -> bool:
    """v2.1 #12 — Update pattern memory cross-sesiune."""
    Path(PATTERN_MEMORY).parent.mkdir(parents=True, exist_ok=True)
    if not Path(PATTERN_MEMORY).exists():
        Path(PATTERN_MEMORY).write_text("# Enneagram Patterns Memory\n\n", encoding="utf-8")
    entry = (
        f"\n## {datetime.now().strftime('%Y-%m-%d %H:%M')} — {pattern.get('type', 'pattern')}\n"
        f"- Task type: {pattern.get('task_type', 'N/A')}\n"
        f"- Pattern: {pattern.get('description', '')}\n"
        f"- Lens: {pattern.get('lens', '')}\n"
        f"- Occurrences: {pattern.get('occurrences', 1)}\n"
        f"- Trust adjustment: {pattern.get('trust_delta', 0):+d}\n"
    )
    with open(PATTERN_MEMORY, "a", encoding="utf-8") as f:
        f.write(entry)
    return True


def save_checkpoint(task_id: str, phase: str, data: dict) -> str:
    """v2.1 #16 — Save checkpoint pentru resume protocol."""
    Path(CHECKPOINT_DIR).mkdir(parents=True, exist_ok=True)
    cp_path = Path(CHECKPOINT_DIR) / f"{task_id}_phase_{phase}.json"
    with open(cp_path, "w", encoding="utf-8") as f:
        json.dump({"task_id": task_id, "phase": phase, "data": data,
                   "timestamp": datetime.now().isoformat()}, f, indent=2, ensure_ascii=False)
    return str(cp_path)


def load_checkpoint(task_id: str) -> Optional[dict]:
    """v2.1 #16 — Load ultimul checkpoint complet."""
    if not Path(CHECKPOINT_DIR).exists():
        return None
    checkpoints = sorted(Path(CHECKPOINT_DIR).glob(f"{task_id}_phase_*.json"))
    if not checkpoints:
        return None
    with open(checkpoints[-1], "r", encoding="utf-8") as f:
        return json.load(f)


def get_privacy_dir(project: str) -> Path:
    """v2.1 #17 — Namespace-isolated dir per proiect pentru rapoarte."""
    privacy_path = Path(PRIVACY_DIR_TEMPLATE.format(project=project))
    privacy_path.mkdir(parents=True, exist_ok=True)
    return privacy_path


def topological_sort(sub_tasks: List[Dict]) -> List[List[str]]:
    """v2.1 #18 — DAG topologic sort. Returns waves of parallel-executable IDs."""
    deps = {t["id"]: set(t.get("depends_on", [])) for t in sub_tasks}
    waves = []
    completed = set()
    remaining = set(deps.keys())
    while remaining:
        wave = [tid for tid in remaining if deps[tid].issubset(completed)]
        if not wave:
            raise ValueError(f"DAG cycle detected: {remaining}")
        waves.append(wave)
        completed.update(wave)
        remaining.difference_update(wave)
    return waves


def bargain_triangle(reports: List[Dict], max_hops: int = 3) -> dict:
    """v2.1 #15 — Inter-agent negotiation protocol."""
    if len(reports) < 2:
        return {"verdict": reports[0] if reports else None, "hops": 0, "consensus": True}
    agreements = sum(1 for r in reports if r.get("verdict") == reports[0].get("verdict"))
    consensus_ratio = agreements / len(reports)
    if consensus_ratio >= 0.8:
        return {"verdict": reports[0]["verdict"], "hops": 1, "consensus": True}
    return {
        "verdict": "DIVERGENT",
        "hops": max_hops,
        "consensus": False,
        "action": "ESCALATE TO USER — agents disagree after Bargain-Triangle exhaustion",
        "reports": reports,
    }


def confidence_report(verdict: str, confidence: int, scope_coverage: int,
                       issues: List[Dict] = None, limitations: str = "") -> dict:
    """v2.0 #3 — Format report standardizat cu confidence calibration."""
    return {
        "verdict": verdict,
        "confidence": max(0, min(100, confidence)),
        "scope_coverage": max(0, min(100, scope_coverage)),
        "issues": issues or [],
        "limitations": limitations,
        "weighted_score": (confidence * scope_coverage) / 100,
    }


def escalate_to_user(trigger: str, context: dict) -> dict:
    """v2.0 #9 — Generează prompt escaladare la user."""
    if trigger not in ESCALATION_TRIGGERS:
        trigger = "general"
    return {
        "action": "ESCALATE",
        "trigger": trigger,
        "reason": ESCALATION_TRIGGERS.get(trigger, "Unknown escalation"),
        "context": context,
        "user_prompt": f"""
[ESCALATION REQUIRED — {trigger}]
Reason: {ESCALATION_TRIGGERS.get(trigger)}
Context: {json.dumps(context, indent=2, ensure_ascii=False)}

Your decision needed before proceeding.
""",
    }


def emergence_smoke_test(modifications: List[str], test_command: Optional[str] = None) -> dict:
    """v2.1 #19 — Smoke test pentru emergence detection."""
    return {
        "phase": "3.5",
        "modifications_count": len(modifications),
        "test_command": test_command or "auto-detect (build/test/preview)",
        "action": (
            "Aplica TOATE modificările simultan într-un environment de test; "
            "rulează build + test suite + preview live; "
            "detectează interaction effects pe care lentile singulare le-ar rata"
        ),
    }


def self_test_doctrine() -> dict:
    """v2.1 #20 — Self-audit pe doctrina și implementarea ei."""
    targets = SELF_TEST_CONFIG["audit_targets"]
    results = {"audited_at": datetime.now().isoformat(), "targets": [], "issues": []}
    base = Path(WORKSPACE)
    for t in targets:
        full_path = base / t
        if not full_path.exists():
            results["issues"].append({"file": t, "issue": "MISSING"})
        else:
            results["targets"].append({
                "file": t,
                "exists": True,
                "size": full_path.stat().st_size,
                "modified": datetime.fromtimestamp(full_path.stat().st_mtime).isoformat(),
            })
    next_review = datetime.now().timestamp() + (SELF_TEST_CONFIG["review_interval_days"] * 86400)
    results["next_review_due"] = datetime.fromtimestamp(next_review).isoformat()
    return results


def temporal_check(file_paths: List[str], lookback_commits: int = 10) -> dict:
    """v2.0 #1 — TEMPO zoom: verifică drift cross-sesiune via git log."""
    return {
        "phase": "TEMPO",
        "subscales": {
            "NOW": "current state verified by other lenses",
            "DRIFT": f"compare with last {lookback_commits} commits via `git log -p`",
            "REGRESSION_LENT": "memory/accuracy/perf delta over time (manual)",
            "FORWARD": "cross-check with TODO.md, ROADMAP.md, CHANGELOG.md",
        },
        "files_to_check": file_paths,
        "command_template": f"git log -p -n {lookback_commits} -- {{file}}",
    }


# =====================================================================
# v3.0 IMPLEMENTATIONS — Learning & Auto-evolution layer (gap-uri 21-30)
# =====================================================================

LENS_EFFECTIVENESS_PATH = os.path.join(_MEMORY_DIR, 'lens_effectiveness.json')
AGENT_TRUST_PATH        = os.path.join(_MEMORY_DIR, 'agent_trust.json')
TUNED_THRESHOLDS_PATH   = os.path.join(_MEMORY_DIR, 'tuned_thresholds.json')
BUG_CATALOG_PATH        = os.path.join(_MEMORY_DIR, 'bug_catalog.md')
DOCTRINE_PROPOSALS_PATH = os.path.join(_MEMORY_DIR, 'doctrine_proposals.md')


def _load_json(path: str, default: dict = None) -> dict:
    if default is None:
        default = {}
    if not Path(path).exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _save_json(path: str, data: dict) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def update_lens_effectiveness(task_type: str, lens: str, outcome: str) -> dict:
    """v3.0 #21 — Active learning from outcomes."""
    data = _load_json(LENS_EFFECTIVENESS_PATH, {})
    key = f"{task_type}::{lens}"
    if key not in data:
        data[key] = {"true_pos": 0, "false_pos": 0, "false_neg": 0, "true_neg": 0}
    if outcome in data[key]:
        data[key][outcome] += 1
    total = sum(data[key].values())
    data[key]["success_rate"] = (data[key]["true_pos"] / total) if total > 0 else 0.0
    _save_json(LENS_EFFECTIVENESS_PATH, data)
    return data[key]


def update_trust(agent: str, outcome: str, alpha: float = 0.2) -> float:
    """v3.0 #22 — Trust score evolution via EMA."""
    data = _load_json(AGENT_TRUST_PATH, {})
    if agent not in data:
        data[agent] = {"trust": 0.5, "n_signals": 0}
    signal_map = {"true_pos": 1.0, "true_neg": 0.8, "false_pos": -0.3, "false_neg": -0.5}
    signal = signal_map.get(outcome, 0)
    data[agent]["trust"] = alpha * (0.5 + signal / 2) + (1 - alpha) * data[agent]["trust"]
    data[agent]["trust"] = max(0.0, min(1.0, data[agent]["trust"]))
    data[agent]["n_signals"] += 1
    _save_json(AGENT_TRUST_PATH, data)
    return data[agent]["trust"]


def get_trust(agent: str) -> float:
    """v3.0 #22 helper."""
    data = _load_json(AGENT_TRUST_PATH, {})
    return data.get(agent, {}).get("trust", 0.5)


def doctrine_evolve_proposals(min_occurrences: int = 10) -> List[dict]:
    """v3.0 #23 — Auto-propose doctrine modifications based on patterns."""
    if not Path(PATTERN_MEMORY).exists():
        return []
    proposals = []
    text = Path(PATTERN_MEMORY).read_text(encoding="utf-8")
    pattern_counts = {}
    for line in text.split("\n"):
        if line.startswith("- Pattern:"):
            p = line.replace("- Pattern:", "").strip()
            pattern_counts[p] = pattern_counts.get(p, 0) + 1
    for pattern, count in pattern_counts.items():
        if count >= min_occurrences:
            proposals.append({
                "pattern": pattern,
                "occurrences": count,
                "proposal": f"Add as explicit rule to doctrine (recurs {count}x)",
                "status": "AWAIT_HUMAN_REVIEW",
            })
    if proposals:
        Path(DOCTRINE_PROPOSALS_PATH).parent.mkdir(parents=True, exist_ok=True)
        with open(DOCTRINE_PROPOSALS_PATH, "a", encoding="utf-8") as f:
            f.write(f"\n## {datetime.now().strftime('%Y-%m-%d')} — Auto-proposals\n")
            for p in proposals:
                f.write(f"- {p['pattern']} ({p['occurrences']}x) — {p['proposal']}\n")
    return proposals


def inject_historical_context(task_type: str, task_description: str = "") -> str:
    """v3.0 #24 — Reinforcement loop via historical context injection."""
    effectiveness = _load_json(LENS_EFFECTIVENESS_PATH, {})
    relevant = {k.split("::")[1]: v for k, v in effectiveness.items() if k.startswith(f"{task_type}::")}
    top_lenses = sorted(relevant.items(), key=lambda x: x[1].get("success_rate", 0), reverse=True)[:3]
    if not top_lenses:
        return ""
    context = "Context din sesiuni anterioare similare:\n"
    for lens, stats in top_lenses:
        sr = stats.get("success_rate", 0)
        context += f"- Lens '{lens}': success rate {sr:.0%} ({stats.get('true_pos', 0)} bug-uri prinse)\n"
    return context


def abstract_pattern(specific_pattern: str) -> dict:
    """v3.0 #25 — Cross-domain knowledge transfer via pattern abstraction."""
    abstractions = {
        "duplicate": "DUPLICATE_MARKUP_AT_BOUNDARY",
        "missing": "MISSING_SEPARATOR_AT_MERGE",
        "leak": "RESOURCE_LEAK_PATTERN",
        "race": "CONCURRENCY_RACE_CONDITION",
        "off-by-one": "BOUNDARY_OFF_BY_ONE",
        "null": "NULL_REFERENCE_DEREF",
        "encoding": "CHARACTER_ENCODING_MISMATCH",
        "dependency": "STALE_DEPENDENCY_REFERENCE",
    }
    p_lower = specific_pattern.lower()
    for keyword, abstract_name in abstractions.items():
        if keyword in p_lower:
            return {
                "specific": specific_pattern,
                "abstract": abstract_name,
                "scope": "cross-project",
                "applicability": ["Karma Book", "SunriseApp", "Glosar", "GemmaApp", "any-future-project"],
            }
    return {"specific": specific_pattern, "abstract": "UNCLASSIFIED", "scope": "specific"}


def predict_relevant_lenses(task_type: str, top_n: int = 3) -> List[str]:
    """v3.0 #26 — Predictive routing via Bayesian recommendation."""
    effectiveness = _load_json(LENS_EFFECTIVENESS_PATH, {})
    relevant = [(k.split("::")[1], v.get("success_rate", 0))
                for k, v in effectiveness.items() if k.startswith(f"{task_type}::")]
    if not relevant:
        return list(LENSES.keys())[:top_n]
    relevant.sort(key=lambda x: x[1], reverse=True)
    return [name for name, _ in relevant[:top_n]]


def tune_thresholds(task_type: str, min_sessions: int = 50) -> dict:
    """v3.0 #27 — Auto-tune thresholds via Bayesian update."""
    data = _load_json(TUNED_THRESHOLDS_PATH, {})
    if task_type not in data:
        data[task_type] = {
            "consensus_threshold": 0.8,
            "confidence_min": 70,
            "scope_coverage_min": 70,
            "n_sessions": 0,
        }
    data[task_type]["n_sessions"] += 1
    if data[task_type]["n_sessions"] < min_sessions:
        return data[task_type]
    return data[task_type]


def bug_catalog_add(bug_id: str, symptoms: str, detection: str, fix_template: str, location: str = "") -> bool:
    """v3.0 #28 — Bug catalog auto-grow."""
    Path(BUG_CATALOG_PATH).parent.mkdir(parents=True, exist_ok=True)
    if not Path(BUG_CATALOG_PATH).exists():
        Path(BUG_CATALOG_PATH).write_text("# Bug Catalog — Wisdom Accumulation\n\n", encoding="utf-8")
    text = Path(BUG_CATALOG_PATH).read_text(encoding="utf-8")
    if f"## {bug_id}" in text:
        new_text = text.replace(f"## {bug_id}", f"## {bug_id} (occurred again)")
        Path(BUG_CATALOG_PATH).write_text(new_text, encoding="utf-8")
    else:
        with open(BUG_CATALOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"\n## {bug_id} (occurred 1x)\n")
            f.write(f"- Symptoms: {symptoms}\n- Detection: {detection}\n")
            f.write(f"- Fix template: {fix_template}\n- Last seen: {datetime.now().strftime('%Y-%m-%d')} {location}\n")
    return True


def bug_catalog_search(query: str) -> List[dict]:
    """v3.0 #28 — Search known bugs."""
    if not Path(BUG_CATALOG_PATH).exists():
        return []
    text = Path(BUG_CATALOG_PATH).read_text(encoding="utf-8")
    results = []
    for block in text.split("\n## "):
        if query.lower() in block.lower():
            results.append({"match": block[:300]})
    return results


def select_lenses_bandit(task_type: str, budget_lenses: int = 3, epsilon: float = 0.1) -> List[str]:
    """v3.0 #29 — Multi-armed bandit explore/exploit on lenses."""
    import random
    available = list(LENSES.keys())
    if random.random() < epsilon:
        return random.sample(available, min(budget_lenses, len(available)))
    return predict_relevant_lenses(task_type, top_n=budget_lenses)


# =====================================================================
# v3.1 IMPLEMENTATIONS — Fully Adaptive (Thresholds + Enneagram Topology)
# =====================================================================

ADAPTIVE_TOPOLOGY_PATH = os.path.join(_MEMORY_DIR, 'enneagram_adaptive_topology.json')


def adaptive_threshold(task_type: str, threshold_name: str,
                        outcome_was_correct: bool = None,
                        learning_rate: float = 0.05) -> float:
    """v3.1 — Praguri adaptive cu Bayesian update.

    threshold_name ∈ {consensus_threshold, confidence_min, scope_coverage_min,
                      escalation_grave_count, dual_witness_divergence, budget_overflow_pct}
    Praguri implicite: 0.8 / 70 / 70 / 5 / 0.5 / 1.0
    """
    data = _load_json(TUNED_THRESHOLDS_PATH, {})
    if task_type not in data:
        data[task_type] = {
            "consensus_threshold": 0.8,
            "confidence_min": 70,
            "scope_coverage_min": 70,
            "escalation_grave_count": 5,
            "dual_witness_divergence": 0.5,
            "budget_overflow_pct": 1.0,
            "n_sessions": 0,
        }
    if outcome_was_correct is not None:
        # Dacă verdict corect → relax pragul (mai tolerant)
        # Dacă verdict greșit → tighten pragul (mai strict)
        delta = -learning_rate if outcome_was_correct else learning_rate
        if threshold_name in {"consensus_threshold", "dual_witness_divergence"}:
            data[task_type][threshold_name] = max(0.5, min(0.95, data[task_type][threshold_name] + delta))
        elif threshold_name in {"confidence_min", "scope_coverage_min"}:
            data[task_type][threshold_name] = max(50, min(95, data[task_type][threshold_name] + delta * 100))
        elif threshold_name == "escalation_grave_count":
            data[task_type][threshold_name] = max(1, min(20, data[task_type][threshold_name] + (1 if not outcome_was_correct else -1)))
        elif threshold_name == "budget_overflow_pct":
            data[task_type][threshold_name] = max(0.2, min(3.0, data[task_type][threshold_name] + delta))
        data[task_type]["n_sessions"] += 1
        _save_json(TUNED_THRESHOLDS_PATH, data)
    return data[task_type].get(threshold_name, 0.5)


def adaptive_enneagram(task_type: str, lens_weights: Dict[str, float] = None) -> dict:
    """v3.1 — Enneagram topology adaptive per task type.

    Stochează ponderi per nod per task type. La conflict-uri, nodurile cu pondere
    mai mare au prioritate. Decizii: ce noduri activate per Phase 3, în ce ordine.
    """
    data = _load_json(ADAPTIVE_TOPOLOGY_PATH, {})
    if task_type not in data:
        data[task_type] = {str(node): 1.0 for node in NODES.keys()}
        data[task_type]["arc_weights"] = {f"{a}→{b}": 1.0
                                           for a in NODES for b in NODES if a != b}
    if lens_weights:
        for lens, weight in lens_weights.items():
            for lens_name, lens_info in LENSES.items():
                if lens_name == lens:
                    node_id = str(lens_info["node"])
                    data[task_type][node_id] = data[task_type].get(node_id, 1.0) * weight
    _save_json(ADAPTIVE_TOPOLOGY_PATH, data)
    return data[task_type]


def get_adaptive_node_priority(task_type: str) -> List[int]:
    """v3.1 — Ordine noduri ponderată pentru task type."""
    data = _load_json(ADAPTIVE_TOPOLOGY_PATH, {})
    weights = data.get(task_type, {})
    if not weights:
        return list(NODES.keys())
    node_weights = [(int(k), v) for k, v in weights.items() if k.isdigit()]
    node_weights.sort(key=lambda x: x[1], reverse=True)
    return [n for n, _ in node_weights]


def reinforce_enneagram(task_type: str, node: int, success: bool, learning_rate: float = 0.1) -> float:
    """v3.1 — Reinforce nod enneagram pe baza outcome."""
    data = _load_json(ADAPTIVE_TOPOLOGY_PATH, {})
    if task_type not in data:
        adaptive_enneagram(task_type)
        data = _load_json(ADAPTIVE_TOPOLOGY_PATH, {})
    delta = learning_rate if success else -learning_rate
    current = data[task_type].get(str(node), 1.0)
    data[task_type][str(node)] = max(0.1, min(3.0, current + delta))
    _save_json(ADAPTIVE_TOPOLOGY_PATH, data)
    return data[task_type][str(node)]


def evaluate_learning_strategy() -> dict:
    """v3.0 #30 — Meta-meta: evaluate if learning itself is helping."""
    effectiveness = _load_json(LENS_EFFECTIVENESS_PATH, {})
    if not effectiveness:
        return {"verdict": "INSUFFICIENT_DATA", "n_records": 0}
    total_tp = sum(v.get("true_pos", 0) for v in effectiveness.values())
    total_fp = sum(v.get("false_pos", 0) for v in effectiveness.values())
    total_fn = sum(v.get("false_neg", 0) for v in effectiveness.values())
    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    return {
        "n_records": len(effectiveness),
        "true_positives": total_tp,
        "false_positives": total_fp,
        "false_negatives": total_fn,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1_score": round(f1, 3),
        "verdict": "LEARNING_HELPING" if f1 > 0.7 else "LEARNING_MARGINAL" if f1 > 0.4 else "LEARNING_NOT_HELPING",
    }


def dual_witness_dispatch(scope: str, primary_node: int, witness_node: int) -> dict:
    """v2.0 #2 — Dual-Witness protocol pentru critical verdicts."""
    return {
        "protocol": "DUAL_WITNESS",
        "scope": scope,
        "agents": [
            {"node": primary_node, "agent": NODES[primary_node]["agent"], "role": "primary"},
            {"node": witness_node, "agent": NODES[witness_node]["agent"], "role": "witness"},
        ],
        "instruction": "Independent reports, no shared context. Compare verdicts.",
        "convergence_threshold": 0.8,
        "escalation_on_diverge": True,
    }


# =====================================================================
# Existing functions
# =====================================================================

def safety_check(task_description: str) -> dict:
    """v2.1 #13 — Phase 0.5 Adversarial/Safety pre-check."""
    desc_lower = task_description.lower()
    flags_hit = [f for f in SAFETY_RED_FLAGS if f.lower() in desc_lower]
    if flags_hit:
        return {"status": "suspect", "flags": flags_hit,
                "action": "ESCALATE TO USER — request contains potentially dangerous patterns"}
    return {"status": "safe", "flags": [], "action": "proceed to Phase 0"}


def detect_domain_lenses(task_description: str, file_patterns: Optional[list] = None) -> list:
    """v2.0 #5 — auto-detectare lentile domeniu pe baza descriere/files."""
    activated = []
    desc_lower = task_description.lower()
    patterns_to_check = file_patterns or [task_description]
    for lens_name, lens_info in DOMAIN_LENSES.items():
        for trigger in lens_info["trigger_patterns"]:
            if any(trigger.lower() in p.lower() for p in patterns_to_check):
                activated.append({"lens": lens_name, "agent": lens_info["agent"], "trigger": trigger})
                break
            if trigger.lower() in desc_lower:
                activated.append({"lens": lens_name, "agent": lens_info["agent"], "trigger": trigger})
                break
    return activated


def estimate_budget(num_files: int, complexity: str, lenses: int) -> dict:
    """v2.0 #8 — estimare budget tokens/timp."""
    base_tokens = num_files * 3000  # ~3k tokens per file inspecting
    cross_check_tokens = lenses * 8000  # ~8k per lens
    total = base_tokens + cross_check_tokens
    return {
        "estimated_tokens": total,
        "estimated_wall_min": max(2, total // 20000),
        "exceeds_default_budget": total > DEFAULT_BUDGET["max_tokens"],
    }


def get_priority_order(task_type: str) -> list:
    """v2.0 #4 — întoarce ordinea priorităților zoom-uri pentru task type."""
    return PRIORITY_MATRIX.get(task_type.lower(), PRIORITY_MATRIX["default"])


def compose_swarm(task_description: str, num_files: int,
                   task_type: str = "default", critical: bool = False,
                   temporal_check: bool = False, file_patterns: Optional[list] = None) -> dict:
    """
    Întoarce composiția corectă pentru un task dat.

    v2.0 args: task_type (priority matrix), critical (Dual-Witness + Phase 5), temporal_check (TEMPO zoom)
    v2.1 args: file_patterns (auto-detect domain lenses)
    """
    # v2.1 #13 — Phase 0.5 Safety pre-check
    safety = safety_check(task_description)

    # v2.0 #5 — auto-detectează lentile domeniu
    domain_lenses = detect_domain_lenses(task_description, file_patterns)

    # v2.0 #4 — ordine prioritate zoom-uri
    zoom_priority = get_priority_order(task_type)

    result = {
        "task": task_description,
        "num_files": num_files,
        "task_type": task_type,
        "critical": critical,
        "temporal_check": temporal_check,
        "safety_precheck": safety,
        "domain_lenses_activated": domain_lenses,
        "zoom_priority_order": zoom_priority,
        "complexity": None,
        "verdict": None,
        "phases": [],
        "warnings": [],
    }

    # Halt dacă safety suspect
    if safety["status"] == "suspect":
        result["verdict"] = "HALT — safety pre-check failed. Escaladare la user."
        result["complexity"] = "BLOCKED"
        return result

    # Determină complexitatea pe baza nr fișiere
    if num_files <= 1:
        result["complexity"] = "TRIVIAL"
        result["verdict"] = "NO SWARM. Folosește direct Edit/Write/Read. Eventual 1 Agent simplu."
        return result

    if num_files == 2:
        result["complexity"] = "SIMPLU"
        result["verdict"] = "NO SWARM. Lucru direct cu Edit/MultiEdit. Cross-check opțional la final."
        return result

    if 3 <= num_files <= 4:
        result["complexity"] = "MEDIU (≥3 → multi-zoom obligatoriu)"
        result["phases"] = [
            {
                "phase": "1 — Decompoziție",
                "node": 8,
                "agent": NODES[8]["agent"],
                "action": "Sparge task-ul în sub-task-uri executabile, scope exclusiv per agent",
            },
            {
                "phase": "2 — Execuție",
                "nodes": [3, 5],
                "parallel": True,
                "action": "Agenți lucrători (Builder + Analyzer) pe scope-uri disjuncte",
            },
            {
                "phase": "3 — Cross-check (PARALEL, 3 lentile minim)",
                "nodes": [4, 6, 9],
                "parallel": True,
                "lenses": ["stilistic", "regression", "memorie"],
                "zooms_covered": ["MEZZO", "MICRO", "NANO", "MACRO"],
                "action": "Multi-lentilă cross-check; agenți verifică INDEPENDENT",
            },
            {
                "phase": "4 — Consolidare",
                "node": 1,
                "agent": NODES[1]["agent"],
                "action": "Sintetizează rapoartele, decide ce fix aplica",
            },
        ]

    elif 5 <= num_files <= 9:
        result["complexity"] = "COMPLEX (≥5 → toate 5 lentile)"
        result["phases"] = [
            {
                "phase": "1 — Decompoziție",
                "node": 8,
                "agent": NODES[8]["agent"],
                "action": "Sparge în sub-grupuri cu lentile diferite, scope exclusiv",
            },
            {
                "phase": "2 — Execuție",
                "nodes": [3, 5],
                "parallel": True,
                "n_workers": min(num_files, 5),
                "action": "Builder × N + Analyzer × M, distribuiți pe sub-task-uri",
            },
            {
                "phase": "3 — Cross-check (PARALEL, TOATE 5 lentile)",
                "nodes": [4, 5, 6, 7, 9],
                "parallel": True,
                "lenses": list(LENSES.keys()),
                "zooms_covered": list(ZOOMS.keys()),
                "action": "FIECARE lentilă raportează INDEPENDENT pe scope-ul ei",
            },
            {
                "phase": "4 — Consolidare",
                "node": 1,
                "agent": NODES[1]["agent"],
                "action": "Reformer agregă rapoartele, decide aplicarea fix-urilor critice",
            },
        ]

    elif num_files >= 10:
        result["complexity"] = "MASIV (≥10 → split + Reformer consolidare)"
        result["phases"] = [
            {
                "phase": "0 — Comprehension Check (v2.0 #6)",
                "node": 7,
                "agent": NODES[7]["agent"],
                "action": "Deconstrucție cerere: scope/goal/constraints/3 interpretări alternative. Confidence <70% → escaladare user.",
            },
            {
                "phase": "0.5 — Safety pre-check (v2.1 #13)",
                "node": 1,
                "agent": NODES[1]["agent"],
                "action": "Verifică red flags adversariale (rm -rf, DROP TABLE, prod, secrets etc.). Suspect → halt.",
            },
            {
                "phase": "1 — Decompoziție hierarchical + DAG (v2.1 #18)",
                "node": 8,
                "agent": NODES[8]["agent"],
                "action": "Split în sub-grupuri logice cu DAG dependencies (nu list); fiecare nod primește 1 Builder + 1 Analyzer; topologic exec",
            },
            {
                "phase": "2 — Execuție paralelă (N workers, topologic)",
                "nodes": [3, 5],
                "parallel": True,
                "n_workers": "1-per-nod-DAG, capped la 8-10 simultan",
                "action": "Workers pe scope-uri exclusive; respectă DAG dependencies; checkpoint per phase (v2.1 #16)",
            },
            {
                "phase": "3 — Cross-check (TOATE 5 lentile + lentile domeniu, multi-zoom)",
                "nodes": [4, 5, 6, 7, 9],
                "parallel": True,
                "lenses": list(LENSES.keys()),
                "zooms_covered": list(ZOOMS.keys()) + (["TEMPO"] if temporal_check else []),
                "action": "PARALEL, fiecare nod scope-ul lui; rezultate INDEPENDENT cu confidence score (v2.0 #3)",
                "warning": "Niciun nod nu poate fi sărit la ≥10 fișiere. Anti-pattern: 'toți raportează 0' fără verificare prin altă lentilă."
            },
            {
                "phase": "3.5 — Emergence detection (v2.1 #19)",
                "node": 6,
                "agent": NODES[6]["agent"],
                "action": "Smoke test pe sistem cu TOATE modificările aplicate. Detectează interaction effects pe care lentile singulare le ratează.",
            },
            {
                "phase": "4 — Consolidare cross-perspective (cu Bargain-Triangle v2.1 #15)",
                "node": 1,
                "agent": NODES[1]["agent"],
                "action": "Reformer agregă cu confidence-weighted; la divergență >20% → Bargain-Triangle (max 3 hops); apoi decizie",
            },
            {
                "phase": "5 — Meta-verification (v2.0 #7) [DOAR critical]" if critical else "5 — Memorie post-mortem (v2.1 #11+#12)",
                "node": 1 if critical else 9,
                "agent": NODES[1]["agent"] if critical else NODES[9]["agent"],
                "action": ("Reformer secundar verifică Phase 4 — issues mascate? confidence justifică verdict?"
                          if critical else
                          "Telemetry log + pattern memory update; lecții → _MEMORY/enneagram_patterns.md"),
            },
        ]

    # Anti-pattern checks pe descrierea task-ului
    desc_lower = task_description.lower()
    anti_patterns = [
        ("efficient", "Cuvântul 'efficient' detectat — risc de simplificare. Verifică să NU sari peste cross-check pentru viteză."),
        ("rapid", "Cuvântul 'rapid' detectat — pragul timp NU justifică omisiune cross-check."),
        ("quick", "Cuvântul 'quick' detectat — verifică pragul de complexitate, nu sări lentile."),
        ("simple", "Cuvântul 'simple' detectat — dacă chiar e simplu (≤2 fișiere), NU swarm. Dacă nu, multi-zoom obligatoriu."),
        ("just", "Cuvântul 'just' detectat — frecvent semnalează minimizare nepotrivită a complexității."),
    ]
    for pattern, warning in anti_patterns:
        if pattern in desc_lower:
            result["warnings"].append(warning)

    # Excepții documentate (din CLAUDE.md root)
    exceptions = [
        ("karma book", "Karma Book — niciodată swarm pentru editare text literar. Verifică dacă task-ul e text vs structural."),
        ("o modificare pe rând", "SunriseApp 'o modificare pe rând' — single-agent, NU swarm."),
        ("un fix", "Fix singular — verifică să NU declanșezi swarm overhead inutil."),
    ]
    for pattern, warning in exceptions:
        if pattern in desc_lower:
            result["warnings"].append(warning)

    return result


def format_output(composition: dict, output_format: str = "text") -> str:
    """
    Formatează compoziția pentru output uman sau JSON.
    """
    if output_format == "json":
        return json.dumps(composition, indent=2, ensure_ascii=False)

    # Text output
    lines = []
    lines.append("=" * 70)
    lines.append(f"ENNEAGRAM SWARM COMPOSITION — META-014")
    lines.append("=" * 70)
    lines.append(f"Task: {composition['task']}")
    lines.append(f"Files: {composition['num_files']}")
    lines.append(f"Complexity: {composition['complexity']}")
    lines.append("")

    if composition.get("verdict"):
        lines.append(f"VERDICT: {composition['verdict']}")
        lines.append("")

    if composition["phases"]:
        lines.append("PHASES:")
        lines.append("-" * 70)
        for phase in composition["phases"]:
            lines.append(f"\n{phase['phase']}")
            if "node" in phase:
                node = phase["node"]
                lines.append(f"  Node {node}: {NODES[node]['role']} ({NODES[node]['agent']})")
            if "nodes" in phase:
                lines.append(f"  Nodes: {phase['nodes']}")
                for n in phase["nodes"]:
                    lines.append(f"    - Node {n}: {NODES[n]['role']} ({NODES[n]['agent']}) — {NODES[n]['lens']}")
            if phase.get("parallel"):
                lines.append(f"  ⚡ PARALEL")
            if "lenses" in phase:
                lines.append(f"  Lentile: {', '.join(phase['lenses'])}")
            if "zooms_covered" in phase:
                lines.append(f"  Zoom-uri acoperite: {', '.join(phase['zooms_covered'])}")
            if "n_workers" in phase:
                lines.append(f"  Workers: {phase['n_workers']}")
            lines.append(f"  Action: {phase['action']}")
            if phase.get("warning"):
                lines.append(f"  ⚠️  {phase['warning']}")

    if composition["warnings"]:
        lines.append("\n" + "=" * 70)
        lines.append("WARNINGS:")
        lines.append("=" * 70)
        for w in composition["warnings"]:
            lines.append(f"⚠️  {w}")

    lines.append("\n" + "=" * 70)
    lines.append("ZOOM REFERENCE:")
    lines.append("=" * 70)
    for zoom, info in ZOOMS.items():
        lines.append(f"  {zoom:6s} — {info['scope']}: {info['checks']}")

    lines.append("\nLENS REFERENCE:")
    lines.append("-" * 70)
    for lens, info in LENSES.items():
        node_n = info["node"]
        lines.append(f"  {lens:11s} → Node {node_n} ({NODES[node_n]['agent']})")
        lines.append(f"               Acoperă: {', '.join(info['covers'])}")
        lines.append(f"               Întreabă: {info['questions']}")

    lines.append("\n" + "=" * 70)
    lines.append("Detalii: D:\\Cloude Code\\_SETTINGS\\RULES\\enneagram_multi_zoom_protocol.md")
    lines.append("=" * 70)

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Enneagram swarm composer — multi-zoom + multi-lentilă (META-014)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("task", nargs="?", default="", help="Descrierea task-ului (între ghilimele)")
    parser.add_argument("--files", type=int, default=1, help="Număr fișiere implicate (default: 1)")
    parser.add_argument("--json", action="store_true", help="Output JSON în loc de text")
    parser.add_argument("--task-type", default="default",
                        choices=list(PRIORITY_MATRIX.keys()),
                        help="Type-task pentru matricea priorităților zoom (v2.0 #4)")
    parser.add_argument("--critical", action="store_true",
                        help="Activează Dual-Witness + Phase 5 meta-verification (v2.0 #7, v2.1)")
    parser.add_argument("--temporal-check", action="store_true",
                        help="Adaugă TEMPO zoom (drift cross-sesiune) — v2.0 #1")
    parser.add_argument("--file-patterns", nargs="*", default=None,
                        help="Lista de file patterns pentru auto-detectare lentile domeniu (v2.0 #5)")
    parser.add_argument("--task-id", default=None,
                        help="Task ID pentru checkpoint/resume (v2.1 #16). Auto-genereazã UUID dacă lipsește.")
    parser.add_argument("--resume", action="store_true",
                        help="Resume de la ultimul checkpoint pentru task-id (v2.1 #16)")
    parser.add_argument("--project", default="default",
                        help="Project namespace pentru privacy isolation (v2.1 #17)")
    parser.add_argument("--telemetry", action="store_true",
                        help="Log session telemetry (v2.1 #11)")
    parser.add_argument("--self-test", action="store_true",
                        help="Run self-audit on doctrine + implementation (v2.1 #20)")
    parser.add_argument("--budget-tokens", type=int, default=None,
                        help="Override default token budget (v2.0 #8)")
    parser.add_argument("--budget-time-min", type=int, default=None,
                        help="Override default wall-time budget in minutes (v2.0 #8)")

    args = parser.parse_args()

    # v2.1 #20 — Self-test mode
    if args.self_test:
        result = self_test_doctrine()
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    # v2.1 #16 — Resume mode
    task_id = args.task_id or str(uuid.uuid4())[:8]
    if args.resume:
        cp = load_checkpoint(task_id)
        if cp:
            print(f"Resuming task {task_id} from phase {cp['phase']}")
            print(json.dumps(cp, indent=2, ensure_ascii=False))
            return
        else:
            print(f"No checkpoint found for task {task_id}")

    composition = compose_swarm(
        args.task, args.files,
        task_type=args.task_type,
        critical=args.critical,
        temporal_check=args.temporal_check,
        file_patterns=args.file_patterns,
    )
    composition["task_id"] = task_id
    composition["project"] = args.project

    # v2.0 #8 — Budget override
    if args.budget_tokens or args.budget_time_min:
        composition["budget_override"] = {
            "max_tokens": args.budget_tokens or DEFAULT_BUDGET["max_tokens"],
            "max_wall_time_min": args.budget_time_min or DEFAULT_BUDGET["max_wall_time_min"],
        }

    # v2.1 #11 — Telemetry log
    if args.telemetry:
        log_path = log_telemetry({
            "task_id": task_id,
            "task": args.task,
            "files": args.files,
            "task_type": args.task_type,
            "complexity": composition.get("complexity"),
            "critical": args.critical,
            "domain_lenses": [d["lens"] for d in composition.get("domain_lenses_activated", [])],
        })
        composition["telemetry_log"] = log_path

    # v2.1 #17 — Privacy dir setup
    privacy_dir = get_privacy_dir(args.project)
    composition["privacy_dir"] = str(privacy_dir)

    output = format_output(composition, "json" if args.json else "text")
    print(output)


if __name__ == "__main__":
    main()
