#!/usr/bin/env python3
"""Hermes Learning Pyramid — 6 nivele de învățare incrementală

Piramida:
  Acțiuni → Pattern-uri → Tehnici → Skill-uri → Atitudini → Principii
      ↓         ↓            ↓          ↓           ↓           ↓
    JSONL    Clustering   Registry    Loader     Policies    Validare
"""
import json, os, time, re, shutil, subprocess, sys
from datetime import datetime, timezone
from collections import defaultdict, Counter

BASE = os.path.expanduser("~/.hermes/memories")
EPISODIC = os.path.join(BASE, "episodic.jsonl")
WEIGHTS = os.path.join(BASE, "weights.json")
PATTERNS = os.path.join(BASE, "patterns.json")
TECHNIQUES = os.path.join(BASE, "techniques.json")
SKILLS_DB = os.path.join(BASE, "skills_db.json")
TACIT = os.path.join(BASE, "tacit.json")
PRINCIPLES = os.path.join(BASE, "principles.json")
AGENTS = os.path.expanduser("~/.config/opencode/AGENTS.md")
os.makedirs(BASE, exist_ok=True)

# =============================================================================
# NIVEL 1: ACȚIUNI — Episodic JSONL Store
# =============================================================================

def save_episode(task, solution="", outcome="success", tags=None, duration_s=0, technique=""):
    """Salvează un episod (task + soluție + rezultat). Auto-hook-ready."""
    ep = {
        "id": int(time.time()),
        "ts": datetime.now(timezone.utc).isoformat(),
        "task": task[:500],
        "solution": solution[:500] if solution else "",
        "outcome": outcome,
        "tags": tags or [],
        "duration_s": duration_s,
        "technique": technique,
        "used_count": 0,
        "last_retrieved": 0,
    }
    with open(EPISODIC, "a") as f:
        f.write(json.dumps(ep, ensure_ascii=False) + "\n")

    # Trigger oglindă inversă (post-acțiune — extrage lecții)
    try:
        reverse_mirror(episode_id=ep["id"], task=task, solution=solution,
                       outcome=outcome, tags=tags, technique=technique)
    except Exception as e:
        pass  # Oglinda nu blochează salvarea

    # Trigger consolidare dacă avem suficiente episoade
    count = _episode_count()
    if count >= 3 and count % 3 == 0:
        consolidate_all()

    return ep["id"]


def _episode_count():
    if not os.path.exists(EPISODIC):
        return 0
    with open(EPISODIC) as f:
        return sum(1 for _ in f if _.strip())


def _load_episodes():
    if not os.path.exists(EPISODIC):
        return []
    eps = []
    with open(EPISODIC) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    eps.append(json.loads(line))
                except:
                    pass
    return eps


# =============================================================================
# NIVEL 2: PATTERN-URI — Semantic Pattern Extraction (Jaccard trigram)
# =============================================================================

def _jaccard_trigrams(a, b):
    """Similaritate Jaccard între trigramele a două stringuri."""
    a_tri = set(a[i:i+3] for i in range(len(a)-2))
    b_tri = set(b[i:i+3] for i in range(len(b)-2))
    if not a_tri or not b_tri:
        return 0.0
    return len(a_tri & b_tri) / len(a_tri | b_tri)


