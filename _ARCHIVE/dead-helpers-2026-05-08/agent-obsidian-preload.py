#!/usr/bin/env python3
"""
Agent Obsidian Context Preloader — Enneagram Edition (META-007 → META-011)

SubagentStart hook:
  1. Determina nodul Enneagram al agentului din task description
  2. Filtreza memory files dupa node_memory_tags (in loc sa caute toate 102 fisiere)
  3. Injecteaza top-5 relevante ca system-reminder

Economie vs. versiunea anterioara: ~60-70% din tokens per subagent
(cautare tintita pe 10-15 fisiere per nod, nu toate 102)
"""
import sys
import json
import os
import re
import subprocess
from datetime import datetime

_HERE           = os.path.dirname(os.path.abspath(__file__))
_WORKSPACE      = os.environ.get('WORKSPACE_DIR', os.path.dirname(_HERE))
MEMORY_DIR      = os.environ.get('CLAUDE_MEMORY_DIR',
                    os.path.join(_WORKSPACE, 'memory'))
NODE_MAP_PATH   = os.path.join(_HERE, 'workspace_node_map.json')
ROUTER_PATH     = os.path.join(_HERE, 'router.js')

SEARCH_DIRS = [
    MEMORY_DIR,
    os.path.join(MEMORY_DIR, "patterns"),
    os.path.join(MEMORY_DIR, "agents"),
]

STOPWORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'this', 'that', 'it', 'is', 'are', 'was',
    'si', 'sa', 'de', 'la', 'in', 'cu', 'pe', 'ca', 'mai', 'un', 'o',
    'fi', 'al', 'ale', 'cel', 'care', 'este', 'sunt', 'face', 'fara',
    'doar', 'daca', 'cand', 'dupa', 'inainte', 'intre', 'prin', 'care',
}


