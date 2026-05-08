#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
auto_learn_consolidate.py v3 — META-017 Consolidator (SessionEnd hook + manual run).

Pipeline:
  1. Load queue (auto_learn.py output)
  2. Single LLM call merged (judge + distill + merge într-un prompt) cu fallback template
  3. Pentru fiecare lecție: integrate (UPDATE same-name auto_learned existent SAU NEW)
     - Conform protocol Obsidian Memory v1: ## [Claude] + ## [User] sections
     - Frontmatter complet: _version, _created, _modified, _modified_by, tags, project, priority
     - Slug LLM-injected sanitizat
     - Backlink dezactivat (era feature creep + risc)
  4. Update MEMORY.md → ## [Claude Index] (1 line per lecție nouă)
  5. Dashboard ping minimal (1 line agregat per consolidate)
  6. Clear queue + mark_consolidated

Run: python auto_learn_consolidate.py [--force]
"""
from __future__ import annotations
import argparse
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

WORKSPACE = Path("D:/Cloude Code")
AUTO_MEM = Path.home() / ".claude" / "projects" / "D--Cloude-Code" / "memory"
OBS_MEM = WORKSPACE / "_MEMORY"
PROJECTS_DIR = WORKSPACE / "PROJECTS"
QUEUE = WORKSPACE / ".claude" / "cache" / "learn_queue.jsonl"
LAST_CONSOLIDATE = WORKSPACE / ".claude" / "cache" / "last_consolidate.txt"
CONSOLIDATE_SENTINEL = WORKSPACE / ".claude" / "cache" / "consolidate_in_progress.sentinel"
LOG = WORKSPACE / ".claude" / "cache" / "auto_learn.log"
DASHBOARD = OBS_MEM / "_DASHBOARD.md"
MEMORY_INDEX_GLOBAL = AUTO_MEM / "MEMORY.md"
MEMORY_INDEX_OBS = OBS_MEM / "MEMORY.md"
OBS_PY = WORKSPACE / ".claude" / "helpers" / "obs.py"

BATCH_SIZE = 5
BATCH_WINDOW_SEC = 3600
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()
LLM_MODEL = "claude-haiku-4-5-20251001"
LLM_TIMEOUT_SEC = 12
SIMILARITY_UPDATE_THRESHOLD = 0.7
TOKEN_MIN_LEN = 4

STOPWORDS = {
    "care", "este", "sunt", "cand", "când", "asa", "așa", "doar", "fara", "fără",
    "aici", "acolo", "atunci", "apoi", "deci", "asta", "acest", "aceasta", "user",
    "asst", "claude", "with", "from", "this", "that", "rule", "auto",
}


def log(msg: str) -> None:
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.now().isoformat(timespec='seconds')}] CONS: {msg}\n")
    except OSError:
        pass


# === QUEUE ===
def queue_load() -> list:
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


def queue_clear() -> None:
    if QUEUE.exists():
        try:
            QUEUE.unlink()
        except OSError:
            pass


def should_consolidate(qlen: int, force: bool) -> bool:
    if force and qlen > 0:
        return True
    if qlen < 1:
        return False
    if qlen >= BATCH_SIZE:
        return True
    if not LAST_CONSOLIDATE.exists():
        return False
    try:
        last_ts = float(LAST_CONSOLIDATE.read_text().strip())
    except (OSError, ValueError):
        return True
    return (datetime.datetime.now().timestamp() - last_ts) > BATCH_WINDOW_SEC


def mark_consolidated() -> None:
    try:
        LAST_CONSOLIDATE.parent.mkdir(parents=True, exist_ok=True)
        LAST_CONSOLIDATE.write_text(str(datetime.datetime.now().timestamp()))
    except OSError:
        pass


# === LLM (single merged call) ===
def llm_merge_call(entries: list) -> list | None:
    """
    Single LLM call: merge + distill + judge final.
    Input: N candidate entries.
    Output: list de lecții finale [{rule, why, how, type, project, title_slug, tags}].
    """
    if not ANTHROPIC_KEY or not entries:
        return None
    try:
        import urllib.request
        import urllib.error
    except ImportError:
        return None

    sys_prompt = (
        "Esti un consolidator de memorie. Primesti N candidate de lectii din conversatii. "
        "Sarcina: judeca care merita pastrate (skip irelevante), grupeaza similare, "
        "distileaza in 1-3 lectii holografice finale. Fiecare lectie: "
        "rule (1 propoz, max 120 chars), why (motiv, max 100), how (cand aplici, max 100), "
        "type (feedback|project|user|reference), project (nume sau null), "
        "title_slug (3-5 cuvinte snake_case fara diacritice/spatii), "
        "tags (lista, max 4). "
        'Raspunde STRICT JSON: {"lessons": [{...}, ...]}'
    )

    payload = "\n\n".join(
        f"[{i+1}] type={e.get('ptype')} project={e.get('project','-')}\n"
        f"USER: {e.get('user_msg','')[:300]}\nASST: {e.get('asst_msg','')[:300]}"
        for i, e in enumerate(entries)
    )

    body = json.dumps({
        "model": LLM_MODEL,
        "max_tokens": 900,
        "system": sys_prompt,
        "messages": [{"role": "user", "content": payload}],
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=body,
            headers={
                "x-api-key": ANTHROPIC_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=LLM_TIMEOUT_SEC) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        parts = data.get("content", [])
        text = "".join(p.get("text", "") for p in parts if p.get("type") == "text").strip()
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return None
        parsed = json.loads(match.group(0))
        lessons = parsed.get("lessons", [])
        return lessons if isinstance(lessons, list) else None
    except (urllib.error.URLError, json.JSONDecodeError, OSError) as exc:
        log(f"llm_call_failed: {type(exc).__name__}: {exc}")
        return None


def template_merge(entries: list) -> list:
    """Fallback fără LLM: 1 lecție per (type, project) distinct."""
    by_key: dict[tuple, list] = {}
    for entry in entries:
        key = (entry.get("ptype", "reference"), entry.get("project"))
        by_key.setdefault(key, []).append(entry)
    lessons = []
    for (ptype, project), group in by_key.items():
        rep = max(group, key=lambda x: len(x.get("user_msg", "")))
        summary_words = " ".join(rep["user_msg"].strip().split()[:14])
        summary = re.sub(r"[\n\r]+", " ", summary_words)[:100]
        rule_lbl = {"feedback": "User a indicat", "project": "Decizie/context proiect",
                    "user": "Profil user", "reference": "Pattern observat"}[ptype]
        why_lbl = {"feedback": "Semnal explicit (corectare/validare) detectat",
                   "project": "Decizie cu motiv menționat (deadline/constraint)",
                   "user": "User a dezvăluit info despre rol/expertiză",
                   "reference": "Pattern non-evident, posibil reutilizabil"}[ptype]
        how_lbl = {"feedback": "Aplică în task-uri similare; verifică contradicții",
                   "project": "Folosește la planificare pe proiectul referit",
                   "user": "Adaptează ton/tehnicalitate la profilul indicat",
                   "reference": "Reverific când apare situație similară"}[ptype]
        lessons.append({
            "rule": f"{rule_lbl}: {summary}",
            "why": why_lbl,
            "how": how_lbl,
            "type": ptype,
            "project": project,
            "title_slug": f"consolidated_{len(lessons)+1}",  # fără prefix ptype (adăugat în integrate)
            "tags": ["auto-learned", ptype],
        })
    return lessons


# === SLUG SANITIZE ===
def safe_slug(raw: str, max_len: int = 40) -> str:
    """Sanitize slug LLM-injected (path traversal protection)."""
    cleaned = re.sub(r"[^a-z0-9_]", "_", raw.lower().strip())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned[:max_len] or "lesson"


def _normalize_tag(tag: str) -> str:
    """Tag Obsidian-safe: lowercase, spațiu→dash, alfanumeric+dash only."""
    cleaned = re.sub(r"[^a-z0-9-]", "-", str(tag).lower().strip())
    cleaned = re.sub(r"-+", "-", cleaned).strip("-")
    return cleaned


# === FRONTMATTER (YAML) ===
def parse_frontmatter(path: Path) -> tuple[dict, str]:
    try:
        import yaml
    except ImportError:
        return {}, path.read_text(encoding="utf-8", errors="ignore")
    try:
        txt = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return {}, ""
    if not txt.startswith("---"):
        return {}, txt
    parts = txt.split("---", 2)
    if len(parts) < 3:
        return {}, txt
    try:
        fm = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        fm = {}
    return fm, parts[2].lstrip("\n")


def write_with_frontmatter(path: Path, fm: dict, body: str) -> None:
    try:
        import yaml
        fm_str = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True).strip()
    except ImportError:
        fm_str = "\n".join(f"{k}: {v}" for k, v in fm.items())
    path.write_text(f"---\n{fm_str}\n---\n\n{body.lstrip()}", encoding="utf-8")


# === BODY PROTOCOL OBSIDIAN v1 ([Claude]/[User]) ===
def build_body_protocol(rule: str, why: str, how: str) -> str:
    """Generează body conform protocol Obsidian Memory v1."""
    return (
        f"## [Claude]\n"
        f"{rule}\n\n"
        f"**Why:** {why}\n"
        f"**How to apply:** {how}\n\n"
        f"## [User]\n"
        f"<!-- spațiu rezervat user pentru notițe / corecții -->\n"
    )


def update_claude_section(body: str, new_claude_block: str) -> str:
    """Updatează DOAR `## [Claude]` (păstrează `## [User]` intact)."""
    if "## [Claude]" not in body:
        # Nu există protocol; rebuild complet
        return new_claude_block + "\n\n## [User]\n<!-- spațiu rezervat user -->\n"
    pattern = re.compile(r"(## \[Claude\].*?)(?=\n## \[User\]|\Z)", re.DOTALL)
    return pattern.sub(new_claude_block, body, count=1)


# === SEMANTIC SEARCH (single helper) ===
def obs_search(query: str, max_files: int = 5) -> list:
    """Helper unic obs.py. Returnează list[Path] absolute."""
    try:
        result = subprocess.run(
            ["python", str(OBS_PY), "search", query[:80], "--max-files", str(max_files), "-i"],
            capture_output=True, text=True, timeout=10,
            encoding="utf-8", errors="ignore",
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        log(f"obs_search_failed: {exc}")
        return []
    if result.returncode != 0:
        return []
    paths = []
    seen = set()
    for line in result.stdout.splitlines():
        match = re.match(r"=== \[\w+\] (.+\.md) ===\s*$", line)
        if not match:
            continue
        rel = match.group(1)
        path = Path(rel)
        if not path.is_absolute():
            path = WORKSPACE / rel
        if path.exists() and str(path) not in seen:
            seen.add(str(path))
            paths.append(path)
            if len(paths) >= max_files:
                break
    return paths


def tokenize(txt: str) -> set:
    return {w for w in re.findall(rf"[a-zA-Z0-9_]{{{TOKEN_MIN_LEN},}}", txt.lower()) if w not in STOPWORDS}


def jaccard(set_a: set, set_b: set) -> float:
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


# === INTEGRATE (UPDATE existing auto_learned SAU NEW) ===
def integrate_lesson(lesson: dict, llm_used: bool) -> tuple[Path | None, str]:
    """
    UPDATE existing auto_learned dacă similaritate ≥0.7 (cu guard `## [User]`).
    Altfel NEW. Backlink-ul e DEZACTIVAT (era feature creep).
    """
    rule = str(lesson.get("rule", ""))[:200]
    why = str(lesson.get("why", ""))[:200]
    how = str(lesson.get("how", ""))[:200]
    ptype = lesson.get("type", "reference")
    project = lesson.get("project")
    raw_slug = str(lesson.get("title_slug", "lesson"))
    slug = safe_slug(raw_slug)

    rule_tokens = tokenize(rule + " " + why)
    candidates = obs_search(rule, max_files=5)
    scored = []
    for cand in candidates:
        try:
            content = cand.read_text(encoding="utf-8", errors="ignore")[:3000]
        except OSError:
            continue
        scored.append((jaccard(rule_tokens, tokenize(content)), cand))
    scored.sort(reverse=True, key=lambda x: x[0])

    # UPDATE: doar pe fișiere proprii (auto_learned) și fără atingere `## [User]`
    if scored and scored[0][0] >= SIMILARITY_UPDATE_THRESHOLD:
        target = scored[0][1]
        fm, body = parse_frontmatter(target)
        if fm.get("auto_learned") and not _user_section_modified(body):
            new_version = int(fm.get("_version", 1)) + 1
            fm["_version"] = new_version
            fm["_modified"] = datetime.datetime.now().isoformat(timespec="seconds")
            fm["_modified_by"] = "claude_auto_learn"
            new_claude = (
                f"## [Claude]\n{rule}\n\n"
                f"**Why:** {why}\n"
                f"**How to apply:** {how}\n\n"
                f"_v{new_version} consolidat {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} "
                f"({'LLM' if llm_used else 'template'})_\n"
            )
            updated_body = update_claude_section(body, new_claude)
            write_with_frontmatter(target, fm, updated_body)
            return target, f"updated_v{new_version}"

    # NEW (routing per proiect)
    if project:
        target_dir = PROJECTS_DIR / project / "_MEMORY"
        scope = f"project:{project}"
    else:
        target_dir = OBS_MEM / "auto"
        scope = "global"
    target_dir.mkdir(parents=True, exist_ok=True)

    sig = hashlib.md5((rule + why).encode("utf-8", errors="ignore")).hexdigest()[:8]
    fname = target_dir / f"{ptype}_{slug}_{sig}.md"

    related = [p.stem for p, score in [(p, s) for s, p in scored if s >= 0.4][:3]]
    tags_raw = lesson.get("tags") or []
    if not isinstance(tags_raw, list):
        tags_raw = [str(tags_raw)]
    tags = ["auto-learned"] + [_normalize_tag(t) for t in tags_raw if t]
    if project:
        tags.append(_normalize_tag(project))
    tags = [t for t in dict.fromkeys(tags) if t][:6]

    now = datetime.datetime.now().isoformat(timespec="seconds")
    fm = {
        "name": fname.stem,
        "description": rule[:80],
        "type": ptype,
        "project": project or "workspace",
        "tags": tags,
        "priority": "medium",
        "scope": scope,
        "auto_learned": True,
        "auto_consolidated": True,
        "llm_used": llm_used,
        "_version": 1,
        "_created": now,
        "_modified": now,
        "_modified_by": "claude_auto_learn",
        "related": related,
    }
    body = build_body_protocol(rule, why, how)
    write_with_frontmatter(fname, fm, body)
    return fname, "new"


def _user_section_modified(body: str) -> bool:
    """Detect dacă `## [User]` are conținut non-placeholder."""
    if "## [User]" not in body:
        return False
    user_part = body.split("## [User]", 1)[1]
    # Strip placeholder-uri
    cleaned = re.sub(r"<!--.*?-->", "", user_part, flags=re.DOTALL).strip()
    return len(cleaned) > 0


# === MEMORY.md AUTO-INDEX (split per-project vs global) ===
AUTO_INDEX_HEADER = "### Auto-Learned (META-017)"
PER_PROJECT_INDEX_TEMPLATE = """## [Claude Index]