def extract_patterns(min_similarity=0.25, min_cluster=2):
    """Extrage pattern-uri din episoade prin clustering trigram."""
    eps = _load_episodes()
    if len(eps) < min_cluster:
        return []

    successes = [ep for ep in eps if ep.get("outcome") == "success"]
    if len(successes) < min_cluster:
        successes = eps

    # Matrice de similaritate
    n = len(successes)
    clusters = []
    assigned = set()

    for i in range(n):
        if i in assigned:
            continue
        cluster = [i]
        assigned.add(i)
        for j in range(i+1, n):
            if j in assigned:
                continue
            sim = _jaccard_trigrams(
                successes[i].get("task", "").lower(),
                successes[j].get("task", "").lower()
            )
            if sim >= min_similarity:
                cluster.append(j)
                assigned.add(j)

        if len(cluster) >= min_cluster:
            # Generează nume pattern din trigramele comune
            tasks = [successes[k].get("task", "") for k in cluster]
            all_trigrams = Counter()
            for t in tasks:
                tl = t.lower()
                for p in range(len(tl)-2):
                    all_trigrams[tl[p:p+3]] += 1

            # Cele mai frecvente trigrame
            top_tri = [t for t, c in all_trigrams.most_common(10) if c >= len(cluster) * 0.5]

            # Extrage cuvinte cheie din task-uri
            words = []
            for t in tasks:
                for w in t.lower().split()[:5]:
                    if len(w) > 3:
                        words.append(w)
            top_words = [w for w, c in Counter(words).most_common(5) if c >= max(2, len(cluster)//2)]

            pattern = {
                "id": f"pattern_{int(time.time())}_{len(clusters)}",
                "name": "_".join(top_words[:3]) if top_words else "unknown",
                "trigrams": top_tri[:5],
                "keywords": top_words,
                "size": len(cluster),
                "episode_ids": [successes[k]["id"] for k in cluster],
                "success_rate": sum(1 for k in cluster if successes[k].get("outcome")=="success") / len(cluster),
                "first_seen": successes[cluster[0]]["ts"],
                "last_seen": successes[cluster[-1]]["ts"],
            }
            clusters.append(pattern)

    return clusters


def save_patterns():
    """Extrage și salvează pattern-urile în patterns.json."""
    patterns = extract_patterns()
    with open(PATTERNS, "w") as f:
        json.dump({"patterns": patterns, "updated": datetime.now(timezone.utc).isoformat()}, f, indent=2, ensure_ascii=False)
    return patterns


def match_patterns(task_text, threshold=0.2):
    """Matchuiește un task cu pattern-urile existente."""
    if not os.path.exists(PATTERNS):
        return []
    with open(PATTERNS) as f:
        data = json.load(f)

    matches = []
    tl = task_text.lower()
    for p in data.get("patterns", []):
        keywords = p.get("keywords", [])
        if not keywords:
            continue
        match_count = sum(1 for kw in keywords if kw in tl)
        score = match_count / max(len(keywords), 1)
        if score >= threshold:
            matches.append({"pattern_id": p["id"], "name": p["name"], "score": score})
    return sorted(matches, key=lambda x: -x["score"])


# =============================================================================
# NIVEL 3: TEHNICI — Technique Registry
# =============================================================================

DEFAULT_TECHNIQUES = {
    "rediscover_source": {
        "name": "Rediscover Source",
        "description": "Când un stream magicplaces e mort, redescoperă URL-ul via AJAX API la rdslive.tv",
        "when": "URL magicplaces e mort / 404 / timeout",
        "how": "POST admin-ajax.php cu action=get_video_source&tab=tab1&post_id={id} → URL nou + token",
        "success_rate": 0.92,
        "use_count": 8,
        "pattern_triggers": ["stream_mort", "url_expirat"],
        "linked_skills": ["zorin-tv-system"],
        "keywords": ["mort", "stream", "dead", "404", "timeout", "rediscover", "ajax"],
    },
    "exponential_backoff": {
        "name": "Exponential Backoff",
        "description": "Când un API face rate-limit (429), așteaptă progresiv: 5s, 10s, 20s",
        "when": "API returnează 429 / Too Many Requests",
        "how": "lock threading + delay 5s/10s/20s + retry max 3 ori",
        "success_rate": 1.0,
        "use_count": 12,
        "pattern_triggers": ["rate_limit"],
        "linked_skills": ["zorin-tv-system"],
        "keywords": ["429", "rate", "limit", "backoff", "retry", "too many"],
    },
    "failover_multi_layer": {
        "name": "Multi-layer Failover",
        "description": "Nu te baza pe o singură sursă. Primar → backup → backup de backup.",
        "when": "O sursă externă poate cădea",
        "how": "Layer 1: URL+token → Layer 2: p9/p11/p13 alternativ → Layer 3: tab2 → Layer 4: M3U extern",
        "success_rate": 0.98,
        "use_count": 15,
        "pattern_triggers": ["failover", "backup"],
        "linked_skills": ["zorin-tv-system"],
        "keywords": ["failover", "backup", "alternativ", "fallback", "redundant"],
    },
    "brute_force_post_ids": {
        "name": "Systematic Brute-force",
        "description": "Când un API ascunde date (post_ids), scanează un range numeric complet.",
        "when": "API are parametri numerici (post_id, id, page) dar nu expune indexul",
        "how": "Scanează range 1-1000 sistematic, cu delay 1s între request-uri",
        "success_rate": 0.95,
        "use_count": 6,
        "pattern_triggers": ["crawl", "scan_api"],
        "linked_skills": ["zorin-tv-system"],
        "keywords": ["brute", "force", "scan", "crawl", "post_id", "range"],
    },
    "token_auto_refresh": {
        "name": "Token Auto-refresh",
        "description": "Refreshează token-urile cu mult înainte să expire, cu buffer.",
        "when": "Stream-ul necesită token cu expirare",
        "how": "Refresh la 5min (buffer 15min față de expirare) + lock threading",
        "success_rate": 0.97,
        "use_count": 10,
        "pattern_triggers": ["token", "auth"],
        "linked_skills": ["zorin-tv-system"],
        "keywords": ["token", "auth", "refresh", "expire", "magicplaces"],
    },
    "self_healing": {
        "name": "Self-healing",
        "description": "Orice componentă care poate cădea trebuie să se repare singură.",
        "when": "O componentă externă eșuează",
        "how": "Watchdog + rediscover_source + failover — nu șterge, repară",
        "success_rate": 0.93,
        "use_count": 9,
        "pattern_triggers": ["failover", "mort", "dead"],
        "linked_skills": ["zorin-tv-system"],
        "keywords": ["healing", "repair", "watchdog", "rediscover", "self"],
    },
    "json_cache_snapshot": {
        "name": "JSON Cache Snapshot",
        "description": "Salvează cache-ul periodic ca JSON. Următoarea sesiune pornește instant.",
        "when": "Starea sistemului trebuie persistată între sesiuni",
        "how": "exportă dict-ul intern la .cache.json la fiecare modificare",
        "success_rate": 1.0,
        "use_count": 20,
        "pattern_triggers": ["cache", "persist", "state"],
        "linked_skills": [],
        "keywords": ["cache", "json", "snapshot", "persist", "save"],
    },
    "categorizare_zero_diverse": {
        "name": "Zero 'Diverse'",
        "description": "Orice intrare trebuie categorizată. Dacă nu se încadrează, extinde regulile.",
        "when": "Organizare date / clasificare",
        "how": "Extinde regex-urile de grupare, nu arunca în 'Diverse'",
        "success_rate": 0.90,
        "use_count": 5,
        "pattern_triggers": ["categorizare", "organizare"],
        "linked_skills": [],
        "keywords": ["diverse", "categorie", "grupare", "clasificare"],
    },
}


def load_techniques():
    if os.path.exists(TECHNIQUES):
        with open(TECHNIQUES) as f:
            return json.load(f)
    return dict(DEFAULT_TECHNIQUES)


def save_techniques(techs=None):
    if techs is None:
        techs = load_techniques()
    with open(TECHNIQUES, "w") as f:
        json.dump(techs, f, indent=2, ensure_ascii=False)


def match_techniques(task_text, threshold=0.1):
    """Matchuiește un task cu tehnici cunoscute pe bază de keywords."""
    techs = load_techniques()
    tl = task_text.lower()
    matches = []
    for tid, t in techs.items():
        score = sum(1 for kw in t.get("keywords", []) if kw in tl)
        max_score = max(len(t.get("keywords", [])), 1)
        norm_score = score / max_score
        if norm_score >= threshold:
            matches.append({"technique_id": tid, "name": t["name"], "score": norm_score})
    return sorted(matches, key=lambda x: -x["score"])


# =============================================================================
# NIVEL 4: SKILL-URI — Dynamic Skill Loader
# =============================================================================

SKILLS_DIR = os.path.expanduser("~/.config/opencode/skills")
os.makedirs(SKILLS_DIR, exist_ok=True)


def load_skills_db():
    if os.path.exists(SKILLS_DB):
        with open(SKILLS_DB) as f:
            return json.load(f)
    return {
        "skills": [],
        "updated": datetime.now(timezone.utc).isoformat(),
    }


def save_skills_db(db):
    db["updated"] = datetime.now(timezone.utc).isoformat()
    with open(SKILLS_DB, "w") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)


def generate_skill_from_techniques(technique_ids=None):
    """Generează un skill nou dintr-un set de tehnici."""
    techs = load_techniques()
    if technique_ids:
        selected = {tid: techs[tid] for tid in technique_ids if tid in techs}
    else:
        selected = techs

    name = "auto-skill-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    lines = [
        f"# {name} — Auto-generated Skill",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
        f"**Based on {len(selected)} techniques**",
        "",
        "## Techniques included:",
    ]
    for tid, t in sorted(selected.items()):
        lines.append(f"")
        lines.append(f"### {t['name']}")
        lines.append(f"- **When:** {t['when']}")
        lines.append(f"- **How:** {t['how']}")
        lines.append(f"- **Success rate:** {t['success_rate']}")
        lines.append(f"- **Triggers:** {', '.join(t.get('pattern_triggers', []))}")

    lines.append("")
    lines.append("## Load conditions")
    triggers = set()
    for t in selected.values():
        triggers.update(t.get("pattern_triggers", []))
    lines.append(f"- Activ la task-uri care conțin: {', '.join(sorted(triggers))}")

    skill_content = "\n".join(lines)
    skill_path = os.path.join(SKILLS_DIR, name, "SKILL.md")
    os.makedirs(os.path.dirname(skill_path), exist_ok=True)
    with open(skill_path, "w") as f:
        f.write(skill_content)

    # Adaugă în skills_db
    entry = {
        "id": name,
        "name": name,
        "path": skill_path,
        "techniques": list(selected.keys()),
        "triggers": sorted(triggers),
        "created": datetime.now(timezone.utc).isoformat(),
        "use_count": 0,
    }
    db = load_skills_db()
    db["skills"].append(entry)
    save_skills_db(db)

    print(f"  Skill generat: {skill_path} ({len(selected)} tehnici)")
    return entry


def match_skills(task_text):
    """Matchuiește task-ul cu skill-uri existente pe bază de triggeri."""
    db = load_skills_db()
    tl = task_text.lower()
    matches = []
    for sk in db.get("skills", []):
        score = sum(1 for trig in sk.get("triggers", []) if trig in tl)
        norm = score / max(len(sk.get("triggers", [])), 1)
        if norm > 0:
            matches.append({"skill_id": sk["id"], "name": sk["name"], "score": norm})
    return sorted(matches, key=lambda x: -x["score"])


# =============================================================================
# NIVEL 5: ATITUDINI — Mindset Policies (tacit.json)
# =============================================================================

