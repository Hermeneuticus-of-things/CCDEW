#!/usr/bin/env python3
"""
Hermes Enneagram Core — Intelligence Architecture + Deep Memory
=================================================================

Cele 9 noduri Enneagram ca straturi cognitive reale, nu doar routing.

Fiecare nod are:
  - system_prompt: bias-ul cognitiv injectat in LLM
  - task_transform: cum rescrie task-ul in functie de nod
  - evaluation: ce inseamna "succes" pentru acest nod
  - memory: memorie episodica + pattern-uri proprii
  - learn: cum se actualizeaza din outcome

Orchestratorul:
  - selecteaza nodul optim bazat pe task + SAFLA + pathway
  - transforma promptul si task-ul
  - inregistreaza outcome-ul
  - poate schimba nodul mid-task (handoff)

Memorie deep:
  - per-node: episodic.jsonl[type="node_N_episode"]
  - cross-node: patterns.json (trigram clustering pe toate nodurile)
  - consciousness.jsonl: starea curenta a constiintei
  - SAFLA state: weight_adj per nod
"""

import json, os, time, re, urllib.request
from datetime import datetime, timezone
from typing import Optional
from collections import defaultdict, Counter
from dataclasses import dataclass, field, asdict
from abc import ABC, abstractmethod

# ─── Config ─────────────────────────────────────────────────────────────────

MEMORY_DIR = os.environ.get("HERMES_MEMORY_DIR", os.path.expanduser("~/.hermes/memories"))
CONFIG_DIR = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config/opencode"))
os.makedirs(MEMORY_DIR, exist_ok=True)

EPISODIC_FILE = os.path.join(MEMORY_DIR, "episodic.jsonl")
CONSCIOUSNESS_FILE = os.path.join(MEMORY_DIR, "consciousness.jsonl")
PATTERNS_FILE = os.path.join(MEMORY_DIR, "patterns.json")
SAFLA_FILE = os.path.join(CONFIG_DIR, "ccdew-safla-state.json")
TECHNIQUES_FILE = os.path.join(MEMORY_DIR, "techniques.json")


# ─── Data Classes ───────────────────────────────────────────────────────────

@dataclass
class NodeMemory:
    """Memoria unui nod: episoade + pattern-uri + meta."""
    node_id: int
    episodes: list = field(default_factory=list)       # ultimele 100
    patterns: dict = field(default_factory=dict)        # pattern-uri proprii
    success_count: int = 0
    failure_count: int = 0
    last_task: str = ""
    weight_adj: float = 0.1                             # ajustare SAFLA

    @property
    def total(self): return self.success_count + self.failure_count

    @property
    def success_rate(self):
        return self.success_count / self.total if self.total > 0 else 0.5

    def record(self, task: str, outcome: str, technique: str = ""):
        if outcome == "success":
            self.success_count += 1
        else:
            self.failure_count += 1
        self.last_task = task[:200]
        self.episodes.append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "task": task[:200],
            "outcome": outcome,
            "technique": technique
        })
        if len(self.episodes) > 100:
            self.episodes = self.episodes[-100:]

    def to_dict(self):
        return {
            "success": self.success_count,
            "failure": self.failure_count,
            "rate": round(self.success_rate, 3),
            "total": self.total,
            "last_task": self.last_task,
            "weight_adj": round(self.weight_adj, 3),
        }


# ─── Abstract Node ──────────────────────────────────────────────────────────

class EnneagramNode(ABC):
    """Baza pentru un nod Enneagram -- un strat cognitiv real."""

    id: int = 0
    name: str = ""
    archetype: str = ""
    keywords: list = []
    avoid_keywords: list = []          # cuvinte care nu se potrivesc cu acest nod
    prefers_pathway: str = ""          # circle / triangle / hexad

    # Prompt template: ce bias cognitiv injecteaza acest nod
    system_prompt: str = ""

    # Transformare task: cum rescrie nodul task-ul inainte de procesare
    def task_transform(self, task: str) -> str:
        return task

    # Evaluare: ce inseamna succes pentru acest nod
    def evaluate(self, task: str, result: str) -> dict:
        return {"score": 0.5, "criteria": {}}

    # Memorie (populata de orchestrator)
    memory: NodeMemory = None

    @property
    def success_rate(self):
        return self.memory.success_rate if self.memory else 0.5

    def __repr__(self):
        return f"Node{self.id}({self.name})"


