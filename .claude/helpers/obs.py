#!/usr/bin/env python3
"""
obs.py — Obsidian multi-vault CLI (zero-MCP, stdlib + PyYAML).

Workspace vault: <WORKSPACE_DIR>
Project vaults:  <WORKSPACE_DIR>/PROJECTS/<Name>/ (with own .obsidian/)
Registry:        <WORKSPACE_DIR>/_SETTINGS/vaults.json

Search target (--vault > --project > --workspace > --all > default workspace):
  obs.py search "x"                       # in workspace
  obs.py --project MyProject search "x"  # in vault MyProject
  obs.py --all search "x"                 # in all (workspace + projects)
  obs.py --vault "/path/to/vault" search "x"  # explicit path

Subcommands:
  search, list, read, fm, tags, replace, backlinks, links,
  link (bidirectional wikilink), vaults (registry), setup (wizard).

Usage examples:
  obs.py setup --auto
  obs.py vaults list
  obs.py --project MyProject list --recent 10
  obs.py --all search "swarm preset"
  obs.py link _MEMORY/feedback_xxx.md PROJECTS/MyProject/CLAUDE.md

Setup: Set WORKSPACE_DIR env var or edit DEFAULT_WORKSPACE below.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML missing. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

# Set WORKSPACE_DIR env variable or change this path to your workspace root
_env_ws = os.environ.get('WORKSPACE_DIR', '')
DEFAULT_WORKSPACE = Path(_env_ws) if _env_ws else Path(__file__).resolve().parent.parent.parent
REGISTRY_REL = Path("_SETTINGS") / "vaults.json"
IGNORE_DIRS = {
    ".git", ".obsidian", "node_modules", "_ARCHIVE", "_INBOX_ZIPS",
    "build", "dist", ".gradle", "__pycache__", ".venv", "venv",
    "_deferred", "_deferred_kotlin", "_deferred_temp", "exports",
    ".idea", ".vscode", ".claude",
    "_WORKSPACE",  # junction back to workspace — never recurse into it
}
FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:[#|][^\]]*)?\]\]")
MDLINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+\.md)(?:#[^)]*)?\)")


# ─── Vault registry ──────────────────────────────────────────────────────

def load_registry(workspace: Path) -> dict:
    cfg = workspace / REGISTRY_REL
    if cfg.exists():
        try:
            return json.loads(cfg.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"workspace": str(workspace), "projects": {}}


def save_registry(workspace: Path, reg: dict) -> Path:
    cfg = workspace / REGISTRY_REL
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text(json.dumps(reg, indent=2, ensure_ascii=False), encoding="utf-8")
    return cfg


def resolve_targets(args, default_workspace: Path) -> list[tuple[str, Path]]:
    """Return list of (label, path) vaults to operate on."""
    if getattr(args, "vault", None):
        p = Path(args.vault).resolve()
        return [(p.name or "vault", p)]
    reg = load_registry(default_workspace)
    workspace = Path(reg.get("workspace", default_workspace)).resolve()
    if getattr(args, "all", False):
        out: list[tuple[str, Path]] = [("workspace", workspace)]
        for name, p in reg.get("projects", {}).items():
            out.append((name, Path(p).resolve()))
        return out
    if getattr(args, "project", None):
        name = args.project
        projects = reg.get("projects", {})
        if name not in projects:
            raise SystemExit(
                f"Proiect necunoscut: {name!r}. "
                f"Existente: {list(projects)} (vezi `obs.py vaults list`)"
            )
        return [(name, Path(projects[name]).resolve())]
    return [("workspace", workspace)]


# ─── Note model ──────────────────────────────────────────────────────────

@dataclass
class Note:
    path: Path
    rel: str
    fm: dict[str, Any]
    body: str

    @property
    def tags(self) -> list[str]:
        t = self.fm.get("tags", [])
        if isinstance(t, str):
            return [s.strip() for s in re.split(r"[,\s]+", t) if s.strip()]
        if isinstance(t, list):
            return [str(x).strip() for x in t]
        return []


def is_ignored(p: Path, vault: Path) -> bool:
    try:
        rel_parts = p.relative_to(vault).parts
    except ValueError:
        return True
    return any(part in IGNORE_DIRS for part in rel_parts)


def iter_md(vault: Path, folder: str | None = None) -> Iterable[Path]:
    root = vault / folder if folder else vault
    if not root.exists():
        return
    for p in root.rglob("*.md"):
        if not is_ignored(p, vault):
            yield p


def parse_note(path: Path, vault: Path) -> Note:
    text = path.read_text(encoding="utf-8", errors="replace")
    fm: dict[str, Any] = {}
    body = text
    m = FM_RE.match(text)
    if m:
        try:
            data = yaml.safe_load(m.group(1)) or {}
            if isinstance(data, dict):
                fm = data
        except yaml.YAMLError:
            fm = {"_parse_error": True}
        body = text[m.end():]
    rel = str(path.relative_to(vault)).replace("\\", "/")
    return Note(path=path, rel=rel, fm=fm, body=body)


def write_note(note: Note) -> None:
    if note.fm:
        fm_text = yaml.safe_dump(
            note.fm, allow_unicode=True, sort_keys=False, default_flow_style=False
        ).rstrip()
        out = f"---\n{fm_text}\n---\n{note.body}"
    else:
        out = note.body
    note.path.write_text(out, encoding="utf-8")


def resolve(vault: Path, target: str) -> Path:
    p = Path(target)
    if p.is_absolute() and p.exists():
        return p
    cand = vault / target
    if cand.exists():
        return cand
    cand_md = vault / (target if target.endswith(".md") else target + ".md")
    if cand_md.exists():
        return cand_md
    matches = [
        x for x in vault.rglob(Path(target).name)
        if x.is_file() and not is_ignored(x, vault)
    ]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise SystemExit(
            f"Ambiguu: {len(matches)} potriviri pentru {target!r}:\n"
            + "\n".join(f"  {m.relative_to(vault)}" for m in matches[:10])
        )
    raise SystemExit(f"Negasit: {target!r} in {vault}")


def single_vault(targets: list[tuple[str, Path]], cmd: str) -> Path:
    if len(targets) != 1:
        raise SystemExit(
            f"`{cmd}` necesita un singur vault — foloseste --project NAME, "
            f"--workspace, sau --vault PATH (nu --all)."
        )
    return targets[0][1]


# ─── Comenzi: search / list (multi-vault) ────────────────────────────────

def cmd_search(args, targets: list[tuple[str, Path]]) -> int:
    pattern = re.compile(args.query, re.IGNORECASE if args.ignore_case else 0)
    tag_filter = args.tag.lower() if args.tag else None
    total_hits = 0
    for label, vault in targets:
        if not vault.is_dir():
            print(f"[{label}] vault does not exist: {vault}", file=sys.stderr)
            continue
        vault_hits = 0
        for path in iter_md(vault, args.in_folder):
            n = parse_note(path, vault)
            if tag_filter and tag_filter not in (t.lower() for t in n.tags):
                continue
            matches: list[tuple[int, str]] = []
            for i, line in enumerate(n.body.splitlines(), 1):
                if pattern.search(line):
                    matches.append((i, line.rstrip()))
                    if len(matches) >= args.max_per_file:
                        break
            if matches:
                vault_hits += 1
                total_hits += 1
                print(f"\n=== [{label}] {n.rel} ===")
                if n.fm.get("name"):
                    print(f"  name: {n.fm['name']}")
                if n.tags:
                    print(f"  tags: {', '.join(n.tags)}")
                for line_no, line in matches:
                    snippet = line if len(line) <= 200 else line[:197] + "..."
                    print(f"  L{line_no}: {snippet}")
                if total_hits >= args.max_files:
                    print(f"\n... stopped at {args.max_files} files.")
                    return 0
    if total_hits == 0:
        print("Niciun rezultat.")
        return 1
    return 0


def cmd_list(args, targets: list[tuple[str, Path]]) -> int:
    tag_filter = args.tag.lower() if args.tag else None
    rows: list[tuple[str, Path, Note, float]] = []
    for label, vault in targets:
        if not vault.is_dir():
            continue
        for path in iter_md(vault, args.folder):
            n = parse_note(path, vault)
            if tag_filter and tag_filter not in (t.lower() for t in n.tags):
                continue
            rows.append((label, path, n, path.stat().st_mtime))
    if args.recent:
        rows.sort(key=lambda r: r[3], reverse=True)
        rows = rows[: args.recent]
    else:
        rows.sort(key=lambda r: (r[0], r[2].rel))
    if args.json:
        out = [
            {
                "vault": label,
                "path": n.rel,
                "name": n.fm.get("name"),
                "type": n.fm.get("type"),
                "tags": n.tags,
                "mtime": int(mt),
            }
            for label, _p, n, mt in rows
        ]
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        for label, _p, n, _mt in rows:
            tag_part = f" [{','.join(n.tags)}]" if n.tags else ""
            name_part = f" — {n.fm['name']}" if n.fm.get("name") else ""
            print(f"[{label}] {n.rel}{tag_part}{name_part}")
        print(f"\n[{len(rows)} fisiere]")
    return 0


# ─── Comenzi: read / fm / tags / replace (single-vault) ──────────────────

def cmd_read(args, targets: list[tuple[str, Path]]) -> int:
    vault = single_vault(targets, "read")
    path = resolve(vault, args.path)
    n = parse_note(path, vault)
    if args.body_only:
        print(n.body)
        return 0
    if args.fm_only:
        print(json.dumps(n.fm, ensure_ascii=False, indent=2, default=str))
        return 0
    print(f"# {n.rel}")
    if n.fm:
        print("\n## frontmatter")
        print(json.dumps(n.fm, ensure_ascii=False, indent=2, default=str))
    print("\n## body")
    print(n.body)
    return 0


def cmd_fm(args, targets: list[tuple[str, Path]]) -> int:
    vault = single_vault(targets, "fm")
    path = resolve(vault, args.path)
    n = parse_note(path, vault)
    if args.action == "get":
        if args.key is None:
            print(json.dumps(n.fm, ensure_ascii=False, indent=2, default=str))
        else:
            v = n.fm.get(args.key)
            if v is None:
                print(f"(missing: {args.key})", file=sys.stderr)
                return 1
            print(json.dumps(v, ensure_ascii=False, default=str)
                  if not isinstance(v, str) else v)
        return 0
    if args.action == "set":
        if args.key is None or args.value is None:
            raise SystemExit("fm set necesita <key> <value>")
        new_val: Any = args.value
        try:
            parsed = yaml.safe_load(args.value)
            if parsed is not None:
                new_val = parsed
        except yaml.YAMLError:
            pass
        n.fm[args.key] = new_val
        write_note(n)
        print(f"OK: {args.key} = {new_val!r}")
        return 0
    if args.action == "del":
        if args.key is None:
            raise SystemExit("fm del necesita <key>")
        if args.key in n.fm:
            del n.fm[args.key]
            write_note(n)
            print(f"OK: deleted {args.key}")
            return 0
        print(f"(already missing: {args.key})")
        return 1
    raise SystemExit(f"actiune fm necunoscuta: {args.action}")


def cmd_tags(args, targets: list[tuple[str, Path]]) -> int:
    vault = single_vault(targets, "tags")
    path = resolve(vault, args.path)
    n = parse_note(path, vault)
    tags = n.tags
    if args.action == "list":
        for t in tags:
            print(t)
        return 0
    if args.tag is None:
        raise SystemExit(f"tags {args.action} necesita <tag>")
    if args.action == "add":
        if args.tag in tags:
            print(f"(already present: {args.tag})")
            return 0
        tags.append(args.tag)
        n.fm["tags"] = tags
        write_note(n)
        print(f"OK: + {args.tag}")
        return 0
    if args.action == "del":
        if args.tag not in tags:
            print(f"(lipsea: {args.tag})")
            return 1
        tags.remove(args.tag)
        n.fm["tags"] = tags
        write_note(n)
        print(f"OK: - {args.tag}")
        return 0
    raise SystemExit(f"actiune tags necunoscuta: {args.action}")


def cmd_replace(args, targets: list[tuple[str, Path]]) -> int:
    vault = single_vault(targets, "replace")
    path = resolve(vault, args.path)
    text = path.read_text(encoding="utf-8")
    if args.regex:
        pattern = re.compile(args.old, re.MULTILINE | (re.IGNORECASE if args.ignore_case else 0))
        new_text, count = pattern.subn(args.new, text)
    else:
        count = text.count(args.old)
        new_text = text.replace(args.old, args.new)
    if count == 0:
        print("(0 replacements — pattern not found)")
        return 1
    if args.dry_run:
        print(f"DRY: ar inlocui {count} aparitii in {path.relative_to(vault)}")
        return 0
    path.write_text(new_text, encoding="utf-8")
    print(f"OK: {count} inlocuiri in {path.relative_to(vault)}")
    return 0


# ─── Comenzi: backlinks / links / link ───────────────────────────────────

def cmd_backlinks(args, targets: list[tuple[str, Path]]) -> int:
    total = 0
    for label, vault in targets:
        if not vault.is_dir():
            continue
        try:
            target = resolve(vault, args.note)
        except SystemExit:
            continue
        target_rel = str(target.relative_to(vault)).replace("\\", "/")
        target_stem = target.stem
        target_name = target.name
        for path in iter_md(vault):
            if path == target:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            wikilinks = [m.group(1).strip() for m in WIKILINK_RE.finditer(text)]
            mdlinks = [m.group(1).strip() for m in MDLINK_RE.finditer(text)]
            matched_refs: list[str] = []
            for w in wikilinks:
                wl = w.split("/")[-1]
                if wl == target_stem or wl == target_name:
                    matched_refs.append(f"[[{w}]]")
            for ml in mdlinks:
                tail = ml.split("/")[-1].split("\\")[-1]
                if (tail == target_name or tail == target_stem + ".md"
                        or ml.endswith(target_rel)):
                    matched_refs.append(f"({ml})")
            if matched_refs:
                rel = str(path.relative_to(vault)).replace("\\", "/")
                print(f"[{label}] {rel}: {' '.join(matched_refs[:5])}")
                total += 1
    if total == 0:
        print("(zero backlinks)")
        return 1
    print(f"\n[{total} fisiere]")
    return 0


def cmd_links(args, targets: list[tuple[str, Path]]) -> int:
    vault = single_vault(targets, "links")
    path = resolve(vault, args.path)
    text = path.read_text(encoding="utf-8")
    wiki = sorted({m.group(1).strip() for m in WIKILINK_RE.finditer(text)})
    md = sorted({m.group(1).strip() for m in MDLINK_RE.finditer(text)})
    print("Wikilinks:")
    for w in wiki:
        print(f"  [[{w}]]")
    print("\nMD links:")
    for m in md:
        print(f"  {m}")
    return 0


RELATED_HEADER = "## Related (auto)"


def _add_link_to_note(path: Path, link_text: str, source_label: str) -> bool:
    text = path.read_text(encoding="utf-8")
    if link_text in text:
        return False
    if RELATED_HEADER in text:
        text = re.sub(
            re.escape(RELATED_HEADER) + r"(.*?)(?=\n##|\Z)",
            lambda m: m.group(0).rstrip() + f"\n- {link_text} ← {source_label}\n",
            text, count=1, flags=re.DOTALL,
        )
    else:
        sep = "\n" if text.endswith("\n") else "\n\n"
        text = text.rstrip() + f"\n\n---\n\n{RELATED_HEADER}\n\n- {link_text} ← {source_label}\n"
    path.write_text(text, encoding="utf-8")
    return True


def cmd_link(args, targets: list[tuple[str, Path]]) -> int:
    vault = single_vault(targets, "link")
    a = resolve(vault, args.path_a)
    b = resolve(vault, args.path_b)
    if a == b:
        raise SystemExit("link: cele doua note sunt identice")
    a_link = f"[[{a.stem}]]"
    b_link = f"[[{b.stem}]]"
    a_changed = _add_link_to_note(a, b_link, "obs.py link")
    b_changed = _add_link_to_note(b, a_link, "obs.py link")
    if a_changed:
        print(f"OK: {a.relative_to(vault)} ← {b_link}")
    else:
        print(f"(already had link: {a.relative_to(vault)})")
    if b_changed:
        print(f"OK: {b.relative_to(vault)} ← {a_link}")
    else:
        print(f"(already had link: {b.relative_to(vault)})")
    return 0


# ─── Comenzi: vaults / setup ─────────────────────────────────────────────

def cmd_vaults(args, default_workspace: Path) -> int:
    workspace = default_workspace
    reg = load_registry(workspace)
    if args.action == "list":
        ws = reg.get("workspace", str(workspace))
        print(f"workspace: {ws}")
        print(f"latest_config_version: v{reg.get('latest_config_version', '?')}")
        projs = reg.get("projects", {})
        if projs:
            print(f"projects ({len(projs)}):")
            for name, info in sorted(projs.items()):
                if isinstance(info, str):
                    p, ver = info, "?"
                else:
                    p, ver = info.get("path", "?"), info.get("config_version", "?")
                exists = "OK" if Path(p).is_dir() else "MISSING"
                print(f"  {name:20s}  [{exists}]  v{ver}  {p}")
        else:
            print("projects: (none)")
        return 0
    if args.action == "status":
        latest = reg.get("latest_config_version", LATEST_CONFIG_VERSION)
        print(f"Schema target: v{latest}\n")
        for name, info in sorted(reg.get("projects", {}).items()):
            if isinstance(info, str):
                info = {"path": info, "config_version": 0}
            p = Path(info.get("path", ""))
            ver = info.get("config_version", 0)
            up_to_date = "✓" if ver >= latest else f"behind (v{ver})"
            features = info.get("features", {})
            stats = info.get("stats", {})
            print(f"=== {name} ===")
            print(f"  path: {p}")
            print(f"  version: v{ver} ({up_to_date})")
            print(f"  features: {', '.join(k for k,v in features.items() if v) or '(none)'}")
            if stats:
                print(f"  stats: {stats}")
            if info.get("configured_at"):
                print(f"  configured_at: {info['configured_at']}")
            if info.get("last_refresh"):
                print(f"  last_refresh: {info['last_refresh']}")
            steps = info.get("steps", [])[-3:]
            if steps:
                print(f"  recent steps: {steps}")
            print()
        hist = reg.get("history", [])
        if hist:
            print(f"--- history (ultimele {min(5, len(hist))} runs) ---")
            for h in hist[-5:]:
                summ = h.get("summary", [])
                changed = sum(1 for s in summ if s.get("from") != s.get("to"))
                print(f"  {h.get('ts')} schema=v{h.get('schema')} "
                      f"projects={len(summ)} upgraded={changed}")
        return 0
    if args.action == "add":
        if not args.name or not args.path:
            raise SystemExit("vaults add necesita <name> <path>")
        path = Path(args.path).resolve()
        if not path.is_dir():
            raise SystemExit(f"path inexistent: {path}")
        reg.setdefault("projects", {})[args.name] = str(path)
        save_registry(workspace, reg)
        print(f"OK: + {args.name} → {path}")
        return 0
    if args.action == "remove":
        if not args.name:
            raise SystemExit("vaults remove necesita <name>")
        if args.name in reg.get("projects", {}):
            del reg["projects"][args.name]
            save_registry(workspace, reg)
            print(f"OK: - {args.name}")
            return 0
        print(f"(lipsea: {args.name})")
        return 1
    raise SystemExit(f"actiune vaults necunoscuta: {args.action}")


# ─── Self-evolving wizard ────────────────────────────────────────────────
#
# PRINCIPIU: Obsidian + obs.py = ECONOMIE de tokeni, nu bloat. Conexiunile
# stau in vault (graph view, backlinks). Claude le acceseaza on-demand via
# obs.py. NU se injecteaza in prompturi (CLAUDE.md/MEMORY.md raman lean).
#
# Generatii de configuratie. Fiecare run aplica upgrade-uri in lant.
# config_version per proiect → wizardul stie ce sa adauge.
#
# v1: .obsidian/ minimal config + register
# v2: + junction _WORKSPACE catre workspace root
# v3: + _INDEX_MEMORY.md generat (regenerat la fiecare run cand apar
#      memory-uri noi cu project:<acest proiect>) — DOAR pentru navigatie
#      in Obsidian, NU citita de Claude in prompt.

LATEST_CONFIG_VERSION = 3


def _make_obsidian_config(obs_dir: Path, vault_name: str) -> None:
    obs_dir.mkdir(exist_ok=True)
    (obs_dir / "app.json").write_text(
        json.dumps({"alwaysUpdateLinks": True, "newLinkFormat": "shortest"}, indent=2),
        encoding="utf-8",
    )
    (obs_dir / "appearance.json").write_text(
        json.dumps({"baseFontSize": 16, "showInlineTitle": True}, indent=2),
        encoding="utf-8",
    )
    (obs_dir / "core-plugins.json").write_text(
        json.dumps([
            "file-explorer", "global-search", "switcher", "graph",
            "backlink", "tag-pane", "outline", "page-preview",
            "templates", "note-composer", "command-palette",
        ], indent=2),
        encoding="utf-8",
    )


def _create_junction(target: Path, source: Path) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(target), str(source)],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        return False, (result.stderr or result.stdout).strip()
    except Exception as e:
        return False, str(e)


def _registry_key(folder_name: str) -> str:
    return re.sub(r"\s+", "", folder_name)


def _project_aliases(folder_name: str, key: str) -> set[str]:
    """Aliasuri folosite pentru a matchui frontmatter `project:` la un proiect."""
    aliases = {key, folder_name, folder_name.replace(" ", ""),
               folder_name.replace(" ", "_"), folder_name.lower(),
               key.lower()}
    # Special frontmatter convention mappings (e.g. proj:MyApp in memory)
    # Add project-specific shortcuts here (project folder name → aliases)
    SHORTCUTS = {
        # "MyProject": ["MyProject", "myproj"],
    }
    if key in SHORTCUTS:
        aliases.update(SHORTCUTS[key])
    return {a.lower() for a in aliases}


def _find_project_memory_notes(workspace: Path, aliases: set[str]) -> list[Note]:
    mem_dir = workspace / "_MEMORY"
    if not mem_dir.is_dir():
        return []
    out: list[Note] = []
    for path in iter_md(mem_dir):
        try:
            n = parse_note(path, workspace)
        except Exception:
            continue
        proj = n.fm.get("project")
        if proj is None:
            continue
        if isinstance(proj, list):
            proj_vals = [str(x).lower() for x in proj]
        else:
            proj_vals = [str(proj).lower()]
        if any(p in aliases for p in proj_vals):
            out.append(n)
    return out


def _generate_memory_index(proj_dir: Path, workspace: Path,
                           project_name: str, key: str) -> tuple[int, bool]:
    """v3: scrie _INDEX_MEMORY.md cu memory notes relevante pentru proiect."""
    aliases = _project_aliases(project_name, key)
    notes = _find_project_memory_notes(workspace, aliases)
    notes.sort(key=lambda n: (n.fm.get("priority") != "critical",
                              n.fm.get("type", "z"), n.rel))
    index_path = proj_dir / "_INDEX_MEMORY.md"

    lines = [
        "---",
        f"name: Index Memory — {project_name}",
        "description: Auto-generated. Memory notes cu `project:` matching acest proiect.",
        "type: index",
        "auto_generated: true",
        f"project: {key}",
        "---",
        "",
        f"# Index Memory — {project_name}",
        "",
        f"> Auto-generat de `obs.py setup`. {len(notes)} memory notes.",
        f"> Sursa: `_WORKSPACE/_MEMORY/` (junction).",
        "",
    ]
    by_type: dict[str, list[Note]] = {}
    for n in notes:
        by_type.setdefault(str(n.fm.get("type", "other")), []).append(n)
    for t in sorted(by_type):
        lines.append(f"## {t}")
        lines.append("")
        for n in by_type[t]:
            title = n.fm.get("name", n.path.stem)
            tags = n.tags
            tag_part = f"  `[{','.join(tags)}]`" if tags else ""
            link = f"_WORKSPACE/_MEMORY/{n.path.name}"
            lines.append(f"- [[{n.path.stem}|{title}]]{tag_part}")
            lines.append(f"  - path: `{link}`")
        lines.append("")

    new_content = "\n".join(lines)
    changed = True
    if index_path.exists():
        old = index_path.read_text(encoding="utf-8")
        if old == new_content:
            changed = False
    if changed:
        index_path.write_text(new_content, encoding="utf-8")
    return len(notes), changed


MEMREF_HEADER = "## Memory References (auto)"


def _add_memory_refs_to_claude(proj_dir: Path, project_name: str,
                                workspace: Path, key: str) -> tuple[int, bool]:
    """v4: insereaza/actualizeaza sectiunea Memory References in CLAUDE.md."""
    claude_md = proj_dir / "CLAUDE.md"
    if not claude_md.exists():
        return 0, False
    aliases = _project_aliases(project_name, key)
    notes = _find_project_memory_notes(workspace, aliases)
    if not notes:
        return 0, False
    notes.sort(key=lambda n: (n.fm.get("priority") != "critical", n.rel))
    text = claude_md.read_text(encoding="utf-8")
    block = [MEMREF_HEADER, "",
             "> Auto-generat din `_MEMORY/` cu `project:` matching. "
             "Vezi si `_INDEX_MEMORY.md`."
             "", ""]
    for n in notes[:30]:
        title = n.fm.get("name", n.path.stem)
        block.append(f"- [[{n.path.stem}|{title}]]")
    block_text = "\n".join(block).rstrip() + "\n"

    if MEMREF_HEADER in text:
        new_text = re.sub(
            re.escape(MEMREF_HEADER) + r".*?(?=\n## |\Z)",
            block_text,
            text, count=1, flags=re.DOTALL,
        )
    else:
        new_text = text.rstrip() + "\n\n---\n\n" + block_text

    changed = new_text != text
    if changed:
        claude_md.write_text(new_text, encoding="utf-8")
    return len(notes), changed


# ─── Upgrade steps ───────────────────────────────────────────────────────

def _upgrade_v1(proj_dir: Path, workspace: Path, key: str,
                meta: dict) -> dict:
    """v1: .obsidian/ + register."""
    obs_dir = proj_dir / ".obsidian"
    if not obs_dir.is_dir():
        _make_obsidian_config(obs_dir, proj_dir.name)
        meta.setdefault("steps", []).append("v1: created .obsidian/")
    else:
        meta.setdefault("steps", []).append("v1: .obsidian/ already present")
    meta["features"] = {**meta.get("features", {}), "obsidian": True}
    return meta


def _upgrade_v2(proj_dir: Path, workspace: Path, key: str,
                meta: dict) -> dict:
    """v2: _WORKSPACE junction."""
    ws_link = proj_dir / "_WORKSPACE"
    if not (ws_link.exists() or ws_link.is_symlink()):
        ok, msg = _create_junction(ws_link, workspace)
        if ok:
            meta.setdefault("steps", []).append("v2: junction _WORKSPACE created")
        else:
            meta.setdefault("steps", []).append(f"v2: junction FAIL ({msg[:60]})")
            meta["features"] = {**meta.get("features", {}), "workspace_junction": False}
            return meta
    else:
        meta.setdefault("steps", []).append("v2: _WORKSPACE already present")
    meta["features"] = {**meta.get("features", {}), "workspace_junction": True}
    return meta


def _upgrade_v3(proj_dir: Path, workspace: Path, key: str,
                meta: dict) -> dict:
    """v3: _INDEX_MEMORY.md (regenerat)."""
    n_notes, changed = _generate_memory_index(proj_dir, workspace,
                                              proj_dir.name, key)
    label = "regenerated" if changed else "no changes"
    meta.setdefault("steps", []).append(
        f"v3: _INDEX_MEMORY.md ({n_notes} notes, {label})"
    )
    meta["features"] = {**meta.get("features", {}), "memory_index": True}
    meta.setdefault("stats", {})["memory_notes_linked"] = n_notes
    return meta


def _upgrade_v4(proj_dir: Path, workspace: Path, key: str,
                meta: dict) -> dict:
    """v4: Memory References section in CLAUDE.md."""
    n_refs, changed = _add_memory_refs_to_claude(proj_dir, proj_dir.name,
                                                  workspace, key)
    if n_refs == 0:
        meta.setdefault("steps", []).append("v4: skipped (no project memory notes)")
        return meta
    label = "added/updated" if changed else "unchanged"
    meta.setdefault("steps", []).append(
        f"v4: CLAUDE.md memory refs ({n_refs} links, {label})"
    )
    meta["features"] = {**meta.get("features", {}), "claude_memory_refs": True}
    return meta


UPGRADE_STEPS = [
    (1, "obsidian-config", _upgrade_v1),
    (2, "workspace-junction", _upgrade_v2),
    (3, "memory-index", _upgrade_v3),
    # v4 (claude-memory-refs) eliminat: bloat in prompt CLAUDE.md → contrar economiei.
]


def cmd_setup(args, default_workspace: Path) -> int:
    workspace = default_workspace
    projects_dir = workspace / "PROJECTS"
    if not projects_dir.is_dir():
        raise SystemExit(f"PROJECTS/ inexistent in {workspace}")

    reg = load_registry(workspace)
    reg["workspace"] = str(workspace)
    reg["latest_config_version"] = LATEST_CONFIG_VERSION
    reg.setdefault("projects", {})
    reg.setdefault("history", [])

    # Migrate legacy: projects[name] = string path → object
    for k, v in list(reg["projects"].items()):
        if isinstance(v, str):
            reg["projects"][k] = {"path": v, "config_version": 0}

    found = sorted([p for p in projects_dir.iterdir() if p.is_dir()])
    auto = args.auto
    print(f"Workspace: {workspace}")
    print(f"Proiecte detectate: {len(found)}")
    print(f"Schema target: v{LATEST_CONFIG_VERSION}\n")

    from datetime import datetime
    run_ts = datetime.now().isoformat(timespec="seconds")
    run_summary: list[dict] = []

    for proj_dir in found:
        name = proj_dir.name
        key = _registry_key(name)
        existing = reg["projects"].get(key, {"path": str(proj_dir),
                                              "config_version": 0})
        cur_ver = existing.get("config_version", 0)
        target_ver = LATEST_CONFIG_VERSION

        print(f"--- {name} (v{cur_ver} → v{target_ver}) ---")
        if cur_ver >= target_ver:
            print(f"  · already up to date (v{cur_ver})")
            # Even at latest, refresh dynamic content (memory index)
            if auto or _ask_yes(f"  refresh dynamic content (memory index)?"):
                _upgrade_v3(proj_dir, workspace, key, existing)
                _upgrade_v4(proj_dir, workspace, key, existing)
            existing["last_refresh"] = run_ts
            reg["projects"][key] = existing
            run_summary.append({"project": key, "from": cur_ver,
                                 "to": cur_ver, "refreshed": True})
            print()
            continue

        if not auto and not _ask_yes(f"  upgrade {name} v{cur_ver} → v{target_ver}?"):
            print("  skip\n")
            continue

        existing["path"] = str(proj_dir)
        existing.setdefault("steps", [])
        for ver, step_name, fn in UPGRADE_STEPS:
            if cur_ver < ver <= target_ver:
                print(f"  → applying v{ver}: {step_name}")
                existing = fn(proj_dir, workspace, key, existing)
        existing["config_version"] = target_ver
        existing["configured_at"] = run_ts
        reg["projects"][key] = existing
        run_summary.append({"project": key, "from": cur_ver, "to": target_ver,
                             "steps": existing.get("steps", [])[-5:]})
        for s in existing.get("steps", [])[-5:]:
            print(f"    {s}")
        print()

    reg["history"].append({
        "ts": run_ts,
        "schema": LATEST_CONFIG_VERSION,
        "summary": run_summary,
    })
    # Cap history to last 20 runs
    reg["history"] = reg["history"][-20:]
    save_registry(workspace, reg)
    print(f"Run saved: {workspace / REGISTRY_REL}")
    print(f"Total proiecte procesate: {len(run_summary)}")
    return 0


def _ask_yes(prompt: str) -> bool:
    try:
        ans = input(f"{prompt} [Y/n]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return False
    return ans in ("", "y", "yes")


# ─── Audit: redundante + token cost ──────────────────────────────────────

def _approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def _claude_md_chain(workspace: Path) -> list[Path]:
    """Fisiere care intra in prompt la session start (root + MEMORY.md)."""
    out: list[Path] = []
    for rel in ("CLAUDE.md", "BEST_PRACTICES.md", "_MEMORY/MEMORY.md"):
        p = workspace / rel
        if p.exists():
            out.append(p)
    return out


def cmd_audit(args, default_workspace: Path) -> int:
    workspace = default_workspace
    mem_dir = workspace / "_MEMORY"

    print(f"=== AUDIT vault: {workspace} ===\n")

    # 1. Token cost al fisierelor auto-loaded
    print("[1] Token cost — files auto-loaded at session start:")
    total_auto = 0
    for p in _claude_md_chain(workspace):
        text = p.read_text(encoding="utf-8", errors="replace")
        tk = _approx_tokens(text)
        total_auto += tk
        rel = p.relative_to(workspace)
        warn = " ⚠ MARE" if tk > 4000 else ""
        print(f"  {tk:>6} tk  {rel}{warn}")
    print(f"  {total_auto:>6} tk  TOTAL auto-loaded")
    print()

    # 2. Memory notes — count + tag/project breakdown
    if mem_dir.is_dir():
        notes = []
        for path in iter_md(mem_dir):
            try:
                notes.append(parse_note(path, workspace))
            except Exception:
                pass
        print(f"[2] _MEMORY/: {len(notes)} note-uri")
        no_proj = [n for n in notes if not n.fm.get("project")]
        no_type = [n for n in notes if not n.fm.get("type")]
        no_tags = [n for n in notes if not n.tags]
        print(f"  without project:  {len(no_proj)}")
        print(f"  without type:     {len(no_type)}")
        print(f"  without tags:     {len(no_tags)}")

        # Duplicate names
        by_name: dict[str, list[Note]] = {}
        for n in notes:
            nm = str(n.fm.get("name", "")).strip().lower()
            if nm:
                by_name.setdefault(nm, []).append(n)
        dups = {k: v for k, v in by_name.items() if len(v) > 1}
        if dups:
            print(f"\n  ⚠ Duplicate names ({len(dups)}):")
            for nm, notes_list in list(dups.items())[:10]:
                print(f"    '{nm}'")
                for n in notes_list:
                    print(f"      - {n.rel}")
        print()

        # 3. Broken refs in MEMORY.md
        memory_index = workspace / "_MEMORY" / "MEMORY.md"
        if memory_index.exists():
            text = memory_index.read_text(encoding="utf-8")
            mdlinks = MDLINK_RE.findall(text)
            broken = []
            for link in mdlinks:
                target = (memory_index.parent / link).resolve()
                if not target.exists():
                    broken.append(link)
            print(f"[3] MEMORY.md: {len(mdlinks)} linkuri, "
                  f"{len(broken)} broken")
            for b in broken[:10]:
                print(f"    ✗ {b}")
            print()

        # 4. Memory notes nelinkuite din MEMORY.md
        if memory_index.exists():
            indexed = set()
            for link in MDLINK_RE.findall(memory_index.read_text(encoding="utf-8")):
                indexed.add(Path(link).name)
            unindexed = [n for n in notes
                         if n.path.name not in indexed
                         and n.path.name != "MEMORY.md"]
            print(f"[4] Note-uri NEINDEXATE in MEMORY.md: {len(unindexed)}")
            for n in unindexed[:10]:
                print(f"    - {n.rel}")
            if len(unindexed) > 10:
                print(f"    ... +{len(unindexed)-10} more")
            print()

        # 5. Auto-generated indexes
        auto_indexes = [n for n in notes if n.fm.get("auto_generated")]
        if auto_indexes:
            print(f"[5] Auto-generated indexes: {len(auto_indexes)}")
            for n in auto_indexes[:10]:
                print(f"    {n.rel}")
            print()

    # 6. Sumar recomandari
    print("=== RECOMANDARI ===")
    if total_auto > 8000:
        print(f"  ⚠ Auto-load = {total_auto} tk > 8000 — slim CLAUDE.md/MEMORY.md")
    else:
        print(f"  ✓ Auto-load = {total_auto} tk (lean)")
    if mem_dir.is_dir() and no_proj:
        print(f"  ⚠ {len(no_proj)} memory notes without `project:` — add it so they appear in _INDEX_MEMORY")
    if mem_dir.is_dir() and dups:
        print(f"  ⚠ {len(dups)} name duplicates — consolidate")
    return 0


# ─── Main ────────────────────────────────────────────────────────────────

def main() -> int:
    p = argparse.ArgumentParser(prog="obs", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--vault", type=Path, help="Vault path explicit (override registry)")
    target = p.add_mutually_exclusive_group()
    target.add_argument("--project", help="Numele proiectului (din registry)")
    target.add_argument("--workspace", action="store_true", help="Forteaza workspace vault")
    target.add_argument("--all", action="store_true", help="Toate vault-urile (workspace + proiecte)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("search", help="Search content + frontmatter (multi-vault)")
    sp.add_argument("query")
    sp.add_argument("--tag")
    sp.add_argument("--in", dest="in_folder")
    sp.add_argument("-i", "--ignore-case", action="store_true")
    sp.add_argument("--max-files", type=int, default=50)
    sp.add_argument("--max-per-file", type=int, default=5)

    lp = sub.add_parser("list", help="List notes (multi-vault)")
    lp.add_argument("--tag")
    lp.add_argument("--folder")
    lp.add_argument("--recent", type=int)
    lp.add_argument("--json", action="store_true")

    rp = sub.add_parser("read", help="Read note (frontmatter parsed)")
    rp.add_argument("path")
    rp.add_argument("--body-only", action="store_true")
    rp.add_argument("--fm-only", action="store_true")

    fp = sub.add_parser("fm", help="Manage frontmatter")
    fp.add_argument("path")
    fp.add_argument("action", choices=["get", "set", "del"])
    fp.add_argument("key", nargs="?")
    fp.add_argument("value", nargs="?")

    tp = sub.add_parser("tags", help="Manage tags array")
    tp.add_argument("path")
    tp.add_argument("action", choices=["add", "del", "list"])
    tp.add_argument("tag", nargs="?")

    rep = sub.add_parser("replace", help="Search-replace in single note")
    rep.add_argument("path")
    rep.add_argument("old")
    rep.add_argument("new")
    rep.add_argument("--regex", action="store_true")
    rep.add_argument("-i", "--ignore-case", action="store_true")
    rep.add_argument("--dry-run", action="store_true")

    bp = sub.add_parser("backlinks", help="Find notes linking to target (multi-vault)")
    bp.add_argument("note")

    lkp = sub.add_parser("links", help="List outgoing links from note")
    lkp.add_argument("path")

    lnp = sub.add_parser("link", help="Bidirectional wikilink between two notes (single vault)")
    lnp.add_argument("path_a")
    lnp.add_argument("path_b")

    vp = sub.add_parser("vaults", help="Manage vault registry")
    vp.add_argument("action", choices=["list", "status", "add", "remove"])
    vp.add_argument("name", nargs="?")
    vp.add_argument("path", nargs="?")

    stp = sub.add_parser("setup", help="Interactive setup wizard for project vaults")
    stp.add_argument("--auto", action="store_true", help="Non-interactiv (configureaza tot)")

    aup = sub.add_parser("audit", help="Audit redundante + token cost")

    args = p.parse_args()
    workspace = (args.vault.resolve() if args.vault else DEFAULT_WORKSPACE).resolve()
    if args.cmd in ("vaults", "setup", "audit"):
        ws = (args.vault.resolve() if args.vault else DEFAULT_WORKSPACE)
        if not ws.is_dir():
            print(f"ERROR: workspace does not exist: {ws}", file=sys.stderr)
            return 2
        return {"vaults": cmd_vaults, "setup": cmd_setup,
                "audit": cmd_audit}[args.cmd](args, ws)

    targets = resolve_targets(args, DEFAULT_WORKSPACE)
    handler = {
        "search": cmd_search,
        "list": cmd_list,
        "read": cmd_read,
        "fm": cmd_fm,
        "tags": cmd_tags,
        "replace": cmd_replace,
        "backlinks": cmd_backlinks,
        "links": cmd_links,
        "link": cmd_link,
    }[args.cmd]
    return handler(args, targets)


if __name__ == "__main__":
    sys.exit(main())
