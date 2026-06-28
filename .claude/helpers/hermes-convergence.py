#!/usr/bin/env python3
"""
Hermes Convergence Engine — Bucla Meta de Convergenta
=====================================================

Masoara daca buclele de invatare CCDEW converg spre 10/1 pe toate axele.

Metrici:
  - Weight stability: cat de stabil e weight_adj per nod in ultimele N episoade
  - Handoff decay: rata de handoff scade in timp?
  - Prompt effectiveness: LLM-ul respecta persona injectata?
  - Composite convergence: 0.0 (zgomot) → 1.0 (convergenta totala)

Output:
  - convergence.json: stare curenta + trend
  - Raport in consola: bara de convergenta per nod

Integrare:
  - pipeline.py: GET /convergence, POST /convergence/record
  - enneagram-core.py: ajusteaza learning_rate pe baza plateau detection
"""

import json, os, sys, time, re
from datetime import datetime, timezone
from collections import deque, defaultdict

# ─── Config ─────────────────────────────────────────────────────────────────
MEMORY_DIR = os.environ.get("HERMES_MEMORY_DIR", os.path.expanduser("~/.hermes/memories"))
CONFIG_DIR = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config/opencode"))
os.makedirs(MEMORY_DIR, exist_ok=True)

EPISODIC_FILE = os.path.join(MEMORY_DIR, "episodic.jsonl")
MIRROR_FILE = os.path.join(MEMORY_DIR, "mirror_inverse.jsonl")
SAFLA_FILE = os.path.join(CONFIG_DIR, "ccdew-safla-state.json")
CONVERGENCE_FILE = os.path.join(MEMORY_DIR, "convergence.json")

NODE_NAMES = {
    1: "Reformer", 2: "Helper", 3: "Achiever", 4: "Individualist",
    5: "Investigator", 6: "Loyalist", 7: "Enthusiast", 8: "Challenger", 9: "Orchestrator"
}

# Cate episoade pastram pentru trend
TREND_WINDOW = 50


# ─── Data Loaders ───────────────────────────────────────────────────────────

def load_jsonl(path):
    if not os.path.exists(path):
        return []
    result = []
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        result.append(json.loads(line))
                    except Exception:
                        pass
    except Exception:
        pass
    return result


def load_safla():
    try:
        with open(SAFLA_FILE) as f:
            return json.load(f)
    except Exception:
        return {"nodes": {}}


# ─── Convergence Metrics ────────────────────────────────────────────────────

