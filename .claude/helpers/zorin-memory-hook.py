#!/usr/bin/env python3
"""Zorin Agent → Hermes Memory hook. Salvează orice eveniment în piramida de învățare."""
import os, sys, json
sys.path.insert(0, os.path.join(os.path.expanduser("~"), "CCDEW", ".claude", "helpers"))
from hermes_memory import save_episode, consolidate_all

if __name__ == "__main__":
    event_type = sys.argv[1] if len(sys.argv) > 1 else "unknown"
    data_raw = sys.argv[2] if len(sys.argv) > 2 else "{}"
    try:
        data = json.loads(data_raw)
    except:
        data = {"raw": data_raw}

    title = data.get("title") or data.get("name") or data.get("id") or event_type
    desc = json.dumps(data, ensure_ascii=False)[:300]

    save_episode(
        task=f"Zorin Agent: {event_type} — {title}",
        solution=desc,
        outcome="info",
        tags=["zorin_agent", event_type] + [data.get("type", "")],
        duration_s=0,
        technique="memory_bus"
    )

    count = sum(1 for _ in open(os.path.expanduser("~/.hermes/memories/episodic.jsonl")) if _.strip())
    if count > 0 and count % 3 == 0:
        consolidate_all()

    print(json.dumps({"saved": True, "episode": title}))
