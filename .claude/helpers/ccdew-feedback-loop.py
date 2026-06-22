#!/usr/bin/env python3
"""
CCDEW Convergent/Divergent Feedback Loop

Automatically runs the divergent→convergent pipeline and memorizes patterns
from the results into the Hermes learning pyramid (episodic.jsonl + techniques.json).

Usage:
  python ccdew-feedback-loop.py "<task>" [--wings 5] [--domain editorial]
  python ccdew-feedback-loop.py --record-only "<pattern>" [--technique name]
"""

import sys
import os
import json
import datetime
import argparse
import hashlib
from pathlib import Path

MEMORY_DIR = Path(os.environ.get('HERMES_MEMORY_DIR', Path.home() / '.hermes' / 'memories'))
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

EPISODIC_FILE = MEMORY_DIR / 'episodic.jsonl'
TECHNIQUES_FILE = MEMORY_DIR / 'techniques.json'

# ── Wing definitions (mirrors ccdew-convergent-divergent.cjs) ──────

WINGS = {
    'maha':     'Zoom-wing: Maha — Systemic/cosmic overview',
    'macro':    'Zoom-wing: Macro — Structural inter-component view',
    'mezzo':    'Zoom-wing: Mezzo — Process/flow view',
    'micro':    'Zoom-wing: Micro — Intra-component view',
    'nano':     'Zoom-wing: Nano — Atomic/microsecond view',
    'stylistic':   'Lens-wing: Stylistic — Aesthetic/literary filter',
    'doctrinal':   'Lens-wing: Doctrinal — Source fidelity filter',
    'structural':  'Lens-wing: Structural — Architectural filter',
    'regression':  'Lens-wing: Regression — What doesn\'t work',
    'memory':      'Lens-wing: Memory — Continuity with past',
    'agent':    'Perspective-wing: Agent — From actor viewpoint',
    'observer': 'Perspective-wing: Observer — From neutral external viewpoint',
    'cosmic':   'Perspective-wing: Cosmic — From systemic viewpoint',
    'sakshi':   'Perspective-wing: Sakshi — From non-involved witness',
    'descriptive': 'Modality-wing: Descriptive — As it is',
    'normative':   'Modality-wing: Normative — As it should be',
    'generative':  'Modality-wing: Generative — What if',
    'critical':    'Modality-wing: Critical — What doesn\'t work',
}

DOMAIN_WINGS = {
    'editorial':    ['doctrinal', 'stylistic', 'structural', 'memory', 'regression'],
    'code-review':  ['regression', 'nano', 'critical', 'normative', 'structural'],
    'architecture': ['macro', 'cosmic', 'normative', 'critical', 'memory'],
    'bug':          ['regression', 'nano', 'observer', 'critical', 'micro'],
    'content':      ['generative', 'stylistic', 'agent', 'descriptive', 'sakshi'],
    'research':     ['macro', 'memory', 'critical', 'doctrinal', 'mezzo'],
    'default':      ['maha', 'macro', 'mezzo', 'micro', 'nano'],
}

# ── Helpers ────────────────────────────────────────────────────────

def pick_wings(task, count=5):
    lower = (task or '').lower()
    domain = 'default'
    for key in DOMAIN_WINGS:
        if key != 'default' and key in lower:
            domain = key
            break
    candidates = DOMAIN_WINGS.get(domain, DOMAIN_WINGS['default'])
    return candidates[:count]

def task_hash(task):
    return hashlib.sha256(task.encode()).hexdigest()[:12]

def read_episodic():
    if not EPISODIC_FILE.exists():
        return []
    entries = []
    for line in EPISODIC_FILE.read_text().strip().split('\n'):
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return entries

def append_episodic(entry):
    with open(EPISODIC_FILE, 'a') as f:
        f.write(json.dumps(entry) + '\n')

def read_techniques():
    if not TECHNIQUES_FILE.exists():
        return {}
    return json.loads(TECHNIQUES_FILE.read_text())

def write_techniques(data):
    TECHNIQUES_FILE.write_text(json.dumps(data, indent=2))

# ── Feedback loop ──────────────────────────────────────────────────

def generate_divergent_prompts(task, wing_ids):
    agents = []
    for i, wid in enumerate(wing_ids):
        wing_desc = WINGS.get(wid, wid)
        prompt = f"""Approach this task ONLY through {wing_desc}.

DO NOT use other angles. Your output is the pure perspective of "{wing_desc}" on the following task.

Task: {task}

Rules:
- Be 100% faithful to the assigned perspective
- Do not try to cover other angles (other agents are covering them)
- Clearly report which angle you speak from
- Output can be short (1-3 paragraphs) but complete from your perspective"""

        agents.append({
            'agent_id': f'agent-{i+1}',
            'wing_id': wid,
            'wing_desc': wing_desc,
            'prompt': prompt,
        })
    return agents