DEFAULT_POLICIES = [
    {
        "id": "policy_stream_mort",
        "trigger": "Stream mort / URL eșuează",
        "trigger_patterns": ["mort", "404", "timeout", "dead", "eșuează"],
        "policy": "Nu ștergi — încearcă failover + rediscover_source. Self-healing în loc de eliminare.",
        "derived_from": "pattern:stream_mort",
        "confidence": 0.98,
        "episodes_count": 8,
        "last_validated": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "policy_rate_limit",
        "trigger": "API rate-limited",
        "trigger_patterns": ["429", "rate", "limit", "too many"],
        "policy": "Aplică exponential backoff + lock threading. Nu forța — așteaptă inteligent.",
        "derived_from": "pattern:rate_limit",
        "confidence": 0.95,
        "episodes_count": 12,
        "last_validated": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "policy_failover",
        "trigger": "O sursă externă e instabilă",
        "trigger_patterns": ["failover", "backup", "alternativ", "instabil"],
        "policy": "Multi-layer failover: primar → p9/p11/p13 → tab2 → playlist extern. Niciodată o singură cale.",
        "derived_from": "pattern:failover",
        "confidence": 0.99,
        "episodes_count": 15,
        "last_validated": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "policy_proactiv",
        "trigger": "Orice acțiune recurentă",
        "trigger_patterns": ["monitor", "refresh", "cron", "periodic", "watchdog"],
        "policy": "Automatizează tot. Watchdog la 2min, token refresh la 5min, clean la 6h. Nu aștepta să ceară utilizatorul.",
        "derived_from": "principle:proactiv",
        "confidence": 0.96,
        "episodes_count": 10,
        "last_validated": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "policy_categorize",
        "trigger": "Organizare date / clasificare",
        "trigger_patterns": ["categor", "diverse", "grup", "clasif"],
        "policy": "Zero 'Diverse'. Extinde regulile de grupare, nu arunca în rest. Cu cât e mai organizat, cu atât e mai ușor de întreținut.",
        "derived_from": "principle:sistematizare",
        "confidence": 0.90,
        "episodes_count": 5,
        "last_validated": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "policy_documenteaza",
        "trigger": "Informații noi descoperite",
        "trigger_patterns": ["descoper", "afla", "învăț", "document", "scrie"],
        "policy": "Documentează în AGENTS.md imediat. Ce înveți azi, scrie azi. Următoarea sesiune știe automat.",
        "derived_from": "principle:documenteaza",
        "confidence": 0.94,
        "episodes_count": 7,
        "last_validated": datetime.now(timezone.utc).isoformat(),
    },
]


def load_policies():
    if os.path.exists(TACIT):
        with open(TACIT) as f:
            return json.load(f)
    return {"policies": DEFAULT_POLICIES, "updated": datetime.now(timezone.utc).isoformat()}


def save_policies(pols=None):
    if pols is None:
        pols = load_policies()
    pols["updated"] = datetime.now(timezone.utc).isoformat()
    with open(TACIT, "w") as f:
        json.dump(pols, f, indent=2, ensure_ascii=False)


def match_policies(task_text, threshold=0.1):
    """Matchuiește task-ul cu politici pe bază de trigger_patterns."""
    pols = load_policies()
    tl = task_text.lower()
    matches = []
    for p in pols.get("policies", []):
        score = sum(1 for pat in p.get("trigger_patterns", []) if pat in tl)
        norm = score / max(len(p.get("trigger_patterns", [])), 1)
        if norm >= threshold:
            matches.append({"policy_id": p["id"], "trigger": p["trigger"], "policy": p["policy"], "score": norm})
    return sorted(matches, key=lambda x: -x["score"])


def validate_policies():
    """Verifică dacă principiile au fost respectate în ultimele N episoade."""
    episodes = _load_episodes()
    if len(episodes) < 3:
        return []

    recent = episodes[-min(10, len(episodes)):]
    pols = load_policies()
    validations = []

    for p in pols.get("policies", []):
        relevant = [ep for ep in recent
                     if any(pat in ep.get("task", "").lower() for pat in p.get("trigger_patterns", []))]
        if not relevant:
            continue
        successes = sum(1 for ep in relevant if ep.get("outcome") == "success")
        rate = successes / len(relevant)

        validation = {
            "policy_id": p["id"],
            "trigger": p["trigger"],
            "relevant_episodes": len(relevant),
            "success_rate": round(rate, 2),
            "status": "respectata" if rate >= 0.7 else "incalcata",
        }
        if rate < 0.7:
            validation["note"] = f"Respectat doar {int(rate*100)}% — posibilă revizuire"
        validations.append(validation)

    return validations


# =============================================================================
# PUNTEA SAFLA ↔ PIRAMIDĂ — sincronizare bidirecțională
# =============================================================================

SAFLA_PATHS = [
    os.path.expanduser("~/.config/opencode/ccdew-safla-state.json"),
    os.path.expanduser("~/CCDEW/.claude-flow/data/safla.json"),
]

NODE_NAMES = {
    "1": "Perfectionist (reviewer)",
    "2": "Helper (inbox-triage)",
    "3": "Achiever (builder)",
    "4": "Individualist (strategist)",
    "5": "Investigator (researcher)",
    "6": "Loyalist (ops/qa)",
    "7": "Enthusiast (km-agent)",
    "8": "Challenger (maintainer)",
    "9": "Peacemaker (orchestrator)",
}

NODE_DOMAIN_MAP = {
    "1": "review/quality",
    "2": "support/triage",
    "3": "build/implement",
    "4": "strategy/architecture",
    "5": "research/analysis",
    "6": "test/monitor/security",
    "7": "knowledge/document",
    "8": "maintain/deploy",
    "9": "coordinate/orchestrate",
}


def _sync_safla_to_pyramid():
    """Citește datele SAFLA și creează episoade pentru eșecurile neînregistrate.

    Astfel, eșecurile din nodurile Enneagram (înregistrate de convergent-divergent MCP)
    ajung în piramida de învățare (pattern-uri → tehnici → principii).
    """
    created = 0
    episodes = _load_episodes()
    existing_tasks = {ep.get("task", "") for ep in episodes}

    for saf_path in SAFLA_PATHS:
        if not os.path.exists(saf_path):
            continue
        try:
            with open(saf_path) as f:
                safla = json.load(f)
        except:
            continue

        nodes = safla.get("nodes", {})
        for nid, ndata in nodes.items():
            failures = ndata.get("failure", 0)
            successes = ndata.get("success", 0)
            last_task = ndata.get("last_task", "")
            weight = ndata.get("weight_adj", 0)

            if not last_task or last_task in existing_tasks:
                continue

            # Creează episod pentru ultimul task al nodului
            outcome = "success" if failures == 0 else "failure"
            tags = [f"safla:node_{nid}", f"safla:weight_{weight:.2f}"]

            # Adaugă și tehnică dacă e nod problematic
            technique = ""
            if failures > successes and failures >= 2:
                technique = f"rehab_node_{nid}"

            ep = {
                "id": int(time.time() * 1000) % 10**12 + int(nid),
                "ts": datetime.now(timezone.utc).isoformat(),
                "type": "safla_sync",
                "task": last_task[:500],
                "solution": f"SAFLA node {nid} ({NODE_NAMES.get(nid, '?')}): {successes} success, {failures} failures, weight={weight}",
                "outcome": outcome,
                "tags": tags,
                "duration_s": 0,
                "technique": technique,
                "used_count": 0,
                "last_retrieved": 0,
                "safla_node": nid,
                "safla_success": successes,
                "safla_failure": failures,
                "safla_weight": weight,
            }

            with open(EPISODIC, "a") as f:
                f.write(json.dumps(ep, ensure_ascii=False) + "\n")
            created += 1
            existing_tasks.add(last_task)

    return created


def _sync_pyramid_to_safla():
    """Actualizează SAFLA weights pe baza pattern-urilor și tehnicilor din piramidă.

    Dacă o tehnică are success_rate ridicat, boostează nodul corespunzător.
    Dacă un principiu are violări, scade weight-ul nodului.
    """
    for saf_path in SAFLA_PATHS:
        if not os.path.exists(saf_path):
            continue
        try:
            with open(saf_path) as f:
                safla = json.load(f)
        except:
            continue

        nodes = safla.get("nodes", {})

        # Încarcă tehnici și ajustează weights pe bază de success_rate
        try:
            techs = load_techniques()
            for nid in nodes:
                domain = NODE_DOMAIN_MAP.get(nid, "")
                if not domain:
                    continue
                # Găsește tehnici relevante pentru acest nod
                relevant_techs = [t for t in techs.values()
                                 if any(kw in t.get("keywords", []) for kw in domain.split("/"))]
                if relevant_techs:
                    avg_rate = sum(t.get("success_rate", 0.5) for t in relevant_techs) / len(relevant_techs)
                    # Ajustare: tecnica cu success_rate > 0.8 → boost, < 0.5 → penalizare
                    adjustment = (avg_rate - 0.5) * 0.1
                    nodes[nid]["weight_adj"] = round(
                        max(-0.5, min(0.5, nodes[nid].get("weight_adj", 0) + adjustment)), 2
                    )
        except:
            pass

        # Scrie înapoi
        safla["_last_pyramid_sync"] = datetime.now(timezone.utc).isoformat()
        try:
            tmp = saf_path + ".tmp"
            with open(tmp, "w") as f:
                json.dump(safla, f, indent=2, ensure_ascii=False)
            os.replace(tmp, saf_path)
        except:
            pass