class ConvergenceMetrics:
    """Calculeaza toti indicatorii de convergenta."""

    def __init__(self):
        self.episodes = load_jsonl(EPISODIC_FILE)
        self.mirrors = load_jsonl(MIRROR_FILE)
        self.safla = load_safla()
        self._load_history()

    def _load_history(self):
        """Incarca istoricul anterior din convergence.json."""
        if os.path.exists(CONVERGENCE_FILE):
            try:
                with open(CONVERGENCE_FILE) as f:
                    self.history = json.load(f)
            except Exception:
                self.history = {"snapshots": [], "plateau_count": 0}
        else:
            self.history = {"snapshots": [], "plateau_count": 0}

    def _save(self):
        with open(CONVERGENCE_FILE, "w") as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)

    # ── 1. Weight Stability ─────────────────────────────────────────────
    def weight_stability(self) -> dict:
        """Cat de stabil e weight_adj per nod. 1.0 = perfect stabil."""
        nodes = self.safla.get("nodes", {})
        if not nodes:
            return {"score": 0.5, "per_node": {}}

        stabilities = {}
        for nid_str, data in nodes.items():
            w = data.get("weight_adj", 0.1)
            # Stability: how close weight is to its running average
            snapshots = self.history.get("snapshots", [])
            if len(snapshots) >= 3:
                weights = [s.get("nodes", {}).get(nid_str, {}).get("weight", w) for s in snapshots[-10:]]
                if weights:
                    avg = sum(weights) / len(weights)
                    variance = sum((x - avg) ** 2 for x in weights) / len(weights)
                    stability = max(0.0, 1.0 - min(variance * 10, 1.0))
                    stabilities[int(nid_str)] = round(stability, 3)
                else:
                    stabilities[int(nid_str)] = 0.5
            else:
                stabilities[int(nid_str)] = 0.5

        avg_stability = sum(stabilities.values()) / len(stabilities) if stabilities else 0.5
        return {"score": round(avg_stability, 3), "per_node": stabilities}

    # ── 2. Handoff Decay ────────────────────────────────────────────────
    def handoff_decay(self) -> dict:
        """Rata de handoff scade in timp? 1.0 = zero handoff-uri necesare."""
        node_eps = [e for e in self.episodes if e.get("type", "").startswith("node_")]
        recent = node_eps[-TREND_WINDOW:] if len(node_eps) > TREND_WINDOW else node_eps
        older = node_eps[:len(node_eps) - len(recent)] if len(node_eps) > len(recent) else []

        if not recent:
            return {"score": 0.5, "recent_handoff_rate": 0, "older_handoff_rate": 0}

        # Handoff = same task appears with different node_id in sequence
        def count_handoffs(eps):
            handoffs = 0
            seen_tasks = set()
            for e in eps:
                t = e.get("task", "")
                n = e.get("node_id") or e.get("tag", "").replace("node_", "")
                key = f"{t}__{n}"
                if t and key not in seen_tasks:
                    seen_tasks.add(key)
            # handoffs = tasks that appear with multiple nodes
            task_nodes = defaultdict(set)
            for e in eps:
                t = e.get("task", "")
                n = e.get("node_id") or 0
                if t:
                    task_nodes[t].add(n)
            handoffs = sum(1 for nodes in task_nodes.values() if len(nodes) > 1)
            return handoffs / max(len(task_nodes), 1)

        recent_rate = count_handoffs(recent)
        older_rate = count_handoffs(older) if older else recent_rate

        # Decay: if recent_rate < older_rate, handoffs are decreasing (good)
        if older_rate > 0:
            decay = max(0.0, 1.0 - (recent_rate / older_rate))
        else:
            decay = 0.5

        return {
            "score": round(decay, 3),
            "recent_handoff_rate": round(recent_rate, 3),
            "older_handoff_rate": round(older_rate, 3),
        }

    # ── 3. Prompt Effectiveness ──────────────────────────────────────────
    def prompt_effectiveness(self) -> dict:
        """LLM-ul respecta persona injectata? (scor 0-1 pe baza trigramelor cheie per nod)."""
        node_eps = [e for e in self.episodes if e.get("type", "").startswith("node_")]
        if not node_eps:
            return {"score": 0.5, "per_node": {}}

        # Persona keywords per node (from system_prompts)
        persona_keywords = {
            9: ["big picture", "sub-task", "coordinate", "architecture", "overview", "component", "plan"],
            8: ["execute", "now", "simple", "minimal", "done", "action", "direct", "implement"],
            7: ["option", "possibilit", "approach", "creativ", "alternativ", "explor", "generat"],
            6: ["fail", "edge case", "assumpt", "verif", "secur", "risk", "error", "test"],
            5: ["analyz", "investig", "understand", "root cause", "evid", "research", "data", "systematic"],
            4: ["unique", "elegant", "design", "meaningful", "authentic", "reframe", "craft"],
            3: ["efficient", "practical", "actionable", "deliver", "minimal", "lean", "ship"],
            2: ["help", "support", "clear", "explain", "document", "maintain", "guide", "access"],
            1: ["quality", "review", "refactor", "consistency", "standard", "correctness", "improve"],
        }

        scores = {}
        for eps_for_node in range(1, 10):
            node_episodes = [e for e in node_eps if e.get("node_id") == eps_for_node or eps_for_node in e.get("tags", [])]
            if not node_episodes:
                scores[eps_for_node] = 0.5
                continue

            kws = persona_keywords.get(eps_for_node, [])
            if not kws:
                scores[eps_for_node] = 0.5
                continue

            match_count = 0
            total_count = 0
            for e in node_episodes[-20:]:  # last 20 per node
                text = (e.get("task", "") + " " + e.get("solution", "")).lower()
                for kw in kws:
                    if kw in text:
                        match_count += 1
                    total_count += 1

            scores[eps_for_node] = round(match_count / max(total_count, 1), 3)

        avg = sum(scores.values()) / len(scores) if scores else 0.5
        return {"score": round(avg, 3), "per_node": scores}

    # ── 4. Composite Convergence ─────────────────────────────────────────
    def composite(self) -> dict:
        """Scor compozit 0.0-1.0: cat de aproape suntem de 10/1 pe toate axele."""
        ws = self.weight_stability()
        hd = self.handoff_decay()
        pe = self.prompt_effectiveness()

        # Composite: weighted average
        composite = ws["score"] * 0.3 + hd["score"] * 0.3 + pe["score"] * 0.4
        composite = round(min(1.0, max(0.0, composite)), 3)

        # Plateau detection
        snapshots = self.history.get("snapshots", [])
        plateau = False
        if len(snapshots) >= 5:
            recent_scores = [s.get("composite", 0) for s in snapshots[-5:]]
            if max(recent_scores) - min(recent_scores) < 0.05:
                plateau = True
                self.history["plateau_count"] = self.history.get("plateau_count", 0) + 1
            else:
                self.history["plateau_count"] = 0

        return {
            "composite": composite,
            "weight_stability": ws,
            "handoff_decay": hd,
            "prompt_effectiveness": pe,
            "plateau": plateau,
            "plateau_count": self.history.get("plateau_count", 0),
            "trend": "converging" if composite > 0.7 else ("plateau" if plateau else "learning"),
        }

    # ── 5. Per-Node convergence ──────────────────────────────────────────
    def per_node(self) -> dict:
        """Cat de aproape e fiecare nod de 10/1."""
        nodes = self.safla.get("nodes", {})
        if not nodes:
            return {}

        ws_per = self.weight_stability().get("per_node", {})
        pe_per = self.prompt_effectiveness().get("per_node", {})

        result = {}
        for nid_str, data in nodes.items():
            nid = int(nid_str)
            s = data.get("success", 0)
            f = data.get("failure", 0)
            total = s + f
            rate = s / total if total > 0 else 0.5
            stability = ws_per.get(nid, 0.5)
            effectiveness = pe_per.get(nid, 0.5)

            # Distance from 10/1: 1.0 = perfect
            # rate: 0-1, stability: 0-1, effectiveness: 0-1
            convergence = round((rate * 0.4 + stability * 0.3 + effectiveness * 0.3), 3)

            result[nid] = {
                "name": NODE_NAMES.get(nid, f"Node {nid}"),
                "rate": round(rate, 3),
                "stability": stability,
                "effectiveness": effectiveness,
                "convergence": convergence,
                "weight": data.get("weight_adj", 0.1),
                "total_episodes": total,
            }

        return result

    # ── Snapshot & Save ───────────────────────────────────────────────────
    def snapshot(self) -> dict:
        """Salveaza un snapshot de convergenta."""
        comp = self.composite()
        nodes = self.per_node()

        snap = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "composite": comp["composite"],
            "trend": comp["trend"],
            "plateau": comp["plateau"],
            "nodes": {str(nid): n["convergence"] for nid, n in nodes.items()},
        }

        self.history.setdefault("snapshots", []).append(snap)
        # Keep last 100 snapshots
        if len(self.history["snapshots"]) > 100:
            self.history["snapshots"] = self.history["snapshots"][-100:]
        self._save()

        return {
            "composite": comp,
            "per_node": nodes,
            "history": {
                "snapshots": len(self.history["snapshots"]),
                "plateau_count": self.history.get("plateau_count", 0),
                "last_10_composite": [s["composite"] for s in self.history["snapshots"][-10:]],
            }
        }

    # ── Suggest learning rate adjustment ────────────────────────────────
    def suggest_lr(self) -> dict:
        """Sugereaza ajustare de learning rate pe baza convergentei."""
        comp = self.composite()
        composite = comp["composite"]
        plateau = comp["plateau"]
        plateau_count = comp["plateau_count"]

        if plateau and plateau_count >= 3:
            lr_adjust = "decrease"  # stuck, reduce learning rate
            reason = "plateau detected for 3+ snapshots"
            new_lr = 0.3  # slower learning to fine-tune
        elif composite > 0.8:
            lr_adjust = "maintain"  # nearly converged
            reason = f"composite={composite} > 0.8"
            new_lr = 0.5
        elif composite < 0.3:
            lr_adjust = "increase"  # still learning a lot
            reason = f"composite={composite} < 0.3"
            new_lr = 1.0
        else:
            lr_adjust = "maintain"
            reason = f"composite={composite} in normal range"
            new_lr = 0.7

        return {"adjustment": lr_adjust, "reason": reason, "suggested_lr": new_lr, "composite": composite}

    # ── Dashboard ────────────────────────────────────────────────────────
    def dashboard(self) -> str:
        """Raport ASCII complet."""
        comp = self.composite()
        nodes = self.per_node()
        lr = self.suggest_lr()

        lines = []
        lines.append("=" * 58)
        lines.append("  HERMES CONVERGENCE DASHBOARD")
        lines.append("=" * 58)
        lines.append("")

        # Composite bar
        c = comp["composite"]
        bar = "█" * int(c * 30) + "░" * (30 - int(c * 30))
        lines.append(f"  Composite: {c:.1%} {bar}")
        lines.append(f"  Trend: {comp['trend']}")
        lines.append(f"  LR adjust: {lr['adjustment']} ({lr['reason']})")
        lines.append("")

        # Sub-scores
        ws = comp["weight_stability"]["score"]
        hd = comp["handoff_decay"]["score"]
        pe = comp["prompt_effectiveness"]["score"]
        lines.append(f"  Weight stability:     {ws:.1%}")
        lines.append(f"  Handoff decay:        {hd:.1%}")
        lines.append(f"  Prompt effectiveness: {pe:.1%}")
        lines.append("")

        # Per-node bars
        lines.append("  " + "-" * 40)
        lines.append(f"  {'Node':8s} {'Conv':6s} {'Rate':6s} {'Stab':6s} {'Eff':6s}  Bar")
        lines.append("  " + "-" * 40)
        for nid in sorted(nodes.keys()):
            n = nodes[nid]
            bar = "█" * int(n["convergence"] * 20) + "░" * (20 - int(n["convergence"] * 20))
            lines.append(f"  {n['name']:10s} {n['convergence']:.1%} {n['rate']:.1%} {n['stability']:.1%} {n['effectiveness']:.1%}  {bar}")

        lines.append("")
        lines.append(f"  Snapshot #{len(self.history.get('snapshots', []))}")
        lines.append("=" * 58)

        return "\n".join(lines)


# ─── CLI ────────────────────────────────────────────────────────────────────

def cli():
    cm = ConvergenceMetrics()

    if len(sys.argv) < 2:
        print(cm.dashboard())
        return

    cmd = sys.argv[1]
    if cmd == "snapshot":
        result = cm.snapshot()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif cmd == "json":
        result = cm.snapshot()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif cmd == "dashboard":
        print(cm.dashboard())
    elif cmd == "lr":
        print(json.dumps(cm.suggest_lr(), indent=2))
    else:
        print(cm.dashboard())


if __name__ == "__main__":
    cli()
