#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
auto_learn.py v3 — META-017 Stop hook (QUEUE-ONLY, ultra-fast).

Doar:
  1. Citește ultimul turn din transcript
  2. Heuristic score (zero LLM)
  3. Project router + Karma editorial guard
  4. Append în queue locked + idempotent
  5. Exit (<100ms)

Consolidarea (LLM merge + scriere Obsidian) e separată în auto_learn_consolidate.py
(rulat la SessionEnd sau manual).
"""
from __future__ import annotations
import json
import os
import sys
import re
import hashlib
import datetime
from pathlib import Path

_SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
WORKSPACE   = Path(os.environ.get('WORKSPACE_DIR', str(_SCRIPT_DIR.parent.parent)))
QUEUE       = WORKSPACE / ".claude-flow" / "data" / "learn_queue.jsonl"
LOG         = WORKSPACE / ".claude-flow" / "data" / "auto_learn.log"
PROJECTS_DIR = WORKSPACE / "PROJECTS"
MAX_LOG_BYTES = 256 * 1024
THRESHOLD = 0.6
MIN_TURN_CHARS = 100

# === DETECTOR (heuristic) ===
TRIGGERS = {
    "feedback_correction": {
        "patterns": [
            r"\bnu\b.{0,15}\b(asa|așa|aia)\b", r"\bstop\b", r"\bgre[sș]it\b",
            r"\b(altfel|altceva)\b", r"NU\s+(face|adaug[ăa]|scrie|modifica)",
            r"\binterzis\b", r"\bnu mai\b", r"\bopre[sș]te\b", r"\binval[iî]d\b",
        ],
        "weight": 0.85, "type": "feedback",
    },
    "feedback_validation": {
        "patterns": [
            r"\bexact\b", r"\bperfect\b", r"\bbravo\b", r"^GO\b",
            r"\baprobat\b", r"\bcorect\b", r"\bmerge bine\b",
        ],
        "weight": 0.55, "type": "feedback",
    },
    "project_decision": {
        "patterns": [
            r"\bdeadline\b", r"\bpentru c[ăa]\b", r"\bmotiv\b", r"\bconstraint\b",
            r"\blivrare\b", r"\bfreeze\b", r"\bblocant\b", r"\bstakeholder\b",
            r"\bpriori?tate\b",
        ],
        "weight": 0.65, "type": "project",
    },
    "user_profile": {
        "patterns": [
            r"\bsunt (un|o) \w+", r"\blucrez (la|cu|pe)\b",
            r"\bexperien[tț][aă]\b", r"\bnivel\b.{0,20}\b(\d+|junior|senior|expert)\b",
            r"\bprofesie\b",
        ],
        "weight": 0.7, "type": "user",
    },
    "reference_pattern": {
        "patterns": [
            r"\bworkaround\b", r"\bbug.{0,5}fix\b", r"\btruc\b", r"\bhack\b",
            r"\bsurprinz\w+\b", r"\bedge case\b",
        ],
        "weight": 0.55, "type": "reference",
    },
}

SKIP_USER_PATTERNS = [
    r"^(salut|buna|bun[ăa]|hi|hello|mersi|mul[tț]umesc|ok|gata|test|cer confirmare)\.?\s*$",
]

KARMA_EDITORIAL_PATHS = [".scriv", "_NANO/", "_MAP/", "Cap.", "_BLOG", "ilustra", "alogen"]


def _scan_project_names() -> list:
    """Dynamic scan PROJECTS/ folder. Cache pentru a nu repeta listdir."""
    if not hasattr(_scan_project_names, "_cache"):
        _scan_project_names._cache = None
    if _scan_project_names._cache is not None:
        return _scan_project_names._cache
    projects_dir = WORKSPACE / "PROJECTS"
    names = []
    if projects_dir.exists():
        try:
            for entry in projects_dir.iterdir():
                if entry.is_dir() and not entry.name.startswith("."):
                    names.append(entry.name)
        except OSError:
            pass
    _scan_project_names._cache = names
    return names


def log(msg: str) -> None:
    """Log line cu rotație 256KB."""
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        if LOG.exists() and LOG.stat().st_size > MAX_LOG_BYTES:
            LOG.rename(LOG.with_suffix(".log.old"))
        with LOG.open("a", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.now().isoformat(timespec='seconds')}] {msg}\n")
    except OSError:
        pass


def heuristic_score(user_msg: str, asst_msg: str) -> tuple[float, list]:
    """Returnează (score, hits)."""
    if not user_msg:
        return 0.0, []
    u_lower = user_msg.lower().strip()
    for skip_pat in SKIP_USER_PATTERNS:
        if re.match(skip_pat, u_lower):
            return 0.0, []
    text = (user_msg + " " + asst_msg).lower()
    if len(text) < MIN_TURN_CHARS:
        return 0.0, []
    hits, score = [], 0.0
    for trig_name, cfg in TRIGGERS.items():
        for pat in cfg["patterns"]:
            try:
                if re.search(pat, text, re.IGNORECASE):
                    hits.append((trig_name, cfg["type"]))
                    if cfg["weight"] > score:
                        score = cfg["weight"]
                    break
            except re.error as exc:
                log(f"regex_error: {trig_name} {pat!r}: {exc}")
                continue
    return score, hits


def detect_project_from_paths(paths: list) -> str | None:
    """Match path-uri editate vs PROJECTS/<N>/ (dynamic scan)."""
    project_names = _scan_project_names()
    counts: dict[str, int] = {}
    for path_str in paths:
        normalized = path_str.replace("\\", "/").lower()
        for name in project_names:
            if f"/projects/{name.lower()}/" in normalized:
                counts[name] = counts.get(name, 0) + 1
    if not counts:
        return None
    return max(counts, key=lambda k: counts[k])


def is_karma_editorial(project: str | None, paths: list) -> bool:
    """Skip auto-learn dacă editare text Karma (corectări fine)."""
    if not project or "karma" not in project.lower():
        return False
    for path_str in paths:
        normalized = path_str.replace("\\", "/").lower()
        if any(signal.lower() in normalized for signal in KARMA_EDITORIAL_PATHS):
            return True
    return False


def get_last_turn_with_paths() -> tuple[str, str, list]:
    """Returnează (user_msg, asst_msg, edited_paths) din ultimul turn."""
    proj_dir = Path.home() / ".claude" / "projects" / "D--Cloude-Code"
    if not proj_dir.exists():
        return "", "", []
    jsonls = sorted(proj_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not jsonls:
        return "", "", []
    latest = jsonls[0]
    try:
        lines = latest.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return "", "", []

    user_msg, asst_msg = "", ""
    paths: list[str] = []
    found_asst = False

    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        etype = entry.get("type")
        msg = entry.get("message", {})
        if not isinstance(msg, dict):
            continue
        content = msg.get("content", "")

        text_parts: list[str] = []
        if isinstance(content, str):
            text_parts.append(content)
        elif isinstance(content, list):
            for chunk in content:
                if not isinstance(chunk, dict):
                    continue
                if chunk.get("type") == "text":
                    text_parts.append(chunk.get("text", ""))
                elif chunk.get("type") == "tool_use":
                    inp = chunk.get("input", {}) or {}
                    for key in ("file_path", "path", "filename"):
                        val = inp.get(key)
                        if isinstance(val, str) and val:
                            paths.append(val)
                            break

        text = " ".join(text_parts).strip()
        if not text and not paths:
            continue

        if etype == "assistant" and not found_asst:
            asst_msg = text + (" " + asst_msg if asst_msg else "")
            if text:
                found_asst = True
        elif etype == "user" and found_asst and not user_msg:
            if "<system-reminder>" in text or "tool_use_id" in text.lower()[:100]:
                continue
            user_msg = text
            break

    return user_msg, asst_msg, paths


def queue_load() -> list:
    """Citește queue (skip linii corupte silent)."""
    if not QUEUE.exists():
        return []
    out = []
    try:
        for line in QUEUE.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    except OSError:
        pass
    return out


CRASH_RECOVERY_THRESHOLD = 8  # spawn consolidate detached dacă queue ≥ N (safety net)
CONSOLIDATE_SCRIPT = WORKSPACE / ".claude" / "helpers" / "auto_learn_consolidate.py"

CONSOLIDATE_SENTINEL = WORKSPACE / ".claude-flow" / "data" / "consolidate_in_progress.sentinel"
CONSOLIDATE_SENTINEL_TTL_SEC = 120  # consider stale după 2min


def _spawn_consolidate_detached() -> None:
    """
    Spawn consolidate background fire-and-forget. Cu sentinel anti-double-spawn.
    """
    # Verifică sentinel: dacă există și e fresh (<TTL), skip spawn
    try:
        if CONSOLIDATE_SENTINEL.exists():
            age = datetime.datetime.now().timestamp() - CONSOLIDATE_SENTINEL.stat().st_mtime
            if age < CONSOLIDATE_SENTINEL_TTL_SEC:
                log(f"CRASH_RECOVERY_SKIP: sentinel fresh ({age:.0f}s)")
                return
    except OSError:
        pass

    try:
        CONSOLIDATE_SENTINEL.parent.mkdir(parents=True, exist_ok=True)
        CONSOLIDATE_SENTINEL.write_text(str(datetime.datetime.now().timestamp()))
        import subprocess
        if os.name == "nt":
            DETACHED_PROCESS = 0x00000008
            CREATE_NEW_PROCESS_GROUP = 0x00000200
            subprocess.Popen(
                ["python", str(CONSOLIDATE_SCRIPT), "--force"],
                creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                close_fds=True,
            )
        else:
            subprocess.Popen(
                ["python", str(CONSOLIDATE_SCRIPT), "--force"],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        log("CRASH_RECOVERY: spawned consolidate detached")
    except Exception as exc:
        log(f"crash_recovery_spawn_failed: {type(exc).__name__}: {exc}")


def queue_append_atomic(entry: dict) -> str:
    """
    Append atomic + idempotent în queue (load+write INSIDE lock — race-free).
    Dedupe pe hash(user_msg[:200] + ts[:16]). Returnează status.
    """
    QUEUE.parent.mkdir(parents=True, exist_ok=True)
    dedupe_key = hashlib.md5(
        (entry["user_msg"][:200] + entry["ts"][:16]).encode("utf-8", errors="ignore")
    ).hexdigest()[:12]
    entry["_dedupe"] = dedupe_key
    line = json.dumps(entry, ensure_ascii=False) + "\n"

    # Lock-file separat (sentinel) ca să serializăm load+write — evită race
    lock_path = QUEUE.with_suffix(".lock")
    queue_size = 0
    status = "appended"

    try:
        import msvcrt
        with lock_path.open("w") as lock_f:
            # Acquire exclusive lock (blocking up to ~3s prin retry)
            for _ in range(30):
                try:
                    msvcrt.locking(lock_f.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    import time as _t
                    _t.sleep(0.1)
            try:
                # CRITICAL SECTION: load + dedupe + write atomic
                existing = {e.get("_dedupe") for e in queue_load()}
                if dedupe_key in existing:
                    status = "duplicate"
                else:
                    with QUEUE.open("a", encoding="utf-8") as f:
                        f.write(line)
                        f.flush()
                queue_size = len(queue_load())
            finally:
                try:
                    lock_f.seek(0)
                    msvcrt.locking(lock_f.fileno(), msvcrt.LK_UNLCK, 1)
                except OSError:
                    pass
    except ImportError:
        try:
            import fcntl
            with lock_path.open("w") as lock_f:
                fcntl.flock(lock_f.fileno(), fcntl.LOCK_EX)
                try:
                    existing = {e.get("_dedupe") for e in queue_load()}
                    if dedupe_key in existing:
                        status = "duplicate"
                    else:
                        with QUEUE.open("a", encoding="utf-8") as f:
                            f.write(line)
                    queue_size = len(queue_load())
                finally:
                    fcntl.flock(lock_f.fileno(), fcntl.LOCK_UN)
        except Exception:
            # Fallback fără lock (best-effort)
            existing = {e.get("_dedupe") for e in queue_load()}
            if dedupe_key in existing:
                status = "duplicate"
            else:
                with QUEUE.open("a", encoding="utf-8") as f:
                    f.write(line)
            queue_size = len(queue_load())

    # Crash-recovery: spawn consolidate detached dacă queue mare
    if status == "appended" and queue_size >= CRASH_RECOVERY_THRESHOLD:
        _spawn_consolidate_detached()

    return status


def main() -> int:
    try:
        user_msg, asst_msg, paths = get_last_turn_with_paths()
        if not user_msg or not asst_msg:
            log("SKIP: no_turn_data")
            return 0

        score, hits = heuristic_score(user_msg, asst_msg)
        if score < THRESHOLD:
            return 0

        project = detect_project_from_paths(paths)
        if is_karma_editorial(project, paths):
            log(f"SKIP_KARMA_EDITORIAL: paths={paths[:3]}")
            return 0

        ptype = hits[0][1] if hits else "reference"
        status = queue_append_atomic({
            "ts": datetime.datetime.now().isoformat(timespec="seconds"),
            "user_msg": user_msg[:1500],
            "asst_msg": asst_msg[:1500],
            "ptype": ptype,
            "score": score,
            "project": project,
            "hits": [h[0] for h in hits],
        })
        log(f"QUEUE_{status}: type={ptype} score={score:.2f} project={project}")
        return 0
    except Exception as exc:
        log(f"ERROR: {type(exc).__name__}: {exc}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