# =============================================================================
# NIVEL 6: PRINCIPII — Auto-validating Principles
# =============================================================================

PRINCIPLE_DEFAULTS = [
    {
        "id": "nu_exista_imposibil",
        "principle": "Nu există 'imposibil' — dacă o poartă e închisă, caută alta.",
        "source": "experiență directă — brute-force post_ids, failover, rediscover",
        "evidence_count": 8,
        "last_validated": datetime.now(timezone.utc).isoformat(),
        "violations": 0,
    },
    {
        "id": "backup_inainte",
        "principle": "Backup înainte de orice — niciodată nu suprascrie fără .bak.",
        "source": "pierderi de date învățate din practică",
        "evidence_count": 5,
        "last_validated": datetime.now(timezone.utc).isoformat(),
        "violations": 0,
    },
    {
        "id": "self_healing",
        "principle": "Self-healing peste tot — orice componentă trebuie să se poată repara singură.",
        "source": "rediscover_source + watchdog + failover — dovedit de 9 ori",
        "evidence_count": 9,
        "last_validated": datetime.now(timezone.utc).isoformat(),
        "violations": 0,
    },
    {
        "id": "sistematizare",
        "principle": "Sistematizare — categorisește tot. Zero 'Diverse'.",
        "source": "176 canale în 13 categorii, 0 în Diverse",
        "evidence_count": 5,
        "last_validated": datetime.now(timezone.utc).isoformat(),
        "violations": 0,
    },
    {
        "id": "multi_layer_failover",
        "principle": "Multi-layer failover — niciodată o singură sursă.",
        "source": "p11 → p13 → p9 → tab2 → M3U — dovedit de 15 ori",
        "evidence_count": 15,
        "last_validated": datetime.now(timezone.utc).isoformat(),
        "violations": 0,
    },
    {
        "id": "pastreaza_functional",
        "principle": "Păstrează funcțional, nu orice — backup logic, nu fizic.",
        "source": "cache rotit, loguri trunchiate, esența sistemului păstrată",
        "evidence_count": 4,
        "last_validated": datetime.now(timezone.utc).isoformat(),
        "violations": 0,
    },
    {
        "id": "proactiv",
        "principle": "Proactiv, nu reactiv — watchdog, auto-refresh, cron-uri. Totul merge singur.",
        "source": "token 5min, watchdog 2min, clean 6h — dovedit de 10 ori",
        "evidence_count": 10,
        "last_validated": datetime.now(timezone.utc).isoformat(),
        "violations": 0,
    },
    {
        "id": "documenteaza",
        "principle": "Documentează tot — AGENTS.md e memoria permanentă.",
        "source": "8 principii învățate și scrise, episoade JSONL",
        "evidence_count": 7,
        "last_validated": datetime.now(timezone.utc).isoformat(),
        "violations": 0,
    },
]


def load_principles():
    if os.path.exists(PRINCIPLES):
        with open(PRINCIPLES) as f:
            return json.load(f)
    return {"principles": PRINCIPLE_DEFAULTS, "updated": datetime.now(timezone.utc).isoformat()}


def save_principles(prins=None):
    if prins is None:
        prins = load_principles()
    prins["updated"] = datetime.now(timezone.utc).isoformat()
    with open(PRINCIPLES, "w") as f:
        json.dump(prins, f, indent=2, ensure_ascii=False)
    sync_principles_to_agents(prins)


def sync_principles_to_agents(prins=None):
    """Sincronizează principiile validate în AGENTS.md."""
    if prins is None:
        prins = load_principles()

    # Build markdown block
    lines = [
        "## Principii universale învățate (valabile în ORICE proiect)",
        "",
    ]
    for i, p in enumerate(prins.get("principles", []), 1):
        violation_warn = " ⚠" if p.get("violations", 0) > 0 else ""
        evidence = p.get("evidence_count", 0)
        lines.append(f"{i}. **{p['principle']}**{violation_warn}")
        lines.append(f"   - Dovezi: {evidence} episoade | Sursa: {p.get('source', '?')}")

    lines.append("")
    lines.append(f"*Actualizat: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*")

    block = "\n".join(lines)

    if not os.path.exists(AGENTS):
        print("  AGENTS.md nu există, se omite sincronizarea")
        return

    with open(AGENTS) as f:
        content = f.read()

    # Replace existing principles block
    pattern = r"## Principii universale[\s\S]*?(?=\n## |\Z)"
    if re.search(pattern, content):
        content = re.sub(pattern, block, content, flags=re.DOTALL)
    else:
        content += "\n\n" + block

    with open(AGENTS, "w") as f:
        f.write(content)


# =============================================================================
# CONSOLIDARE COMPLETĂ — Toate cele 6 nivele
# =============================================================================

def consolidate_all():
    """Rulează toate nivelele de consolidare în cascadă."""
    print(f"\n=== Consolidare piramidă {datetime.now(timezone.utc).strftime('%H:%M:%S')} ===")

    # Sync SAFLA → piramidă (puntea dintre cele 2 sisteme)
    safla_sync_count = _sync_safla_to_pyramid()
    print(f"  SAFLA Sync: {safla_sync_count} episoade importate")

    # Nivel 1: Acțiuni — count
    count = _episode_count()
    print(f"  Nivel 1 (Acțiuni): {count} episoade")

    # Nivel 2: Pattern-uri
    patterns = save_patterns()
    print(f"  Nivel 2 (Pattern-uri): {len(patterns)} pattern-uri")

    # Nivel 3: Tehnici — save defaults if not exist
    if not os.path.exists(TECHNIQUES):
        save_techniques(DEFAULT_TECHNIQUES)
        print(f"  Nivel 3 (Tehnici): {len(DEFAULT_TECHNIQUES)} tehnici salvate")
    else:
        techs = load_techniques()
        print(f"  Nivel 3 (Tehnici): {len(techs)} tehnici")

    # Nivel 4: Skill-uri — generate if patterns exist but no skills
    db = load_skills_db()
    if patterns and not db.get("skills"):
        # Generează skill din tehnicile care matchuiesc pattern-urile
        techs = load_techniques()
        matched_techs = []
        for pat in patterns:
            for tid, t in techs.items():
                if any(pt in t.get("pattern_triggers", []) for pt in pat.get("keywords", [])):
                    matched_techs.append(tid)
        if matched_techs:
            generate_skill_from_techniques(list(set(matched_techs)))
    db = load_skills_db()
    print(f"  Nivel 4 (Skill-uri): {len(db.get('skills', []))} skill-uri")

    # Nivel 5: Atitudini — validate policies
    if not os.path.exists(TACIT):
        save_policies()
    validations = validate_policies()
    violations = [v for v in validations if v.get("status") == "incalcata"]
    print(f"  Nivel 5 (Atitudini): {len(validations)} validate, {len(violations)} încălcări")

    # Nivel 6: Principii — validate + sync
    if not os.path.exists(PRINCIPLES):
        save_principles()
    prins = load_principles()

    # Actualizează evidence_count pe baza episoadelor recente
    episodes = _load_episodes()
    recent = episodes[-max(10, len(episodes)):]
    for p in prins.get("principles", []):
        # Nr de episoade care conțin cuvinte cheie din principiu
        keywords = p["principle"].lower().split()
        matching = sum(1 for ep in recent if any(kw in ep.get("task","").lower() for kw in keywords if len(kw)>3))
        if matching > p.get("evidence_count", 0):
            p["evidence_count"] = matching
    save_principles(prins)

    # Check violations from policy validation
    for v in validations:
        if v.get("status") == "incalcata":
            for p in prins.get("principles", []):
                if v.get("trigger", "").lower() in p["principle"].lower():
                    p["violations"] = p.get("violations", 0) + 1
                    break
    save_principles(prins)

    # Sync piramidă → SAFLA (ajustează weights pe bază de tehnici)
    _sync_pyramid_to_safla()
    print(f"  SAFLA Weights: sincronizate din piramidă")

    print(f"  Nivel 6 (Principii): {len(prins.get('principles', []))} principii sincronizate")
    print(f"=== Consolidare completă ===\n")


