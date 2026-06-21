#!/usr/bin/env python3
"""
Zorin Agent — Browser v1.0
Cercetare web, scraping, form filling.
"""
import os, sys, json, time, threading, requests
from datetime import datetime, timezone
from urllib.parse import urlparse

HOME = os.path.expanduser("~")
BUS_URL = "http://127.0.0.1:8765"
STATE_DIR = os.path.join(HOME, ".local", "state", "zorin-agent", "browser")
os.makedirs(STATE_DIR, exist_ok=True)
HISTORY_FILE = os.path.join(STATE_DIR, "history.json")

class AgentBrowser:
    def __init__(self):
        self.running = False
        self.history = []

    def _bus(self, method, path, data=None):
        try:
            url = f"{BUS_URL}{path}"
            r = (requests.get if method == "GET" else requests.post)(url, json=data, timeout=3)
            return r.json()
        except: return {}

    def _log(self, event, data=None):
        self._bus("POST", "/message/send", {
            "from": "zorin-agent-browser", "to": "*",
            "type": "log", "payload": {"event": event, "data": data or {}}
        })

    def register(self):
        self._bus("POST", "/agent/register", {
            "name": "zorin-agent-browser",
            "type": "browser",
            "capabilities": ["web_search", "web_fetch", "scrape", "research"]
        })

    def heartbeat(self):
        while self.running:
            self._bus("POST", "/agent/heartbeat", {"name": "zorin-agent-browser"})
            time.sleep(30)

    def fetch_page(self, url, format="markdown"):
        try:
            r = requests.get(f"http://127.0.0.1:8642/fetch?url={url}&format={format}", timeout=15)
            content = r.text[:5000]
            self._save_to_history(url, "fetch", len(content))
            return {"url": url, "ok": True, "content": content}
        except Exception as e:
            return {"url": url, "ok": False, "error": str(e)}

    def search_web(self, query, count=5):
        try:
            r = requests.post(f"http://127.0.0.1:8642/search", json={
                "query": query, "count": count
            }, timeout=15)
            results = r.json()
            self._save_to_history(query, "search")
            return {"query": query, "results": results.get("results", results)[:count]}
        except Exception as e:
            return {"query": query, "error": str(e)}

    def research(self, topic, depth=3):
        result = {"topic": topic, "depth": depth, "sources": [], "summary": ""}
        # Search first
        search_res = self.search_web(topic, depth)
        if "results" in search_res:
            for r_item in search_res["results"]:
                url = r_item.get("url", "")
                title = r_item.get("title", "")
                result["sources"].append({"url": url, "title": title})
                if len(result["sources"]) >= depth:
                    break
        self._log("research_done", {"topic": topic, "sources": len(result["sources"])})
        return result

    def _save_to_history(self, query, action, size=0):
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "query": query[:100],
            "action": action,
            "size": size
        }
        self.history.append(entry)
        self.history = self.history[-500:]
        with open(HISTORY_FILE, "w") as f:
            json.dump(self.history[-100:], f, indent=2)

    def run(self):
        self.running = True
        self.register()
        threading.Thread(target=self.heartbeat, daemon=True).start()
        self._log("browser_agent_ready")
        print(json.dumps({"event": "zorin_browser_ready"}))
        while self.running: time.sleep(1)

    def stop(self): self.running = False

if __name__ == "__main__":
    agent = AgentBrowser()
    try:
        if "--fetch" in sys.argv:
            url = sys.argv[sys.argv.index("--fetch")+1]
            print(json.dumps(agent.fetch_page(url)))
        elif "--search" in sys.argv:
            q = " ".join(sys.argv[sys.argv.index("--search")+1:])
            print(json.dumps(agent.search_web(q)))
        elif "--research" in sys.argv:
            q = " ".join(sys.argv[sys.argv.index("--research")+1:])
            print(json.dumps(agent.research(q)))
        else:
            agent.run()
    except KeyboardInterrupt:
        agent.stop()
