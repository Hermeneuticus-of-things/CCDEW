#!/usr/bin/env python3
"""
Zorin Agent — Hardware v1.0
Verifică IO, drivere, hardware, kernel, disk health.
"""
import os, sys, json, time, threading, requests, subprocess
from datetime import datetime, timezone

HOME = os.path.expanduser("~")
BUS_URL = "http://127.0.0.1:8765"
STATE_DIR = os.path.join(HOME, ".local", "state", "zorin-agent", "hardware")
os.makedirs(STATE_DIR, exist_ok=True)
REPORTS_FILE = os.path.join(STATE_DIR, "reports.json")

class AgentHardware:
    def __init__(self):
        self.running = False
        self.reports = []

    def _bus(self, method, path, data=None):
        try:
            url = f"{BUS_URL}{path}"
            r = (requests.get if method == "GET" else requests.post)(url, json=data, timeout=3)
            return r.json()
        except: return {}

    def _log(self, event, data=None):
        self._bus("POST", "/message/send", {
            "from": "zorin-agent-hardware", "to": "*",
            "type": "log", "payload": {"event": event, "data": data or {}}
        })

    def register(self):
        self._bus("POST", "/agent/register", {
            "name": "zorin-agent-hardware",
            "type": "hardware",
            "capabilities": ["disk_health", "drivers", "kernel", "io_stats", "temperature", "hardware_scan"]
        })

    def heartbeat(self):
        while self.running:
            self._bus("POST", "/agent/heartbeat", {"name": "zorin-agent-hardware"})
            time.sleep(30)

    def _run(self, cmd, timeout=10):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return {"ok": r.returncode == 0, "stdout": r.stdout.strip()[:1000], "stderr": r.stderr.strip()[:500]}
        except subprocess.TimeoutExpired: return {"ok": False, "error": "timeout"}
        except FileNotFoundError: return {"ok": False, "error": f"command not found: {cmd[0]}"}
        except Exception as e: return {"ok": False, "error": str(e)}

    def disk_health(self):
        result = {}
        # S.M.A.R.T. data
        smart = self._run(["sudo", "smartctl", "--scan"], 5)
        if smart["ok"]:
            devices = [l.split()[0] for l in smart["stdout"].split("\n") if l.strip()]
            for dev in devices[:4]:
                data = self._run(["sudo", "smartctl", "-H", dev], 5)
                result[dev] = {"health": data["stdout"][:200] if data["ok"] else "unavailable"}
        # Disk usage
        df = self._run(["df", "-h", "--output=source,fstype,size,used,avail,pcent,target"], 5)
        result["df"] = df["stdout"] if df["ok"] else df.get("error")
        # NVMe (if exists)
        nvme = self._run(["sudo", "nvme", "list"], 5)
        if nvme["ok"]:
            result["nvme"] = nvme["stdout"]
        return result

    def drivers(self):
        result = {}
        # Loaded kernel modules
        lsmod = self._run(["lsmod"], 5)
        if lsmod["ok"]:
            modules = [l.split()[0] for l in lsmod["stdout"].split("\n")[1:] if l.strip()]
            result["modules_count"] = len(modules)
            result["modules"] = modules[:50]
        # GPU driver
        gpu = self._run(["lspci", "-k"], 5)
        if gpu["ok"]:
            gpu_lines = [l for l in gpu["stdout"].split("\n") if "VGA" in l or "3D" in l or "Kernel driver" in l]
            result["gpu"] = gpu_lines[:10]
        # dmesg for driver errors
        dmesg = self._run(["dmesg", "-l", "err", "-P"], 5)
        if dmesg["ok"]:
            errors = [l for l in dmesg["stdout"].split("\n") if l.strip() and "driver" in l.lower()]
            result["driver_errors"] = errors[-10:]
        return result

    def kernel(self):
        result = {}
        uname = self._run(["uname", "-a"], 5)
        result["version"] = uname["stdout"] if uname["ok"] else "unknown"
        # Kernel parameters
        cmdline = self._run(["cat", "/proc/cmdline"], 5)
        result["cmdline"] = cmdline["stdout"] if cmdline["ok"] else ""
        # Zram / swap
        zram = self._run(["zramctl"], 5)
        result["zram"] = zram["stdout"] if zram["ok"] else ""
        return result

    def io_stats(self):
        result = {}
        iostat = self._run(["iostat", "-x", "1", "2"], 10)
        if iostat["ok"]:
            lines = iostat["stdout"].split("\n")
            result["iostat"] = lines[-20:]
        io = self._run(["cat", "/proc/diskstats"], 5)
        if io["ok"]:
            disks = [l for l in io["stdout"].split("\n") if l.strip() and ("nvme" in l or "sd" in l)][:10]
            result["diskstats"] = disks
        return result

    def temperature(self):
        result = {}
        sensors = self._run(["sensors", "-j"], 10)
        if sensors["ok"]:
            try:
                result["sensors"] = json.loads(sensors["stdout"])
            except:
                result["sensors_raw"] = sensors["stdout"][:500]
        else:
            # Try thermal zone
            thermal = self._run(["cat", "/sys/class/thermal/thermal_zone*/temp"], 5)
            if thermal["ok"]:
                temps = [t.strip() for t in thermal["stdout"].split("\n") if t.strip()]
                result["thermal_zones"] = temps
        return result

    def full_report(self):
        report = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "disk_health": self.disk_health(),
            "drivers": self.drivers(),
            "kernel": self.kernel(),
            "io": self.io_stats(),
            "temperature": self.temperature()
        }
        self.reports.append(report)
        self.reports = self.reports[-100:]
        with open(REPORTS_FILE, "w") as f:
            json.dump(self.reports[-10:], f, indent=2)
        self._log("hardware_report", {"ts": report["ts"]})
        return report

    def monitor_loop(self):
        while self.running:
            report = self.full_report()
            # Alert if issues found
            drivers = report.get("drivers", {})
            if drivers.get("driver_errors"):
                self._bus("POST", "/task/create", {
                    "title": "⚠️ Erori drivere detectate",
                    "description": json.dumps(drivers["driver_errors"]),
                    "priority": 8, "assigned_to": "zorin-agent-core"
                })
            time.sleep(3600)

    def run(self):
        self.running = True
        self.register()
        threading.Thread(target=self.heartbeat, daemon=True).start()
        threading.Thread(target=self.monitor_loop, daemon=True).start()
        self._log("hardware_agent_ready")
        print(json.dumps({"event": "zorin_hardware_ready"}))
        while self.running: time.sleep(1)

    def stop(self): self.running = False

if __name__ == "__main__":
    agent = AgentHardware()
    try:
        if "--report" in sys.argv:
            print(json.dumps(agent.full_report(), indent=2))
        elif "--disk" in sys.argv:
            print(json.dumps(agent.disk_health(), indent=2))
        elif "--drivers" in sys.argv:
            print(json.dumps(agent.drivers(), indent=2))
        elif "--kernel" in sys.argv:
            print(json.dumps(agent.kernel(), indent=2))
        elif "--temp" in sys.argv:
            print(json.dumps(agent.temperature(), indent=2))
        else:
            agent.run()
    except KeyboardInterrupt:
        agent.stop()
