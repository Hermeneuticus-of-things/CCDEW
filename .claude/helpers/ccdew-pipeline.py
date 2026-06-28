#!/usr/bin/env python3
"""
CCDEW Pipeline — Unified Divergent/Convergent Engine
====================================================

Inlocuieste 7 hook-uri independente cu 2 faze (pre + post),
fiecare cu etapa divergenta (paralela, ne-fatala) si convergenta (sinteza).

Arhitectura:
  Tool action
    │
    ├─ PRE-ACTION (divergent → convergent)
    │   ├── secret_scan()     ─┐
    │   ├── permissions()      ─┤─ paralel → converge → verdict
    │   └── (future: lint...) ─┘
    │
    ├─ [EXECUTA ACTIUNEA]
    │
    └─ POST-ACTION (divergent → convergent)
        ├── safla_learn()     ─┐
        ├── instincts()        ─┤─ paralel → converge → store + sync
        ├── codeburn()         ─┘
        └── (future: ...)

Bridge: HTTP server pe 127.0.0.1:18777
  GET  /bridge.json  → stare pathway curenta (fara race condition)
  POST /bridge       → actualizeaza bridge din Python
  GET  /health       → alive check
  GET  /pipeline/status → ultimul verdict
"""

import json
import os
import sys
import time
import traceback
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, parse_qs

# ─── Load Enneagram Core (intelligence architecture + deep memory) ──
_ENNEAGRAM_CORE_PATH = os.path.join(
    os.environ.get("CCDEW_HELPERS_DIR", os.path.expanduser("~/CCDEW/.claude/helpers")),
    "hermes-enneagram-core.py"
)
_enneagram_core = None
if os.path.exists(_ENNEAGRAM_CORE_PATH):
    try:
        import importlib.util
        _spec = importlib.util.spec_from_file_location("enneagram_core", _ENNEAGRAM_CORE_PATH)
        _ec_mod = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_ec_mod)
        _enneagram_core = _ec_mod
    except Exception as e:
        print(f"[ccdew-pipeline] Enneagram core load error: {e}", file=sys.stderr)

# --- Config ---
BRIDGE_PORT = 18777
HELPERS_DIR = os.environ.get("CCDEW_HELPERS_DIR", os.path.expanduser("~/CCDEW/.claude/helpers"))
MEMORY_DIR = os.environ.get("HERMES_MEMORY_DIR", os.path.expanduser("~/.hermes/memories"))
CONFIG_DIR = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config/opencode"))

BRIDGE_FILE = os.path.join(MEMORY_DIR, "pathway-bridge.json")
SAFLA_FILE = os.path.join(CONFIG_DIR, "ccdew-safla-state.json")
EPISODIC_FILE = os.path.join(MEMORY_DIR, "episodic.jsonl")
CONSCIOUSNESS_FILE = os.path.join(MEMORY_DIR, "consciousness.jsonl")

os.makedirs(MEMORY_DIR, exist_ok=True)

# --- Bridge State (thread-safe, in-memory) ---
_bridge_state = {
    "version": "2.0",
    "updated": datetime.now(timezone.utc).isoformat(),
    "pathway": "circle",
    "pathway_label": "Cerc exterior (9→1)",
    "active_node": 9,
    "confidence": 0.5,
    "flow": 0.5,
    "confusion": 0.0,
    "preferred_nodes": [9, 8, 7, 6, 5, 4, 3, 2, 1],
    "routing_hint": "all_nodes_equal",
    "safla_hint": "all_nodes_equal",
    "best_pathway": None,
    "best_score": 0,
    "best_label": None,
    "pipeline_status": "idle"
}
_bridge_lock = __import__("threading").Lock()


def update_bridge(**kwargs):
    """Thread-safe update al bridge-ului in memorie."""
    with _bridge_lock:
        _bridge_state.update(kwargs)
        _bridge_state["updated"] = datetime.now(timezone.utc).isoformat()


def get_bridge():
    """Thread-safe citire bridge."""
    with _bridge_lock:
        return dict(_bridge_state)


# ─── Sub-step wrappers (ne-fatale) ─────────────────────────────────

