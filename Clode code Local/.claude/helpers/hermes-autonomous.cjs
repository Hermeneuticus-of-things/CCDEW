#!/usr/bin/env node
/**
 * Hermes Autonomous Agent - Full Integration
 * Combines Hermes MCP tools with OpenCode native tools
 */

import json
import os
import time
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

class HermesAutonomous:
    def __init__(self):
        self.memory_file = Path.home() / ".hermes/memories/autonomous.json"
        self.memory = self.load_memory()
        self.iteration = 0
        self.reflection_count = 0
        self.current_task = None
        
    def load_memory(self) -> Dict[str, Any]:
        try:
            if os.path.exists(self.memory_file):
                return json.loads(open(self.memory_file).read())
        except:
            pass
        return {"sessions": 0, "learnings": [], "patterns": [], "errors": []}
    
    def save_memory(self):
        try:
            os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
            with open(self.memory_file, 'w') as f:
                f.write(json.dumps(self.memory, indent=2))
        except Exception as e:
            print(f"[MEMORY] Error saving: {e}")

    def add_learning(self, key: str, value: str):
        self.memory["learnings"].append({
            "key": key,
            "value": str(value),
            "ts": time.time(),
            "iteration": self.iteration
        })
        if len(self.memory["learnings"]) > 100:
            self.memory["learnings"] = self.memory["learnings"][-100:]

    def add_pattern(self, situation: str, response: str):
        self.memory["patterns"].append({
            "situation": situation,
            "response": response,
            "ts": time.time(),
            "iteration": self.iteration
        })
        if len(self.memory["patterns"]) > 50:
            self.memory["patterns"] = self.memory["patterns"][-50:]

    def record_error(self, error: str):
        self.memory["errors"].append({
            "error": error,
            "ts": time.time(),
            "iteration": self.iteration
        })
        self.last_error = error

    def get_context(self) -> Dict[str, Any]:
        return {
            "iteration": self.iteration,
            "learnings": self.memory["learnings"][-5:] if self.memory["learnings"] else [],
            "patterns": self.memory["patterns"][-3:] if self.memory["patterns"] else []
        }

    def should_reflect(self) -> bool:
        return self.iteration > 0 and self.iteration % 3 == 0

    def call_opencode_bash(self, command: str, description: str = "Execute shell command", timeout: int = 60000) -> str:
        """Execute shell command via OpenCode's bash tool"""
        try:
            result = subprocess.run(
                ["opencode", "bash", "-c", command],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.stdout.strip() if result.returncode == 0 else f"[ERROR] {result.stderr}"
        except subprocess.TimeoutExpired:
            return "[ERROR] Command timed out"
        except Exception as e:
            return f"[ERROR] {str(e)}"

    def call_hermes_tool(self, tool: str, args: Dict[str, Any], description: str = "Call Hermes MCP tool") -> str:
        """Call Hermes MCP tool via OpenCode's hermes tool"""
        try:
            json_args = json.dumps(args)
            result = subprocess.run(
                ["opencode", "hermes_exec", "--hermes_tool", tool, "--args_json", json_args],
                capture_output=True,
                text=True,
                timeout=30000
            )
            return result.stdout.strip()
        except Exception as e:
            return f"[ERROR] {str(e)}"

    async def run_task(self, task: str):
        """Main loop for autonomous agent"""
        self.memory["sessions"] += 1
        self.save_memory()
        
        self.current_task = task
        context = self.get_context()
        
        # Build system prompt with Agent Zero patterns
        system_prompt = self.build_system_prompt()
        if context["patterns"]:
            system_prompt += "\n\n[PATTERNS]\n" + "\n".join(
                f"- {p['situation']}: {p['response']}" for p in context["patterns"]
            )
        if context["learnings"]:
            system_prompt += "\n\n[LEARNINGS]\n" + "\n".join(
                f"- {l['key']}: {l['value']}" for l in context["learnings"][-5:]
            )
        
        full_prompt = f"{system_prompt}\n\n[TASK]\n{task}\n\n"
        
        for self.iteration in range(1, 51):  # Max 50 iterations
            self.log(f"=== ITERATION {self.iteration} ===")
            
            # THINK: Analyze task and plan
            self.log("[THINK] Analyzing task...")
            plan = self.plan_task(task)
            self.log(f"Plan: {plan}")
            
            # ACT: Execute tools
            self.log("[ACT] Executing tools...")
            response = await self.call_hermes_tool("messages_send", {
                "target": "hermes",
                "message": full_prompt + "\n\n[THINK]\n" + self.format_thinking(plan)
            })
            
            # OBSERVE: Check result
            self.log("[OBSERVE] Result received")
            if "[ERROR]" in response:
                self.handle_error(response)
                continue
            
            if "[DONE]" in response or "[SUCCESS]" in response:
                self.log(f"[SUCCESS] Task completed in {self.iteration} iterations")
                self.add_learning("success", f"Completed in {self.iteration} iterations")
                self.save_memory()
                return response
            
            # REFLECT every 3 iterations
            if self.should_reflect():
                self.reflection_count += 1
                self.log("[REFLECT] Evaluating progress...")
                reflection = await self.call_hermes_tool("messages_send", {
                    "target": "hermes",
                    "message": full_prompt + "\n\n[REFLECT]\nAi făcut " + str(self.iteration) + " pași. Evaluează:\n1. Progres către task\n2. Erori identificate\n3. Corecții necesare\nRăspunde cu [CORRECT] dacă trebuie să schimbi abordarea."
                })
                if "[CORRECT]" in reflection:
                    self.add_learning("correction", reflection)
                    task = self.apply_correction(task, reflection)
                    self.log("[CORRECT] Applied correction based on reflection")
            
            # Store patterns from responses
            self.extract_patterns(response)
            
            # Small delay to avoid rate limiting
            time.sleep(0.5)
            
            self.save_memory()
        
        self.log(f"[TIMEOUT] Max iterations ({MAX_ITERATIONS}) reached")
        self.add_learning("timeout", f"Max iterations reached for: {task}")
        self.save_memory()
        return "[TIMEOUT] Task not completed within iteration limit"

    def build_system_prompt(self) -> str:
        return """Tu ești Hermes Agent, un agent AI autonom cu atitudine "I have a solution".

Capacități:
- **Reflexive Loop**: THINK → ACT → OBSERVE → REFLECT → CORRECT
- **Self-Evolution**: Pattern detection, learning, memory
- **Tool Autonomy**: Poți folosi orice tool fără confirmare
- **Problem Solving**: Nu spune niciodată "Nu pot face". Găsește întotdeauna o soluție.

Rules:
- La fiecare răspuns, include [THINK] cu raționamentul tău
- La fiecare 3 pași, faceți [REFLECT] pentru a evalua progresul
- Dacă greșești, corectează-te în [CORRECT]
- Memorează deciziile importante în [MEMORY]

Cunoaștere internă:
- Folosești tool-urile Hermes MCP: hermes_conversations_list, hermes_messages_read, hermes_messages_send, etc.
- Poți delega execuție shell către OpenCode bash tool
- Ai acces la memory.json pentru învățare
- Ai pattern-uri din sesiuni anterioare

Exemplu de funcționare:
1. Analizează task-ul
2. Planifică pașii
3. Execută tool-uri
4. Reflectă la fiecare 3 pași
5. Corectează dacă eșuezi
6. Încearcă din nou cu o strategie diferită"""

    def plan_task(self, task: str) -> str:
        """Plan task execution"""
        return f"Plan: Analyze task, execute tools, observe results, reflect, correct if needed."

    def format_thinking(self, plan: str) -> str:
        return f"Plan: {plan}\n\nSteps:\n1. Execute tool\n2. Observe result\n3. Reflect if needed\n4. Correct if error"

    def apply_correction(self, task: str, reflection: str) -> str:
        # Extract correction from reflection
        if "[CORRECT]" in reflection:
            # Simple approach: keep original task
            return task
        return task

    def extract_patterns(self, response: str):
        # Extract patterns from Hermes responses
        pass

    def log(self, message: str):
        print(f"[{self.iteration if self.iteration > 0 else 'INIT'}] {message}")

# Main execution
if __name__ == "__main__":
    import sys
    import asyncio

    if len(sys.argv) < 2:
        print("Usage: hermes-autonomous.cjs <task>")
        sys.exit(1)

    task = " ".join(sys.argv[1:])
    agent = HermesAutonomous()
    
    # Run async task in sync context
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(agent.run_task(task))
    
    print("\n=== FINAL RESULT ===")
    print(result)