#!/usr/bin/env python3
"""
Obsidian Session Context Injector

At SessionStart:
  1. Detects active project from cwd or recently modified files
  2. Writes session-critical-index.json (index for agents)
  3. Injects SLIM summary + hint targeted at the active project

Setup: Set WORKSPACE_DIR environment variable or edit WORKSPACE below.
KNOWN_PROJECTS: Add your project slugs here to enable auto-detection.
"""
import os
import re
import sys
import json
import time

# ── CONFIGURE PATHS ──────────────────────────────────────────────────────────
_script_dir = os.path.dirname(os.path.abspath(__file__))
WORKSPACE   = os.environ.get('WORKSPACE_DIR', os.path.normpath(os.path.join(_script_dir, '..', '..')))

MEMORY_DIR   = os.path.join(WORKSPACE, '_MEMORY')
INDEX_PATH   = os.path.join(WORKSPACE, '.claude-flow', 'data', 'session-critical-index.json')
PROJECTS_DIR = os.path.join(WORKSPACE, 'PROJECTS')

# ── KNOWN PROJECTS ────────────────────────────────────────────────────────────
# Add your projects here: slug (lowercase) → obs.py search tag
# Example:
#   "myapp":    "project:MyApp",
#   "my app":   "project:MyApp",
KNOWN_PROJECTS = {
    "consiliu": "project:Consiliu",
}

def detect_active_project():
    """
    Detects active project in priority order:
    1. CLAUDE_PROJECT env variable (set by hook if available)
    2. Current cwd contains PROJECTS/<Name>/
    3. Most recently modified file in PROJECTS/ (last 2 hours)
    Returns (project_name, obs_query) or (None, None)
    """
    # 1. Explicit env var
    env_proj = os.environ.get('CLAUDE_PROJECT', '').strip().lower()
    if env_proj and env_proj in KNOWN_PROJECTS:
        return env_proj, KNOWN_PROJECTS[env_proj]

    # 2. cwd contains PROJECTS/<Name>
    cwd = os.getcwd().replace('\\', '/').lower()
    if 'projects/' in cwd:
        after = cwd.split('projects/')[1]
        project_slug = after.split('/')[0].replace(' ', '').lower()
        for key, val in KNOWN_PROJECTS.items():
            if project_slug.startswith(key.replace(' ', '')):
                return key, val

    # 3. Recently modified file in PROJECTS/ (last 2 hours = 7200s)
    if os.path.isdir(PROJECTS_DIR):
        now = time.time()
        best = None
        best_mtime = 0
        for proj_name in os.listdir(PROJECTS_DIR):
            proj_path = os.path.join(PROJECTS_DIR, proj_name)
            if not os.path.isdir(proj_path):
                continue
            for root, dirs, files in os.walk(proj_path):
                dirs[:] = [d for d in dirs if not d.startswith('.')][:3]
                for fname in files:
                    if not fname.endswith(('.md', '.kt', '.py', '.js', '.ts', '.json')):
                        continue
                    fpath = os.path.join(root, fname)
                    try:
                        mtime = os.path.getmtime(fpath)
                        if mtime > best_mtime and (now - mtime) < 7200:
                            best_mtime = mtime
                            best = proj_name
                    except Exception:
                        pass
        if best:
            slug = best.lower().replace(' ', '')
            for key, val in KNOWN_PROJECTS.items():
                if slug.startswith(key.replace(' ', '')):
                    return best, val
            # Unknown project — use folder name directly
            return best, f"project:{best.replace(' ', '')}"

    return None, None


def parse_frontmatter(content):
    if not content.startswith("---"):
        return {}
    end = content.find("\n---", 3)
    if end == -1:
        return {}
    fm = {}
    for line in content[3:end].splitlines():
        m = re.match(r'^(\w+):\s*(.+)', line.strip())
        if m:
            fm[m.group(1)] = m.group(2).strip()
    return fm

def load_critical_files():
    entries = []
    try:
        for fname in sorted(os.listdir(MEMORY_DIR)):
            if not fname.endswith(".md") or fname == "MEMORY.md":
                continue
            fpath = os.path.join(MEMORY_DIR, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
                fm = parse_frontmatter(content)
                if fm.get("priority") != "critical":
                    continue
                end = content.find("\n---", 3)
                body = content[end + 4:].strip() if end != -1 else content.strip()
                compact_lines = [l for l in body.splitlines() if l.strip()][:3]
                compact = " | ".join(compact_lines)[:300]
                tags_raw = fm.get("tags", "")
                tags = re.findall(r'[\w-]+', tags_raw)
                entries.append({
                    "name": fm.get("name", fname),
                    "tags": tags,
                    "priority": fm.get("priority", "normal"),
                    "project": fm.get("project", "workspace"),
                    "body": body,
                    "compact": compact,
                    "file": fname,
                })
            except Exception:
                continue
    except Exception as e:
        print(f"[obsidian-context] ERROR loading files: {e}", file=sys.stderr)
    return entries

def write_index(entries):
    """Write session-critical-index.json organized by project and tags."""
    by_project = {}
    by_tag = {}
    for e in entries:
        # Include tags and priority so SSA can correctly pin critical memories.
        # Without these fields, ssa.cjs loadObsidianEntries() saw every pinned
        # check fall through to false → critical entries silently dropped.
        compact_record = {
            "name": e["name"],
            "compact": e["compact"],
            "file": e["file"],
            "tags": e.get("tags", []),
            "priority": e.get("priority", "normal"),
        }
        p = e["project"]
        if p not in by_project:
            by_project[p] = []
        by_project[p].append(compact_record)
        for t in e["tags"]:
            if t not in by_tag:
                by_tag[t] = []
            by_tag[t].append(compact_record)

    all_entries = [e for proj in by_project.values() for e in proj]
    index = {
        "generated": __import__('datetime').datetime.now().isoformat(),
        "total": len(entries),
        "memory_dir": MEMORY_DIR,
        "by_project": by_project,
        "by_tag": by_tag,
        "all": all_entries,
    }
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

def main():
    entries = load_critical_files()
    if not entries:
        print("[obsidian-context] No critical entries found.", file=sys.stderr)
        return

    try:
        write_index(entries)
    except Exception as e:
        print(f"[obsidian-context] Index write failed (non-critical): {e}", file=sys.stderr)

    projects = sorted({e['project'] for e in entries if e.get('project') and e['project'] != 'workspace-meta'})
    active_proj, obs_query = detect_active_project()

    lines = [
        f"[Obsidian] {len(entries)} critical memories indexed. Projects: {', '.join(projects) or 'all'}.",
        f"On-demand: python .claude/helpers/obs.py search \"<query>\"",
        f"Agent index: {INDEX_PATH}",
    ]
    if active_proj and obs_query:
        lines.append(f"[Active project detected: {active_proj}] → obs.py search \"{obs_query}\"")

    print("\n".join(lines))

if __name__ == "__main__":
    main()
