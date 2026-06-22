#!/usr/bin/env python3
"""
Enneagram Agent Topology Router
Directed graph: 9 nodes, 27 arcs (hexad + triangle + 18 wings).

Usage:
  python enneagram_router.py matrix               # adjacency matrix
  python enneagram_router.py path <s> <d>         # shortest path BFS
  python enneagram_router.py all_paths <s> <d>    # all paths (max 5 hops)
  python enneagram_router.py neighbors <n>        # arcs from node n
  python enneagram_router.py describe <n>         # role + detailed transitions
  python enneagram_router.py route <task_type>    # recommended start node for task
  python enneagram_router.py spawn <task_type>    # generate swarm_init snippet
"""

import sys
from collections import deque

# ─── ENNEAGRAM GRAPH ──────────────────────────────────────────────────────────

ARCS_ORIGINAL = [
    # Hexad (1→4→2→8→5→7→1)
    (1, 4), (4, 2), (2, 8), (8, 5), (5, 7), (7, 1),
    # Fast triangle (3→6→9→3)
    (3, 6), (6, 9), (9, 3),
]

ARCS_WINGS = [
    # Bidirectional adjacencies on circle 1-2-3-4-5-6-7-8-9-1
    (1, 2), (2, 1),
    (2, 3), (3, 2),
    (3, 4), (4, 3),
    (4, 5), (5, 4),
    (5, 6), (6, 5),
    (6, 7), (7, 6),
    (7, 8), (8, 7),
    (8, 9), (9, 8),
    (9, 1), (1, 9),
]

ALL_ARCS = ARCS_ORIGINAL + ARCS_WINGS

GRAPH = {i: [] for i in range(1, 10)}
for src, dst in ALL_ARCS:
    if dst not in GRAPH[src]:
        GRAPH[src].append(dst)

# ─── AGENT ROLES ──────────────────────────────────────────────────────────────

ROLES = {
    1: {
        "name": "Reformer / QA",
        "subagent": "reviewer",
        "cycle": "hexad",
        "short": "Quality verification, code review, best-practices compliance",
    },
    2: {
        "name": "Integrator",
        "subagent": "backend-dev",
        "cycle": "hexad",
        "short": "Component integration, API connections, dependency management",
    },
    3: {
        "name": "Builder",
        "subagent": "coder",
        "cycle": "triangle",
        "short": "Code implementation, feature writing, direct execution",
    },
    4: {
        "name": "Contextualizer",
        "subagent": "researcher",
        "cycle": "hexad",
        "short": "Research, gathering context, documentation, external sources",
    },
    5: {
        "name": "Analyzer",
        "subagent": "analyst",
        "cycle": "hexad",
        "short": "Deep analysis, debugging, profiling, pattern detection",
    },
    6: {
        "name": "Validator",
        "subagent": "tester",
        "cycle": "triangle",
        "short": "Testing, validation, QA, edge cases, regression",
    },
    7: {
        "name": "Architect",
        "subagent": "architecture",
        "cycle": "hexad",
        "short": "System design, planning, architecture, trade-offs",
    },
    8: {
        "name": "Orchestrator",
        "subagent": "sparc-orchestrator",
        "cycle": "hexad",
        "short": "Task routing, swarm coordination, dispatching, prioritization",
    },
    9: {
        "name": "Memory / Consolidator",
        "subagent": "memory-specialist",
        "cycle": "triangle",
        "short": "State consolidation, Obsidian sync, cross-session memory, synthesis",
    },
}

# ─── FRACTAL ZOOM LEVELS (META-014 multi-zoom protocol) ─────────────────────