def _safe_run(name: str, fn, *args, **kwargs):
    """Run a sub-step; return (name, success, data_or_error)."""
    try:
        result = fn(*args, **kwargs)
        return (name, True, result)
    except Exception as e:
        return (name, False, {"error": str(e), "traceback": traceback.format_exc()})


# ─── Pre-action sub-steps ──────────────────────────────────────────

def secret_scan(action_data: dict) -> dict:
    """Scaneaza actiunea pentru secrete (token-uri, parole, chei)."""
    text = json.dumps(action_data) if isinstance(action_data, dict) else str(action_data)
    patterns = [
        "ghp_", "gho_", "ghu_", "ghs_", "ghr_",
        "sk-", "pk-", "api_key", "api-key", "api.secret",
        "password", "passwd", "secret", "token",
        "-----BEGIN", "AKIA", "eyJ", "xox[bpsar]"
    ]
    found = [p for p in patterns if p in text.lower() or p in text]
    return {"blocked": len(found) > 0, "matches": found, "severity": "high" if found else "none"}


def permissions_check(action_data: dict) -> dict:
    """Verifica permisiuni pentru actiunea ceruta."""
    action_type = action_data.get("action_type", action_data.get("type", "unknown"))
    # Whitelist de actiuni permise mereu
    always_ok = ["read", "list", "get", "search", "status", "help", "info"]
    if any(a in action_type.lower() for a in always_ok):
        return {"allowed": True, "reason": "read-only action"}
    return {"allowed": True, "reason": "default allow (future: policy engine)"}


# ─── Post-action sub-steps ─────────────────────────────────────────

def safla_learn(action_data: dict, outcome: str = "success") -> dict:
    """Inregistreaza in SAFLA."""


    saf = {}
    if os.path.exists(SAFLA_FILE):
        try:
            with open(SAFLA_FILE) as f:
                saf = json.load(f)
        except Exception:
            saf = {}
    if "nodes" not in saf:
        saf["nodes"] = {}
    node_id = str(action_data.get("node", action_data.get("active_node", 9)))
    if node_id not in saf["nodes"]:
        saf["nodes"][node_id] = {"success": 0, "failure": 0, "last_task": "", "weight_adj": 0.1}

    if outcome == "success":
        saf["nodes"][node_id]["success"] += 1
    else:
        saf["nodes"][node_id]["failure"] += 1
    saf["nodes"][node_id]["last_task"] = action_data.get("task", "")[:200]
    saf["total_feedbacks"] = saf.get("total_feedbacks", 0) + 1
    saf["updated"] = datetime.now(timezone.utc).isoformat()
    with open(SAFLA_FILE, "w") as f:
        json.dump(saf, f, indent=2, ensure_ascii=False)
    return {"node": node_id, "outcome": outcome, "total_feedbacks": saf["total_feedbacks"]}


def instincts_check(action_data: dict) -> dict:
    """Verifica pattern-uri invatate (instincts)."""
    patterns_path = os.path.join(MEMORY_DIR, "patterns.json")
    if not os.path.exists(patterns_path):
        return {"matched": False, "pattern": None}
    try:
        with open(patterns_path) as f:
            patterns = json.load(f)
        task = action_data.get("task", "")
        if not task:
            return {"matched": False, "pattern": None}
        for p in patterns:
            if isinstance(p, dict) and "trigrams" in p:
                if any(t in task for t in p["trigrams"]):
                    return {"matched": True, "pattern": p.get("pattern", "unknown")}
        return {"matched": False, "pattern": None}
    except Exception:
        return {"matched": False, "pattern": None, "error": True}


def codeburn_track(action_data: dict) -> dict:
    """Tracking cost (token count estimate)."""
    task_len = len(action_data.get("task", ""))
    solution_len = len(action_data.get("solution", ""))
    est_tokens = (task_len + solution_len) // 4
    return {"estimated_tokens": est_tokens, "task_chars": task_len, "solution_chars": solution_len}


# ─── Pipeline Engine ────────────────────────────────────────────────