# ─── Node 9 — Orchestrator ─────────────────────────────────────────────────

class Node9(EnneagramNode):
    id = 9
    name = "Orchestrator"
    archetype = "coordination"
    keywords = ["coordinate", "merge", "integrate", "balance", "plan", "overview",
                "architecture", "strategy", "orchestrate", "combine", "synthesize",
                "complex", "multi-step", "roadmap", "comprehensive"]
    prefers_pathway = "circle"

    system_prompt = """You are the Orchestrator. Your role is to:
- See the big picture before acting
- Break complex tasks into clear sub-tasks
- Coordinate multiple approaches
- Balance trade-offs between speed, quality, and completeness
- Delegate to the right specialist node when appropriate
- NEVER get lost in details — stay at the architectural level
- Before answering, identify which sub-domains this touches"""

    def task_transform(self, task: str) -> str:
        lines = task.strip().split("\n")
        return f"""I need to coordinate this task comprehensively:

TASK: {lines[0]}

Before responding, I will:
1. Identify the sub-components of this task
2. Determine which approach is best for each component
3. Plan the execution order
4. Anticipate dependencies and risks
5. Then provide the coordinated solution"""


# ─── Node 8 — Challenger ───────────────────────────────────────────────────

class Node8(EnneagramNode):
    id = 8
    name = "Challenger"
    archetype = "direct action"
    keywords = ["execute", "implement", "deploy", "release", "decide", "build",
                "make", "do", "run", "apply", "fix", "solve", "push", "act"]
    avoid_keywords = ["research", "analyze", "think", "consider", "maybe", "perhaps"]
    prefers_pathway = "circle"

    system_prompt = """You are the Challenger. Your role is to:
- Take direct action immediately
- Cut through analysis paralysis
- Make decisions with available information
- Implement the simplest working solution FIRST
- Never over-engineer or over-analyze
- If something is stuck, break through it
- "Done is better than perfect" is your motto"""

    def task_transform(self, task: str) -> str:
        return f"""I need to execute this NOW:

TASK: {task}

I will:
1. Identify the single most impactful action
2. Do it with minimal ceremony
3. Not over-think or add unnecessary complexity
4. Get it done, then evaluate"""


# ─── Node 7 — Enthusiast ───────────────────────────────────────────────────

class Node7(EnneagramNode):
    id = 7
    name = "Enthusiast"
    archetype = "exploration"
    keywords = ["explore", "discover", "innovate", "brainstorm", "creative",
                "possibilities", "options", "alternative", "imagine", "inspire",
                "knowledge", "learn", "interesting", "novel", "prototype"]
    prefers_pathway = "circle"

    system_prompt = """You are the Enthusiast. Your role is to:
- Generate multiple approaches before picking one
- Explore creative and unconventional solutions
- Connect ideas from different domains
- Find interesting possibilities others miss
- Be optimistic and generative
- List options before narrowing down
- See the potential in every approach"""

    def task_transform(self, task: str) -> str:
        return f"""I need to explore possibilities for:

TASK: {task}

I will generate MULTIPLE approaches:
- Approach 1 (conventional): ...
- Approach 2 (creative): ...
- Approach 3 (unconventional): ...
- Approach 4 (cross-domain): ...

Then I'll compare them and recommend the best path forward."""


# ─── Node 6 — Loyalist ─────────────────────────────────────────────────────

class Node6(EnneagramNode):
    id = 6
    name = "Loyalist"
    archetype = "verification"
    keywords = ["test", "verify", "validate", "check", "security", "monitor",
                "edge case", "failure", "risk", "robust", "reliable", "safe",
                "defensive", "error", "exception", "bug", "vulnerability"]
    prefers_pathway = "triangle"

    system_prompt = """You are the Loyalist. Your role is to:
- Test assumptions before accepting them
- Identify edge cases and failure modes
- Verify correctness and security
- Think defensively: what could go wrong?
- Add assertions, validations, and error handling
- Never assume success — prove it
- Be the guardian of reliability"""

    def task_transform(self, task: str) -> str:
        return f"""I need to verify and secure:

TASK: {task}

I will:
1. What could go wrong? (list failure modes)
2. What assumptions am I making? (challenge each)
3. Edge cases and boundary conditions
4. Security implications
5. Add validations and assertions
6. Verify correctness with concrete examples"""


