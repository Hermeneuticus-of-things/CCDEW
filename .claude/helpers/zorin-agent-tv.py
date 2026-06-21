#!/usr/bin/env python3
"""
Zorin Agent — TV v1.0
Monitorizare 176 canale, failover, auto-repair.
"""
import os, sys, json, time, threading, requests, subprocess
from datetime import datetime, timezone
from pathlib import Path

HOME = os.path.expanduser("~")
BUS_URL = "http://127.0.0.1:8765"
HELPERS = os.path.join(HOME, "CCDEW", ".claude", "helpers")
STATE_DIR = os.path.join(HOME, ".local", "state", "zorin-agent", "tv")
os.makedirs(STATE_DIR, exist_ok=True)
CHANNELS_CACHE = os.path.join(STATE_DIR, "channels.json")
STATUS_FILE = os.path.join(STATE_DIR, "status.json")

class AgentTV:
    def __init__(self):
        self.running = False
        self.channels = []
        self.server_url = "http://localhost:8899"

    def _bus(self, method, path, data=None):
        try:
            url = f"{BUS_URL}{path}"
            r = (requests.get if method == "GET" else requests.post)(url, json=data, timeout=3)
            return r.json()
        except: return {}

    def _log(self, event, data=None):
        self._bus("POST", "/message/send", {
            "from": "zorin-agent-tv", "to": "*",
            "type": "log", "payload": {"event": event, "data": data or {}}
        })

    def register(self):
        self._bus("POST", "/agent/register", {
            "name": "zorin-agent-tv",
            "type": "tv",
            "capabilities": ["channel_monitor", "stream_health", "failover", "auto_repair", "token_refresh"]
        })

    def heartbeat(self):
        while self.running:
            self._bus("POST", "/agent/heartbeat", {"name": "zorin-agent-tv"})
            time.sleep(30)

    def get_channels(self):
        try:
            r = requests.get(f"{self.server_url}/channels.json", timeout=5)
            data = r.json()
            self.channels = data if isinstance(data, list) else data.get("channels", [])
            with open(CHANNELS_CACHE, "w") as f:
                json.dump(self.channels, f, indent=2)
            return self.channels
        except: return self.channels

    def get_status(self):
        try:
            r = requests.get(f"{self.server_url}/status.json", timeout=5)
            return r.json()
        except: return {"error": "server down"}

    def check_stream(self, url, timeout=5):
        try:
            r = requests.get(url, stream=True, timeout=timeout)
            return {"ok": r.status_code == 200, "status": r.status_code}
        except: return {"ok": False, "error": "timeout/refused"}

    def probe_all(self):
        try:
            r = requests.get(f"{self.server_url}/probe-all", timeout=300)
            return r.json()
        except: return {"error": "probe failed"}

    def run_cleanup(self):
        try:
            r = subprocess.run(
                [sys.executable, os.path.join(HELPERS, "zorin-tv-clean.py")],
                capture_output=True, text=True, timeout=120
            )
            return {"ok": r.returncode == 0, "output": r.stdout[-300:]}
        except: return {"error": "cleanup failed"}

    def refresh_token(self):
        try:
            r = subprocess.run(
                [sys.executable, os.path.join(HELPERS, "refresh-magicplaces-token.py")],
                capture_output=True, text=True, timeout=30
            )
            return {"ok": r.returncode == 0}
        except: return {"error": "token refresh failed"}

    def monitor_loop(self):
        while self.running:
            status = self.get_status()
            channels = self.get_channels()
            if isinstance(status, dict) and "error" not in status:
                self._log("tv_status", {"channels": len(channels), "server": "ok"})
                # Refresh token every cycle
                self.refresh_token()
            else:
                self._bus("POST", "/task/create", {
                    "title": "⚠️ Server TV nu răspunde",
                    "description": "Încerc restart watchdog...",
                    "priority": 10, "assigned_to": "zorin-agent-core"
                })
                # Try restart
                subprocess.run(
                    ["bash", os.path.join(HELPERS, "zorin-tv-watchdog.sh")],
                    capture_output=True, timeout=30
                )
            time.sleep(120)

    def run(self):
        self.running = True
        self.register()
        threading.Thread(target=self.heartbeat, daemon=True).start()
        threading.Thread(target=self.monitor_loop, daemon=True).start()
        self._log("tv_agent_ready")
        print(json.dumps({"event": "zorin_tv_ready"}))
        while self.running: time.sleep(1)

    def stop(self): self.running = False

if __name__ == "__main__":
    agent = AgentTV()
    try:
        if "--status" in sys.argv:
            print(json.dumps(agent.get_status(), indent=2))
        elif "--probe" in sys.argv:
            print(json.dumps(agent.probe_all(), indent=2))
        elif "--clean" in sys.argv:
            print(json.dumps(agent.run_cleanup()))
        elif "--channels" in sys.argv:
            ch = agent.get_channels()
            print(f"Total canale: {len(ch)}")
            for c in ch[:10]:
                print(f"  {c.get('name','?')}")
        else:
            agent.run()
    except KeyboardInterrupt:
        agent.stop()