ZOOM_LEVELS = [
    {"id": "MAHA",  "scope": "Whole system/project",              "key_question": "Is the global architecture still coherent?",             "bug_types": "Center of gravity shifted, broken introductory promise, component imbalance"},
    {"id": "MACRO", "scope": "Cross-module / cross-chapter",       "key_question": "Do components still communicate?",                      "bug_types": "Broken cross-references, broken structural parallels, drift"},
    {"id": "MEZZO", "scope": "Module / chapter / subsection",      "key_question": "Canonical host respected? Rhythm/style consistent?",     "bug_types": "Duplicated/missing host, broken rhythm, voice shift"},
    {"id": "MICRO", "scope": "Function / paragraph",               "key_question": "Internal logic intact?",                                "bug_types": "Logic bug, fine distinction lost, incorrect merge"},
    {"id": "NANO",  "scope": "Character / token / sentence",        "key_question": "Lexical details clean?",                               "bug_types": "ASCII vs Unicode, doubled punctuation, double space, broken markup"},
]

LENSES = [
    {"id": "stylistic",     "name": "Stylistic",         "node": 4, "subagent": "researcher",         "checks": "Rhythm, voice, reader-experience, fluency"},
    {"id": "doctrinal",     "name": "Doctrinal/Technical","node": 5, "subagent": "analyst",           "checks": "Conceptual precision, pattern detection, fine distinctions"},
    {"id": "structural",    "name": "Structural",        "node": 7, "subagent": "system-architect",   "checks": "Design coherence, narrative arc, balance"},
    {"id": "regression",    "name": "Regression",        "node": 6, "subagent": "tester",             "checks": "Introduced bugs, broken grammar, mechanical consistency"},
    {"id": "memory",        "name": "Memory/Consistency", "node": 9, "subagent": "memory-coordinator", "checks": "Cross-file consistency, indexes, references"},
]

# Priority matrix: which zoom wins when conflicted (META-014 §D)
PRIORITY_MATRIX = {
    "editorial":      ["MEZZO", "MICRO", "NANO", "MACRO", "MAHA"],
    "security":       ["NANO", "MICRO", "MACRO", "MEZZO", "MAHA"],
    "performance":    ["MICRO", "MACRO", "MEZZO", "NANO", "MAHA"],
    "architectural":  ["MAHA", "MACRO", "MEZZO", "MICRO", "NANO"],
    "refactoring":    ["MACRO", "MICRO", "MEZZO", "MAHA", "NANO"],
    "default":        ["MEZZO", "MICRO", "MACRO", "NANO", "MAHA"],
}

# Thresholds for mandatory multi-zoom (META-014 §Applicability)
THRESHOLDS = {
    "min_files_multi_zoom": 3,
    "min_files_all_lenses": 5,
    "min_files_orchestrator_split": 10,
}

# ─── ROUTING HINTS (task type → recommended start node) ──────────────────────

TASK_ROUTING = {
    "review":      1,
    "qa":          1,
    "quality":     1,
    "integrate":   2,
    "integration": 2,
    "api":         2,
    "connect":     2,
    "build":       3,
    "implement":   3,
    "code":        3,
    "write":       3,
    "research":    4,
    "context":     4,
    "docs":        4,
    "search":      4,
    "debug":       5,
    "analyze":     5,
    "profile":     5,
    "inspect":     5,
    "test":        6,
    "validate":    6,
    "regression":  6,
    "design":      7,
    "plan":        7,
    "architect":   7,
    "orchestrate": 8,
    "route":       8,
    "coordinate":  8,
    "memory":      9,
    "consolidate": 9,
    "obsidian":    9,
    "persist":     9,
}

# ─── BFS ──────────────────────────────────────────────────────────────────────

def bfs_path(start, end):
    if start == end:
        return [start]
    queue = deque([[start]])
    visited = {start}
    while queue:
        path = queue.popleft()
        node = path[-1]
        for nb in GRAPH[node]:
            if nb == end:
                return path + [nb]
            if nb not in visited:
                visited.add(nb)
                queue.append(path + [nb])
    return None

def arc_type(a, b):
    return "O" if (a, b) in ARCS_ORIGINAL else "W"

# ─── CLI COMMANDS ─────────────────────────────────────────────────────────────