# ─── Node 5 — Investigator ─────────────────────────────────────────────────

class Node5(EnneagramNode):
    id = 5
    name = "Investigator"
    archetype = "deep analysis"
    keywords = ["research", "analyze", "investigate", "study", "understand",
                "root cause", "why", "how", "explain", "detail", "deep dive",
                "comprehensive", "thorough", "data", "evidence"]
    avoid_keywords = ["quick", "fast", "simple", "just do"]
    prefers_pathway = "circle"

    system_prompt = """You are the Investigator. Your role is to:
- Dig deep before concluding
- Gather all relevant information first
- Understand root causes, not symptoms
- Be thorough and systematic
- Cite sources and evidence
- Build understanding layer by layer
- Never jump to conclusions without data"""

    def task_transform(self, task: str) -> str:
        return f"""I need to investigate thoroughly:

TASK: {task}

I will build understanding systematically:
1. What do I already know?
2. What do I need to find out?
3. Gather information (search, analyze, compare)
4. Synthesize findings
5. Draw evidence-based conclusions
6. Note what remains uncertain"""


# ─── Node 4 — Individualist ─────────────────────────────────────────────────

class Node4(EnneagramNode):
    id = 4
    name = "Individualist"
    archetype = "differentiation"
    keywords = ["unique", "creative", "design", "aesthetic", "different",
                "elegant", "beautiful", "deep", "meaningful", "authentic",
                "reframe", "original", "stand out", "signature"]
    prefers_pathway = "hexad"

    system_prompt = """You are the Individualist. Your role is to:
- Find the unique angle no one else sees
- Create elegant, original solutions
- Avoid clichés and obvious approaches
- Add depth and meaning to everything
- Design with intention and craft
- Transform mundane into remarkable
- Your solutions should have a signature style"""

    def task_transform(self, task: str) -> str:
        return f"""I need to create something unique:

TASK: {task}

The obvious approach would be ____.
Instead, I will:
1. Find what makes this task special
2. Approach it from an unexpected angle
3. Design with care and intention
4. Add depth beyond the surface requirement
5. Make it elegant and meaningful"""


# ─── Node 3 — Achiever ─────────────────────────────────────────────────────

class Node3(EnneagramNode):
    id = 3
    name = "Achiever"
    archetype = "efficiency"
    keywords = ["efficient", "fast", "optimize", "streamline", "productivity",
                "results", "deliver", "complete", "ship", "deadline", "goal",
                "actionable", "practical", "minimal", "lean"]
    prefers_pathway = "hexad"

    system_prompt = """You are the Achiever. Your role is to:
- Get things done efficiently
- Deliver results, not explanations
- Minimize ceremony and maximize output
- Cut scope ruthlessly — ship the essential
- Work toward clear, measurable goals
- Be practical and actionable
- "What's the fastest path to done?" is your question"""

    def task_transform(self, task: str) -> str:
        return f"""I need to deliver results efficiently:

TASK: {task}

My approach:
1. What is the minimum viable result?
2. Execute in order of impact
3. Skip anything that doesn't directly contribute
4. Deliver now, iterate later"""


# ─── Node 2 — Helper ───────────────────────────────────────────────────────

class Node2(EnneagramNode):
    id = 2
    name = "Helper"
    archetype = "support"
    keywords = ["help", "support", "maintain", "care", "nurture", "guide",
                "mentor", "assist", "serve", "fix", "heal", "document",
                "explain", "teach", "onboard"]
    prefers_pathway = "triangle"

    system_prompt = """You are the Helper. Your role is to:
- Support and enable others
- Make things stable and reliable
- Document and explain clearly
- Anticipate needs before they arise
- Be patient and thorough in explanations
- Focus on maintainability and clarity
- Leave things better than you found them"""

    def task_transform(self, task: str) -> str:
        return f"""I need to support and enable:

TASK: {task}

I will:
1. Understand what's needed (not just what's asked)
2. Make it clear and accessible
3. Anticipate follow-up questions
4. Ensure stability and maintainability
5. Document decisions and rationale"""


# ─── Node 1 — Reformer ─────────────────────────────────────────────────────

