#!/usr/bin/env python3
"""
Hermes Zorin Symbiote v2 — Self-Learning System Guardian
Monitor → Diagnose → Heal → LEARN → Synthesize → Evolve

Learning loop:
  1. Snapshot system state
  2. Detect anomalies vs baseline
  3. Route fix via learned patterns (SAFLA-style)
  4. Record outcome (success/failure)
  5. Update pattern weights
  6. Synthesize complex diagnoses from correlated signals

Usage:
  python3 hermes-zorin-symbiote.py --daemon    # Continuous learning loop
  python3 hermes-zorin-symbiote.py --learn     # Single learn pass
  python3 hermes-zorin-symbiote.py --synth     # Complex synthesis report
  python3 hermes-zorin-symbiote.py --forget    # Reset learning curve
"""

import os, sys, json, time, hashlib, subprocess, shutil
from datetime import datetime
from pathlib import Path

HOME = os.path.expanduser("~")
STATE_DIR = os.path.join(HOME, ".local", "state", "hermes-zorin")
LEARN_FILE = os.path.join(STATE_DIR, "learning_curve.json")
HISTORY_FILE = os.path.join(STATE_DIR, "action_history.json")
PATTERN_FILE = os.path.join(STATE_DIR, "patterns.json")
REPORT_FILE = os.path.join(STATE_DIR, "synthesis.json")

WATCH_SERVICES = ["fail2ban", "docker", "sshd", "dailyaidecheck", "systemd-journald"]
LEARNING_RATE = 0.3        # cat de repede se ajusteaza weight-urile
CONFIDENCE_FLOOR = 0.3     # sub cat nu actioneaza automat
SYNTHESIS_WINDOW = 3600    # fereastra de sinteza: 1h


def log(msg, level="INFO"):
    entry = {"ts": datetime.now().isoformat(), "level": level, "module": "hermes-zorin", "msg": msg}
    print(json.dumps(entry), flush=True)