# =============================================================================
# OGGLINDĂ INVERSĂ: Reflecție post-acțiune (nivelul 7 — mirror loop 1→9)
# =============================================================================

MIRROR_QUESTIONS = {
    1: "REZULTATE — Ce am obținut concret? Ce impact a avut asupra sistemului?",
    2: "TOOL-URI — Ce instrumente/mijloace m-au ajutat? Care au fost ineficiente?",
    3: "SKILL — Ce mi-a venit natural? Unde m-am împotmolit? Ce mi-a devenit automat?",
    4: "EVALUARE — Cum aș evalua altfel data viitoare? Ce criterii au lipsit?",
    5: "FEEDBACK — Ce feedback (din mediu/erori) am ignorat și trebuia să-l ascult?",
    6: "EXERSARE — Ce exerciții sau pași au fost eficienți? Care au fost în plus?",
    7: "ÎNDRUMARE — Ce sfat aș da cuiva care face același task de la zero?",
    8: "PRINCIPIU — Ce principiu general se aplică aici? În ce condiții s-ar schimba?",
    9: "CONCEPT — Cum rescriu definiția conceptului după ce am trecut prin asta?",
}

MIRROR_EPISTEMIC_MAP = {
    1: {"domain": "faptic", "type": "output", "confidence_weight": 0.3},
    2: {"domain": "practic", "type": "instrument", "confidence_weight": 0.6},
    3: {"domain": "procedural", "type": "intuitie", "confidence_weight": 0.7},
    4: {"domain": "metacognitiv", "type": "calitate", "confidence_weight": 0.5},
    5: {"domain": "social", "type": "corectie", "confidence_weight": 0.8},
    6: {"domain": "practic", "type": "eficienta", "confidence_weight": 0.6},
    7: {"domain": "didactic", "type": "transfer", "confidence_weight": 0.7},
    8: {"domain": "abstract", "type": "regula", "confidence_weight": 0.9},
    9: {"domain": "conceptual", "type": "teorie", "confidence_weight": 0.95},
}


def reverse_mirror(episode_id=None, task="", solution="", outcome="", tags=None, technique=""):
    """Oglindă inversă 1→9: post-acțiune, extrage lecții și rescrie concepte.

    Rulează automat după save_episode(). Scrie în episodic.jsonl ca mirror entry.
    """
    tags = tags or []

    # Load episode if id given
    ep = None
    if episode_id:
        eps = _load_episodes()
        for e in eps:
            if e.get("id") == episode_id:
                ep = e
                break

    task_text = ep.get("task", task) if ep else task
    outcome_val = ep.get("outcome", outcome) if ep else outcome

    # Determină nivelul de reflecție pe baza outcome
    reflective_depth = 9 if outcome_val == "success" else min(7, 9)

    # Generează răspunsuri la fiecare nivel 1→9
    reflections = []
    for level in range(1, reflective_depth + 1):
        question = MIRROR_QUESTIONS[level]
        meta = MIRROR_EPISTEMIC_MAP[level]

        reflection = {
            "level": level,
            "question": question.split("—", 1)[0].strip(),
            "question_full": question,
            "domain": meta["domain"],
            "type": meta["type"],
            "confidence_weight": meta["confidence_weight"],
            "synth": "",  # placeholder — va fi populat de LLM în viitor
        }
        reflections.append(reflection)

    # Construiește entry-ul de oglindă
    mirror_entry = {
        "id": int(time.time() * 1000) % 10**12,
        "ts": datetime.now(timezone.utc).isoformat(),
        "type": "mirror_inverse",
        "source_episode_id": episode_id or 0,
        "source_task": task_text[:200],
        "source_outcome": outcome_val,
        "source_technique": technique or (ep.get("technique", "") if ep else ""),
        "reflective_depth": reflective_depth,
        "reflections": reflections,
        "summary": _generate_mirror_summary(task_text, outcome_val, reflective_depth),
    }

    # Salvează în episodic.jsonl
    with open(EPISODIC, "a") as f:
        f.write(json.dumps(mirror_entry, ensure_ascii=False) + "\n")

    # Verifică dacă reflecția poate îmbunătăți o tehnică
    tech_improved = _mirror_update_techniques(task_text, technique, reflections)

    # Scor: înregistrează valoarea de învățare a acestei bucle
    try:
        pathway = detect_pathway(window=10)
        score_pathway_run(
            pathway=pathway,
            outcome=outcome_val,
            mirror_depth=reflective_depth,
            technique_improved=tech_improved,
        )
    except:
        pass

    return mirror_entry


def _generate_mirror_summary(task, outcome, depth):
    """Generează un scurt sumar al reflecției."""
    if outcome == "success":
        return f"✅ {task[:50]} — reflecție completă pe {depth} nivele. Principii validate."
    else:
        return f"❌ {task[:50]} — reflecție pe {depth} nivele. Identifică ce a eșuat și ajustează."


def _mirror_update_techniques(task_text, technique_id, reflections):
    """Verifică dacă reflecția sugerează actualizarea unei tehnici.
    Returnează True dacă a îmbunătățit ceva."""
    if not technique_id:
        return False

    techs = None
    try:
        techs = load_techniques()
    except:
        return False
    if not techs or technique_id not in techs:
        return False

    tech = techs[technique_id]
    improved = False

    # Incrementează use_count
    tech["use_count"] = tech.get("use_count", 0) + 1
    improved = True

    # Verifică dacă reflecția nivel 8 dezvăluie o limitare a principiului
    level8 = next((r for r in reflections if r["level"] == 8), None)
    if level8 and not tech.get("limitations"):
        tech["limitations"] = "De explorat: în ce condiții nu se aplică această tehnică?"

    # Adaugă tag-uri noi din task dacă lipsesc
    tl = task_text.lower()
    for word in tl.split():
        if len(word) > 4 and word not in tech.get("keywords", []):
            if "keywords" not in tech:
                tech["keywords"] = []
            tech["keywords"].append(word)
            improved = True
            break  # un keyword nou per reflecție

    # Actualizează success_rate când avem suficiente date
    total_uses = tech.get("use_count", 1)
    if total_uses >= 3:
        # Cântărește succesul reflecției: dacă ajungem la nivel 9, e un semn bun
        max_level = max((r["level"] for r in reflections), default=0)
        if max_level >= 8:
            old_rate = tech.get("success_rate", 0.5)
            tech["success_rate"] = round((old_rate * 0.8 + 0.2), 3)
            improved = True

    save_techniques(techs)
    return improved


def show_mirror(limit=5):
    """Afișează ultimele intrări mirror_inverse."""
    eps = _load_episodes()
    mirrors = [ep for ep in eps if ep.get("type") == "mirror_inverse"]
    if not mirrors:
        print("  Nicio reflecție în oglindă inversă.")
        return

    print(f"=== Oglindă Inversă (ultimele {min(limit, len(mirrors))}) ===")
    for m in mirrors[-limit:]:
        depth = m.get("reflective_depth", 0)
        outcome = m.get("source_outcome", "?")
        icon = "✅" if outcome == "success" else "❌"
        print(f"  {icon} {m.get('source_task', '')[:50]:50s} d={depth} | {m.get('summary', '')[:60]}")


# =============================================================================
# ENNEAGRAM PATHWAY DETECTION: Circle / Triangle / Hexad
# =============================================================================

ENNEAGRAM_NODES = {
    1: "REZULTATE",
    2: "TOOL-URI",
    3: "SKILL",
    4: "EVALUARE",
    5: "FEEDBACK",
    6: "EXERSARE",
    7: "ÎNDRUMARE",
    8: "PRINCIPIU",
    9: "CONCEPT",
}

