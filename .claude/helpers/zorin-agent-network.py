#!/usr/bin/env python3
"""
Zorin Agent — Network v1.0
Gestionare Teleport/QNAP/WireGuard, monitorizare rețea.
"""
import os, sys, json, time, threading, requests, subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

HOME = os.path.expanduser("~")
BUS_URL = "http://127.0.0.1:8765"
STATE_DIR = os.path.join(HOME, ".local", "state", "zorin-agent", "network")
os.makedirs(STATE_DIR, exist_ok=True)
LOGS_FILE = os.path.join(STATE_DIR, "network_logs.json")

class AgentNetwork:
    def __init__(self):
        self.running = False
        self.logs = []
        self.targets = {
            "QNAP": "192.168.123.25",
            "gateway": "192.168.123.11",
            "internet": "8.8.8.8",
            "tailscale": "100.100.100.100"
        }

    def _bus(self, method, path, data=None):
        try:
            url = f"{BUS_URL}{path}"
            r = (requests.get if method == "GET" else requests.post)(url, json=data, timeout=3)
            return r.json()
        except: return {}

    def _log(self, event, data=None):
        self._bus("POST", "/message/send", {
            "from": "zorin-agent-network", "to": "*",
            "type": "log", "payload": {"event": event, "data": data or {}}
        })

    def register(self):
        self._bus("POST", "/agent/register", {
            "name": "zorin-agent-network",
            "type": "network",
            "capabilities": ["ping_monitor", "qnap_access", "wireguard", "teleport", "dns_check"]
        })

    def heartbeat(self):
        while self.running:
            self._bus("POST", "/agent/heartbeat", {"name": "zorin-agent-network"})
            time.sleep(30)

    def ping(self, host, count=2):
        try:
            r = subprocess.run(["ping", "-c", str(count), "-W", "2", host],
                             capture_output=True, text=True, timeout=5)
            return {"host": host, "alive": r.returncode == 0, "output": r.stdout[-200:]}
        except: return {"host": host, "alive": False, "error": "timeout"}

    def check_all(self):
        results = {}
        for name, ip in self.targets.items():
            results[name] = self.ping(ip)
            time.sleep(0.5)
        results["timestamp"] = datetime.now(timezone.utc).isoformat()
        self.logs.append(results)
        self.logs = self.logs[-1000:]
        with open(LOGS_FILE, "w") as f:
            json.dump(self.logs, f, indent=2)
        down = [k for k, v in results.items() if isinstance(v, dict) and not v.get("alive", True)]
        if down:
            self._bus("POST", "/task/create", {
                "title": f"⚠️ Hosturi down: {', '.join(down)}",
                "description": json.dumps(results),
                "priority": 9, "assigned_to": "zorin-agent-core"
            })
        self._log("network_check", {"hosts": len(self.targets), "down": len(down)})
        return results

    def qnap_ssh(self, cmd="uptime"):
        try:
            r = subprocess.run(
                ["ssh", "-o", "ConnectTimeout=5", "-o", "StrictHostKeyChecking=no",
                 f"admin@{self.targets['QNAP']}", cmd],
                capture_output=True, text=True, timeout=10
            )
            return {"ok": r.returncode == 0, "output": r.stdout.strip()[:300]}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def tailscale_status(self):
        try:
            r = subprocess.run(["tailscale", "status"], capture_output=True, text=True, timeout=5)
            lines = r.stdout.strip().split("\n")
            peers = [l for l in lines if l.strip() and not l.startswith("#")]
            return {"peers": len(peers), "output": r.stdout[:500]}
        except: return {"error": "tailscale not available"}

    def monitor_loop(self):
        while self.running:
            self.check_all()
            time.sleep(120)

    def run(self):
        self.running = True
        self.register()
        threading.Thread(target=self.heartbeat, daemon=True).start()
        threading.Thread(target=self.monitor_loop, daemon=True).start()
        self._log("network_agent_ready")
        print(json.dumps({"event": "zorin_network_ready"}))
        while self.running: time.sleep(1)

    def stop(self): self.running = False

if __name__ == "__main__":
    agent = AgentNetwork()
    try:
        if "--check" in sys.argv:
            print(json.dumps(agent.check_all(), indent=2))
        elif "--qnap" in sys.argv:
            print(json.dumps(agent.qnap_ssh()))
        elif "--tailscale" in sys.argv:
            print(json.dumps(agent.tailscale_status()))
        else:
            agent.run()
    except KeyboardInterrupt:
        agent.stop()