def generate_convergent_prompt(task, agents):
    agent_list = '\n'.join(
        f'  Agent {a["agent_id"]}: {a["wing_desc"]}'
        for a in agents
    )
    placeholder_list = '\n'.join(
        f'  [Output from {a["agent_id"]} — {a["wing_desc"]}]'
        for a in agents
    )
    return f"""You are the Convergent Reformer/Synthesizer. You receive {len(agents)} divergent perspectives on the same task.

Your task:
1. Identify CONVERGENCES — where all perspectives agree
2. Identify PRODUCTIVE DIVERGENCES — where perspectives say different and useful things
3. Identify UNRESOLVED TENSIONS — where perspectives contradict and CANNOT be reconciled
4. Produce a UNIFIED OUTPUT that preserves diversity of perspectives but gives an integrated verdict

Original task: {task}

Agents:
{agent_list}

{placeholder_list}

--
Respond with:
## Convergences
...
## Productive Divergences
...
## Unresolved Tensions
...
## Integrated Verdict
..."""

def record_pattern(task, agents, outcome='pending'):
    """Record the divergent/convergent cycle into Hermes memory."""
    entry = {
        'type': 'divergent_convergent_cycle',
        'task_preview': task[:100],
        'task_hash': task_hash(task),
        'domain': _detect_domain(task),
        'agents': len(agents),
        'wings': [a['wing_id'] for a in agents],
        'outcome': outcome,
        'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    append_episodic(entry)
    return entry

def _detect_domain(task):
    lower = task.lower()
    for key in DOMAIN_WINGS:
        if key != 'default' and key in lower:
            return key
    return 'default'

def record_technique(name, task, wing_ids, outcome):
    """Register or update a technique in techniques.json."""
    techniques = read_techniques()
    slug = name.lower().replace(' ', '_')
    techniques[slug] = {
        'name': name,
        'description': f'Divergent/Convergent pattern discovered from: {task[:100]}',
        'when': f'Task matches domain "{_detect_domain(task)}"',
        'how': f'Use wings: {", ".join(wing_ids)}',
        'success_rate': 1.0 if outcome == 'success' else 0.5,
        'use_count': 1,
        'pattern_triggers': [f'domain:{_detect_domain(task)}'] + [f'wing:{w}' for w in wing_ids],
        'linked_skills': ['convergent-divergent'],
    }
    write_techniques(techniques)
    return slug

def cmd_generate(args):
    """Generate divergent prompts + convergent prompt for a task."""
    task = args.task
    count = min(args.wings or 5, 18)
    wing_ids = pick_wings(task, count)
    agents = generate_divergent_prompts(task, wing_ids)
    convergent_prompt = generate_convergent_prompt(task, agents)

    episode = record_pattern(task, agents)

    print(json.dumps({
        'task': task,
        'domain': _detect_domain(task),
        'task_hash': episode['task_hash'],
        'divergent_agents': agents,
        'convergent_prompt': convergent_prompt,
        'workflow': [
            '1. Run each divergent agent with its prompt (in parallel)',
            '2. Collect all outputs',
            '3. Feed outputs to the convergent prompt via a Reformer agent',
            '4. Record the outcome: --record <pattern> [--technique name]',
        ],
        'memory': {
            'episode_id': episode['task_hash'],
            'status': 'recorded_in_episodic',
        },
    }, indent=2, ensure_ascii=False))

def cmd_record(args):
    """Record a pattern from a completed cycle."""
    pattern = args.record_only
    technique = args.technique or f'divergent-convergent-{task_hash(pattern)}'

    entry = {
        'type': 'pattern_discovered',
        'pattern': pattern[:200],
        'task_hash': task_hash(pattern),
        'technique': technique,
        'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'outcome': 'success',
    }
    append_episodic(entry)
    record_technique(technique, pattern, ['auto-detected'], 'success')

    print(json.dumps({
        'status': 'recorded',
        'technique': technique,
        'file': str(EPISODIC_FILE),
    }, indent=2))

def cmd_stats(args):
    """Show feedback loop statistics."""
    episodes = read_episodic()
    cycles = [e for e in episodes if e.get('type') == 'divergent_convergent_cycle']
    patterns = [e for e in episodes if e.get('type') == 'pattern_discovered']
    techniques = read_techniques()

    print(json.dumps({
        'total_divergent_convergent_cycles': len(cycles),
        'total_patterns_discovered': len(patterns),
        'techniques_registered': len(techniques),
        'recent_cycles': cycles[-5:] if cycles else [],
        'recent_patterns': patterns[-5:] if patterns else [],
    }, indent=2, ensure_ascii=False))

# ── CLI ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='CCDEW Convergent/Divergent Feedback Loop')
    parser.add_argument('task', nargs='?', help='Task description')
    parser.add_argument('--wings', type=int, default=5, help='Number of divergent wings (default: 5)')
    parser.add_argument('--domain', help='Domain (editorial, code-review, etc.)')
    parser.add_argument('--record-only', help='Record a discovered pattern without generating')
    parser.add_argument('--technique', help='Technique name (for --record-only)')
    parser.add_argument('--stats', action='store_true', help='Show statistics')

    args = parser.parse_args()

    if args.stats:
        cmd_stats(args)
    elif args.record_only:
        cmd_record(args)
    elif args.task:
        cmd_generate(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
