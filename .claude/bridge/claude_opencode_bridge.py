#!/usr/bin/env python3
"""
claude_opencode_bridge.py — Bridge bidirectional Claude Code <-> OpenCode

Ruleaza ca daemon pe localhost:9130.
Ambele parti (Claude Code prin MCP, OpenCode prin HTTP) se conecteaza la bridge.

Arhitectura:
  Claude Code Desktop  ←→  MCP Server (stdio)  ←→  Bridge :9130  ←→  OpenCode HTTP
"""

import json, os, sys, time, threading, uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

PORT = 9130
TOKEN = "bridge-2026"
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bridge")
os.makedirs(DATA_DIR, exist_ok=True)

# Message queues: { "claude": [...], "opencode": [...] }
_queues = {"claude": [], "opencode": []}
_lock = threading.Lock()

def log(msg):
    ts = time.strftime("%H:%M:%S")
    print(f"[bridge {ts}] {msg}")

class BridgeHandler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _json(self, data, code=200):
        b = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def _body(self):
        n = int(self.headers.get("Content-Length", 0))
        if n:
            return json.loads(self.rfile.read(n))
        return {}

    def _check_token(self):
        q = parse_qs(urlparse(self.path).query)
        token = q.get("token", [None])[0] or self.headers.get("X-Bridge-Token")
        return token == TOKEN

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/health":
            self._json({"ok": True, "service": "claude-opencode-bridge", "port": PORT,
                        "queues": {k: len(v) for k, v in _queues.items()}})

        elif path == "/pending":
            if not self._check_token():
                self._json({"error": "unauthorized"}, 401)
                return
            q = parse_qs(urlparse(self.path).query)
            to = q.get("to", [None])[0]
            if to not in _queues:
                self._json({"error": f"unknown queue: {to}"}, 400)
                return
            with _lock:
                msgs = list(_queues[to])
                _queues[to] = []
            self._json({"messages": msgs, "count": len(msgs)})

        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path

        if path == "/send":
            if not self._check_token():
                self._json({"error": "unauthorized"}, 401)
                return
            data = self._body()
            to = data.get("to", "opencode")  # claude or opencode
            if to not in _queues:
                self._json({"error": f"unknown recipient: {to}"}, 400)
                return
            msg = {
                "id": str(uuid.uuid4())[:8],
                "from": data.get("from", "unknown"),
                "type": data.get("type", "message"),
                "payload": data.get("payload", {}),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            }
            with _lock:
                _queues[to].append(msg)
            log(f"{data.get('from','?')} -> {to}: {data.get('type','?')} ({msg['id']})")
            self._json({"status": "queued", "id": msg["id"], "queue_size": len(_queues[to])})

        elif path == "/clear":
            if not self._check_token():
                self._json({"error": "unauthorized"}, 401)
                return
            with _lock:
                _queues["claude"].clear()
                _queues["opencode"].clear()
            self._json({"status": "cleared"})

        else:
            self._json({"error": "not found"}, 404)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Bridge-Token")
        self.end_headers()


if __name__ == "__main__":
    print(f"[Bridge] Claude Code <-> OpenCode on :{PORT}")
    print(f"  Token: {TOKEN}")
    print(f"  Data:  {DATA_DIR}")
    HTTPServer(("127.0.0.1", PORT), BridgeHandler).serve_forever()