def cmd_matrix(_):
    nodes = range(1, 10)
    print("\n   " + " ".join(str(n) for n in nodes))
    for src in nodes:
        row = f"{src}: "
        for dst in nodes:
            if dst in GRAPH[src]:
                row += ("O " if (src, dst) in ARCS_ORIGINAL else "W ")
            else:
                row += ". "
        print(row)
    print("\nO=original arc (hexad/triangle)  W=wing  .=absent")
    print(f"Total: {len(ALL_ARCS)} arcs (9 original + 18 wings)\n")

def cmd_path(args):
    if len(args) < 2:
        print("Usage: path <start> <end>"); return
    s, d = int(args[0]), int(args[1])
    p = bfs_path(s, d)
    if p:
        labels = " → ".join(f"{n}[{ROLES[n]['name']}]" for n in p)
        types  = " → ".join(arc_type(p[i], p[i+1]) for i in range(len(p)-1))
        print(f"\nShortest path ({len(p)-1} hops):")
        print(f"  {labels}")
        print(f"  arc types: {types}\n")
    else:
        print(f"No path from {s} to {d}")

def cmd_all_paths(args):
    if len(args) < 2:
        print("Usage: all_paths <start> <end> [max_hops]"); return
    s, d, max_h = int(args[0]), int(args[1]), int(args[2]) if len(args) > 2 else 5
    results = []

    def dfs(cur, path, visited):
        if len(path) - 1 >= max_h:
            return
        if cur == d and len(path) > 1:
            results.append(list(path)); return
        for nx in GRAPH[cur]:
            if nx not in visited or nx == d:
                visited.add(nx)
                path.append(nx)
                dfs(nx, path, visited)
                path.pop()
                visited.discard(nx)

    dfs(s, [s], {s})
    results.sort(key=len)
    print(f"\n{len(results)} paths from {s} to {d} (max {max_h} hops):")
    for i, p in enumerate(results[:20], 1):
        types = ",".join(arc_type(p[j], p[j+1]) for j in range(len(p)-1))
        print(f"  {i}. {' → '.join(str(x) for x in p)}  [{types}]  ({len(p)-1} hops)")
    print()

def cmd_neighbors(args):
    if not args:
        print("Usage: neighbors <node>"); return
    n = int(args[0])
    r = ROLES[n]
    print(f"\nNode {n}: {r['name']} [{r['subagent']}] — {r['cycle']}")
    print(f"  {r['short']}")
    print(f"\n  OUT arcs from {n}:")
    for dst in sorted(GRAPH[n]):
        print(f"    {n} → {dst}  {ROLES[dst]['name']}  [{arc_type(n,dst)}]")
    incoming = [src for src in range(1,10) if n in GRAPH[src]]
    print(f"\n  IN arcs to {n}:")
    for src in sorted(incoming):
        print(f"    {src} → {n}  {ROLES[src]['name']}  [{arc_type(src,n)}]")
    print()

def cmd_describe(args):
    if not args:
        print("Usage: describe <node>"); return
    n = int(args[0])
    r = ROLES[n]
    sep = "=" * 58
    print(f"\n{sep}")
    print(f"  Node {n}: {r['name']}  ({r['cycle']})")
    print(sep)
    print(f"  subagent_type : {r['subagent']}")
    print(f"  role          : {r['short']}")
    print(f"\n  Sends to (OUT arcs):")
    for dst in sorted(GRAPH[n]):
        print(f"    → {dst} {ROLES[dst]['name']}  [{arc_type(n,dst)}]")
    incoming = [src for src in range(1,10) if n in GRAPH[src]]
    print(f"\n  Receives from (IN arcs):")
    for src in sorted(incoming):
        print(f"    ← {src} {ROLES[src]['name']}  [{arc_type(src,n)}]")
    print(f"\n  Shortest paths to all other nodes:")
    for dst in range(1,10):
        if dst == n: continue
        p = bfs_path(n, dst)
        if p:
            print(f"    {n}→{dst}: {' → '.join(str(x) for x in p)}  ({len(p)-1} hops)")
    print()