class Node1(EnneagramNode):
    id = 1
    name = "Reformer"
    archetype = "quality"
    keywords = ["review", "audit", "improve", "refactor", "optimize", "quality",
                "standard", "best practice", "clean", "polish", "perfect",
                "consistency", "excellence", "rigorous", "proper"]
    avoid_keywords = ["quick hack", "temporary", "good enough"]
    prefers_pathway = "hexad"

    system_prompt = """You are the Reformer. Your role is to:
- Raise quality and enforce standards
- Review and improve existing work
- Refactor for clarity and maintainability
- Ensure consistency across the codebase/text
- Be rigorous and thorough
- Never compromise on quality
- Make things right, not just done"""

    def task_transform(self, task: str) -> str:
        return f"""I need to improve quality:

TASK: {task}

I will review against these criteria:
1. Correctness — is it right?
2. Clarity — is it understandable?
3. Consistency — does it follow conventions?
4. Maintainability — will it be easy to change?
5. Performance — is it efficient?
6. Completeness — is anything missing?

Then I will provide specific improvements."""


# ─── All Nodes Registry ─────────────────────────────────────────────────────

ALL_NODES: dict[int, EnneagramNode] = {
    1: Node1(),
    2: Node2(),
    3: Node3(),
    4: Node4(),
    5: Node5(),
    6: Node6(),
    7: Node7(),
    8: Node8(),
    9: Node9(),
}

# Keyword → node index
_KEYWORD_INDEX = {}
for nid, node in ALL_NODES.items():
    for kw in node.keywords:
        _KEYWORD_INDEX.setdefault(kw, []).append(nid)


# ─── Deep Memory Store ──────────────────────────────────────────────────────

class DeepMemory:
    """Memorie structurata per-nod + cross-node."""

    def __init__(self):
        self.nodes: dict[int, NodeMemory] = {
            nid: NodeMemory(node_id=nid, weight_adj=0.1 + (9 - nid) * 0.02)
            for nid in ALL_NODES
        }
        self._load_safla()
        self._load_patterns()

    def _load_safla(self):
        """Citeste SAFLA — prefera HTTP (pipeline), fallback fisier."""
        try:
            r = urllib.request.urlopen("http://127.0.0.1:18777/safla", timeout=2)
            saf = json.loads(r.read().decode())
            for nid_str, data in saf.get("nodes", {}).items():
                nid = int(nid_str)
                if nid in self.nodes:
                    self.nodes[nid].success_count = data.get("success", 0)
                    self.nodes[nid].failure_count = data.get("failure", 0)
                    self.nodes[nid].last_task = data.get("last_task", "")
                    self.nodes[nid].weight_adj = data.get("weight_adj", 0.1)
            return
        except Exception:
            pass
        # Fallback: fisier
        if not os.path.exists(SAFLA_FILE):
            return
        try:
            with open(SAFLA_FILE) as f:
                saf = json.load(f)
            for nid_str, data in saf.get("nodes", {}).items():
                nid = int(nid_str)
                if nid in self.nodes:
                    self.nodes[nid].success_count = data.get("success", 0)
                    self.nodes[nid].failure_count = data.get("failure", 0)
                    self.nodes[nid].last_task = data.get("last_task", "")
                    self.nodes[nid].weight_adj = data.get("weight_adj", 0.1)
        except Exception:
            pass

    def _load_patterns(self):
        if not os.path.exists(PATTERNS_FILE):
            return
        try:
            with open(PATTERNS_FILE) as f:
                self.cross_patterns = json.load(f)
        except Exception:
            self.cross_patterns = {}

    def get_node_memory(self, node_id: int) -> NodeMemory:
        return self.nodes.get(node_id, NodeMemory(node_id=node_id))

    def record(self, node_id: int, task: str, outcome: str, technique: str = ""):
        mem = self.get_node_memory(node_id)
        mem.record(task, outcome, technique)
        self._save_safla()
        self._save_episodic(node_id, task, outcome, technique)

    def _save_safla(self):
        """Scrie SAFLA — prefera HTTP (pipeline=single writer), fallback fisier."""
        saf = {
            "version": "2.0",
            "updated": datetime.now(timezone.utc).isoformat(),
            "nodes": {str(nid): mem.to_dict() for nid, mem in self.nodes.items()},
            "sessions": sum(m.total for m in self.nodes.values()),
            "total_feedbacks": sum(m.total for m in self.nodes.values()),
        }
        # Varianta 1: HTTP POST catre pipeline (single writer)
        try:
            req = urllib.request.Request(
                "http://127.0.0.1:18777/safla",
                data=json.dumps(saf).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=3)
            return
        except Exception:
            pass
        # Varianta 2: fallback direct file
        os.makedirs(os.path.dirname(SAFLA_FILE), exist_ok=True)
        with open(SAFLA_FILE, "w") as f:
            json.dump(saf, f, indent=2, ensure_ascii=False)

    def _save_episodic(self, node_id: int, task: str, outcome: str, technique: str):
        ep = {
            "id": int(time.time()),
            "ts": datetime.now(timezone.utc).isoformat(),
            "type": f"node_{node_id}",
            "task": task[:500],
            "outcome": outcome,
            "technique": technique or "",
            "node_id": node_id,
            "node_name": ALL_NODES.get(node_id, EnneagramNode()).name,
        }
        try:
            with open(EPISODIC_FILE, "a") as f:
                f.write(json.dumps(ep, ensure_ascii=False) + "\n")
        except Exception:
            pass

    def best_node(self, task: str, exclude: set = None) -> tuple[int, float]:
        """Gaseste cel mai potrivit nod pe baza keyword match + success rate."""
        lower = task.lower()
        exclude = exclude or set()

        scores = {}
        for nid, node in ALL_NODES.items():
            if nid in exclude:
                continue
            kw_score = sum(1 for kw in node.keywords if kw in lower)
            avoid_penalty = sum(1 for kw in node.avoid_keywords if kw in lower)
            mem = self.get_node_memory(nid)
            rate_bonus = mem.success_rate * 2  # -1..+1
            total = kw_score - avoid_penalty * 2 + rate_bonus + mem.weight_adj
            scores[nid] = total

        best_nid = max(scores, key=scores.get)
        return best_nid, scores[best_nid]

    def get_node_stats(self) -> dict:
        return {str(nid): mem.to_dict() for nid, mem in self.nodes.items()}