class PipelineResult:
    def __init__(self, phase: str):
        self.phase = phase
        self.divergent_results = []
        self.convergent_verdict = {}
        self.failures = []
        self.start_time = time.time()
        self.end_time = None

    @property
    def elapsed(self):
        return (self.end_time or time.time()) - self.start_time

    @property
    def success(self):
        return len(self.failures) == 0

    def to_dict(self):
        return {
            "phase": self.phase,
            "success": self.success,
            "failures": self.failures,
            "divergent_results": self.divergent_results,
            "convergent_verdict": self.convergent_verdict,
            "elapsed_s": round(self.elapsed, 3)
        }


class Pipeline:
    """Divergent → Convergent Pipeline."""

    def __init__(self):
        self._executor = ThreadPoolExecutor(max_workers=4)

    def run_pre(self, action_data: dict) -> PipelineResult:
        """Faza Pre-Action: divergenta (paralel) → convergenta (verdict)."""
        result = PipelineResult("pre")

        # ── DIVERGENT: ruleaza toate verificarile in paralel ──
        futures = {
            self._executor.submit(_safe_run, "secret_scan", secret_scan, action_data),
            self._executor.submit(_safe_run, "permissions", permissions_check, action_data),
        }
        checks = {}
        for f in as_completed(futures):
            name, ok, data = f.result()
            result.divergent_results.append({"step": name, "ok": ok, "data": data})
            checks[name] = (ok, data)
            if not ok:
                result.failures.append(f"{name} failed: {data.get('error', 'unknown')}")

        # ── CONVERGENT: sinteza ──
        sec = checks.get("secret_scan", (True, {"blocked": False}))
        perm = checks.get("permissions", (True, {"allowed": True}))

        blocked = sec[1].get("blocked", False)
        allowed = perm[1].get("allowed", True)

        result.convergent_verdict = {
            "verdict": "block" if blocked else ("allow" if allowed else "block"),
            "reason": "secret detected" if blocked else ("permission denied" if not allowed else "all checks passed"),
            "secret_matches": sec[1].get("matches", []) if sec[0] else [],
            "permissions": perm[1] if perm[0] else {"error": "permissions check failed"}
        }
        result.end_time = time.time()

        update_bridge(pipeline_status=f"pre_{'passed' if result.success else 'failed'}")
        return result

    def run_post(self, action_data: dict, outcome: str = "success") -> PipelineResult:
        """Faza Post-Action: divergenta (paralel) → convergenta (stocare + sincronizare)."""
        result = PipelineResult("post")

        # ── DIVERGENT: toate observatiile in paralel ──
        futures = {
            self._executor.submit(_safe_run, "safla", safla_learn, action_data, outcome),
            self._executor.submit(_safe_run, "instincts", instincts_check, action_data),
            self._executor.submit(_safe_run, "codeburn", codeburn_track, action_data),
        }
        observations = {}
        for f in as_completed(futures):
            name, ok, data = f.result()
            result.divergent_results.append({"step": name, "ok": ok, "data": data})
            observations[name] = (ok, data)
            if not ok:
                result.failures.append(f"{name} failed: {data.get('error', 'unknown')}")

        # ── CONVERGENT: salveaza episodic ──
        episode = {
            "id": int(time.time()),
            "ts": datetime.now(timezone.utc).isoformat(),
            "task": action_data.get("task", "")[:500],
            "solution": action_data.get("solution", "")[:500],
            "outcome": outcome,
            "tags": action_data.get("tags", []),
            "duration_s": action_data.get("duration_s", 0),
            "technique": action_data.get("technique", ""),
            "estimated_tokens": observations.get("codeburn", (True, {}))[1].get("estimated_tokens", 0)
        }

        try:
            with open(EPISODIC_FILE, "a") as f:
                f.write(json.dumps(episode, ensure_ascii=False) + "\n")
            stored = True
        except Exception as e:
            stored = False
            result.failures.append(f"episodic write failed: {e}")

        result.convergent_verdict = {
            "episode_id": episode["id"],
            "episode_stored": stored,
            "outcome": outcome,
            "safla_updated": observations.get("safla", (True, {}))[0],
            "instincts_match": observations.get("instincts", (True, {}))[1].get("matched", False),
            "estimated_tokens": episode["estimated_tokens"],
            "failures": result.failures
        }
        result.end_time = time.time()

        update_bridge(pipeline_status=f"post_{'done' if stored else 'partial_fail'}")
        return result

    def run(self, phase: str, action_data: dict, outcome: str = "success") -> dict:
        """Unified entry point."""
        if phase == "pre":
            return self.run_pre(action_data).to_dict()
        elif phase == "post":
            return self.run_post(action_data, outcome).to_dict()
        else:
            return {"error": f"unknown phase: {phase}", "phase": phase}