def cmd_route(args):
    if not args:
        print(f"Usage: route <task_type>")
        print(f"  Types: {', '.join(sorted(TASK_ROUTING))}")
        return
    t = args[0].lower()
    n = TASK_ROUTING.get(t)
    if n:
        r = ROLES[n]
        print(f"\nTask '{t}' → Node {n}: {r['name']} [{r['subagent']}]")
        print(f"  {r['short']}")
        print(f"\n  Next hops:")
        for dst in sorted(GRAPH[n]):
            print(f"    → {dst} {ROLES[dst]['name']}  [{arc_type(n,dst)}]")
        print()
    else:
        print(f"Task '{t}' unknown. Types: {', '.join(sorted(TASK_ROUTING))}")

def cmd_spawn(args):
    """Generate a swarm_init code snippet based on task_type."""
    if not args:
        print("Usage: spawn <task_type>"); return
    t = args[0].lower()
    n = TASK_ROUTING.get(t, 8)
    r = ROLES[n]
    # Calculate which agents are hit on the default path
    if n in [1,4,2,8,5,7]:
        path_nodes = [1,4,2,8,5,7]
    else:
        path_nodes = [3,6,9]

    print(f"""
// Enneagram swarm snippet — task: {t} — start node {n}
// Auto-generated by enneagram_router.py

const swarm = await mcp__claude_flow__swarm_init({{
  topology: "hierarchical-mesh",
  maxAgents: {len(path_nodes)},
  strategy: "specialized",
  memoryNamespace: "enneagram-{t}",
  flashAttention: true,
  agentDbIntegration: true,
}});

// Agent start: Node {n} — {r['name']}
await mcp__claude_flow__agent_spawn({{
  swarmId: swarm.swarmId,
  agentType: "{r['subagent']}",
  task: "<<task_description>>",
  context: {{
    enneagram_node: {n},
    next_hops: {sorted(GRAPH[n])},
    arc_types: {{
      {", ".join(f'{dst}: "{arc_type(n,dst)}"' for dst in sorted(GRAPH[n]))}
    }}
  }}
}});
""")

# ─── NEW COMMANDS (Fractal Zoom + Lenses) ──────────────────────────────────

def cmd_zoom(args):
    """Show zoom level details."""
    if not args:
        print("Fractal Zoom Levels (META-014):\n")
        for z in ZOOM_LEVELS:
            print(f"  {z['id']:6s} | {z['scope']:35s} | {z['key_question']}")
        print(f"\n  No zoom can be skipped. NANO bugs are invisible at MAHA. MAHA bugs are invisible at NANO.")
        return
    zoom_id = args[0].upper()
    for z in ZOOM_LEVELS:
        if z['id'] == zoom_id:
            print(f"\n{'='*60}")
            print(f"  {z['id']} — Scope: {z['scope']}")
            print(f"{'='*60}")
            print(f"  Key question : {z['key_question']}")
            print(f"  Bug types    : {z['bug_types']}")
            print()
            return
    print(f"Unknown zoom: {zoom_id}. Options: {', '.join(z['id'] for z in ZOOM_LEVELS)}")

def cmd_lenses(args):
    """Show lens details."""
    if not args:
        print("\nMulti-Lens Verification (META-014):\n")
        print(f"{'Lens':20s} {'Node':6s} {'Agent':20s} {'What it checks'}")
        print("-" * 80)
        for l in LENSES:
            print(f"  {l['name']:20s} Node {l['node']:<2d} {l['subagent']:20s} {l['checks']}")
        print("\n  Cross-check protocol: combined reports = real coverage.")
        print("  A single agent covers at most 1 lens × 2 zoom levels.\n")
    else:
        lens_id = args[0].lower()
        for l in LENSES:
            if l['id'] == lens_id:
                print(f"\n{'='*60}")
                print(f"  {l['name']}")
                print(f"{'='*60}")
                print(f"  Node     : {l['node']} ({ROLES[l['node']]['name']})")
                print(f"  Agent    : {l['subagent']}")
                print(f"  Checks   : {l['checks']}")
                print()
                return
        print(f"Unknown lens: {lens_id}. Options: {', '.join(l['id'] for l in LENSES)}")