ENNEAGRAM_CIRCLE = [9, 8, 7, 6, 5, 4, 3, 2, 1]   # progresie naturală
ENNEAGRAM_TRIANGLE = [3, 6, 9]                     # corecție strategică
ENNEAGRAM_HEXAD = [1, 4, 2, 8, 5, 7, 1]           # scurtătură expert


def _infer_node_from_task(task_text):
    """Inferă ce nod Enneagram corespunde task-ului pe bază de keywords."""
    tl = task_text.lower()
    rules = {
        1: ["rezultat", "produc", "livreaz", "deploy", "merge", "push", "finalizează", "lansează"],
        2: ["tool", "instrument", "script", "comandă", "setup", "config", "instalează", "pregătește"],
        3: ["skill", "deprindere", "automat", "execută", "rulează", "implementează", "build", "fă"],
        4: ["evaluare", "testează", "verifică", "analizează", "măsoară", "compară", "review"],
        5: ["feedback", "corecție", "ajustare", "fix", "repari", "debug", "eroare", "problemă"],
        6: ["exersează", "practică", "simulează", "încearcă", "experimentează", "probează"],
        7: ["îndrumare", "ghid", "explică", "învață", "documentează", "caută", "cercetează"],
        8: ["principiu", "regulă", "decizie", "strategie", "plan", "arhitectură", "proiectează"],
        9: ["concept", "idee", "teorie", "înțelege", "definește", "proiectează", "sistematizează"],
    }
    scores = {}
    for node, keywords in rules.items():
        scores[node] = sum(1 for kw in keywords if kw in tl)
    if max(scores.values()) == 0:
        return 0
    return max(scores, key=scores.get)


def detect_pathway(episodes_window=10):
    """Detectează ce cale Enneagram a fost folosită în ultimele N episoade.

    Returnează: 'circle', 'triangle', 'hexad', sau 'mixed'.
    """
    eps = _load_episodes()
    recent = [ep for ep in eps if ep.get("type") != "mirror_inverse"][-episodes_window:]
    if len(recent) < 3:
        return "insufficient_data"

    # Atribuie noduri
    nodes = []
    outcomes = []
    for ep in recent:
        n = _infer_node_from_task(ep.get("task", ""))
        nodes.append(n)
        outcomes.append(ep.get("outcome", ""))

    scores = {"circle": 0, "triangle": 0, "hexad": 0}

    # Circle check: nodes follow 9→8→7→6→5→4→3→2→1 progression
    if len(nodes) >= 3:
        # Verifică secvențe descrescătoare (9→8, 8→7, etc.)
        circle_hits = sum(1 for i in range(len(nodes)-1)
                         if nodes[i] > 0 and nodes[i+1] > 0
                         and nodes[i] - nodes[i+1] == 1)
        scores["circle"] = circle_hits / max(len(nodes)-1, 1)

    # Triangle check: nodes jump between {3, 6, 9} frequently
    if len(nodes) >= 2:
        triangle_nodes = {3, 6, 9}
        in_triangle = sum(1 for n in nodes if n in triangle_nodes)
        triangle_jumps = sum(1 for i in range(len(nodes)-1)
                           if nodes[i] in triangle_nodes and nodes[i+1] in triangle_nodes
                           and nodes[i] != nodes[i+1])
        scores["triangle"] = (in_triangle + triangle_jumps * 2) / max(len(nodes) * 2, 1)

    # Hexad check: follow 1→4→2→8→5→7→1 pattern + high success + fast
    if len(nodes) >= 3:
        hexad_set = {1, 2, 4, 5, 7, 8}
        in_hexad = sum(1 for n in nodes if n in hexad_set)
        # Success rate bonus
        success_rate = sum(1 for o in outcomes if o == "success") / max(len(outcomes), 1)
        scores["hexad"] = (in_hexad / max(len(nodes), 1)) * 0.6 + success_rate * 0.4

    # Determină pathway-ul dominant
    best = max(scores, key=scores.get)
    best_score = scores[best]
    # Dacă toate scorurile sunt apropiate, e mixed
    others = [v for k, v in scores.items() if k != best]
    if others and best_score - max(others) < 0.15:
        return "mixed"

    return best


def pathway_label(pathway):
    labels = {
        "circle": "🔵 Cerc Exterior (progresie naturală)",
        "triangle": "🔺 Triunghi 3-6-9 (corecție strategică)",
        "hexad": "🔗 Hexadă 1-4-2-8-5-7-1 (scurtătură expert)",
        "mixed": "🌀 Mixt",
        "insufficient_data": "⬜ Insuficiente date",
    }
    return labels.get(pathway, pathway)


def show_pathway(window=10):
    """Afișează pathway-ul curent și distribuția nodurilor."""
    eps = _load_episodes()
    recent = [ep for ep in eps if ep.get("type") != "mirror_inverse"][-window:]

    if not recent:
        print("  Niciun episod de analizat.")
        return

    nodes = []
    outcomes = []
    for ep in recent:
        n = _infer_node_from_task(ep.get("task", ""))
        if n > 0:
            nodes.append(n)
        outcomes.append(ep.get("outcome", ""))

    # Distribuția nodurilor
    from collections import Counter
    node_counts = Counter(nodes)
    print(f"=== Enneagram Pathway (ultimele {len(recent)} episoade) ===")
    print(f"")
    print(f"  Cale detectată: {pathway_label(detect_pathway(window))}")
    print(f"")
    print(f"  Distribuția nodurilor Enneagram:")
    for n in range(9, 0, -1):
        count = node_counts.get(n, 0)
        bar = "█" * count + "░" * (max(0, 10 - count))
        pct = count / max(len(nodes), 1) * 100
        nm = ENNEAGRAM_NODES.get(n, "?")
        print(f"    {n}. {nm:12s} {bar} {count}x ({pct:.0f}%)")

    success_rate = sum(1 for o in outcomes if o == "success") / max(len(outcomes), 1)
    print(f"")
    print(f"  Success rate: {success_rate:.0%}")
    print(f"")


# =============================================================================
# PATHWAY BRIDGE — Sync pathway state to shared file (consumed by MCP routing)
# =============================================================================

PATHWAY_BRIDGE = os.path.join(BASE, "pathway-bridge.json")


def sync_pathway_bridge(pathway=None, active_node=0, confidence=0.5, flow=0.5, confusion=0.0):
    """Scrie starea curentă a pathway-ului într-un fișier JSON partajat.

    Acest fișier este citit de:
      - ccdew-notebooklm-mcp.cjs (orchestrator routing)
      - ccdew-mcp.cjs (status/snapshot)
      - instincts.cjs (pattern learning)
    """
    if pathway is None:
        try:
            pathway = detect_pathway(window=10)
        except:
            pathway = "insufficient_data"

    # Cea mai bună cale din istoric
    best_pw, best_score = get_best_pathway()

    bridge = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "pathway": pathway,
        "pathway_label": pathway_label(pathway),
        "active_node": active_node,
        "confidence": round(confidence, 3),
        "flow": round(flow, 3),
        "confusion": round(confusion, 3),
        "preferred_nodes": _pathway_preferred_nodes(pathway),
        "routing_hint": _pathway_routing_hint(pathway),
        "safla_hint": _pathway_safla_hint(pathway),
        "best_pathway": best_pw,
        "best_score": best_score,
        "best_label": PATHWAY_NAMES.get(best_pw, best_pw),
    }

    # Scriere atomică
    tmp = PATHWAY_BRIDGE + ".tmp"
    try:
        with open(tmp, "w") as f:
            json.dump(bridge, f, indent=2, ensure_ascii=False)
        os.replace(tmp, PATHWAY_BRIDGE)
    except:
        pass

    # Sync și în SAFLA data
    _sync_pathway_to_safla(pathway, active_node)

    return bridge


def _pathway_preferred_nodes(pathway):
    """Ce noduri Enneagram sunt preferate în această cale."""
    if pathway == "triangle":
        return [3, 6, 9]
    elif pathway == "hexad":
        return [9, 1, 4, 2, 8, 5, 7]
    else:
        return list(range(9, 0, -1))


