#!/usr/bin/env python3
"""
Zorin Agent — Developer Assistant v1.0
Code review, git ops, test running, project management.
"""
import os, sys, json, time, threading, requests, subprocess
from datetime import datetime, timezone
from pathlib import Path

HOME = os.path.expanduser("~")
BUS_URL = "http://127.0.0.1:8765"
STATE_DIR = os.path.join(HOME, ".local", "state", "zorin-agent", "dev")
os.makedirs(STATE_DIR, exist_ok=True)

PROJECTS_FILE = os.path.join(STATE_DIR, "projects.json")
BUILDS_FILE = os.path.join(STATE_DIR, "builds.json")

class AgentDev:
    def __init__(self):
        self.running = False
        self.projects = self._load(PROJECTS_FILE, [])
        self.builds = self._load(BUILDS_FILE, [])

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
            "from": "zorin-agent-dev",
            "to": "*",
            "type": "log",
            "payload": {"event": event, "data": data or {}}
        })

    def register(self):
        self._bus("POST", "/agent/register", {
            "name": "zorin-agent-dev",
            "type": "developer",
            "capabilities": ["code_review", "git_ops", "test_runner", "builds", "project_scan"]
        })

    def heartbeat(self):
        while self.running:
            self._bus("POST", "/agent/heartbeat", {"name": "zorin-agent-dev"})
            time.sleep(30)

    def scan_projects(self, root=HOME):
        """Scanează directoare pentru proiecte (git repo-uri)."""
        found = []
        for item in os.listdir(root):
            item_path = os.path.join(root, item)
            git_dir = os.path.join(item_path, ".git")
            if os.path.isdir(item_path) and os.path.isdir(git_dir):
                p = {
                    "name": item,
                    "path": item_path,
                    "detected": datetime.now(timezone.utc).isoformat(),
                    "lang": self._detect_lang(item_path)
                }
                found.append(p)
                if p not in self.projects:
                    self.projects.append(p)
        self._save(PROJECTS_FILE, self.projects)
        self._log("projects_scanned", {"found": len(found), "total": len(self.projects)})
        return found

    def _detect_lang(self, path):
        exts = set()
        for root, dirs, files in os.walk(path):
            for f in files:
                ext = os.path.splitext(f)[1]
                if ext: exts.add(ext)
            break
        lang_map = {
            ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
            ".rs": "Rust", ".go": "Go", ".java": "Java", ".c": "C",
            ".cpp": "C++", ".html": "HTML", ".css": "CSS", ".json": "JSON",
            ".md": "Markdown", ".sh": "Shell", ".yaml": "YAML", ".yml": "YAML"
        }
        for ext, lang in lang_map.items():
            if ext in exts:
                return lang
        return "Unknown"

    def git_status(self, project_path):
        try:
            r = subprocess.run(
                ["git", "status", "--short"],
                cwd=project_path, capture_output=True, text=True, timeout=10
            )
            return {"branch": self._git_branch(project_path), "changes": r.stdout.strip() or "clean"}
        except:
            return {"error": "not a git repo"}

    def _git_branch(self, path):
        try:
            r = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=path, capture_output=True, text=True, timeout=5
            )
            return r.stdout.strip()
        except:
            return "unknown"

    def run_tests(self, project_path):
        results = {"passed": 0, "failed": 0, "output": ""}
        # Detect test framework
        if os.path.exists(os.path.join(project_path, "package.json")):
            cmd = ["npm", "test", "--", "--reporter", "json"]
        elif os.path.exists(os.path.join(project_path, "Cargo.toml")):
            cmd = ["cargo", "test"]
        elif os.path.exists(os.path.join(project_path, "pytest.ini")) or \
             os.path.exists(os.path.join(project_path, "setup.py")):
            cmd = ["python3", "-m", "pytest", "-x", "-v", "--tb=short"]
        elif os.path.exists(os.path.join(project_path, "go.mod")):
            cmd = ["go", "test", "./..."]
        else:
            # Generic: run pytest or check for test dirs
            test_dir = os.path.join(project_path, "tests")
            if os.path.isdir(test_dir):
                cmd = ["python3", "-m", "pytest", "-x", "-v", "--tb=short"]
            else:
                return {"error": "no test framework detected"}

        try:
            r = subprocess.run(cmd, cwd=project_path, capture_output=True, text=True, timeout=120)
            results["output"] = (r.stdout + r.stderr)[-1000:]
            results["returncode"] = r.returncode
            results["passed"] = 1 if r.returncode == 0 else 0
            results["failed"] = 0 if r.returncode == 0 else 1
        except subprocess.TimeoutExpired:
            results["error"] = "test timeout (120s)"
        except Exception as e:
            results["error"] = str(e)

        build = {
            "id": f"build-{int(time.time())}",
            "project": os.path.basename(project_path),
            "ts": datetime.now(timezone.utc).isoformat(),
            "result": "passed" if results.get("returncode") == 0 else "failed",
            "summary": results.get("output", "")[:200]
        }
        self.builds.append(build)
        self._save(BUILDS_FILE, self.builds)
        self._log("test_run", {"project": os.path.basename(project_path), "result": build["result"]})
        return results

    def run(self):
        self.running = True
        self.register()
        threading.Thread(target=self.heartbeat, daemon=True).start()
        # Scan projects at startup
        self.scan_projects()
        self._log("dev_agent_ready", {"projects": len(self.projects)})
        print(json.dumps({"event": "zorin_dev_ready", "projects": len(self.projects)}))
        while self.running:
            time.sleep(1)

    def stop(self):
        self.running = False


if __name__ == "__main__":
    agent = AgentDev()
    try:
        if "--scan" in sys.argv:
            root = sys.argv[sys.argv.index("--scan") + 1] if "--scan" in sys.argv and len(sys.argv) > sys.argv.index("--scan") + 1 else HOME
            found = agent.scan_projects(root)
            print(json.dumps(found, indent=2))
        elif "--status" in sys.argv:
            idx = sys.argv.index("--status")
            path = sys.argv[idx+1] if len(sys.argv) > idx+1 else "."
            print(json.dumps(agent.git_status(path)))
        elif "--test" in sys.argv:
            idx = sys.argv.index("--test")
            path = sys.argv[idx+1] if len(sys.argv) > idx+1 else "."
            print(json.dumps(agent.run_tests(path)))
        else:
            agent.run()
    except KeyboardInterrupt:
        agent.stop()