def cmd_priority(args):
    """Show priority matrix per task type (conflict resolution)."""
    print("\nPriority Matrix — which zoom wins when conflicted:\n")
    print(f"{'Domain':16s} {'Priority order':40s}")
    print("-" * 60)
    for domain, zooms in PRIORITY_MATRIX.items():
        print(f"  {domain:16s} {' → '.join(zooms)}")
    print()

def cmd_compose(args):
    """Full swarm composition for a task (Phase 1-4)."""
    if not args:
        print("Usage: compose <task_description> [--files N]")
        return
    
    task = args[0]
    n_files = 1
    if len(args) > 1 and args[1].startswith('--files'):
        try:
            n_files = int(args[2])
        except (ValueError, IndexError):
            pass

    lower = task.lower()
    
    # Detect domain
    domain = "default"
    for key in ["editorial", "security", "performance", "architectural", "refactoring", "code", "bug"]:
        if key in lower:
            domain = key
            break
    
    # Determine mandatory levels
    need_multi_zoom = n_files >= THRESHOLDS["min_files_multi_zoom"]
    need_all_lenses = n_files >= THRESHOLDS["min_files_all_lenses"]
    need_split = n_files >= THRESHOLDS["min_files_orchestrator_split"]
    
    priority = PRIORITY_MATRIX.get(domain, PRIORITY_MATRIX["default"])
    
    print(f"\n{'='*70}")
    print(f"  Swarm Composition — \"{task}\"")
    print(f"  Domain: {domain}  |  Files: {n_files}")
    print(f"{'='*70}")
    
    print(f"\n  ⚙ Thresholds:")
    print(f"    Multi-zoom check: {'MANDATORY' if need_multi_zoom else 'optional'} ({n_files} ≥ {THRESHOLDS['min_files_multi_zoom']})")
    print(f"    All 5 lenses:     {'MANDATORY' if need_all_lenses else 'optional'} ({n_files} ≥ {THRESHOLDS['min_files_all_lenses']})")
    print(f"    Orchestrator:     {'MANDATORY' if need_split else 'optional'}  ({n_files} ≥ {THRESHOLDS['min_files_orchestrator_split']})")
    
    print(f"\n  🔍 Priority (conflict resolution): {' → '.join(priority)}")
    
    # Phase 1: Decomposition
    print(f"\n  Phase 1 — Decomposition (Node 8 Orchestrator)")
    print(f"    Break task into executable sub-tasks")
    
    # Phase 2: Execution
    start_node = TASK_ROUTING.get(domain, TASK_ROUTING.get("default", 8))
    exec_agent = ROLES[start_node]
    print(f"\n  Phase 2 — Execution (Node {start_node}: {exec_agent['name']})")
    print(f"    Agent: {exec_agent['subagent']} | {exec_agent['short']}")
    
    # Phase 3: Multi-zoom + Multi-lens
    print(f"\n  Phase 3 — Multi-zoom + Multi-lens cross-check:")
    ph3_nodes = [(4, "Mezzo + Micro stylistic"),
                 (5, "Micro + Nano doctrinal/technical"),
                 (6, "Nano regression"),
                 (7, "Maha + Macro structural"),
                 (9, "Macro consistency cross-file")]
    
    if not need_multi_zoom:
        print(f"    (optional — skip for <{THRESHOLDS['min_files_multi_zoom']} files)")
    else:
        for node, desc in ph3_nodes:
            r = ROLES[node]
            print(f"    Agent {node} {r['name']:25s} → {desc}")
    
    # Phase 4: Consolidation
    print(f"\n  Phase 4 — Consolidation (Node 1 Reformer)")
    print(f"    Synthesize reports, decide which fixes to apply")
    
    print(f"\n  Anti-patterns to avoid:")
    print(f"    ❌ 8 × general-purpose parallel (that is not enneagram, it is parallel-spawn)")
    print(f"    ❌ All agents report 0 issues without cross-check")
    print(f"    ❌ Skipping Validator (Node 6) for 'mechanical/trivial' tasks")
    
    print()

