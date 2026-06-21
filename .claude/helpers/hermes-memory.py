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

    print(f"  Nivel 6 (Principii): {len(prins.get('principles', []))} principii sincronizate")
    print(f"=== Consolidare completă ===\n")


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

    elif cmd == "status":
        count = _episode_count()
        print(f"=== Piramid Learning Status ===")
        print(f"")
        print(f"  Nivel 1 (Acțiuni):    {count} episoade")

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
        print("Comenzi: save, consolidate, patterns, match, validate, generate-skill, status, techniques, principles, save-auto")