def load_node_map():
    try:
        with open(NODE_MAP_PATH, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def get_enneagram_node(task, node_map):
    """Returneaza (node_int, tags_list) pentru task-ul dat, via router.js."""
    try:
        result = subprocess.run(
            ['node', ROUTER_PATH, task[:200]],
            capture_output=True, text=True, timeout=3
        )
        if result.returncode == 0:
            data = json.loads(result.stdout.strip())
            node = data.get('node', 3)
            tags = node_map.get('node_memory_tags', {}).get(str(node), [])
            return node, tags, data.get('node_name', 'Builder')
    except Exception:
        pass
    # Fallback: nod 3 (Builder) — cel mai comun
    tags = node_map.get('node_memory_tags', {}).get('3', ['android', 'code'])
    return 3, tags, 'Builder'


def parse_frontmatter(content):
    if not content.startswith("---"):
        return {}, content
    end = content.find("\n---", 3)
    if end == -1:
        return {}, content
    fm = {}
    for line in content[3:end].splitlines():
        m = re.match(r'^(\w+):\s*(.+)', line.strip())
        if m:
            fm[m.group(1)] = m.group(2).strip()
    return fm, content[end + 4:].strip()


def resolve_related(fname, visited=None):
    """Urmareste legatura 'related:' un singur hop — conexiunile holografice."""
    if visited is None:
        visited = set()
    related_files = []
    for search_dir in SEARCH_DIRS:
        fpath = os.path.join(search_dir, fname)
        if not os.path.exists(fpath):
            continue
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
            fm, _ = parse_frontmatter(content)
            related_raw = fm.get('related', '')
            # Accepta: [a.md, b.md] sau a.md, b.md
            related = re.findall(r'[\w_-]+\.md', related_raw)
            for r in related:
                if r not in visited and r not in ('MEMORY.md', '.gitkeep'):
                    visited.add(r)
                    related_files.append(r)
        except Exception:
            pass
        break
    return related_files


def search_memories(keywords, node_tags):
    """
    Scoring combinat:
    - +3 pentru fiecare node_tag prezent in fisier (relevanta structurala)
    - +1 pentru fiecare keyword prezent in continut (relevanta semantica)
    - +2 bonus pentru fisiere ajunse prin conexiuni holografice (related:)
    """
    scored = {}  # fname -> dict

    for search_dir in SEARCH_DIRS:
        if not os.path.exists(search_dir):
            continue
        for fname in os.listdir(search_dir):
            if not fname.endswith('.md') or fname in ('MEMORY.md', '.gitkeep'):
                continue
            fpath = os.path.join(search_dir, fname)
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    content = f.read()
                content_lower = content.lower()
                fm, body = parse_frontmatter(content)

                file_tags_raw = fm.get('tags', '') + ' ' + fm.get('project', '')
                file_tags = file_tags_raw.lower()
                tag_score = sum(3 for t in node_tags if t.lower() in file_tags)
                kw_score  = sum(1 for kw in keywords if kw in content_lower)
                total = tag_score + kw_score
                if total == 0:
                    continue

                preview_lines = [l for l in body.splitlines() if l.strip()][:2]
                preview = ' | '.join(preview_lines)[:200]
                entry = {
                    'score': total,
                    'tag_score': tag_score,
                    'name': fm.get('name', fname.replace('.md', '')),
                    'type': fm.get('type', 'unknown'),
                    'preview': preview,
                    'subdir': 'patterns' if 'patterns' in fpath else (
                               'agents'  if 'agents'  in fpath else 'memory'),
                    'fname': fname,
                }
                if fname not in scored or scored[fname]['score'] < total:
                    scored[fname] = entry

                # Urmareste conexiunile holografice (related: +2 bonus)
                if total >= 3:
                    for rel_fname in resolve_related(fname):
                        if rel_fname in scored:
                            scored[rel_fname]['score'] += 2
                            scored[rel_fname]['tag_score'] += 2
                        else:
                            # Incarca fisierul connected
                            for sd in SEARCH_DIRS:
                                rel_path = os.path.join(sd, rel_fname)
                                if os.path.exists(rel_path):
                                    try:
                                        with open(rel_path, 'r', encoding='utf-8') as rf:
                                            rel_content = rf.read()
                                        rel_fm, rel_body = parse_frontmatter(rel_content)
                                        rel_prev = ' | '.join(
                                            [l for l in rel_body.splitlines() if l.strip()][:2]
                                        )[:200]
                                        scored[rel_fname] = {
                                            'score': 2,
                                            'tag_score': 2,
                                            'name': rel_fm.get('name', rel_fname.replace('.md', '')),
                                            'type': rel_fm.get('type', 'unknown'),
                                            'preview': rel_prev,
                                            'subdir': 'patterns' if 'patterns' in rel_path else (
                                                       'agents'  if 'agents'  in rel_path else 'memory'),
                                            'fname': rel_fname,
                                        }
                                    except Exception:
                                        pass
                                    break
            except Exception:
                continue

    results = list(scored.values())
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:5]


def extract_keywords(text):
    words = re.findall(r'\b\w{4,}\b', text.lower())
    return [w for w in words if w not in STOPWORDS][:12]


try:
    data = json.load(sys.stdin)
    tool_input = data.get('tool_input', {})
    task = tool_input.get('prompt', '') or tool_input.get('description', '') or str(data)[:500]

    node_map = load_node_map()
    node, node_tags, node_name = get_enneagram_node(task, node_map)
    keywords = extract_keywords(task)

    relevant = search_memories(keywords, node_tags) if (keywords or node_tags) else []

    ts = datetime.now().strftime('%Y%m%d-%H%M%S')
    slug = '-'.join(keywords[:3]) if keywords else 'task'
    agent_memory_path = f"_MEMORY/agents/{ts}-{slug[:30]}.md"

    lines = [f"=== AGENT CONTEXT [Nod {node}: {node_name}] ==="]

    if relevant:
        lines.append(f"[Top {len(relevant)} memory relevante pentru nod {node}]")
        for r in relevant:
            tag_marker = "★" if r['tag_score'] > 0 else " "
            lines.append(f"\n{tag_marker} {r['name']} ({r['type']})")
            lines.append(f"  {r['preview']}")

    lines.append(f"\n[Agent memory path: {agent_memory_path}]")
    lines.append("Format frontmatter: name / type / tags / project / priority")
    lines.append("=== END ===")

    print('\n'.join(lines))
except Exception:
    pass  # Hooks nu crapa Claude Code