def cmd_wings(args):
    """Show Enneagram wings information (18 wings from convergent/divergent protocol)."""
    print(f"\n{'='*70}")
    print(f"  Enneagram Wings Registry — 18 wings (convergent/divergent protocol)")
    print(f"{'='*70}\n")
    
    categories = {
        'zoom': 'Zoom Levels (5)',
        'lens': 'Lenses (5)',
        'perspective': 'Perspectives (4)',
        'modality': 'Modalities (4)',
    }
    
    wing_data = [
        ('maha', 'zoom', 'Zoom-aripa Maha', 'System-level view'),
        ('macro', 'zoom', 'Zoom-aripa Macro', 'Component-level view'),
        ('mezzo', 'zoom', 'Zoom-aripa Mezzo', 'Process/flow view'),
        ('micro', 'zoom', 'Zoom-aripa Micro', 'Intra-component view'),
        ('nano', 'zoom', 'Zoom-aripa Nano', 'Atomic view'),
        ('stylistic', 'lens', 'Lentila stylistica', 'Aesthetic/literary filter'),
        ('doctrinal', 'lens', 'Lentila doctrinala', 'Source fidelity filter'),
        ('structural', 'lens', 'Lentila structurala', 'Architectural filter'),
        ('regression', 'lens', 'Lentila regression', 'What doesn\'t work'),
        ('memory', 'lens', 'Lentila memorie', 'Continuity with past'),
        ('agent', 'perspective', 'Perspectiva agent', 'From actor view'),
        ('observer', 'perspective', 'Perspectiva observator', 'External neutral'),
        ('cosmic', 'perspective', 'Perspectiva cosmic', 'Systemic view'),
        ('sakshi', 'perspective', 'Perspectiva Saksi', 'Non-involved witness'),
        ('descriptive', 'modality', 'Modalitate descriptiva', 'As it is'),
        ('normative', 'modality', 'Modalitate normativa', 'As it should be'),
        ('generative', 'modality', 'Modalitate generativa', 'What if'),
        ('critical', 'modality', 'Modalitate critica', 'What doesn\'t work'),
    ]
    
    for cat, label in categories.items():
        print(f"  [{label}]")
        print(f"  {'─' * 60}")
        for w_id, w_cat, w_name, w_desc in wing_data:
            if w_cat == cat:
                print(f"    {w_id:20s} {w_name:30s} {w_desc}")
        print()

# ─── MAIN ──────────────────────────────────────────────────────────────────────

COMMANDS = {
    "matrix":    cmd_matrix,
    "path":      cmd_path,
    "all_paths": cmd_all_paths,
    "neighbors": cmd_neighbors,
    "describe":  cmd_describe,
    "route":     cmd_route,
    "spawn":     cmd_spawn,
    "zoom":      cmd_zoom,
    "lenses":    cmd_lenses,
    "priority":  cmd_priority,
    "compose":   cmd_compose,
    "wings":     cmd_wings,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print("Enneagram Agent Topology Router — Fractal Zoom Edition v2.0")
        print()
        print("Enneagram graph commands:")
        print(f"  matrix                  Adjacency matrix (9×9)")
        print(f"  path <s> <d>            Shortest path BFS")
        print(f"  all_paths <s> <d>       All paths (max 5 hops)")
        print(f"  neighbors <n>           Arcs from node n")
        print(f"  describe <n>            Role + detailed transitions")
        print(f"  route <task_type>       Recommended start node for task")
        print(f"  spawn <task_type>       Generate swarm_init snippet")
        print()
        print("Fractal zoom + lens commands (META-014):")
        print(f"  zoom [level]            Show zoom level details")
        print(f"  lenses [name]           Show lens details")
        print(f"  priority                Show priority matrix (conflict resolution)")
        print(f"  compose <task> [--files N]  Full swarm composition")
        print(f"  wings                   Show 18 wings registry")
        print()
        sys.exit(0)
    COMMANDS[sys.argv[1]](sys.argv[2:])