{header}
{entries}

## [User Index]
<!-- Note user — Claude nu scrie aici -->
"""


def _append_to_index_file(index_file: Path, entries_to_add: list) -> None:
    """Helper: append linii sub AUTO_INDEX_HEADER cu dedupe pe filename."""
    try:
        content = index_file.read_text(encoding="utf-8")
    except OSError:
        return

    marker = "## [Claude Index]"
    if marker not in content:
        return

    new_lines = []
    for path, _status in entries_to_add:
        rel = path.name
        if f"]({rel})" in content or f"[[{path.stem}]]" in content:
            continue
        new_lines.append(
            f"- [{path.stem}]({rel}) — auto-learned {datetime.datetime.now().strftime('%Y-%m-%d')}"
        )
    if not new_lines:
        return

    if AUTO_INDEX_HEADER in content:
        idx = content.find(AUTO_INDEX_HEADER)
        after_header = content.find("\n", idx) + 1
        next_section = content.find("\n### ", after_header)
        if next_section == -1:
            next_section = content.find("\n## [User Index]", after_header)
        if next_section == -1:
            next_section = len(content)
        block = "\n".join(new_lines) + "\n"
        content = content[:next_section].rstrip() + "\n" + block + content[next_section:]
    else:
        user_idx = content.find("\n## [User Index]")
        insertion = user_idx if user_idx != -1 else len(content)
        section = f"\n\n{AUTO_INDEX_HEADER}\n" + "\n".join(new_lines) + "\n"
        content = content[:insertion] + section + content[insertion:]

    try:
        index_file.write_text(content, encoding="utf-8")
    except OSError as exc:
        log(f"index_update_failed {index_file}: {exc}")


def _ensure_project_memory_index(project: str) -> Path:
    """Creează `PROJECTS/<project>/_MEMORY/MEMORY.md` dacă lipsește."""
    project_index = PROJECTS_DIR / project / "_MEMORY" / "MEMORY.md"
    if project_index.exists():
        return project_index
    project_index.parent.mkdir(parents=True, exist_ok=True)
    project_index.write_text(
        PER_PROJECT_INDEX_TEMPLATE.format(
            header=AUTO_INDEX_HEADER, entries="<!-- vid -->"
        ),
        encoding="utf-8",
    )
    return project_index


def update_memory_index(written: list) -> None:
    """
    Split routing:
    - Lecții per-proiect (path conține `PROJECTS/<N>/_MEMORY/`) → indexează în `PROJECTS/<N>/_MEMORY/MEMORY.md`
    - Lecții globale (`_MEMORY/auto/`) → indexează în global MEMORY.md (auto-memory + Obsidian)
    Dedupe pe filename, secțiune dedicată `### Auto-Learned (META-017)`.
    """
    if not written:
        return
    new_entries = [(p, s) for p, s in written if s == "new"]
    if not new_entries:
        return

    # Group per destination
    per_project: dict[str, list] = {}
    global_entries: list = []
    for path, status in new_entries:
        path_str = str(path).replace("\\", "/")
        proj_match = re.search(r"/PROJECTS/([^/]+)/_MEMORY/", path_str)
        if proj_match:
            per_project.setdefault(proj_match.group(1), []).append((path, status))
        else:
            global_entries.append((path, status))

    # Per-project: indexează în PROJECTS/<N>/_MEMORY/MEMORY.md (auto-create dacă lipsește)
    for project, entries in per_project.items():
        project_index = _ensure_project_memory_index(project)
        _append_to_index_file(project_index, entries)

    # Global: indexează în global MEMORY.md (auto-memory + Obsidian)
    if global_entries:
        for index_file in (MEMORY_INDEX_GLOBAL, MEMORY_INDEX_OBS):
            if index_file.exists():
                _append_to_index_file(index_file, global_entries)


# === DASHBOARD PING (1 line agregat) ===
def dashboard_ping(written: list, batch_size: int, llm_used: bool) -> None:
    if not DASHBOARD.exists() or not written:
        return
    try:
        badge = "🤖" if llm_used else "📋"
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        statuses = ", ".join(f"{s}:[[{p.stem}]]" for p, s in written[:5])
        line = f"\n- `{now}` {badge} **auto-learn** ({batch_size}→{len(written)}): {statuses}\n"
        with DASHBOARD.open("a", encoding="utf-8") as f:
            f.write(line)
    except OSError as exc:
        log(f"dashboard_ping_failed: {exc}")


# === MAIN ===
def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Force consolidate even below batch threshold")
    args = parser.parse_args()

    queue = queue_load()
    if not should_consolidate(len(queue), args.force):
        log(f"SKIP: queue={len(queue)} (not ready)")
        return 0

    log(f"START: {len(queue)} candidates, force={args.force}, llm={'yes' if ANTHROPIC_KEY else 'no'}")

    lessons = llm_merge_call(queue)
    llm_used = lessons is not None
    if not lessons:
        lessons = template_merge(queue)
        log(f"FALLBACK: template, {len(lessons)} lessons")
    else:
        log(f"LLM_OK: {len(lessons)} lessons")

    written = []
    for lesson in lessons:
        try:
            path, status = integrate_lesson(lesson, llm_used)
            if path:
                written.append((path, status))
                log(f"INTEGRATED [{status}]: {path}")
        except Exception as exc:
            log(f"integrate_error: {type(exc).__name__}: {exc}")

    update_memory_index(written)
    dashboard_ping(written, len(queue), llm_used)
    queue_clear()
    mark_consolidated()
    # Cleanup sentinel (anti-double-spawn în auto_learn.py)
    try:
        if CONSOLIDATE_SENTINEL.exists():
            CONSOLIDATE_SENTINEL.unlink()
    except OSError:
        pass
    log(f"DONE: {len(queue)} -> {len(written)} ({[s for _, s in written]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