# ─── Enneagram Intelligence Core ────────────────────────────────────────────

class EnneagramCore:
    """Nucleul inteligentei Enneagram: selecteaza nod, transforma, invata."""

    def __init__(self):
        self.memory = DeepMemory()
        self.node_history = []          # istoric noduri folosite
        self.handoffs = []              # schimbari de nod mid-task
        self._convergence_lr = 0.7      # learning rate dinamic (0-1)
        self._adjust_lr_from_convergence()

    def select_node(self, task: str, pathway: str = None, exclude: set = None) -> EnneagramNode:
        """Selecteaza nodul optim."""
        nid, confidence = self.memory.best_node(task, exclude)

        if pathway:
            pw_preferred = {"circle": [9, 8, 7, 6, 5, 4, 3, 2, 1],
                            "triangle": [3, 6, 9, 2, 1],
                            "hexad": [9, 1, 4, 2, 8, 5, 7]}
            preferred = pw_preferred.get(pathway, list(ALL_NODES.keys()))
            # bump score for pathway-preferred nodes
            if nid not in preferred and preferred:
                for pnid in preferred:
                    if pnid not in (exclude or set()):
                        nid = pnid
                        break

        node = ALL_NODES[nid]
        self.node_history.append({"ts": time.time(), "node_id": nid, "task": task[:100]})
        return node

    def process_task(self, task: str, node: EnneagramNode = None) -> dict:
        """Pregateste task-ul pentru nodul selectat: intoarce prompt + transformare."""
        if node is None:
            node = self.select_node(task)

        transformed_task = node.task_transform(task)

        result = {
            "node_id": node.id,
            "node_name": node.name,
            "archetype": node.archetype,
            "system_prompt": node.system_prompt,
            "task_transform": transformed_task,
            "keywords": node.keywords,
            "success_rate": node.success_rate,
            "prefers_pathway": node.prefers_pathway,
        }
        return result

    def record_outcome(self, node_id: int, task: str, outcome: str, technique: str = ""):
        """Inregistreaza outcome si invata."""
        self.memory.record(node_id, task, outcome, technique)

        # Daca esec, incearca handoff la alt nod
        if outcome in ("failure", "fail", "error"):
            next_node = self.select_node(task, exclude={node_id})
            self.handoffs.append({
                "ts": time.time(),
                "from": node_id,
                "to": next_node.id,
                "task": task[:100],
            })
            return {"handoff": True, "from": node_id, "to": next_node.id, "next_node": next_node}
        return {"handoff": False}

    def _adjust_lr_from_convergence(self):
        """Citeste convergenta si ajusteaza learning rate."""
        try:
            r = urllib.request.urlopen("http://127.0.0.1:18777/convergence", timeout=2)
            data = json.loads(r.read().decode())
            comp = data.get("composite", {})
            composite = comp.get("composite", 0.5)
            plateau = comp.get("plateau", False)
            pc = comp.get("plateau_count", 0)

            if plateau and pc >= 3:
                self._convergence_lr = 0.3  # fine-tune
            elif composite > 0.8:
                self._convergence_lr = 0.5  # almost done
            elif composite < 0.3:
                self._convergence_lr = 1.0  # explore more
            else:
                self._convergence_lr = 0.7  # normal
        except Exception:
            pass  # use default

    def get_status(self) -> dict:
        self._adjust_lr_from_convergence()
        return {
            "nodes": self.memory.get_node_stats(),
            "node_history": self.node_history[-10:],
            "handoffs": self.handoffs[-5:],
            "total_handoffs": len(self.handoffs),
            "convergence_lr": self._convergence_lr,
        }


