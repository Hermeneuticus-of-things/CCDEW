#!/usr/bin/env python3
"""
Hermes ↔ Agent Zero Bridge — Coordonare profundă în CCDEW.

Arhitectură:
  Hermes (creier) ←→ Bridge ←→ Agent Zero (corp)
  
Hermes decide, Agent Zero execută, CCDEW memorează.

Usage:
  from hermes_a0.bridge import HermesA0Bridge
  
  bridge = HermesA0Bridge()
  result = bridge.execute_task("Verifică email-urile și salvează informații importante")
"""

import os, sys, json, time, hashlib
from datetime import datetime

# ── Paths ─────────────────────────────────────────────────────────────────────
CCDEW_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
MEMORY_DIR = os.path.join(CCDEW_ROOT, "_MEMORY")
SEMANTIC_DIR = os.path.join(MEMORY_DIR, "semantic")
IDENTITY_DIR = os.path.join(MEMORY_DIR, "identity")
EPISODIC_DIR = os.path.join(CCDEW_ROOT, ".claude-flow", "sessions")
BRIDGE_STATE = os.path.join(CCDEW_ROOT, ".claude-flow", "data", "hermes-a0-bridge.json")

HERMES_AGENT = os.path.expanduser("~/.hermes/hermes-agent")
A0_URL = os.environ.get("AGENT_ZERO_URL", "http://localhost:5080")

# ── Hermes LLM ───────────────────────────────────────────────────────────────
def call_hermes(messages, max_tokens=1000, temperature=0.1, timeout=30):
    """Call Hermes auxiliary_client for reasoning/analysis."""
    sys.path.insert(0, HERMES_AGENT)
    from agent.auxiliary_client import call_llm
    return call_llm(messages=messages, max_tokens=max_tokens, temperature=temperature, timeout=timeout)


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


