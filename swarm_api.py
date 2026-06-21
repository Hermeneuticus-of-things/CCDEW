#!/usr/bin/env python3
"""Swarm Agents API — swarm orchestration cu 10 agenți"""
import json, os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

PORT = 9199

AGENTS = {
    "reviewer": {
        "name": "Reviewer",
        "node": 1,
        "role": "Code Review / Quality Gate",
        "wrappers": ["reviewer:gate", "reviewer:audit"],
        "capabilities": ["code review", "quality check", "security audit"],
        "description": "Verifică calitatea codului, securitatea și best practices.",
    },
    "inbox-triage": {
        "name": "Inbox Triage",
        "node": 2,
        "role": "Email / Support Triage",
        "wrappers": ["inbox:triage", "inbox:sort"],
        "capabilities": ["email sorting", "priority assessment", "support routing"],
        "description": "Triază inbox-ul, prioritizează și rutează task-uri.",
    },
    "builder": {
        "name": "Builder",
        "node": 3,
        "role": "Implementation / Build",
        "wrappers": ["builder:task", "builder:build"],
        "capabilities": ["code implementation", "build automation", "feature development"],
        "description": "Implementează cod, construiește feature-uri și automatizări.",
    },
    "strategist": {
        "name": "Strategist",
        "node": 4,
        "role": "Strategy / Planning",
        "wrappers": ["strategist:review", "strategist:plan"],
        "capabilities": ["strategic planning", "roadmap", "architecture decisions"],
        "description": "Planifică strategii, roadmap-uri și decizii arhitecturale.",
    },
    "researcher": {
        "name": "Researcher",
        "node": 5,
        "role": "Deep Research / Analysis",
        "wrappers": ["researcher:quick", "researcher:deep"],
        "capabilities": ["deep research", "data analysis", "investigation"],
        "description": "Cercetare profundă, analiză de date și investigații.",
    },
    "ops-watch": {
        "name": "Ops Watch",
        "node": 6,
        "role": "Monitoring / Security",
        "wrappers": ["ops:health", "ops:monitor"],
        "capabilities": ["system monitoring", "security scanning", "health checks"],
        "description": "Monitorizează sisteme, securitate și sănătatea serviciilor.",
    },
    "qa": {
        "name": "QA",
        "node": 6,
        "role": "Testing / Validation",
        "wrappers": ["qa:smoke", "qa:regression"],
        "capabilities": ["testing", "validation", "regression testing"],
        "description": "Testează, validează și verifică regresii.",
    },
    "km-agent": {
        "name": "Knowledge Manager",
        "node": 7,
        "role": "Knowledge Management",
        "wrappers": ["km:health", "km:sync"],
        "capabilities": ["knowledge management", "documentation", "memory consolidation"],
        "description": "Gestionează cunoștințele, documentația și memoria.",
    },
    "maintainer": {
        "name": "Maintainer",
        "node": 8,
        "role": "Maintenance / Decisive Actions",
        "wrappers": ["maintainer:check", "maintainer:fix"],
        "capabilities": ["maintenance", "bug fixes", "decisive actions"],
        "description": "Mentenanță, reparații și acțiuni decisive.",
    },
    "orchestrator": {
        "name": "Orchestrator",
        "node": 9,
        "role": "Mission Orchestration / Dispatch",
        "wrappers": ["orchestrator:plan", "orchestrator:dispatch"],
        "capabilities": ["orchestration", "dispatch", "coordination"],
        "description": "Orchestrează misiuni, dispecerizează și coordonează.",
    },
}

WORKFLOWS = {
    "hexad": {"agents": ["reviewer", "researcher", "inbox-triage", "maintainer", "ops-watch", "km-agent"], "nodes": [1, 5, 2, 8, 6, 7]},
    "triangle": {"agents": ["builder", "qa", "orchestrator"], "nodes": [3, 6, 9]},
    "support": {"agents": ["inbox-triage", "maintainer"], "nodes": [2, 8]},
    "research": {"agents": ["researcher", "km-agent"], "nodes": [5, 7]},
    "review": {"agents": ["reviewer", "qa"], "nodes": [1, 6]},
}

class SwarmAPI(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    
    def _json(self, data, code=200):
        b = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)
    
    def _body(self):
        n = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(n)) if n else {}
    
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    
    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/swarm/health":
            self._json({"status": "ok", "port": PORT})
        elif path == "/swarm/agents":
            self._json(AGENTS)
        elif path == "/swarm/workflows":
            self._json(WORKFLOWS)
        else:
            self._json({"error": "not found"}, 404)
    
    def do_POST(self):
        path = urlparse(self.path).path
        data = self._body()
        
        if path == "/swarm/spawn":
            workflow = data.get("workflow", "triangle")
            task = data.get("task", "")
            if workflow not in WORKFLOWS:
                self._json({"error": f"unknown workflow: {workflow}"}, 400)
                return
            wf = WORKFLOWS[workflow]
            self._json({
                "workflow": workflow,
                "chain": wf["agents"],
                "nodes": wf["nodes"],
                "agent_count": len(wf["agents"]),
                "task": task[:100],
                "swarm_init": f"Swarm chain: {' → '.join(wf['agents'])}",
            })
        
        elif path == "/swarm/assign":
            node = data.get("node")
            task = data.get("task", "")
            for aid, agent in AGENTS.items():
                if agent["node"] == node:
                    self._json({"agent": aid, "name": agent["name"], "role": agent["role"], "task": task[:100]})
                    return
            self._json({"error": f"no agent for node {node}"}, 404)
        
        else:
            self._json({"error": "not found"}, 404)

if __name__ == "__main__":
    print(f"[SwarmAPI] Starting on :{PORT}")
    print(f"  Agents: GET http://0.0.0.0:{PORT}/swarm/agents")
    print(f"  Spawn:  POST http://0.0.0.0:{PORT}/swarm/spawn")
    HTTPServer(("0.0.0.0", PORT), SwarmAPI).serve_forever()
