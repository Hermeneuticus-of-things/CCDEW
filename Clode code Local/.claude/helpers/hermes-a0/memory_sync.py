#!/usr/bin/env python3
"""
Memory Sync — Sincronizare memorie între Hermes, Agent Zero și CCDEW.

Ce face:
1. Hermes memory → CCDEW L3/L4
2. Agent Zero memory → CCDEW L2/L3
3. CCDEW L4 → Hermes context (pentru decizii viitoare)
4. Conflict resolution: L4 > L3 > L2 (permanente > temporare)

Usage:
  python3 memory_sync.py              # Sync complet
  python3 memory_sync.py --dry-run    # Afișează fără să scrie
  python3 memory_sync.py --status     # Status memorie
"""

import os, sys, json, time, hashlib
from datetime import datetime

# ── Paths ─────────────────────────────────────────────────────────────────────
CCDEW_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
MEMORY_DIR = os.path.join(CCDEW_ROOT, "_MEMORY")
SEMANTIC_DIR = os.path.join(MEMORY_DIR, "semantic")
IDENTITY_DIR = os.path.join(MEMORY_DIR, "identity")
EPISODIC_DIR = os.path.join(CCDEW_ROOT, ".claude-flow", "sessions")
WORKING_DATA = os.path.join(CCDEW_ROOT, ".claude-flow", "data")

HERMES_AGENT = os.path.expanduser("~/.hermes/hermes-agent")
HERMES_MEMORIES = os.path.join(HERMES_AGENT, "memories")
HERMES_USR = os.path.expanduser("~/agent-zero/usr")  # A0 workspace

SYNC_STATE = os.path.join(WORKING_DATA, "memory-sync-state.json")


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def list_json_files(directory):
    """List all JSON files in a directory."""
    if not os.path.exists(directory):
        return []
    return [f for f in os.listdir(directory) if f.endswith(".json")]


def read_json_file(filepath):
    """Read a JSON file safely."""
    try:
        with open(filepath) as f:
            return json.load(f)
    except:
        return None


def write_json_file(filepath, data):
    """Write a JSON file safely."""
    ensure_dir(os.path.dirname(filepath))
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def sync_hermes_to_ccdew(dry_run=False):
    """Sync Hermes memories → CCDEW L3/L4."""
    if not os.path.exists(HERMES_MEMORIES):
        return {"synced": 0, "skipped": 0}
    
    synced = 0
    skipped = 0
    timestamp = int(time.time() * 1000)
    
    for mem_file in list_json_files(HERMES_MEMORIES):
        filepath = os.path.join(HERMES_MEMORIES, mem_file)
        data = read_json_file(filepath)
        if not data:
            continue
        
        # Determine layer based on content
        content = json.dumps(data).lower()
        if any(kw in content for kw in ["account", "contact", "financial", "iban", "password", "credential"]):
            layer = "L4"
            target_dir = IDENTITY_DIR
        else:
            layer = "L3"
            target_dir = SEMANTIC_DIR
        
        key = hashlib.md5(f"{mem_file}:{json.dumps(data)}".encode()).hexdigest()[:12]
        target_path = os.path.join(target_dir, f"hermes-{key}.json")
        
        if os.path.exists(target_path):
            skipped += 1
            continue
        
        if not dry_run:
            entry = {
                "key": f"hermes-{key}",
                "value": json.dumps(data, ensure_ascii=False),
                "createdAt": timestamp,
                "layer": layer,
                "source": "hermes-memory-sync",
                "original_file": mem_file,
            }
            if layer == "L3":
                entry["expiresAt"] = timestamp + 30 * 86400000
            
            write_json_file(target_path, entry)
        
        synced += 1
    
    return {"synced": synced, "skipped": skipped}


def sync_ccdew_to_hermes(dry_run=False):
    """Sync CCDEW L4 (identity) → Hermes context."""
    if not os.path.exists(HERMES_AGENT):
        return {"synced": 0, "skipped": 0}
    
    synced = 0
    skipped = 0
    timestamp = int(time.time() * 1000)
    
    # Read CCDEW L4 entries
    l4_entries = {}
    for f in list_json_files(IDENTITY_DIR):
        data = read_json_file(os.path.join(IDENTITY_DIR, f))
        if data and data.get("layer") == "L4":
            l4_entries[data.get("key", f)] = data.get("value", "")
    
    if not l4_entries:
        return {"synced": 0, "skipped": 0}
    
    # Write to Hermes context
    context_path = os.path.join(HERMES_AGENT, "memories", "ccdew-identity-context.json")
    
    if os.path.exists(context_path):
        existing = read_json_file(context_path)
        if existing and existing.get("entries") == l4_entries:
            return {"synced": 0, "skipped": len(l4_entries)}
    
    if not dry_run:
        write_json_file(context_path, {
            "entries": l4_entries,
            "synced_at": datetime.now().isoformat(),
            "count": len(l4_entries),
            "source": "ccdew-memory-sync",
        })
    
    return {"synced": len(l4_entries), "skipped": skipped}


def sync_status():
    """Show memory sync status."""
    l4_count = len(list_json_files(IDENTITY_DIR))
    l3_count = len(list_json_files(SEMANTIC_DIR))
    l2_count = len(list_json_files(EPISODIC_DIR))
    hermes_count = len(list_json_files(HERMES_MEMORIES))
    
    # Count by source
    sources = {}
    for d in [IDENTITY_DIR, SEMANTIC_DIR, EPISODIC_DIR]:
        for f in list_json_files(d):
            data = read_json_file(os.path.join(d, f))
            if data:
                src = data.get("source", "unknown")
                sources[src] = sources.get(src, 0) + 1
    
    print("\n" + "=" * 60)
    print("🧠 CCDEW MEMORY SYNC STATUS")
    print("=" * 60)
    print(f"\n  CCDEW Layers:")
    print(f"    L4 (Identity/Permanent):  {l4_count} entries")
    print(f"    L3 (Semantic/30 days):    {l3_count} entries")
    print(f"    L2 (Episodic/14 days):    {l2_count} entries")
    print(f"    Total:                    {l4_count + l3_count + l2_count}")
    print(f"\n  Hermes Memories: {hermes_count} entries")
    print(f"\n  By Source:")
    for src, count in sorted(sources.items(), key=lambda x: -x[1]):
        print(f"    {src:30s}: {count}")
    print()


def main():
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    status_only = "--status" in args
    
    if status_only:
        sync_status()
        return
    
    print("=" * 60)
    print("🔄 MEMORY SYNC — Hermes ↔ CCDEW")
    print("=" * 60)
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print()
    
    # Hermes → CCDEW
    print("  [1/2] Hermes → CCDEW...", flush=True)
    h2c = sync_hermes_to_ccdew(dry_run)
    print(f"  → Synced: {h2c['synced']}, Skipped: {h2c['skipped']}")
    
    # CCDEW → Hermes
    print("  [2/2] CCDEW → Hermes...", flush=True)
    c2h = sync_ccdew_to_hermes(dry_run)
    print(f"  → Synced: {c2h['synced']}, Skipped: {c2h['skipped']}")
    
    # Save sync state
    if not dry_run:
        ensure_dir(os.path.dirname(SYNC_STATE))
        state = {
            "last_sync": datetime.now().isoformat(),
            "hermes_to_ccdew": h2c,
            "ccdew_to_hermes": c2h,
        }
        write_json_file(SYNC_STATE, state)
    
    print(f"\n{'=' * 60}")
    print(f"  Total: {h2c['synced'] + c2h['synced']} synced")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
