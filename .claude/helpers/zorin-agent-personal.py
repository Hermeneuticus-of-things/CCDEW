#!/usr/bin/env python3
"""
Zorin Agent — Personal Assistant v1.0
Task-uri zilnice, reminders, calendar, email, notes.
"""
import os, sys, json, time, threading, requests, subprocess
from datetime import datetime, timezone
from pathlib import Path

HOME = os.path.expanduser("~")
BUS_URL = "http://127.0.0.1:8765"
STATE_DIR = os.path.join(HOME, ".local", "state", "zorin-agent", "personal")
os.makedirs(STATE_DIR, exist_ok=True)

REMINDERS_FILE = os.path.join(STATE_DIR, "reminders.json")
NOTES_FILE = os.path.join(STATE_DIR, "notes.json")
AGENDA_FILE = os.path.join(STATE_DIR, "agenda.json")

class AgentPersonal:
    def __init__(self):
        self.running = False
        self.reminders = self._load(REMINDERS_FILE, [])
        self.notes = self._load(NOTES_FILE, [])
        self.agenda = self._load(AGENDA_FILE, {})

    def _load(self, path, default):
        if os.path.exists(path):
            try:
                with open(path) as f: return json.load(f)
            except: pass
        return default

    def _save(self, path, data):
        with open(path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _bus(self, method, path, data=None):
        try:
            url = f"{BUS_URL}{path}"
            if method == "GET":
                r = requests.get(url, timeout=3)
            else:
                r = requests.post(url, json=data, timeout=3)
            return r.json()
        except:
            return {}

    def _log(self, event, data=None):
        self._bus("POST", "/message/send", {
            "from": "zorin-agent-personal",
            "to": "*",
            "type": "log",
            "payload": {"event": event, "data": data or {}}
        })

    def register(self):
        self._bus("POST", "/agent/register", {
            "name": "zorin-agent-personal",
            "type": "personal",
            "capabilities": ["reminders", "notes", "agenda", "email_summary", "daily_tasks"]
        })

    def heartbeat(self):
        while self.running:
            self._bus("POST", "/agent/heartbeat", {"name": "zorin-agent-personal"})
            time.sleep(30)

    def add_reminder(self, title, when, priority=5):
        r = {
            "id": f"rem-{int(time.time())}",
            "title": title,
            "when": when,
            "priority": priority,
            "created": datetime.now(timezone.utc).isoformat(),
            "done": False
        }
        self.reminders.append(r)
        self._save(REMINDERS_FILE, self.reminders)
        self._log("reminder_added", {"title": title, "when": when})
        self._bus("POST", "/memory/store", {
            "agent": "zorin-agent-personal",
            "namespace": "reminders",
            "key": r["id"],
            "value": title
        })
        return r

    def get_reminders(self, pending_only=True):
        if pending_only:
            return [r for r in self.reminders if not r["done"]]
        return self.reminders

    def done_reminder(self, rid):
        for r in self.reminders:
            if r["id"] == rid:
                r["done"] = True
                self._save(REMINDERS_FILE, self.reminders)
                self._log("reminder_done", {"id": rid})
                return True
        return False

    def add_note(self, title, content, tags=None):
        n = {
            "id": f"note-{int(time.time())}",
            "title": title,
            "content": content,
            "tags": tags or [],
            "created": datetime.now(timezone.utc).isoformat()
        }
        self.notes.append(n)
        self._save(NOTES_FILE, self.notes)
        self._log("note_added", {"title": title})
        return n

    def search_notes(self, query):
        q = query.lower()
        return [n for n in self.notes if q in n["title"].lower() or q in n["content"].lower()]

    def daily_agenda(self):
        today = datetime.now().strftime("%Y-%m-%d")
        pending = self.get_reminders()
        return {
            "date": today,
            "reminders": pending[:10],
            "notes_count": len(self.notes),
            "total_reminders": len(pending)
        }

    def check_reminders_loop(self):
        while self.running:
            now = datetime.now()
            for r in self.reminders:
                if r["done"]:
                    continue
                try:
                    rtime = datetime.fromisoformat(r["when"])
                    if rtime <= now and (now - rtime).seconds < 60:
                        self._bus("POST", "/task/create", {
                            "title": f"⏰ Reminder: {r['title']}",
                            "description": f"Reminder activ: {r['title']}",
                            "assigned_to": "zorin-agent-core",
                            "priority": r["priority"]
                        })
                        r["done"] = True
                        self._save(REMINDERS_FILE, self.reminders)
                except:
                    pass
            time.sleep(30)

    def run(self):
        self.running = True
        self.register()
        threading.Thread(target=self.heartbeat, daemon=True).start()
        threading.Thread(target=self.check_reminders_loop, daemon=True).start()
        self._log("personal_agent_ready", {"reminders": len(self.reminders), "notes": len(self.notes)})
        print(json.dumps({"event": "zorin_personal_ready"}))
        while self.running:
            time.sleep(1)

    def stop(self):
        self.running = False


if __name__ == "__main__":
    agent = AgentPersonal()
    try:
        if "--add-reminder" in sys.argv:
            idx = sys.argv.index("--add-reminder")
            title = sys.argv[idx+1]
            when = sys.argv[idx+2] if len(sys.argv) > idx+2 else datetime.now().isoformat()
            r = agent.add_reminder(title, when)
            print(json.dumps(r))
        elif "--list" in sys.argv:
            print(json.dumps(agent.get_reminders(), indent=2))
        elif "--add-note" in sys.argv:
            idx = sys.argv.index("--add-note")
            title = sys.argv[idx+1]
            content = sys.argv[idx+2] if len(sys.argv) > idx+2 else ""
            n = agent.add_note(title, content)
            print(json.dumps(n))
        elif "--agenda" in sys.argv:
            print(json.dumps(agent.daily_agenda(), indent=2))
        else:
            agent.run()
    except KeyboardInterrupt:
        agent.stop()
