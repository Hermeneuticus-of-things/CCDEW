#!/usr/bin/env python3
"""
Zorin Agent — Scheduler v1.0
Task-uri programate pe bus (gen cron, dar integrat).
"""
import os, sys, json, time, threading, requests
from datetime import datetime, timezone, timedelta
from typing import Callable

HOME = os.path.expanduser("~")
BUS_URL = "http://127.0.0.1:8765"
STATE_DIR = os.path.join(HOME, ".local", "state", "zorin-agent", "scheduler")
os.makedirs(STATE_DIR, exist_ok=True)
SCHEDULES_FILE = os.path.join(STATE_DIR, "schedules.json")
HISTORY_FILE = os.path.join(STATE_DIR, "history.json")

class AgentScheduler:
    def __init__(self):
        self.running = False
        self.schedules = []  # {id, name, cron, action, target, enabled, last_run}
        self.history = []

    def _bus(self, method, path, data=None):
        try:
            url = f"{BUS_URL}{path}"
            r = (requests.get if method == "GET" else requests.post)(url, json=data, timeout=3)
            return r.json()
        except: return {}

    def _log(self, event, data=None):
        self._bus("POST", "/message/send", {
            "from": "zorin-agent-scheduler", "to": "*",
            "type": "log", "payload": {"event": event, "data": data or {}}
        })

    def register(self):
        self._bus("POST", "/agent/register", {
            "name": "zorin-agent-scheduler",
            "type": "scheduler",
            "capabilities": ["cron", "scheduled_tasks", "recurring_jobs", "timers"]
        })

    def heartbeat(self):
        while self.running:
            self._bus("POST", "/agent/heartbeat", {"name": "zorin-agent-scheduler"})
            time.sleep(30)

    def add_schedule(self, name, interval_seconds, action, target="zorin-agent-core", params=None):
        sched = {
            "id": f"sched-{int(time.time())}",
            "name": name,
            "interval": interval_seconds,
            "action": action,
            "target": target,
            "params": params or {},
            "enabled": True,
            "created": datetime.now(timezone.utc).isoformat(),
            "last_run": None,
            "next_run": (datetime.now(timezone.utc) + timedelta(seconds=interval_seconds)).isoformat()
        }
        self.schedules.append(sched)
        self._save()
        self._log("schedule_added", {"name": name, "interval": interval_seconds})
        return sched

    def remove_schedule(self, sched_id):
        self.schedules = [s for s in self.schedules if s["id"] != sched_id]
        self._save()

    def _save(self):
        with open(SCHEDULES_FILE, "w") as f:
            json.dump(self.schedules, f, indent=2, ensure_ascii=False)

    def _load(self):
        if os.path.exists(SCHEDULES_FILE):
            try:
                with open(SCHEDULES_FILE) as f:
                    self.schedules = json.load(f)
            except: pass

    def execute_schedule(self, sched):
        now = datetime.now(timezone.utc)
        sched["last_run"] = now.isoformat()
        sched["next_run"] = (now + timedelta(seconds=sched["interval"])).isoformat()

        if sched["action"] == "task":
            self._bus("POST", "/task/create", {
                "title": sched["name"],
                "description": sched.get("params", {}).get("desc", ""),
                "assigned_to": sched["target"],
                "priority": sched.get("params", {}).get("priority", 5)
            })
        elif sched["action"] == "message":
            self._bus("POST", "/message/send", {
                "from": "zorin-agent-scheduler",
                "to": sched["target"],
                "type": "schedule",
                "payload": sched["params"]
            })
        elif sched["action"] == "memory":
            self._bus("POST", "/memory/store", {
                "agent": "zorin-agent-scheduler",
                "namespace": sched.get("params", {}).get("namespace", "scheduled"),
                "key": sched.get("params", {}).get("key", sched["id"]),
                "value": sched.get("params", {}).get("value", sched["name"])
            })

        entry = {"ts": now.isoformat(), "schedule_id": sched["id"], "name": sched["name"], "action": sched["action"]}
        self.history.append(entry)
        self.history = self.history[-500:]
        with open(HISTORY_FILE, "w") as f:
            json.dump(self.history[-100:], f, indent=2)
        self._save()

    def schedule_loop(self):
        while self.running:
            now = datetime.now(timezone.utc)
            for s in self.schedules:
                if not s["enabled"]:
                    continue
                try:
                    next_run = datetime.fromisoformat(s["next_run"])
                    if now >= next_run:
                        self.execute_schedule(s)
                except: pass
            time.sleep(5)

    def run(self):
        self.running = True
        self._load()
        self.register()
        threading.Thread(target=self.heartbeat, daemon=True).start()
        threading.Thread(target=self.schedule_loop, daemon=True).start()
        self._log("scheduler_ready", {"schedules": len(self.schedules)})
        print(json.dumps({"event": "zorin_scheduler_ready", "schedules": len(self.schedules)}))
        while self.running: time.sleep(1)

    def stop(self): self.running = False

if __name__ == "__main__":
    agent = AgentScheduler()
    try:
        if "--add" in sys.argv:
            idx = sys.argv.index("--add")
            name = sys.argv[idx+1]
            interval = int(sys.argv[idx+2])
            action = sys.argv[idx+3] if len(sys.argv) > idx+3 else "task"
            s = agent.add_schedule(name, interval, action)
            print(json.dumps(s))
        elif "--list" in sys.argv:
            print(json.dumps(agent.schedules, indent=2))
        elif "--remove" in sys.argv:
            sid = sys.argv[sys.argv.index("--remove")+1]
            agent.remove_schedule(sid)
            print({"removed": sid})
        else:
            agent.run()
    except KeyboardInterrupt:
        agent.stop()