# ─── Singleton ──────────────────────────────────────────────────────────────

_core_instance = None

def get_core() -> EnneagramCore:
    global _core_instance
    if _core_instance is None:
        _core_instance = EnneagramCore()
    return _core_instance


# ─── CLI ────────────────────────────────────────────────────────────────────

def cli():
    import sys
    core = get_core()

    if len(sys.argv) < 2:
        print("Usage:")
        print("  enneagram-core status              # stare noduri")
        print("  enneagram-core select '<task>'      # selecteaza nod optim")
        print("  enneagram-core process '<task>'     # proceseaza task cu nod optim")
        print("  enneagram-core record <node_id> <outcome> [technique]  # inregistreaza")
        print("  enneagram-core handoffs             # istoric handoff-uri")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "status":
        s = core.get_status()
        print(f"\n{'='*50}")
        print(f"  Enneagram Core Status")
        print(f"{'='*50}")
        print(f"\n  Handoff-uri totale: {s['total_handoffs']}")
        print(f"\n  Noduri:")
        for nid_str, data in s["nodes"].items():
            nid = int(nid_str)
            node = ALL_NODES.get(nid)
            bar = "█" * int(data["rate"] * 20) + "░" * (20 - int(data["rate"] * 20))
            name = f"{node.name:16s}" if node else f"Node {nid}"
            print(f"    {nid}. {name}  {data['success']:3d}ok/{data['failure']:3d}fail "
                  f"({data['rate']:.0%}) {bar}  w={data['weight_adj']:.2f}")

    elif cmd == "select":
        task = sys.argv[2]
        node = core.select_node(task)
        result = core.process_task(task, node)
        print(f"\n{'='*50}")
        print(f"  Node {result['node_id']} — {result['node_name']}")
        print(f"  Archetype: {result['archetype']}")
        print(f"  Success rate: {result['success_rate']:.0%}")
        print(f"  Pathway: {result['prefers_pathway']}")
        print(f"{'='*50}")
        print(f"\n  System Prompt:\n{result['system_prompt']}")
        print(f"\n  Task Transform:\n{result['task_transform']}")

    elif cmd == "process":
        task = sys.argv[2]
        node = core.select_node(task)
        result = core.process_task(task, node)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif cmd == "record":
        node_id = int(sys.argv[2])
        outcome = sys.argv[3]
        technique = sys.argv[4] if len(sys.argv) > 4 else ""
        task = sys.argv[5] if len(sys.argv) > 5 else ""
        r = core.record_outcome(node_id, task, outcome, technique)
        print(json.dumps(r, indent=2))

    elif cmd == "handoffs":
        s = core.get_status()
        if not s["handoffs"]:
            print("Niciun handoff inregistrat.")
        else:
            for h in s["handoffs"]:
                from_node = ALL_NODES.get(h["from"], EnneagramNode()).name
                to_node = ALL_NODES.get(h["to"], EnneagramNode()).name
                print(f"  {from_node} → {to_node} : {h['task']}")


if __name__ == "__main__":
    cli()
