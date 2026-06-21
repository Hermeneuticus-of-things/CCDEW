#!/usr/bin/env python3
"""
Zorin Agent — Shared Memory Bus v1.0
Bus central între toți agenții Zorin Agent.
Memorie comună, task-uri, mesaje, evenimente.
"""
import os, sys, json, time, threading, http.server, socketserver, queue, subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, parse_qs

HOME = os.path.expanduser("~")
MEMORY_DIR = os.path.join(HOME, ".hermes", "memories")
STATE_DIR = os.path.join(HOME, ".local", "state", "sgenic")
BUS_PORT = 8765
DASHBOARD_PORT = 8766

os.makedirs(STATE_DIR, exist_ok=True)
os.makedirs(MEMORY_DIR, exist_ok=True)

AGENTS_DB = os.path.join(STATE_DIR, "agents.json")
TASKS_DB = os.path.join(STATE_DIR, "tasks.json")
MEMORY_BUS = os.path.join(STATE_DIR, "memory_bus.jsonl")
EVENTS_LOG = os.path.join(STATE_DIR, "events.jsonl")

agents = {}
tasks = {}
msg_queue = queue.Queue()

class ZorinAgentBus:
    def __init__(self):
        self.agents = self._load_json(AGENTS_DB, {})
        self.tasks = self._load_json(TASKS_DB, {"pending": [], "active": [], "done": []})

    def _load_json(self, path, default):
        if os.path.exists(path):
            try:
                with open(path) as f: return json.load(f)
            except: pass
        return default

    def _save_json(self, path, data):
        with open(path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def register_agent(self, name, agent_type, capabilities):
        self.agents[name] = {
            "name": name,
            "type": agent_type,
            "capabilities": capabilities,
            "last_seen": datetime.now(timezone.utc).isoformat(),
            "status": "active"
        }
        self._save_json(AGENTS_DB, self.agents)
        self._log_event("agent_registered", {"name": name, "type": agent_type})
        return {"status": "ok", "agent": name}

    def agents_list(self):
        return list(self.agents.values())

    def post_message(self, sender, target, msg_type, payload):
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "from": sender,
            "to": target,
            "type": msg_type,
            "payload": payload
        }
        with open(MEMORY_BUS, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        msg_queue.put(entry)
        self._log_event("message", {"from": sender, "to": target, "type": msg_type})
        return {"status": "ok", "id": entry["ts"]}

    def get_messages(self, target=None, limit=50):
        if not os.path.exists(MEMORY_BUS):
            return []
        msgs = []
        with open(MEMORY_BUS) as f:
            for line in f:
                line = line.strip()
                if line:
                    msgs.append(json.loads(line))
        if target:
            msgs = [m for m in msgs if m["to"] == target or m["to"] == "*"]
        return msgs[-limit:]

    def create_task(self, title, description, assigned_to=None, priority=5):
        task = {
            "id": f"task-{int(time.time())}",
            "title": title,
            "description": description,
            "assigned_to": assigned_to,
            "priority": priority,
            "status": "pending",
            "created": datetime.now(timezone.utc).isoformat(),
            "completed": None,
            "result": None
        }
        self.tasks["pending"].append(task)
        self.tasks["pending"].sort(key=lambda t: -t["priority"])
        self._save_json(TASKS_DB, self.tasks)
        self._log_event("task_created", {"id": task["id"], "title": title})
        return task

    def update_task(self, task_id, status, result=None):
        for pool in ["pending", "active", "done"]:
            for t in self.tasks[pool]:
                if t["id"] == task_id:
                    t["status"] = status
                    if status == "in_progress":
                        self.tasks["active"].append(self.tasks[pool].pop(self.tasks[pool].index(t)))
                    elif status in ["done", "failed"]:
                        t["completed"] = datetime.now(timezone.utc).isoformat()
                        t["result"] = result
                        if pool != "done":
                            self.tasks["done"].append(self.tasks[pool].pop(self.tasks[pool].index(t)))
                    self._save_json(TASKS_DB, self.tasks)
                    self._log_event("task_updated", {"id": task_id, "status": status})
                    return {"status": "ok"}
        return {"status": "error", "msg": "task not found"}

    def get_tasks(self, status=None):
        if status:
            return self.tasks.get(status, [])
        return self.tasks

    def store_memory(self, agent_name, namespace, key, value):
        mem_file = os.path.join(MEMORY_DIR, f"sgenic_{namespace}.json")
        mem = {}
        if os.path.exists(mem_file):
            try:
                with open(mem_file) as f: mem = json.load(f)
            except: pass
        mem[key] = {"value": value, "ts": datetime.now(timezone.utc).isoformat(), "agent": agent_name}
        with open(mem_file, "w") as f:
            json.dump(mem, f, indent=2, ensure_ascii=False)
        self._log_event("memory_stored", {"namespace": namespace, "key": key})
        return {"status": "ok"}

    def read_memory(self, namespace, key=None):
        mem_file = os.path.join(MEMORY_DIR, f"sgenic_{namespace}.json")
        if not os.path.exists(mem_file):
            return {}
        with open(mem_file) as f:
            mem = json.load(f)
        if key:
            return mem.get(key, {})
        return mem

    def search_memory(self, namespace, query):
        mem_file = os.path.join(MEMORY_DIR, f"sgenic_{namespace}.json")
        if not os.path.exists(mem_file):
            return []
        with open(mem_file) as f:
            mem = json.load(f)
        results = []
        q = query.lower()
        for k, v in mem.items():
            if q in k.lower() or q in str(v.get("value", "")).lower():
                results.append({"key": k, **v})
        return results

    def _log_event(self, event_type, data):
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "type": event_type,
            "data": data
        }
        with open(EVENTS_LOG, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        if event_type in ("task_created", "task_updated", "agent_registered", "message"):
            try:
                hook = os.path.join(HOME, "CCDEW", ".claude", "helpers", "zorin-memory-hook.py")
                subprocess.Popen(
                    [sys.executable, hook, event_type, json.dumps(data, ensure_ascii=False)],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
            except:
                pass

    def get_events(self, limit=100):
        if not os.path.exists(EVENTS_LOG):
            return []
        events = []
        with open(EVENTS_LOG) as f:
            for line in f:
                line = line.strip()
                if line:
                    events.append(json.loads(line))
        return events[-limit:]

    def get_status(self):
        return {
            "agents": len(self.agents),
            "pending_tasks": len(self.tasks["pending"]),
            "active_tasks": len(self.tasks["active"]),
            "done_tasks": len(self.tasks["done"]),
            "memory_dir": MEMORY_DIR,
            "bus_port": BUS_PORT,
            "dashboard_port": DASHBOARD_PORT
        }


bus = ZorinAgentBus()


class BusHTTPHandler(http.server.BaseHTTPRequestHandler):
    def _json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length)) if length else {}

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        if path == "/status":
            self._json(bus.get_status())
        elif path == "/agents":
            self._json(bus.agents_list())
        elif path == "/tasks":
            self._json(bus.get_tasks(qs.get("status", [None])[0]))
        elif path == "/messages":
            target = qs.get("target", [None])[0]
            limit = int(qs.get("limit", [50])[0])
            self._json(bus.get_messages(target, limit))
        elif path == "/memory":
            ns = qs.get("namespace", ["default"])[0]
            key = qs.get("key", [None])[0]
            self._json(bus.read_memory(ns, key))
        elif path == "/events":
            limit = int(qs.get("limit", [100])[0])
            self._json(bus.get_events(limit))
        elif path == "/search":
            ns = qs.get("namespace", ["default"])[0]
            query = qs.get("query", [""])[0]
            self._json(bus.search_memory(ns, query))
        else:
            self._json({"error": "unknown path"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        body = self._read_body()

        if path == "/agent/register":
            self._json(bus.register_agent(
                body.get("name"), body.get("type"), body.get("capabilities", [])
            ))
        elif path == "/agent/heartbeat":
            name = body.get("name")
            if name and name in bus.agents:
                bus.agents[name]["last_seen"] = datetime.now(timezone.utc).isoformat()
                bus._save_json(AGENTS_DB, bus.agents)
                self._json({"status": "ok"})
            else:
                self._json({"status": "error", "msg": "agent not found"}, 404)
        elif path == "/message/send":
            self._json(bus.post_message(
                body.get("from"), body.get("to"),
                body.get("type"), body.get("payload")
            ))
        elif path == "/task/create":
            self._json(bus.create_task(
                body.get("title"), body.get("description"),
                body.get("assigned_to"), body.get("priority", 5)
            ))
        elif path == "/task/update":
            self._json(bus.update_task(
                body.get("id"), body.get("status"), body.get("result")
            ))
        elif path == "/memory/store":
            self._json(bus.store_memory(
                body.get("agent"), body.get("namespace"),
                body.get("key"), body.get("value")
            ))
        else:
            self._json({"error": "unknown path"}, 404)

    def log_message(self, format, *args):
        pass


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

def run_bus_server():
    server = ReusableTCPServer(("127.0.0.1", BUS_PORT), BusHTTPHandler)
    print(json.dumps({"event": "zorin_bus_started", "port": BUS_PORT}))
    server.serve_forever()


DASHBOARD_HTML = r'''<!DOCTYPE html>
<html lang="ro">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Zorin Agent — Dashboard</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Segoe UI', system-ui, sans-serif; background: #0f172a; color: #e2e8f0; line-height: 1.6; }
  .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
  header { text-align: center; padding: 30px 0; border-bottom: 2px solid #22d3ee; margin-bottom: 30px; }
  header h1 { font-size: 2.5rem; background: linear-gradient(90deg, #22d3ee, #a78bfa, #f472b6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
  header p { color: #94a3b8; margin-top: 10px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-bottom: 30px; }
  .card { background: #1e293b; border-radius: 12px; padding: 20px; border: 1px solid #334155; transition: transform 0.2s; }
  .card:hover { transform: translateY(-2px); border-color: #22d3ee; }
  .card h3 { font-size: 0.875rem; text-transform: uppercase; letter-spacing: 0.05em; color: #94a3b8; margin-bottom: 10px; }
  .card .value { font-size: 2.5rem; font-weight: 700; }
  .card .sub { font-size: 0.875rem; color: #64748b; margin-top: 5px; }
  .cyan { color: #22d3ee; } .purple { color: #a78bfa; } .pink { color: #f472b6; } .green { color: #34d399; } .orange { color: #fb923c; }
  table { width: 100%; border-collapse: collapse; margin-top: 10px; }
  th, td { padding: 10px; text-align: left; border-bottom: 1px solid #334155; font-size: 0.875rem; }
  th { color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 0.75rem; font-weight: 600; }
  .badge-active { background: #065f46; color: #6ee7b7; }
  .badge-pending { background: #78350f; color: #fcd34d; }
  .badge-done { background: #1e3a5f; color: #93c5fd; }
  #refresh-btn { background: #22d3ee; color: #0f172a; border: none; padding: 8px 20px; border-radius: 8px; font-weight: 600; cursor: pointer; margin-bottom: 20px; }
  #refresh-btn:hover { background: #06b6d4; }
  .task-card { background: #1e293b; border-radius: 8px; padding: 15px; margin-bottom: 10px; border-left: 4px solid #22d3ee; }
  .task-card.done { border-left-color: #34d399; }
  .task-card.failed { border-left-color: #f87171; }
  .task-title { font-weight: 600; }
  .task-meta { font-size: 0.75rem; color: #64748b; margin-top: 5px; }
  .msg-bubble { background: #1e293b; border-radius: 8px; padding: 10px 15px; margin-bottom: 8px; }
  .msg-from { font-weight: 600; color: #22d3ee; font-size: 0.8rem; }
  .msg-to { color: #64748b; font-size: 0.75rem; }
  .msg-body { margin-top: 5px; }
  footer { text-align: center; padding: 30px; color: #475569; font-size: 0.8rem; }
</style>
</head>
<body>
<div class="container">
  <header>
    <h1>✦ Zorin Agent</h1>
    <p>Synergic Agentic Operating System — Zorin OS 18.1</p>
  </header>
  <button id="refresh-btn" onclick="loadAll()">⟳ Refresh</button>
  <div id="stats" class="grid"></div>
  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
    <div>
      <h2 style="margin-bottom: 15px; color: #22d3ee;">🧠 Task-uri Active</h2>
      <div id="tasks"></div>
    </div>
    <div>
      <h2 style="margin-bottom: 15px; color: #a78bfa;">📨 Mesaje Recente</h2>
      <div id="messages"></div>
    </div>
  </div>
  <div style="margin-top: 30px;">
    <h2 style="margin-bottom: 15px; color: #f472b6;">🤖 Agenți</h2>
    <div id="agents"></div>
  </div>
  <footer>Zorin Agent v1.0 — Shared Memory Bus</footer>
</div>
<script>
async function api(path) {
  const r = await fetch('http://localhost:' + BUS_PORT + path);
  return r.json();
}
async function loadAll() {
  const [status, agents, tasks, msgs, events] = await Promise.all([
    api('/status'), api('/agents'), api('/tasks'),
    api('/messages?limit=10'), api('/events?limit=10')
  ]);
  document.getElementById('stats').innerHTML = `
    <div class="card"><h3>Agenți Activi</h3><div class="value cyan">${status.agents}</div><div class="sub">înregistrați</div></div>
    <div class="card"><h3>Task-uri Active</h3><div class="value purple">${status.active_tasks}</div><div class="sub">${status.pending_tasks} în așteptare</div></div>
    <div class="card"><h3>Task-uri Finalizate</h3><div class="value pink">${status.done_tasks}</div><div class="sub">total completate</div></div>
    <div class="card"><h3>Memorie Partajată</h3><div class="value green">${status.memory_dir}</div><div class="sub">namespace-uri active</div></div>
  `;
  const tdiv = document.getElementById('tasks');
  const alltasks = [...(tasks.pending||[]), ...(tasks.active||[]), ...(tasks.done||[])].slice(-10);
  tdiv.innerHTML = alltasks.length ? alltasks.map(t => `
    <div class="task-card ${t.status}">
      <div class="task-title">${t.title}</div>
      <div class="task-meta">#${t.id} | prioritate ${t.priority} | ${t.status} ${t.assigned_to ? '| asignat: ' + t.assigned_to : ''}</div>
      ${t.description ? '<div style="font-size:0.85rem;color:#94a3b8;margin-top:5px">' + t.description + '</div>' : ''}
    </div>
  `).join('') : '<p style="color:#64748b">Niciun task.</p>';
  const mdiv = document.getElementById('messages');
  mdiv.innerHTML = msgs.length ? msgs.reverse().map(m => `
    <div class="msg-bubble">
      <div class="msg-from">${m.from} → <span class="msg-to">${m.to}</span></div>
      <div class="msg-body">${typeof m.payload === 'object' ? JSON.stringify(m.payload) : m.payload}</div>
      <div class="msg-to">${new Date(m.ts).toLocaleTimeString()}</div>
    </div>
  `).join('') : '<p style="color:#64748b">Niciun mesaj.</p>';
  const adiv = document.getElementById('agents');
  adiv.innerHTML = agents.length ? '<table><tr><th>Nume</th><th>Tip</th><th>Status</th><th>Capabilități</th><th>Văzut</th></tr>' + agents.map(a => `
    <tr>
      <td style="color:#22d3ee">${a.name}</td>
      <td>${a.type}</td>
      <td><span class="badge badge-active">${a.status}</span></td>
      <td>${(a.capabilities||[]).join(', ')}</td>
      <td>${new Date(a.last_seen).toLocaleTimeString()}</td>
    </tr>
  `).join('') + '</table>' : '<p style="color:#64748b">Niciun agent înregistrat.</p>';
}
const BUS_PORT = ${BUS_PORT};
setInterval(loadAll, 5000);
loadAll();
</script>
</body>
</html>'''


class DashboardHTTPHandler(http.server.BaseHTTPRequestHandler):
    def _html(self, content, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))

    def _json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/" or path == "/dashboard":
            self._html(DASHBOARD_HTML)
        else:
            self._json({"error": "unknown"}, 404)

    def log_message(self, format, *args):
        pass


def run_dashboard_server():
    server = ReusableTCPServer(("127.0.0.1", DASHBOARD_PORT), DashboardHTTPHandler)
    print(json.dumps({"event": "sgenic_dashboard_started", "url": f"http://localhost:{DASHBOARD_PORT}"}))
    server.serve_forever()


if __name__ == "__main__":
    import sys
    if "--bus-only" in sys.argv:
        run_bus_server()
    elif "--dashboard-only" in sys.argv:
        run_dashboard_server()
    else:
        threading.Thread(target=run_bus_server, daemon=True).start()
        threading.Thread(target=run_dashboard_server, daemon=True).start()
        print(json.dumps({"event": "zorin_agent_started", "bus": BUS_PORT, "dashboard": DASHBOARD_PORT}))
        try:
            while True: time.sleep(1)
        except KeyboardInterrupt:
            print("Zorin Agent oprit.")
