#!/usr/bin/env python3
"""
Hermes Agent Loop — Full Deep Cycle
====================================
Testeaza bucla completa cap-coada:

  1. PRIMESTE task
  2. SELECTEAZA nod optim (Core → DeepMemory → SAFLA)
  3. INJECTEAZA system_prompt + task_transform
  4. EXECUTA (simulat: afiseaza promptul construit)
  5. EVALUEAZA outcome
  6. INREGISTREAZA (Core → Pipeline → SAFLA → Bridge)
  7. HANDOFF daca esec
  8. RAPORTEAZA

Usage:
  python3 hermes-agent-loop.py "<task>" [--outcome success|failure] [--node N]
  python3 hermes-agent-loop.py --full-cycle "<task>"   # ruleaza totul
  python3 hermes-agent-loop.py --test                   # test automat
"""

import json, os, sys, time, urllib.request, urllib.parse
from datetime import datetime, timezone

# ─── Config ───────────────────────────────────────────────────────────────────
BRIDGE_URL = "http://127.0.0.1:18777"
HELPERS_DIR = os.environ.get("CCDEW_HELPERS_DIR",
    os.path.expanduser("~/CCDEW/.claude/helpers"))
CORE_PATH = os.path.join(HELPERS_DIR, "hermes-enneagram-core.py")


def http_get(path):
    try:
        r = urllib.request.urlopen(f"{BRIDGE_URL}{path}", timeout=3)
        return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)}


def http_post(path, data):
    try:
        req = urllib.request.Request(
            f"{BRIDGE_URL}{path}",
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        r = urllib.request.urlopen(req, timeout=5)
        return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)}


