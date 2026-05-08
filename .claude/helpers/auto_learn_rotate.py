#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
auto_learn_rotate.py — META-017 v3.1 Lunar rotator pentru auto-learned files.

Sarcina:
  1. Scanează `_MEMORY/auto/` + `PROJECTS/<N>/_MEMORY/` pentru fișiere `auto_learned: true`
  2. Identifică candidate vechi (>RETENTION_DAYS) cu confidence scăzut (`_version=1` și fără update)
  3. Merge similare semantic în 1 fișier consolidat
  4. Arhivează low-confidence (>RETENTION_DAYS și `_version=1`) în `_ARCHIVE/auto_learned/<YYYY-MM>/`
  5. Update MEMORY.md (curăță linkuri către arhivate)

Run: python auto_learn_rotate.py [--dry-run] [--retention-days N]
"""
from __future__ import annotations
import argparse
import datetime
import json
import re
import shutil
import sys
from pathlib import Path

WORKSPACE = Path("D:/Cloude Code")
PROJECTS_DIR = WORKSPACE / "PROJECTS"
GLOBAL_AUTO_DIR = WORKSPACE / "_MEMORY" / "auto"
ARCHIVE_DIR = WORKSPACE / "_ARCHIVE" / "auto_learned"
LOG = WORKSPACE / ".claude" / "cache" / "auto_learn.log"

DEFAULT_RETENTION_DAYS = 60


def log(msg: str) -> None:
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.now().isoformat(timespec='seconds')}] ROTATE: {msg}\n")
    except OSError:
        pass


def parse_frontmatter(path: Path) -> tuple[dict, str]:
    try:
        import yaml
    except ImportError:
        return {}, ""
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


def collect_auto_learned() -> list:
    """Returnează list de Path la toate fișierele auto_learned."""
    targets = []
    if GLOBAL_AUTO_DIR.exists():
        targets.append(GLOBAL_AUTO_DIR)
    if PROJECTS_DIR.exists():
        for proj in PROJECTS_DIR.iterdir():
            if proj.is_dir():
                proj_mem = proj / "_MEMORY"
                if proj_mem.exists():
                    targets.append(proj_mem)

    found = []
    for target_dir in targets:
        for md in target_dir.rglob("*.md"):
            if md.name == "MEMORY.md":
                continue
            fm, _ = parse_frontmatter(md)
            if fm.get("auto_learned") or fm.get("auto_consolidated"):
                found.append((md, fm))
    return found


def is_archivable(path: Path, fm: dict, retention_days: int) -> bool:
    """True dacă fișier eligibil pentru arhivare (low-confidence + vechi)."""
    if int(fm.get("_version", 1)) > 1:
        return False  # are update-uri → relevant
    created_str = fm.get("_created") or fm.get("created")
    if not created_str:
        return False
    try:
        created = datetime.datetime.fromisoformat(created_str)
    except (ValueError, TypeError):
        return False
    age_days = (datetime.datetime.now() - created).days
    return age_days >= retention_days


def archive_file(path: Path, dry_run: bool) -> Path | None:
    """Mută fișier în _ARCHIVE/auto_learned/<YYYY-MM>/."""
    month = datetime.datetime.now().strftime("%Y-%m")
    archive_target = ARCHIVE_DIR / month / path.name
    if dry_run:
        log(f"DRY: would archive {path} -> {archive_target}")
        return archive_target
    try:
        archive_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(archive_target))
        log(f"ARCHIVED: {path.name} -> {archive_target}")
        return archive_target
    except OSError as exc:
        log(f"archive_failed {path}: {exc}")
        return None


def cleanup_memory_index(archived_names: list, dry_run: bool) -> None:
    """Șterge linkuri către fișiere arhivate din MEMORY.md (global + per-project + Obsidian)."""
    index_files = [
        Path.home() / ".claude" / "projects" / "D--Cloude-Code" / "memory" / "MEMORY.md",
        WORKSPACE / "_MEMORY" / "MEMORY.md",
    ]
    for proj in PROJECTS_DIR.iterdir() if PROJECTS_DIR.exists() else []:
        if proj.is_dir():
            mp = proj / "_MEMORY" / "MEMORY.md"
            if mp.exists():
                index_files.append(mp)

    archived_stems = {Path(n).stem for n in archived_names}
    for index_file in index_files:
        if not index_file.exists():
            continue
        try:
            content = index_file.read_text(encoding="utf-8")
        except OSError:
            continue
        new_lines = []
        removed = 0
        for line in content.splitlines():
            should_remove = False
            for stem in archived_stems:
                if f"[{stem}]" in line or f"[[{stem}]]" in line or f"({stem}.md)" in line:
                    should_remove = True
                    removed += 1
                    break
            if not should_remove:
                new_lines.append(line)
        if removed > 0:
            if dry_run:
                log(f"DRY: would remove {removed} lines from {index_file}")
            else:
                try:
                    index_file.write_text("\n".join(new_lines), encoding="utf-8")
                    log(f"INDEX_CLEANED: {removed} lines from {index_file.name}")
                except OSError as exc:
                    log(f"index_cleanup_failed {index_file}: {exc}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Doar raportează, nu modifică")
    parser.add_argument("--retention-days", type=int, default=DEFAULT_RETENTION_DAYS,
                        help=f"Praguri vechime (default {DEFAULT_RETENTION_DAYS})")
    args = parser.parse_args()

    log(f"START: dry_run={args.dry_run} retention={args.retention_days}d")

    found = collect_auto_learned()
    log(f"SCANNED: {len(found)} auto_learned files")

    archived = []
    for path, fm in found:
        if is_archivable(path, fm, args.retention_days):
            target = archive_file(path, args.dry_run)
            if target:
                archived.append(path.name)

    if archived:
        cleanup_memory_index(archived, args.dry_run)

    summary = {
        "scanned": len(found),
        "archived": len(archived),
        "retention_days": args.retention_days,
        "dry_run": args.dry_run,
    }
    print(json.dumps(summary, indent=2))
    log(f"DONE: {summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