# ─── HTTP Server ────────────────────────────────────────────────────

_pipeline_global = Pipeline()


class BridgeHandler(BaseHTTPRequestHandler):
    """Serveste bridge state fara race condition (in-memory)."""

    def log_message(self, format, *args):
        pass

    def _json_response(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def do_GET(self):
        if self.path == "/bridge.json" or self.path == "/bridge":
            b = get_bridge()
            # Add Enneagram core status if available
            try:
                if _enneagram_core:
                    core = _enneagram_core.get_core()
                    b["nodes"] = core.memory.get_node_stats()
            except Exception:
                pass
            self._json_response(b)
        elif self.path == "/health":
            self._json_response({"status": "alive", "ts": datetime.now(timezone.utc).isoformat()})
        elif self.path == "/pipeline/status":
            self._json_response(get_bridge().get("pipeline_status", "idle"))
        elif self.path == "/core/status":
            try:
                if _enneagram_core:
                    core = _enneagram_core.get_core()
                    self._json_response(core.get_status())
                else:
                    self._json_response({"error": "core not loaded"})
            except Exception as e:
                self._json_response({"error": str(e)}, 500)
        elif self.path.startswith("/core/select"):
            qs = parse_qs(urlparse(self.path).query)
            task = qs.get("task", [""])[0]
            if not task:
                self._json_response({"error": "task parameter required"}, 400)
            else:
                try:
                    core = _enneagram_core.get_core()
                    node = core.select_node(task)
                    result = core.process_task(task, node)
                    self._json_response(result)
                except Exception as e:
                    self._json_response({"error": str(e)}, 500)
        else:
            self._json_response({"error": "not found"}, 404)

    def do_POST(self):
        if self.path == "/bridge":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length) if length > 0 else b"{}"
            try:
                data = json.loads(body)
                update_bridge(**data)
                self._json_response({"status": "updated", "bridge": get_bridge()})
            except json.JSONDecodeError:
                self._json_response({"error": "invalid json"}, 400)
        elif self.path == "/pipeline/pre":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length) if length > 0 else b"{}"
            try:
                data = json.loads(body)
                result = _pipeline_global.run_pre(data)
                self._json_response(result.to_dict())
            except Exception as e:
                self._json_response({"error": str(e)}, 500)
        elif self.path == "/pipeline/post":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length) if length > 0 else b"{}"
            try:
                data = json.loads(body)
                result = _pipeline_global.run_post(
                    data, data.get("outcome", "success")
                )
                self._json_response(result.to_dict())
            except Exception as e:
                self._json_response({"error": str(e)}, 500)
        else:
            self._json_response({"error": "not found"}, 404)


def serve_forever(port=BRIDGE_PORT):
    """Porneste HTTP server."""
    server = HTTPServer(("127.0.0.1", port), BridgeHandler)
    print(f"[ccdew-pipeline] bridge HTTP server on 127.0.0.1:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[ccdew-pipeline] shutting down", flush=True)
        server.server_close()


# ─── CLI ────────────────────────────────────────────────────────────

def cli():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  ccdew-pipeline serve                    # HTTP server")
        print("  ccdew-pipeline pre  '{\"task\":\"...\"}'    # Pre-action")
        print("  ccdew-pipeline post '{\"task\":\"...\"}'    # Post-action")
        print("  ccdew-pipeline bridge                   # Show bridge state")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "serve":
        serve_forever()

    elif cmd == "bridge":
        print(json.dumps(get_bridge(), indent=2, ensure_ascii=False))

    elif cmd in ("pre", "post"):
        data_str = sys.argv[2] if len(sys.argv) > 2 else "{}"
        try:
            data = json.loads(data_str)
        except json.JSONDecodeError:
            data = {"task": data_str}
        outcome = sys.argv[3] if len(sys.argv) > 3 else "success"
        pipe = Pipeline()
        result = pipe.run(cmd, data, outcome)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
