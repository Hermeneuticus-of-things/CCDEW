#!/usr/bin/env python3
"""
Zorin Agent — Vault v1.0
Interfață securizată parole pe bus, cu PIN și amprentă.
"""
import os, sys, json, time, threading, requests, subprocess, hashlib
from datetime import datetime, timezone
from pathlib import Path

HOME = os.path.expanduser("~")
BUS_URL = "http://127.0.0.1:8765"
VAULT_DIR = os.path.join(HOME, ".hermes", ".sys_1dd21f77ace54b6d")
STATE_DIR = os.path.join(HOME, ".local", "state", "zorin-agent", "vault")
os.makedirs(STATE_DIR, exist_ok=True)
ACCESS_LOG = os.path.join(STATE_DIR, "access.json")
PIN = os.environ.get("HERMES_VAULT_PIN") or "CHANGE_ME"

class AgentVault:
    def __init__(self):
        self.running = False
        self.authenticated = False
        self.auth_method = None

    def _bus(self, method, path, data=None):
        try:
            url = f"{BUS_URL}{path}"
            r = (requests.get if method == "GET" else requests.post)(url, json=data, timeout=3)
            return r.json()
        except: return {}

    def _log(self, event, data=None):
        self._bus("POST", "/message/send", {
            "from": "zorin-agent-vault", "to": "*",
            "type": "log", "payload": {"event": event, "data": data or {}}
        })

    def register(self):
        self._bus("POST", "/agent/register", {
            "name": "zorin-agent-vault",
            "type": "vault",
            "capabilities": ["password_store", "auth_pin", "auth_fingerprint", "sensitive_data"]
        })

    def heartbeat(self):
        while self.running:
            self._bus("POST", "/agent/heartbeat", {"name": "zorin-agent-vault"})
            time.sleep(30)

    def _list_entries(self):
        entries = []
        if os.path.isdir(VAULT_DIR):
            for f in os.listdir(VAULT_DIR):
                if f.endswith(".enc"):
                    entries.append(f.replace(".enc", ""))
        return entries

    def _read_entry(self, name):
        path = os.path.join(VAULT_DIR, f"{name}.enc")
        if not os.path.exists(path):
            return None
        try:
            r = subprocess.run(
                ["openssl", "enc", "-aes-256-cbc", "-d", "-pbkdf2",
                 "-pass", f"pass:{PIN}", "-in", path],
                capture_output=True, text=True, timeout=10
            )
            if r.returncode == 0:
                return r.stdout.strip()
        except: pass
        return None

    def _log_access(self, name, method, success):
        entry = {"ts": datetime.now(timezone.utc).isoformat(), "entry": name,
                 "method": method, "success": success}
        log = []
        if os.path.exists(ACCESS_LOG):
            try:
                with open(ACCESS_LOG) as f: log = json.load(f)
            except: pass
        log.append(entry)
        log = log[-500:]
        with open(ACCESS_LOG, "w") as f:
            json.dump(log, f, indent=2)

    def auth_pin(self, pin):
        if pin == PIN:
            self.authenticated = True
            self.auth_method = "pin"
            return True
        return False

    def auth_fingerprint(self):
        try:
            r = subprocess.run(["fprintd-verify"], capture_output=True, text=True, timeout=15)
            success = r.returncode == 0
            if success:
                self.authenticated = True
                self.auth_method = "fingerprint"
            return success
        except: return False

    def list_names(self):
        if not self.authenticated:
            return {"error": "needs auth"}
        entries = self._list_entries()
        # Group by sensitivity
        sens_file = os.path.join(VAULT_DIR, ".sensitivity")
        levels = {"PUBLIC": [], "PRIVATE": [], "SECRET": []}
        if os.path.exists(sens_file):
            try:
                with open(sens_file) as f:
                    sens = json.load(f)
                for e in entries:
                    level = sens.get(e, "PUBLIC")
                    if level in levels:
                        levels[level].append(e)
                    else:
                        levels["PUBLIC"].append(e)
                return levels
            except: pass
        return {"all": entries}

    def get_password(self, name):
        if not self.authenticated:
            return {"error": "needs auth"}
        val = self._read_entry(name)
        if val is not None:
            self._log_access(name, self.auth_method, True)
            return {"name": name, "value": val}
        self._log_access(name, self.auth_method, False)
        return {"error": "not found"}

    def search(self, query):
        if not self.authenticated:
            return {"error": "needs auth"}
        q = query.lower()
        entries = self._list_entries()
        matches = [e for e in entries if q in e.lower()]
        results = {}
        for m in matches:
            val = self._read_entry(m)
            if val:
                results[m] = val[:100]
        return results

    def run(self):
        self.running = True
        self.register()
        threading.Thread(target=self.heartbeat, daemon=True).start()
        self._log("vault_agent_ready")
        print(json.dumps({"event": "zorin_vault_ready"}))
        while self.running: time.sleep(1)

    def stop(self): self.running = False

if __name__ == "__main__":
    agent = AgentVault()
    try:
        if "--auth-pin" in sys.argv:
            pin = sys.argv[sys.argv.index("--auth-pin")+1]
            print(json.dumps({"ok": agent.auth_pin(pin)}))
        elif "--auth-fp" in sys.argv:
            print(json.dumps({"ok": agent.auth_fingerprint()}))
        elif "--list" in sys.argv:
            print(json.dumps(agent.list_names(), indent=2))
        elif "--get" in sys.argv:
            name = sys.argv[sys.argv.index("--get")+1]
            print(json.dumps(agent.get_password(name)))
        elif "--search" in sys.argv:
            q = " ".join(sys.argv[sys.argv.index("--search")+1:])
            print(json.dumps(agent.search(q)))
        else:
            agent.run()
    except KeyboardInterrupt:
        agent.stop()
