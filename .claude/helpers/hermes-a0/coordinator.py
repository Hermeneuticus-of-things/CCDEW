#!/usr/bin/env python3
"""
Hermes-A0 Coordinator — Orchestrator profund în CCDEW.

Arhitectură:
┌─────────────────────────────────────────────────┐
│              CCDEW Coordinator                   │
│                                                  │
│  ┌──────────┐    decide    ┌──────────────┐     │
│  │  Hermes  │ ──────────→ │  Agent Zero  │     │
│  │ (creier) │  ←────────── │   (corp)     │     │
│  └──────────┘   rezultat   └──────────────┘     │
│       ↓                                         │
│  ┌──────────┐                                   │
│  │  CCDEW   │  memorie L0-L4                    │
│  │  Memory  │                                   │
│  └──────────┘                                   │
└─────────────────────────────────────────────────┘

Usage:
  python3 coordinator.py <task>           # Execută task
  python3 coordinator.py --status         # Status sistem
  python3 coordinator.py --sync           # Sync memorie
  python3 coordinator.py --email-scan     # Scan email-uri
"""

import os, sys, json, time
from datetime import datetime

# ── Setup paths ──────────────────────────────────────────────────────────────
COORDINATOR_DIR = os.path.dirname(os.path.abspath(__file__))
CCDEW_ROOT = os.path.dirname(os.path.dirname(COORDINATOR_DIR))
sys.path.insert(0, COORDINATOR_DIR)

from bridge import HermesA0Bridge
from memory_sync import sync_status, sync_hermes_to_ccdew, sync_ccdew_to_hermes

STATE_FILE = os.path.join(CCDEW_ROOT, ".claude-flow", "data", "coordinator-state.json")


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def load_state():
    try:
        if os.path.exists(STATE_FILE):
            return json.loads(open(STATE_FILE).read())
    except:
        pass
    return {"tasks": [], "syncs": 0, "last_run": None}


def save_state(state):
    ensure_dir(os.path.dirname(STATE_FILE))
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def show_status():
    """Show full system status."""
    print("\n" + "=" * 70)
    print("🧠 CCDEW HERMES-A0 COORDINATOR — STATUS")
    print("=" * 70)
    
    state = load_state()
    print(f"\n  Tasks executed: {len(state.get('tasks', []))}")
    print(f"  Memory syncs: {state.get('syncs', 0)}")
    print(f"  Last run: {state.get('last_run', 'never')}")
    
    # Memory layers
    memory_dir = os.path.join(CCDEW_ROOT, "_MEMORY")
    for layer, dirname in [("L4 Identity", "identity"), ("L3 Semantic", "semantic")]:
        path = os.path.join(memory_dir, dirname)
        if os.path.exists(path):
            count = len([f for f in os.listdir(path) if f.endswith(".json")])
            print(f"  {layer}: {count} entries")
    
    # Hermes
    hermes_mem = os.path.expanduser("~/.hermes/hermes-agent/memories")
    if os.path.exists(hermes_mem):
        count = len([f for f in os.listdir(hermes_mem) if f.endswith(".json")])
        print(f"  Hermes memories: {count} entries")
    
    # Agent Zero
    import subprocess
    try:
        result = subprocess.run(["docker", "ps", "--filter", "name=agent-zero", "--format", "{{.Status}}"],
                               capture_output=True, text=True, timeout=5)
        if result.stdout.strip():
            print(f"  Agent Zero: {result.stdout.strip()}")
        else:
            print(f"  Agent Zero: not running")
    except:
        print(f"  Agent Zero: unknown")
    
    # Recent tasks
    tasks = state.get("tasks", [])[-5:]
    if tasks:
        print(f"\n  Recent tasks:")
        for t in tasks:
            status_icon = {"success": "✅", "failed": "❌", "partial": "⚠️"}.get(
                t.get("execution", {}).get("status", "?"), "❓")
            print(f"    {status_icon} [{t.get('timestamp', '')[:19]}] {t.get('description', '')[:60]}")
    
    print()


def run_email_scan():
    """Run email scan through the coordinator."""
    bridge = HermesA0Bridge()
    
    print("\n📧 Email Scan via Hermes-A0 Bridge")
    print("=" * 60)
    
    # Execute email analysis task
    result = bridge.execute_task(
        "Scanează toate email-urile din conturile IMAP Betterbird. "
        "Identifică email-uri importante: securitate, financiar, conturi, contacte. "
        "Salvează informațiile importante în memoria CCDEW (L4 permanent, L3 30 zile). "
        "Ignoră spam, newsletter, promoții."
    )
    
    return result


def main():
    args = sys.argv[1:]
    
    if not args:
        print("Usage:")
        print("  coordinator.py <task>           # Execută task")
        print("  coordinator.py --status         # Status sistem")
        print("  coordinator.py --sync           # Sync memorie")
        print("  coordinator.py --email-scan     # Scan email-uri")
        return
    
    cmd = args[0]
    
    if cmd == "--status":
        show_status()
    
    elif cmd == "--sync":
        print("🔄 Memory Sync...")
        h2c = sync_hermes_to_ccdew()
        print(f"  Hermes → CCDEW: {h2c['synced']} synced")
        c2h = sync_ccdew_to_hermes()
        print(f"  CCDEW → Hermes: {c2h['synced']} synced")
        
        state = load_state()
        state["syncs"] = state.get("syncs", 0) + 1
        state["last_run"] = datetime.now().isoformat()
        save_state(state)
    
    elif cmd == "--email-scan":
        run_email_scan()
    
    else:
        # Execute custom task
        task = " ".join(args)
        bridge = HermesA0Bridge()
        result = bridge.execute_task(task)
        
        state = load_state()
        state["tasks"].append(result)
        state["last_run"] = datetime.now().isoformat()
        save_state(state)


if __name__ == "__main__":
    main()