def python_core(*args):
    """Call core CLI directly."""
    try:
        result = subprocess.check_output(
            [sys.executable, CORE_PATH] + list(args),
            stderr=subprocess.STDOUT, timeout=10, text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        return f"Error: {e.output}"
    except Exception as e:
        return f"Error: {e}"


import subprocess  # noqa: E402


def step_select(task):
    """Pas 1-2: Selecteaza nod optim prin HTTP."""
    print("\n" + "=" * 60)
    print(f"  STEP 1-2: SELECT NODE")
    print(f"  Task: {task}")
    print("=" * 60)

    result = http_get(f"/core/select?task={urllib.parse.quote(task[:200])}")

    if "error" in result:
        print(f"  [FALLBACK] Core HTTP indisponibil ({result['error']})")
        # Fallback: CLI direct
        out = python_core("select", task)
        print(out)
        return {"node_id": 9, "node_name": "Orchestrator", "fallback": True}

    print(f"  Node: {result['node_id']} — {result['node_name']} ({result['archetype']})")
    print(f"  Success Rate: {result.get('success_rate', 0.5)*100:.0f}%")
    print(f"  Pathway: {result.get('prefers_pathway', 'circle')}")
    return result


def step_inject(core_result, task):
    """Pas 3: Construieste promptul complet cu injectie."""
    print("\n" + "=" * 60)
    print(f"  STEP 3: PROMPT INJECTION")
    print("=" * 60)

    sysp = core_result.get("system_prompt", "")
    ttf = core_result.get("task_transform", task)
    nid = core_result.get("node_id", 9)
    nname = core_result.get("node_name", "Orchestrator")

    full_prompt = f"""[Enneagram Node {nid} — {nname}]

## Persona
{sysp}

## Task Transformation
{ttf}

## Original Task
{task}

## Response
"""
    print(f"  Prompt length: {len(full_prompt)} chars")
    print(f"  System prompt: {sysp.split(chr(10))[0]}...")
    return full_prompt


def step_execute(full_prompt):
    """Pas 4: Executa (simulat — afiseaza promptul gata de LLM)."""
    print("\n" + "=" * 60)
    print(f"  STEP 4: EXECUTE (prompt ready for LLM)")
    print("=" * 60)
    print(f"\n{full_prompt}")
    return full_prompt


def step_record(task, outcome, node_id, technique=""):
    """Pas 5-6-7: Inregistreaza outcome → Core + Pipeline + SAFLA + Bridge."""
    print("\n" + "=" * 60)
    print(f"  STEP 5-6: RECORD OUTCOME")
    print(f"  Outcome: {outcome}")
    print("=" * 60)

    data = {
        "task": task[:500],
        "solution": "",
        "outcome": outcome,
        "node_id": node_id,
        "active_node": node_id,
        "technique": technique,
        "tags": [],
        "duration_s": 0,
    }

    # POST la /core/outcome (care face Pipeline + Core + SAFLA)
    result = http_post("/core/outcome", data)

    if "error" in result:
        print(f"  [ERROR] {result['error']}")
        # Fallback direct
        py_out = python_core("record", str(node_id), outcome, technique, task[:100])
        print(f"  [FALLBACK] Recorded via CLI: {py_out.strip()}")
        return {"status": "fallback", "outcome": outcome}

    print(f"  Status: {result.get('status', 'unknown')}")
    if result.get("handoff"):
        print(f"  HANDOFF: Node {result['handoff']['from']} → Node {result['handoff']['to']}")
    print(f"  Pipeline: episode stored = {result.get('pipeline', {}).get('episode_stored', False)}")
    return result


def full_cycle(task, outcome="success", technique=""):
    """Run the complete deep cycle."""
    print("\n" + "#" * 60)
    print(f"  HERMES AGENT LOOP — FULL DEEP CYCLE")
    print(f"  Started: {datetime.now(timezone.utc).isoformat()}")
    print("#" * 60)

    # 1-2. SELECT
    core_result = step_select(task)

    # 3. INJECT
    prompt = step_inject(core_result, task)

    # 4. EXECUTE (simulated)
    step_execute(prompt)

    # 5-6. RECORD
    node_id = core_result.get("node_id", 9)
    result = step_record(task, outcome, node_id, technique)

    print("\n" + "=" * 60)
    print(f"  CYCLE COMPLETE")
    print(f"  Node: {core_result.get('node_name', '?')} ({node_id})")
    print(f"  Outcome: {outcome}")
    print(f"  Handoff: {'Yes' if result.get('handoff') else 'No'}")
    print(f"  Prompt size: {len(prompt)} chars")
    print("=" * 60)

    return {
        "node": core_result,
        "prompt": prompt,
        "outcome": result,
    }


def self_test():
    """Run an automatic test cycle on sample tasks."""
    tasks = [
        "deploy kubernetes cluster with monitoring",
        "review code quality for auth module",
        "fix critical security vulnerability in API",
        "explore new architecture options for microservices",
        "help team onboard to new CI/CD pipeline",
    ]

    print(f"\n{'#'*60}")
    print(f"  SELF-TEST: {len(tasks)} tasks through full deep cycle")
    print(f"{'#'*60}")

    for i, task in enumerate(tasks, 1):
        print(f"\n{'─'*60}")
        print(f"  TEST {i}/{len(tasks)}")
        print(f"{'─'*60}")
        try:
            result = full_cycle(task, "success", "auto-test")
            node_name = result["node"].get("node_name", "?")
            print(f"  \u2713 [{node_name}] {task[:50]}...")
        except Exception as e:
            print(f"  \u2717 Error: {e}")

    print(f"\n{'#'*60}")
    print(f"  SELF-TEST COMPLETE")
    print(f"{'#'*60}")


if __name__ == "__main__":
    import subprocess

    if "--test" in sys.argv:
        self_test()
    elif "--full-cycle" in sys.argv:
        idx = sys.argv.index("--full-cycle")
        task = sys.argv[idx + 1] if len(sys.argv) > idx + 1 else "default task"
        outcome = "success"
        technique = ""
        for i, a in enumerate(sys.argv):
            if a == "--outcome" and i + 1 < len(sys.argv):
                outcome = sys.argv[i + 1]
            if a == "--technique" and i + 1 < len(sys.argv):
                technique = sys.argv[i + 1]
        full_cycle(task, outcome, technique)
    elif len(sys.argv) >= 2 and not sys.argv[1].startswith("--"):
        task = sys.argv[1]
        outcome = "success"
        for i, a in enumerate(sys.argv):
            if a == "--outcome" and i + 1 < len(sys.argv):
                outcome = sys.argv[i + 1]
        # Run full cycle with selection
        cr = step_select(task)
        prompt = step_inject(cr, task)
        step_execute(prompt)
        step_record(task, outcome, cr.get("node_id", 9))
    else:
        print(__doc__)