class HermesA0Bridge:
    """
    Coordonare Hermes ↔ Agent Zero.
    
    Hermes = creier (decizii, analiză, memorie)
    Agent Zero = corp (execuție, sandbox, tools)
    CCDEW = sistem de memorie (L0-L4)
    """
    
    def __init__(self):
        self.state = self._load_state()
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def _load_state(self):
        try:
            if os.path.exists(BRIDGE_STATE):
                return json.loads(open(BRIDGE_STATE).read())
        except:
            pass
        return {"tasks": [], "executions": 0, "last_sync": None}
    
    def _save_state(self):
        ensure_dir(os.path.dirname(BRIDGE_STATE))
        with open(BRIDGE_STATE, "w") as f:
            json.dump(self.state, f, indent=2)
    
    # ── Step 1: Hermes decide ─────────────────────────────────────────────
    def analyze_task(self, task_description):
        """Hermes analizează task-ul și decide ce trebuie făcut."""
        prompt = f"""Ești Hermes — creierul sistemului CCDEW.
Analizează acest task și returnează DOAR JSON:

{{
  "task_type": "email_analysis" | "web_research" | "code_execution" | "file_operation" | "system_admin" | "data_analysis" | "other",
  "needs_agent_zero": true|false,
  "reasoning": "de ce are nevoie de Agent Zero sau nu",
  "steps": ["pasul 1", "pasul 2", "pasul 3"],
  "priority": "critical" | "high" | "medium" | "low",
  "estimated_time_minutes": 5,
  "memory_layers": ["L4", "L3", "L2"],
  "success_criteria": "cum știm că task-ul e complet"
}}

Task: {task_description}"""

        try:
            result = call_hermes(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800, temperature=0.1, timeout=30
            )
            content = result.choices[0].message.content.strip()
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1]) if len(lines) > 2 else content.strip("` \n")
            return json.loads(content)
        except Exception as e:
            return {
                "task_type": "other",
                "needs_agent_zero": False,
                "reasoning": f"Hermes analysis failed: {e}",
                "steps": [task_description],
                "priority": "medium",
                "estimated_time_minutes": 5,
                "memory_layers": ["L2"],
                "success_criteria": "Task executat"
            }
    
    # ── Step 2: Agent Zero execută ────────────────────────────────────────
    def execute_via_a0(self, task_description, steps=None):
        """Trimite task-ul la Agent Zero pentru execuție în sandbox."""
        # Agent Zero nu are API simplu — folosim Hermes pentru execuție locală
        # În viitor: A0 CLI connector sau API
        
        prompt = """Ești Agent Zero — corpul sistemului. Ai acces la:
- Terminal Linux
- Sistem de fișiere
- Browser
- Python, Node.js, bash
- Instalare pachete

Execută acest task și returnează rezultatul ca JSON:
{{
  "status": "success" | "partial" | "failed",
  "output": "rezultatul execuției",
  "files_created": ["lista fișiere"],
  "errors": ["erori dacă există"],
  "next_action": "ce ar trebui făcut după"
}}

Task: {task}
Pași: {steps}"""

        try:
            steps_text = "\n".join([f"  {i+1}. {s}" for i, s in enumerate(steps or [])])
            result = call_hermes(
                messages=[{"role": "user", "content": prompt.format(task=task_description, steps=steps_text)}],
                max_tokens=2000, temperature=0.1, timeout=60
            )
            content = result.choices[0].message.content.strip()
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1]) if len(lines) > 2 else content.strip("` \n")
            return json.loads(content)
        except Exception as e:
            return {
                "status": "failed",
                "output": f"Execuție eșuată: {e}",
                "files_created": [],
                "errors": [str(e)],
                "next_action": "Verifică manual"
            }
    
    # ── Step 3: Hermes analizează rezultatul ──────────────────────────────
    def analyze_result(self, task_description, execution_result):
        """Hermes analizează rezultatul execuției."""
        prompt = f"""Analizează rezultatul execuției și extrage informații pentru memorie.
Returnează DOAR JSON:

{{
  "summary_ro": "rezumat în română",
  "importance": "critical" | "high" | "medium" | "low",
  "action_items": ["acțiuni care trebuie luate"],
  "memory_entries": [
    {{"layer": "L4|L3|L2", "key": "cheie", "value": "valoare"}}
  ],
  "follow_up_needed": true|false,
  "follow_up_task": "task de follow-up dacă e necesar"
}}

Task original: {task_description}
Rezultat execuție: {json.dumps(execution_result, ensure_ascii=False)[:2000]}"""

        try:
            result = call_hermes(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000, temperature=0.1, timeout=30
            )
            content = result.choices[0].message.content.strip()
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1]) if len(lines) > 2 else content.strip("` \n")
            return json.loads(content)
        except Exception as e:
            return {
                "summary_ro": f"Task: {task_description[:50]}",
                "importance": "medium",
                "action_items": [],
                "memory_entries": [],
                "follow_up_needed": False,
                "follow_up_task": ""
            }
    
    # ── Step 4: CCDEW memorează ───────────────────────────────────────────
    def store_memory(self, memory_entries, task_id):
        """Salvează în straturile de memorie CCDEW."""
        timestamp = int(time.time() * 1000)
        stored = []
        
        for entry in memory_entries:
            layer = entry.get("layer", "L2")
            key = entry.get("key", "")
            value = entry.get("value", "")
            
            if not key or not value:
                continue
            
            if layer == "L4":
                filepath = os.path.join(IDENTITY_DIR, key + ".json")
                if not os.path.exists(filepath):
                    ensure_dir(IDENTITY_DIR)
                    with open(filepath, "w") as f:
                        json.dump({"key": key, "value": value, "createdAt": timestamp, "layer": "L4", "source": "hermes-a0-bridge", "task_id": task_id}, f, indent=2)
                    stored.append({"layer": "L4", "key": key})
            
            elif layer == "L3":
                filepath = os.path.join(SEMANTIC_DIR, key + ".json")
                ensure_dir(SEMANTIC_DIR)
                with open(filepath, "w") as f:
                    json.dump({"key": key, "value": value, "createdAt": timestamp, "expiresAt": timestamp + 30*86400000, "layer": "L3", "source": "hermes-a0-bridge", "task_id": task_id}, f, indent=2)
                stored.append({"layer": "L3", "key": key})
            
            elif layer == "L2":
                filepath = os.path.join(EPISODIC_DIR, f"hermes-a0-{task_id}-{key}.json")
                ensure_dir(EPISODIC_DIR)
                with open(filepath, "w") as f:
                    json.dump({"sessionId": f"hermes-a0-{task_id}-{key}", "summary": value, "createdAt": timestamp, "layer": "L2", "source": "hermes-a0-bridge"}, f, indent=2)
                stored.append({"layer": "L2", "key": key})
        
        return stored
    
    # ── Main: Execute full pipeline ───────────────────────────────────────
    def execute_task(self, task_description):
        """Pipeline complet: Hermes decide → A0 execută → Hermes analizează → CCDEW memorează."""
        task_id = hashlib.md5(f"{task_description}:{time.time()}".encode()).hexdigest()[:8]
        
        print(f"\n🧠 Hermes-A0 Bridge — Task: {task_description[:60]}...")
        print(f"   Task ID: {task_id}")
        
        # Step 1: Hermes decide
        print("   [1/4] Hermes analizează task-ul...", flush=True)
        analysis = self.analyze_task(task_description)
        print(f"   → Type: {analysis.get('task_type')}, Priority: {analysis.get('priority')}")
        print(f"   → Needs A0: {analysis.get('needs_agent_zero')}")
        
        # Step 2: Execute
        print("   [2/4] Execuție...", flush=True)
        execution = self.execute_via_a0(task_description, analysis.get("steps"))
        print(f"   → Status: {execution.get('status')}")
        
        # Step 3: Hermes analizează rezultatul
        print("   [3/4] Hermes analizează rezultatul...", flush=True)
        result_analysis = self.analyze_result(task_description, execution)
        print(f"   → Importance: {result_analysis.get('importance')}")
        print(f"   → Summary: {result_analysis.get('summary_ro', '')[:80]}")
        
        # Step 4: CCDEW memorează
        print("   [4/4] CCDEW memorează...", flush=True)
        stored = self.store_memory(result_analysis.get("memory_entries", []), task_id)
        print(f"   → Stored: {len(stored)} entries")
        
        # Update state
        self.state["tasks"].append({
            "task_id": task_id,
            "description": task_description[:200],
            "analysis": analysis,
            "execution": execution,
            "result": result_analysis,
            "stored": stored,
            "timestamp": datetime.now().isoformat(),
        })
        self.state["executions"] += 1
        self.state["last_sync"] = datetime.now().isoformat()
        self._save_state()
        
        return {
            "task_id": task_id,
            "analysis": analysis,
            "execution": execution,
            "result_analysis": result_analysis,
            "stored": stored,
        }


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Hermes ↔ Agent Zero Bridge")
    parser.add_argument("task", nargs="?", default=None, help="Task description")
    parser.add_argument("--status", action="store_true", help="Show bridge status")
    args = parser.parse_args()
    
    bridge = HermesA0Bridge()
    
    if args.status:
        print(f"Executions: {bridge.state.get('executions', 0)}")
        print(f"Last sync: {bridge.state.get('last_sync', 'never')}")
        for t in bridge.state.get("tasks", [])[-5:]:
            print(f"  [{t['timestamp'][:19]}] {t['description'][:60]} → {t['execution'].get('status', '?')}")
    elif args.task:
        result = bridge.execute_task(args.task)
        print(f"\n✅ Task complete: {result['task_id']}")
    else:
        print("Usage: bridge.py <task> | --status")
