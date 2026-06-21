#!/usr/bin/env python3
"""
Zorin Agent — File v1.0
Organizare fișiere, curățenie, backup inteligent.
"""
import os, sys, json, time, threading, requests, subprocess, shutil
from datetime import datetime, timezone
from pathlib import Path

HOME = os.path.expanduser("~")
BUS_URL = "http://127.0.0.1:8765"
STATE_DIR = os.path.join(HOME, ".local", "state", "zorin-agent", "file")
os.makedirs(STATE_DIR, exist_ok=True)
SCANS_FILE = os.path.join(STATE_DIR, "scans.json")
BACKUP_SCRIPT = os.path.join(HOME, ".hermes", "migration-backup.sh")
REVERT_SCRIPT = os.path.join(HOME, ".hermes", "migration-revert.sh")

class AgentFile:
    def __init__(self):
        self.running = False
        self.scans = []

    def _bus(self, method, path, data=None):
        try:
            url = f"{BUS_URL}{path}"
            r = (requests.get if method == "GET" else requests.post)(url, json=data, timeout=3)
            return r.json()
        except: return {}

    def _log(self, event, data=None):
        self._bus("POST", "/message/send", {
            "from": "zorin-agent-file", "to": "*",
            "type": "log", "payload": {"event": event, "data": data or {}}
        })

    def register(self):
        self._bus("POST", "/agent/register", {
            "name": "zorin-agent-file",
            "type": "file",
            "capabilities": ["disk_scan", "cleanup", "backup", "dedup", "organize"]
        })

    def heartbeat(self):
        while self.running:
            self._bus("POST", "/agent/heartbeat", {"name": "zorin-agent-file"})
            time.sleep(30)

    def disk_usage(self, path="/"):
        try:
            r = subprocess.run(["df", "-h", path], capture_output=True, text=True, timeout=5)
            lines = r.stdout.strip().split("\n")
            if len(lines) >= 2:
                parts = lines[1].split()
                return {"mount": parts[5], "size": parts[1], "used": parts[2],
                        "avail": parts[3], "use_pct": parts[4]}
        except: pass
        return {"error": "df failed"}

    def scan_large_files(self, path=HOME, min_mb=100):
        large = []
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]
            if len(large) >= 50: break
            for f in files:
                fpath = os.path.join(root, f)
                try:
                    size = os.path.getsize(fpath)
                    if size > min_mb * 1024 * 1024 and not os.path.islink(fpath):
                        large.append({"path": fpath, "size_mb": round(size / 1024 / 1024, 1)})
                except: pass
        large.sort(key=lambda x: -x["size_mb"])
        result = {"scanned_at": datetime.now(timezone.utc).isoformat(), "min_mb": min_mb, "files": large[:30]}
        self.scans.append(result)
        self.scans = self.scans[-100:]
        with open(SCANS_FILE, "w") as f:
            json.dump(self.scans, f, indent=2)
        self._log("large_files_scan", {"found": len(large)})
        return result

    def cleanup_cache(self, target=os.path.join(HOME, ".cache")):
        try:
            r = subprocess.run(["du", "-sh", target], capture_output=True, text=True, timeout=10)
            before = r.stdout.strip().split()[0] if r.stdout.strip() else "0"
            # Clean pip cache
            subprocess.run(["pip3", "cache", "purge"], capture_output=True, timeout=30)
            # Clean apt cache
            subprocess.run(["sudo", "apt-get", "clean"], capture_output=True, timeout=30)
            # Clean thumbnails
            thumb_dir = os.path.join(HOME, ".cache", "thumbnails")
            if os.path.isdir(thumb_dir):
                shutil.rmtree(thumb_dir, ignore_errors=True)
            # Clean npm cache
            subprocess.run(["npm", "cache", "clean", "--force"], capture_output=True, timeout=30)
            r2 = subprocess.run(["du", "-sh", target], capture_output=True, text=True, timeout=10)
            after = r2.stdout.strip().split()[0] if r2.stdout.strip() else "0"
            self._log("cache_cleaned", {"before": before, "after": after})
            return {"before": before, "after": after}
        except Exception as e:
            return {"error": str(e)}

    def backup(self, source, dest):
        try:
            if os.path.exists(BACKUP_SCRIPT):
                subprocess.run(["bash", BACKUP_SCRIPT], capture_output=True, timeout=60)
                self._log("backup_run", {"script": BACKUP_SCRIPT})
                return {"ok": True, "script": BACKUP_SCRIPT}
            else:
                subprocess.run(["cp", "-r", source, dest], capture_output=True, timeout=60)
                self._log("backup_cp", {"from": source, "to": dest})
                return {"ok": True}
        except Exception as e:
            return {"error": str(e)}

    def organize_dir(self, target):
        """Organizează fișiere în subfoldere după extensie."""
        ext_map = {
            "Imagini": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"],
            "Video": [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv"],
            "Audio": [".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac"],
            "Documente": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".odt"],
            "Arhive": [".zip", ".tar", ".gz", ".bz2", ".7z", ".rar"],
            "Programe": [".deb", ".rpm", ".AppImage", ".exe", ".msi"],
        }
        moved = 0
        for f in os.listdir(target):
            fpath = os.path.join(target, f)
            if os.path.isfile(fpath):
                ext = os.path.splitext(f)[1].lower()
                for folder, exts in ext_map.items():
                    if ext in exts:
                        dest_dir = os.path.join(target, folder)
                        os.makedirs(dest_dir, exist_ok=True)
                        shutil.move(fpath, os.path.join(dest_dir, f))
                        moved += 1
                        break
        self._log("files_organized", {"folder": target, "moved": moved})
        return {"folder": target, "moved": moved}

    def run(self):
        self.running = True
        self.register()
        threading.Thread(target=self.heartbeat, daemon=True).start()
        self._log("file_agent_ready")
        print(json.dumps({"event": "zorin_file_ready"}))
        while self.running: time.sleep(1)

    def stop(self): self.running = False

if __name__ == "__main__":
    agent = AgentFile()
    try:
        if "--du" in sys.argv:
            path = sys.argv[sys.argv.index("--du")+1] if "--du" in sys.argv and len(sys.argv) > sys.argv.index("--du")+1 else "/"
            print(json.dumps(agent.disk_usage(path)))
        elif "--scan" in sys.argv:
            path = sys.argv[sys.argv.index("--scan")+1] if "--scan" in sys.argv and len(sys.argv) > sys.argv.index("--scan")+1 else HOME
            print(json.dumps(agent.scan_large_files(path)))
        elif "--clean" in sys.argv:
            print(json.dumps(agent.cleanup_cache()))
        elif "--organize" in sys.argv:
            path = sys.argv[sys.argv.index("--organize")+1]
            print(json.dumps(agent.organize_dir(path)))
        else:
            agent.run()
    except KeyboardInterrupt:
        agent.stop()