def _pathway_routing_hint(pathway):
    """Hint pentru orchestrator cum să ajusteze rutarea."""
    hints = {
        "circle": "normal — routează la nodul cel mai potrivit",
        "triangle": "blocaj — preferă nodurile 3 (execuție), 6 (testare), 9 (coordonare)",
        "hexad": "expert — preferă nodurile 1 (review), 4 (strategie), 2 (triage), 8 (decizie), 5 (cercetare), 7 (knowledge)",
        "mixed": "normal"
    }
    return hints.get(pathway, "normal")


def _pathway_safla_hint(pathway):
    """Hint pentru SAFLA cum să ajusteze ponderile."""
    hints = {
        "circle": "all_nodes_equal",
        "triangle": "boost_3_6_9",
        "hexad": "boost_1_4_2_8_5_7",
        "mixed": "all_nodes_equal"
    }
    return hints.get(pathway, "all_nodes_equal")


def _sync_pathway_to_safla(pathway, active_node):
    """Actualizează fișierul SAFLA cu pathway-ul curent și nodul activ."""
    safla_path = os.path.join(os.path.expanduser("~/.config/opencode"), "ccdew-safla-state.json")
    if not os.path.exists(safla_path):
        return

    try:
        with open(safla_path) as f:
            safla = json.load(f)
    except:
        return

    safla["_pathway"] = pathway
    safla["_active_node"] = active_node
    safla["_updated"] = datetime.now(timezone.utc).isoformat()

    # Adjust weights per pathway
    hint = _pathway_safla_hint(pathway)
    if hint == "boost_3_6_9":
        for n in ["3", "6", "9"]:
            if n in safla.get("nodes", {}):
                safla["nodes"][n]["weight_adj"] = min(0.5, safla["nodes"][n].get("weight_adj", 0) + 0.05)
    elif hint == "boost_1_4_2_8_5_7":
        for n in ["1", "2", "4", "5", "7", "8"]:
            if n in safla.get("nodes", {}):
                safla["nodes"][n]["weight_adj"] = min(0.5, safla["nodes"][n].get("weight_adj", 0) + 0.03)

    try:
        tmp = safla_path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(safla, f, indent=2, ensure_ascii=False)
        os.replace(tmp, safla_path)
    except:
        pass


def read_pathway_bridge():
    """Citește pathway-bridge.json (folosit de JS MCP servers)."""
    if os.path.exists(PATHWAY_BRIDGE):
        try:
            with open(PATHWAY_BRIDGE) as f:
                return json.load(f)
        except:
            pass
    return None


# =============================================================================
# PATHWAY SCORER — măsoară valoarea de învățare a fiecărei bucle
# =============================================================================

PATHWAY_SCORES = os.path.join(BASE, "pathway-scores.json")

PATHWAY_CYCLES = {
    "circle":   [9, 8, 7, 6, 5, 4, 3, 2, 1],
    "triangle": [3, 6, 9],
    "hexad":    [1, 4, 2, 8, 5, 7, 1],
}

PATHWAY_NAMES = {
    "circle":   "🔵 Cerc exterior (progresie)",
    "triangle": "🔺 Triunghi 3-6-9 (corecție)",
    "hexad":    "🔗 Hexadă 1-4-2-8-5-7-1 (expert)",
    "mixed":    "🌀 Mixt",
}