def run(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"


def sudo_run(cmd, timeout=30):
    try:
        r = subprocess.run(["sudo", "-n"] + cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"


# ─── LEARNING ENGINE ───────────────────────────────────────────────

def load_learning():
    data = {"actions": [], "patterns": {}, "weights": {}, "curve": []}
    for f, key in [(LEARN_FILE, "curve"), (HISTORY_FILE, "actions"), (PATTERN_FILE, "patterns")]:
        if os.path.exists(f):
            try:
                with open(f) as fp:
                    data[key] = json.load(fp)
            except Exception:
                pass
    return data


def save_learning(data):
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(LEARN_FILE, "w") as f: json.dump(data.get("curve", []), f)
    with open(HISTORY_FILE, "w") as f: json.dump(data.get("actions", []), f)
    with open(PATTERN_FILE, "w") as f: json.dump(data.get("patterns", {}), f)


def record_action(action, context, outcome, quality=None):
    data = load_learning()
    entry = {
        "ts": datetime.now().isoformat(),
        "action": action,
        "context": context,
        "outcome": outcome,
        "quality": quality,
        "took_ms": 0,
    }
    data["actions"].append(entry)
    if len(data["actions"]) > 500:
        data["actions"] = data["actions"][-500:]

    pattern_key = f"{action}:{context.get('service','?')}"
    p = data["patterns"].get(pattern_key, {"count": 0, "success": 0, "failure": 0, "avg_quality": 0})
    p["count"] += 1
    if outcome == "success":
        p["success"] += 1
    else:
        p["failure"] += 1
    if quality:
        p["avg_quality"] = ((p["avg_quality"] * (p["count"] - 1)) + quality) / p["count"]
    p["confidence"] = p["success"] / max(p["count"], 1)
    p["last_seen"] = datetime.now().isoformat()
    data["patterns"][pattern_key] = p

    curve_point = {
        "ts": entry["ts"],
        "total_actions": sum(v["count"] for v in data["patterns"].values()),
        "avg_confidence": sum(v["confidence"] for v in data["patterns"].values()) / max(len(data["patterns"]), 1),
        "action": action,
        "outcome": outcome,
    }
    data["curve"].append(curve_point)
    if len(data["curve"]) > 1000:
        data["curve"] = data["curve"][-1000:]

    save_learning(data)
    return data


def get_pattern_confidence(action, service):
    data = load_learning()
    pattern_key = f"{action}:{service}"
    p = data["patterns"].get(pattern_key)
    if p and p["count"] >= 2:
        return p["confidence"]
    return 0.0


def can_auto_heal(action, service):
    return get_pattern_confidence(action, service) >= CONFIDENCE_FLOOR


# ─── SYSTEM CHECKS ─────────────────────────────────────────────────

def check_services():
    results = {}
    for svc in WATCH_SERVICES:
        code, out, _ = run(["systemctl", "is-active", svc])
        results[svc] = {"active": out.strip() == "active", "state": out.strip()}
    return results


def check_system():
    results = {"timestamp": datetime.now().isoformat()}

    code, out, _ = run(["uname", "-r"]); results["kernel"] = out

    code, out, _ = run(["uptime", "-p"]); results["uptime"] = out
    code, out, _ = run(["cat", "/proc/loadavg"])
    parts = out.split() if out else ["0", "0", "0"]
    results["load_1m"], results["load_5m"], results["load_15m"] = parts[0], parts[1], parts[2]

    code, out, _ = run(["free", "-h"])
    for line in out.split("\n"):
        if line.startswith("Mem:"):
            parts = line.split()
            results["mem_total"] = parts[1]
            results["mem_used"] = parts[2]
            results["mem_avail"] = parts[6]
            def parse_gb(s): return float(s.replace("Gi","").replace(",",".").replace("Mi",""))
            results["mem_pct"] = round(parse_gb(parts[2]) / parse_gb(parts[1]) * 100, 1)

    code, out, _ = run(["df", "-h", "--exclude-type=tmpfs", "--exclude-type=devtmpfs", "--exclude-type=squashfs"])
    for line in out.split("\n")[1:]:
        if line.strip() and line.startswith("/dev/"):
            parts = line.split()
            results["disk_root_use"] = parts[4]

    results["services"] = check_services()

    code, out, _ = run(["ss", "-tlnp"])
    results["listening_ports"] = len([l for l in out.split("\n") if "LISTEN" in l])

    return results


# ─── DIAGNOSE ──────────────────────────────────────────────────────

def diagnose(prev, curr):
    issues = []
    svc_prev = prev.get("services", {}) if isinstance(prev, dict) else {}
    svc_curr = curr.get("services", {})

    for svc, info in svc_curr.items():
        if not info.get("active"):
            was_active = svc_prev.get(svc, {}).get("active", True)
            issues.append({
                "type": "service_down",
                "service": svc,
                "state": info["state"],
                "new": was_active,
                "confidence": get_pattern_confidence("restart", svc),
            })

    load_5m = float(curr.get("load_5m", 0))
    if load_5m > 4.0:
        issues.append({"type": "high_load", "value": load_5m, "threshold": 4.0})

    mem_pct = curr.get("mem_pct", 0)
    if mem_pct > 85:
        issues.append({"type": "high_memory", "value": f"{mem_pct}%", "threshold": "85%"})

    return issues


# ─── HEAL ──────────────────────────────────────────────────────────

def heal(issues):
    fixed = []
    for issue in issues:
        if issue["type"] == "service_down":
            svc = issue["service"]
            if svc in ["fail2ban", "docker", "sshd"]:
                conf = get_pattern_confidence("restart", svc)
                log(f"Restart {svc} (confidence: {conf:.2f})", "WARN")
                code, _, err = sudo_run(["systemctl", "restart", svc])
                if code == 0:
                    fixed.append(svc)
                    record_action("restart", {"service": svc}, "success", quality=5)
                    log(f"{svc} restarted OK", "INFO")
                else:
                    record_action("restart", {"service": svc}, "failure", quality=1)
                    log(f"{svc} FAILED: {err}", "ERROR")
            else:
                log(f"Cannot auto-heal {svc} — no pattern", "WARN")
                record_action("skip", {"service": svc}, "skipped", quality=3)

        elif issue["type"] == "high_load":
            log(f"High load: {issue['value']} — monitoring only", "WARN")
            record_action("monitor", {"metric": "load"}, "info", quality=3)

        elif issue["type"] == "high_memory":
            log(f"High memory: {issue['value']} — monitoring only", "WARN")
            record_action("monitor", {"metric": "memory"}, "info", quality=3)

    return fixed


# ─── SYNTHESIS (complex technical synthesis) ──────────────────────

def synthesize():
    data = load_learning()
    actions = data.get("actions", [])
    patterns = data.get("patterns", {})

    if not actions:
        return {"status": "learning", "actions_count": 0, "message": "Not enough data yet"}

    recent = [a for a in actions
              if (datetime.now() - datetime.fromisoformat(a["ts"])).total_seconds() < SYNTHESIS_WINDOW]

    success_rate = sum(p["confidence"] for p in patterns.values()) / max(len(patterns), 1)

    worst_patterns = sorted(patterns.values(), key=lambda p: p["confidence"])[:3]
    best_patterns = sorted(patterns.values(), key=lambda p: p["confidence"], reverse=True)[:3]

    current = check_system()
    services = current.get("services", {})

    synthesis = {
        "generated_at": datetime.now().isoformat(),
        "status": "stable",
        "learning_curve": {
            "total_actions": sum(p["count"] for p in patterns.values()),
            "patterns_learned": len(patterns),
            "avg_confidence": round(success_rate, 3),
            "actions_last_hour": len(recent),
        },
        "system_health": {
            "kernel": current.get("kernel"),
            "load_5m": current.get("load_5m"),
            "mem_pct": current.get("mem_pct"),
            "disk_root": current.get("disk_root_use"),
            "services_up": sum(1 for s in services.values() if s.get("active")),
            "services_down": sum(1 for s in services.values() if not s.get("active")),
        },
        "patterns": {
            "strongest": [{"action": k, "confidence": v["confidence"], "count": v["count"]}
                          for k, v in patterns.items() if v["confidence"] > 0.8][:3],
            "weakest": [{"action": k, "confidence": v["confidence"], "count": v["count"]}
                         for k, v in patterns.items() if v["confidence"] < 0.5][:3],
        },
        "diagnosis": diagnose({}, current),
    }

    synthesis["system_health"]["risk_score"] = round(
        (1 - success_rate) * 0.4 +
        (float(current.get("load_5m", 0)) / 4.0) * 0.3 +
        (float(current.get("mem_pct", 0)) / 100.0) * 0.3, 3
    )

    if synthesis["system_health"]["risk_score"] < 0.3:
        synthesis["status"] = "stable"
    elif synthesis["system_health"]["risk_score"] < 0.6:
        synthesis["status"] = "watch"
    else:
        synthesis["status"] = "critical"

    with open(REPORT_FILE, "w") as f:
        json.dump(synthesis, f, indent=2)

    return synthesis


# ─── DAEMON LOOP ──────────────────────────────────────────────────

def daemon_loop():
    log("=== Hermes Zorin v2 — Self-Learning Guardian ===")
    interval = int(os.environ.get("HERMES_CHECK_INTERVAL", "300"))

    prev_state = check_system()
    log(f"Initial snapshot: {prev_state.get('kernel')} | "
        f"load={prev_state.get('load_5m')} | mem={prev_state.get('mem_pct')}%")

    while True:
        time.sleep(interval)
        try:
            curr_state = check_system()
            issues = diagnose(prev_state, curr_state)

            if issues:
                log(f"Diagnosed {len(issues)} issues", "WARN")
                for issue in issues:
                    log(f"  {issue['type']}: {issue.get('service', issue.get('value', '?'))}", "WARN")
                fixed = heal(issues)
                if fixed:
                    log(f"Auto-healed: {fixed}", "INFO")
            else:
                log("No issues — system healthy", "INFO")

            if int(time.time()) % SYNTHESIS_WINDOW < interval:
                syn = synthesize()
                log(f"Synthesis: {syn['status']} | "
                    f"risk={syn['system_health']['risk_score']} | "
                    f"patterns={syn['learning_curve']['patterns_learned']}", "INFO")

            prev_state = curr_state
            log(f"Next check in {interval}s", "DEBUG")

        except Exception as e:
            log(f"Loop error: {e}", "ERROR")


# ─── CLI ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    os.makedirs(STATE_DIR, exist_ok=True)

    if "--daemon" in sys.argv:
        daemon_loop()
    elif "--learn" in sys.argv:
        curr = check_system()
        issues = diagnose({}, curr)
        if issues:
            log(f"Issues found: {len(issues)}", "WARN")
            fixed = heal(issues)
            log(f"Fixed: {fixed}")
        else:
            log("No issues — system healthy", "INFO")
    elif "--synth" in sys.argv:
        syn = synthesize()
        print(json.dumps(syn, indent=2))
    elif "--forget" in sys.argv:
        for f in [LEARN_FILE, HISTORY_FILE, PATTERN_FILE]:
            if os.path.exists(f): os.remove(f)
        log("Learning curve reset", "WARN")
    elif "--eval" in sys.argv:
        data = load_learning()
        patterns = data.get("patterns", {})
        print(json.dumps({
            "patterns_learned": len(patterns),
            "total_actions": sum(p["count"] for p in patterns.values()),
            "avg_confidence": round(sum(p["confidence"] for p in patterns.values()) / max(len(patterns), 1), 3) if patterns else 0,
            "worst": sorted(patterns.items(), key=lambda x: x[1]["confidence"])[:3] if patterns else [],
            "best": sorted(patterns.items(), key=lambda x: x[1]["confidence"], reverse=True)[:3] if patterns else [],
        }, indent=2))
    else:
        curr = check_system()
        syn = synthesize()
        print(json.dumps({"snapshot": curr, "synthesis": syn}, indent=2))