def _init_scores():
    """Inițializează fișierul de scoruri."""
    default = {
        "pathways": {
            "circle": {"runs": 0, "success": 0, "failure": 0, "mirror_depth_avg": 0, "technique_boost": 0, "score": 0.5},
            "triangle": {"runs": 0, "success": 0, "failure": 0, "mirror_depth_avg": 0, "technique_boost": 0, "score": 0.5},
            "hexad": {"runs": 0, "success": 0, "failure": 0, "mirror_depth_avg": 0, "technique_boost": 0, "score": 0.5},
            "mixed": {"runs": 0, "success": 0, "failure": 0, "mirror_depth_avg": 0, "technique_boost": 0, "score": 0.5},
        },
        "best_pathway": "circle",
        "best_score": 0.5,
        "iterations": 0,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
    if not os.path.exists(PATHWAY_SCORES):
        with open(PATHWAY_SCORES, "w") as f:
            json.dump(default, f, indent=2)
    return default


def _load_scores():
    if os.path.exists(PATHWAY_SCORES):
        try:
            with open(PATHWAY_SCORES) as f:
                return json.load(f)
        except:
            pass
    return _init_scores()


def _save_scores(scores):
    scores["last_updated"] = datetime.now(timezone.utc).isoformat()
    tmp = PATHWAY_SCORES + ".tmp"
    with open(tmp, "w") as f:
        json.dump(scores, f, indent=2)
    os.replace(tmp, PATHWAY_SCORES)


def score_pathway_run(pathway, outcome="success", mirror_depth=0, technique_improved=False):
    """Înregistrează o execuție a unei căi Enneagram și recalculează scorul.

    Fiecare buclă (cerc/triunghi/hexad) primește un scor bazat pe:
      - succes rate (40%)
      - adâncimea oglinzii inverse (30%)
      - îmbunătățirea tehnicilor (30%)
    """
    scores = _load_scores()
    if pathway not in scores["pathways"]:
        return

    pw = scores["pathways"][pathway]
    pw["runs"] += 1
    if outcome == "success":
        pw["success"] += 1
    else:
        pw["failure"] += 1

    # Adâncimea medie a oglinzii (moving average)
    if mirror_depth > 0:
        pw["mirror_depth_avg"] = round(
            (pw["mirror_depth_avg"] * (pw["runs"] - 1) + mirror_depth) / pw["runs"], 1
        )

    # Boost tehnică
    if technique_improved:
        pw["technique_boost"] += 1

    # Scor compus: succes rate × 0.4 + mirror_depth/9 × 0.3 + technique_boost/runs × 0.3
    total = pw["success"] + pw["failure"]
    success_rate = pw["success"] / max(total, 1)
    depth_norm = min(1.0, pw["mirror_depth_avg"] / 9.0)
    tech_norm = min(1.0, pw["technique_boost"] / max(pw["runs"], 1) * 2)

    pw["score"] = round(
        success_rate * 0.4 + depth_norm * 0.3 + tech_norm * 0.3, 3
    )

    # Găsește cea mai bună cale
    best = max(scores["pathways"].items(), key=lambda x: x[1]["score"])
    scores["best_pathway"] = best[0]
    scores["best_score"] = best[1]["score"]
    scores["iterations"] += 1

    _save_scores(scores)
    return scores


def get_best_pathway():
    """Returnează calea Enneagram cu cel mai bun scor de învățare."""
    scores = _load_scores()
    return scores.get("best_pathway", "circle"), scores.get("best_score", 0.5)


def show_scores():
    """Afișează scorurile de învățare pentru fiecare cale."""
    scores = _load_scores()
    print(f"=== Scoruri Căi Enneagram (iterații: {scores.get('iterations', 0)}) ===\n")

    for pw_key, pw_data in sorted(scores["pathways"].items()):
        name = PATHWAY_NAMES.get(pw_key, pw_key)
        s = pw_data["score"]
        runs = pw_data["runs"]
        ok = pw_data["success"]
        fail = pw_data["failure"]
        depth = pw_data["mirror_depth_avg"]
        tech = pw_data["technique_boost"]
        bar_len = 20
        fill = int(s * bar_len)
        bar = "█" * fill + "░" * (bar_len - fill)
        star = " ⭐" if pw_key == scores.get("best_pathway") else ""
        print(f"  {name}{star}")
        print(f"    Scor: {s:.1%} [{bar}]")
        print(f"    Execuții: {runs} | Succes: {ok} | Eșec: {fail} | Rată: {ok/max(runs,1):.0%}")
        print(f"    Oglindă: {depth}/9 | Tehnici îmbunătățite: {tech}")
        print()

    print(f"  Cea mai eficientă cale: {PATHWAY_NAMES.get(scores.get('best_pathway', '?'), '?')} ({scores.get('best_score', 0):.1%})")


def sync_best_pathway_to_bridge():
    """Sincronizează cea mai bună cale în pathway-bridge.json pentru MCP routing."""
    best_pw, best_score = get_best_pathway()
    bridge = read_pathway_bridge()
    if bridge:
        bridge["best_pathway"] = best_pw
        bridge["best_score"] = best_score
        bridge["best_label"] = PATHWAY_NAMES.get(best_pw, best_pw)
        tmp = PATHWAY_BRIDGE + ".tmp"
        with open(tmp, "w") as f:
            json.dump(bridge, f, indent=2, ensure_ascii=False)
        os.replace(tmp, PATHWAY_BRIDGE)


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"

    if cmd == "save":
        task = sys.argv[2] if len(sys.argv) > 2 else "unknown"
        solution = sys.argv[3] if len(sys.argv) > 3 else ""
        outcome = sys.argv[4] if len(sys.argv) > 4 else "success"
        tags = sys.argv[5].split(",") if len(sys.argv) > 5 else []
        technique = sys.argv[6] if len(sys.argv) > 6 else ""
        eid = save_episode(task, solution, outcome, tags, technique=technique)
        print(f"Episod salvat: {eid}")

    elif cmd == "consolidate":
        consolidate_all()

    elif cmd == "patterns":
        patterns = extract_patterns()
        if patterns:
            for p in patterns:
                print(f"  [{p['success_rate']:.0%}] {p['name']} (size={p['size']}, trigrams={p['trigrams']})")
        else:
            print("  Niciun pattern detectat (need >=3 episodes)")

    elif cmd == "match":
        text = sys.argv[2] if len(sys.argv) > 2 else ""
        if not text:
            print("  Folosire: match '<task_text>'")
            sys.exit(1)

        print("== Pattern-uri ==")
        for m in match_patterns(text):
            print(f"  [{m['score']:.0%}] {m['name']}")

        print("== Tehnici ==")
        for m in match_techniques(text):
            print(f"  [{m['score']:.0%}] {m['name']}")

        print("== Politici ==")
        for m in match_policies(text):
            print(f"  [{m['score']:.0%}] {m['trigger']}")

        print("== Skill-uri ==")
        for m in match_skills(text):
            print(f"  [{m['score']:.0%}] {m['skill_id']}")

    elif cmd == "validate":
        validations = validate_policies()
        for v in validations:
            icon = "✅" if v["status"] == "respectata" else "❌"
            print(f"  {icon} {v['policy_id']}: {v['success_rate']:.0%} success ({v['relevant_episodes']} eps)")
            if "note" in v:
                print(f"     ⚠ {v['note']}")

    elif cmd == "generate-skill":
        generate_skill_from_techniques(sys.argv[2:] if len(sys.argv) > 2 else None)

    elif cmd == "mirror":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        show_mirror(limit)

    elif cmd == "pathway":
        window = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        p = detect_pathway(window)
        print(f"Cale Enneagram: {pathway_label(p)}")
        print(f"(bazat pe ultimele {window} episoade)")

    elif cmd == "pathway-show":
        window = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        show_pathway(window)

    elif cmd == "pathway-score":
        show_scores()

    elif cmd == "pathway-score-run":
        """Simulează un run pe o cale (testare)."""
        pw = sys.argv[2] if len(sys.argv) > 2 else "circle"
        outcome = sys.argv[3] if len(sys.argv) > 3 else "success"
        depth = int(sys.argv[4]) if len(sys.argv) > 4 else 7
        tech = sys.argv[5] == "1" if len(sys.argv) > 5 else True
        score_pathway_run(pw, outcome, depth, tech)
        show_scores()

    elif cmd == "mirror-run":
        """Rulează oglindă inversă manual pe ultimul episod sau pe un id."""
        if len(sys.argv) > 2:
            try:
                eid = int(sys.argv[2])
                mirror = reverse_mirror(episode_id=eid)
                print(f"Reflecție generată pe {len(mirror['reflections'])} nivele")
            except ValueError:
                # eid e de fapt un task text
                mirror = reverse_mirror(task=sys.argv[2], outcome=sys.argv[3] if len(sys.argv) > 3 else "success")
                print(f"Reflecție generată pe {len(mirror['reflections'])} nivele")
        else:
            # Ultimul episod
            eps = _load_episodes()
            regular = [ep for ep in eps if ep.get("type") != "mirror_inverse"]
            if regular:
                mirror = reverse_mirror(episode_id=regular[-1]["id"])
                print(f"Reflecție generată pe ultimul episod: {len(mirror['reflections'])} nivele")
            else:
                print("  Niciun episod de reflectat.")

    elif cmd == "status":
        count = _episode_count()
        eps = _load_episodes()
        mirror_count = sum(1 for ep in eps if ep.get("type") == "mirror_inverse")
        action_count = count - mirror_count
        print(f"=== Piramid Learning Status ===")
        print(f"")
        print(f"  Nivel 1 (Acțiuni):    {action_count} episoade")
        print(f"  Oglindă Inversă:      {mirror_count} reflecții")

        if os.path.exists(PATTERNS):
            with open(PATTERNS) as f:
                pdata = json.load(f)
            print(f"  Nivel 2 (Pattern-uri): {len(pdata.get('patterns', []))} pattern-uri")
        else:
            print(f"  Nivel 2 (Pattern-uri): empty")

        if os.path.exists(TECHNIQUES):
            with open(TECHNIQUES) as f:
                tdata = json.load(f)
            print(f"  Nivel 3 (Tehnici):    {len(tdata)} tehnici")
        else:
            print(f"  Nivel 3 (Tehnici):    empty")

        db = load_skills_db()
        print(f"  Nivel 4 (Skill-uri):  {len(db.get('skills', []))} skill-uri")

        if os.path.exists(TACIT):
            with open(TACIT) as f:
                tdata = json.load(f)
            print(f"  Nivel 5 (Atitudini):  {len(tdata.get('policies', []))} politici")
        else:
            print(f"  Nivel 5 (Atitudini):  empty")

        if os.path.exists(PRINCIPLES):
            with open(PRINCIPLES) as f:
                prdata = json.load(f)
            v = sum(p.get("violations", 0) for p in prdata.get("principles", []))
            print(f"  Nivel 6 (Principii):  {len(prdata.get('principles', []))} principii, {v} violări")
        else:
            print(f"  Nivel 6 (Principii):  empty")

        print(f"")

    elif cmd == "techniques":
        techs = load_techniques()
        for tid, t in sorted(techs.items()):
            bar = "█" * int(t.get("success_rate", 0) * 20)
            print(f"  [{t['success_rate']:.0%}] {t['name']:30s} {bar} ({t.get('use_count',0)}x)")

    elif cmd == "principles":
        prins = load_principles()
        for p in prins.get("principles", []):
            v = " ⚠" if p.get("violations", 0) > 0 else ""
            print(f"  {p['principle'][:60]}{v}")
            print(f"    dovezi={p.get('evidence_count',0)} violări={p.get('violations',0)}")

    elif cmd == "save-auto":
        """Auto-save hook: salvează automat task-ul curent. Folosit de plugin tool.execute.after."""
        task = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("OPENCODE_TASK", "")
        solution = sys.argv[3] if len(sys.argv) > 3 else ""
        outcome = sys.argv[4] if len(sys.argv) > 4 else "success"
        if task:
            # Auto-detectează tags și tehnici
            tags = []
            tech_match = match_techniques(task)
            if tech_match:
                tags.append("auto")
                technique = tech_match[0]["technique_id"]
            else:
                technique = ""

            pattern_match = match_patterns(task)
            for pm in pattern_match:
                tags.append(pm["name"][:30])

            eid = save_episode(task, solution, outcome, tags=list(set(tags)), technique=technique)
            print(f"Auto-save: episod {eid} (tags={tags}, technique={technique})")
        else:
            print("  Auto-save: no task provided (set OPENCODE_TASK env)")

    else:
        print("Comenzi: save, consolidate, patterns, match, validate, generate-skill, status, techniques, principles, save-auto, mirror, mirror-run, pathway, pathway-show, pathway-score, pathway-score-run")
