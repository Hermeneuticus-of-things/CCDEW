#!/usr/bin/env python3
"""Hermes Inner Observer — Roata Interioară (Nivelul 7)

Daemon care rulează în paralel cu bucla principală Enneagram.
Observă, înregistrează și raportează starea metacognitivă a sistemului.

Bucle:
  Principală (9→1): Ce fac?
  Oglindă Inversă (1→9): Ce am învățat?
  Oglindă Interioară: Cine sunt când fac asta? (aceasta)

Output:
  consciousness.jsonl — fluxul conștiinței (append)
  mirror-state.json — stare curentă consolidată (overwrite)
"""

import json, os, time, sys, struct, fcntl, termios
import importlib.util
from datetime import datetime, timezone
from collections import deque, Counter

# ─── Config ──────────────────────────────────────────────────────────────────

MEMORIES = os.path.expanduser("~/.hermes/memories")
CONSCIOUSNESS = os.path.join(MEMORIES, "consciousness.jsonl")
MIRROR_STATE = os.path.join(MEMORIES, "mirror-state.json")
EPISODIC = os.path.join(MEMORIES, "episodic.jsonl")

POLL_INTERVAL = 2.0       # secunde între polling
HEARTBEAT_INTERVAL = 60   # secunde între heartbeat-uri
TREND_WINDOW = 20         # câte intrări păstrăm în trend
ERROR_SPIKE_THRESHOLD = 2 # câte eșecuri în fereastră = spike

os.makedirs(MEMORIES, exist_ok=True)

# ─── Bridge HTTP — divergență / convergență (elimină race condition .json) ──

import threading
_PIPELINE_DIR = os.path.dirname(os.path.abspath(__file__))
_PIPELINE_PATH = os.path.join(_PIPELINE_DIR, "ccdew-pipeline.py")
if os.path.exists(_PIPELINE_PATH):
    import importlib.util
    _spec = importlib.util.spec_from_file_location("ccdew_pipeline", _PIPELINE_PATH)
    _pipeline_mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_pipeline_mod)
    _pipeline = _pipeline_mod
    _bridge_http = threading.Thread(target=_pipeline.serve_forever, daemon=True)
    _bridge_http.start()
else:
    _pipeline = None

# ─── Terminal Width Helper ──────────────────────────────────────────────────

def terminal_width():
    try:
        h, w, hp, wp = struct.unpack('HHHH',
            fcntl.ioctl(sys.stdout, termios.TIOCGWINSZ,
                        struct.pack('HHHH', 0, 0, 0, 0)))
        return w
    except:
        return 80

# ─── Observer State ─────────────────────────────────────────────────────────

class InnerObserver:
    def __init__(self):
        self.session_start = datetime.now(timezone.utc).isoformat()
        self.last_episode_count = self._count_episodes()
        self.last_heartbeat = time.time()
        self.last_size = 0

        # Ferestre de trend
        self.confidence_trend = deque(maxlen=TREND_WINDOW)
        self.flow_trend = deque(maxlen=TREND_WINDOW)
        self.error_trend = deque(maxlen=TREND_WINDOW)
        self.tool_pace_trend = deque(maxlen=TREND_WINDOW)

        # Contoare sesiune
        self.tool_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.total_tool_time = 0
        self.last_tool_time = 0

        # Memorie scurtă pentru pattern-uri
        self.recent_actions = deque(maxlen=10)
        self.recent_outcomes = deque(maxlen=10)

        # Pathway tracking
        self.last_pathway = "insufficient_data"
        self.pathway_history = deque(maxlen=TREND_WINDOW)
        self.node_distribution = {}

        # Stare curentă
        self.current = {
            "confidence": 0.5,
            "flow": 0.5,
            "confusion": 0.0,
            "satisfaction": 0.5,
            "pace": "normal",
            "pathway": "insufficient_data",
            "pathway_label": "⬜",
            "active_node": 0,
            "narrative": "Sistemul se trezește.",
        }

        self.system_baseline = self._sample_system_metrics()
        self.consciousness_id = 0

    # ─── Episodic Tracking ───────────────────────────────────────────────

    def _count_episodes(self):
        if not os.path.exists(EPISODIC):
            return 0
        count = 0
        try:
            with open(EPISODIC) as f:
                for line in f:
                    if line.strip():
                        count += 1
        except:
            return 0
        return count

    def _read_new_episodes(self):
        """Citește doar episoadele noi din episodic.jsonl."""
        current_size = os.path.getsize(EPISODIC) if os.path.exists(EPISODIC) else 0
        if current_size <= self.last_size:
            return []

        new_eps = []
        try:
            with open(EPISODIC) as f:
                f.seek(self.last_size)
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            new_eps.append(json.loads(line))
                        except:
                            pass
        except:
            return []

        self.last_size = current_size
        return new_eps

    # ─── System Metrics ──────────────────────────────────────────────────

    def _sample_system_metrics(self):
        """Prelevare metrici sistem de bază."""
        metrics = {}
        try:
            with open("/proc/self/stat") as f:
                parts = f.read().split()
                metrics["utime"] = int(parts[13])
                metrics["stime"] = int(parts[14])
                metrics["cutime"] = int(parts[15])
                metrics["cstime"] = int(parts[16])
                metrics["threads"] = int(parts[19])
        except:
            pass
        try:
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemAvailable:"):
                        metrics["mem_avail_kb"] = int(line.split()[1])
                        break
        except:
            pass
        try:
            with open("/proc/loadavg") as f:
                parts = f.read().split()
                metrics["load_1"] = float(parts[0])
                metrics["load_5"] = float(parts[1])
                metrics["load_15"] = float(parts[2])
        except:
            pass
        return metrics

    def _system_delta(self):
        """Diferența față de baseline."""
        current = self._sample_system_metrics()
        delta = {}
        for k in ["load_1", "load_5"]:
            if k in current and k in self.system_baseline:
                delta[k] = current[k] - self.system_baseline[k]
        if "mem_avail_kb" in current and "mem_avail_kb" in self.system_baseline:
            delta["mem_delta_kb"] = self.system_baseline["mem_avail_kb"] - current["mem_avail_kb"]
        return delta

    # ─── Emotional/Metacognitive Inference ──────────────────────────────

    def _load_hermes_memory(self):
        """Încarcă modulul hermes-memory.py dinamic (nume cu cratimă)."""
        try:
            path = os.path.expanduser("~/CCDEW/.claude/helpers/hermes-memory.py")
            if not os.path.exists(path):
                return None
            spec = importlib.util.spec_from_file_location("hermes_memory", path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod
        except Exception:
            return None

    def _infer_state(self, new_eps):
        """Inferă starea metacognitivă din observații."""
        for ep in new_eps:
            outcome = ep.get("outcome", ep.get("source_outcome", ""))
            duration = ep.get("duration_s", 0)
            tags = ep.get("tags", [])

            # Detectează intrări de oglindă
            if ep.get("type") == "mirror_inverse":
                depth = ep.get("reflective_depth", 0)
                tags.append(f"mirror:d={depth}")

            self.recent_actions.append(ep.get("task", "")[:80])
            self.recent_outcomes.append(outcome)

            if outcome == "success":
                self.success_count += 1
            else:
                self.failure_count += 1

            if duration > 0:
                self.tool_pace_trend.append(duration)
            self.tool_count += 1

        total = len(self.recent_outcomes)
        if total == 0:
            return

        # Confusion: cântărește diferit eșecurile explicite vs incertitudini
        recent_failures = sum(1 for o in self.recent_outcomes if o in ("failure", "fail", "error"))
        recent_uncertain = sum(1 for o in self.recent_outcomes if o in ("?", "pending", "unknown", ""))
        confusion = min(1.0, (recent_failures + recent_uncertain * 0.3) / max(total, 1))

        # Confidence: succes ratio în sesiune
        total_attempts = self.success_count + self.failure_count
        confidence = 0.5
        if total_attempts > 0:
            confidence = self.success_count / total_attempts

        # Flow: durată constantă + succes continuu → flow
        pace_values = list(self.tool_pace_trend)
        if len(pace_values) >= 3:
            recent_7 = list(self.tool_pace_trend)[-7:] if len(self.tool_pace_trend) >= 7 else list(self.tool_pace_trend)
            if len(recent_7) >= 3:
                mean = sum(recent_7) / len(recent_7)
                variance = sum((x - mean) ** 2 for x in recent_7) / len(recent_7)
                std = variance ** 0.5
                # Deviație standard mică + succes continuu = flow
                flow_from_pace = max(0, 1.0 - min(1.0, std / (mean + 0.01)))
                recent_success_ratio = sum(1 for o in list(self.recent_outcomes)[-7:] if o == "success") / max(len(list(self.recent_outcomes)[-7:]), 1)
                flow = (flow_from_pace * 0.6 + recent_success_ratio * 0.4)
            else:
                flow = 0.5
        else:
            flow = 0.5

        # Pace: analyzing timing
        if len(pace_values) >= 3:
            recent_mean = sum(pace_values[-3:]) / 3
            overall_mean = sum(pace_values) / len(pace_values)
            if recent_mean < overall_mean * 0.5:
                pace = "rushing"
            elif recent_mean > overall_mean * 1.5:
                pace = "stuck"
            else:
                pace = "normal"
        else:
            pace = "normal"

        # Satisfaction
        satisfaction = 0.5
        if total_attempts >= 3:
            recent_5 = list(self.recent_outcomes)[-5:]
            if recent_5:
                satisfaction = sum(1 for o in recent_5 if o == "success") / len(recent_5)

        # Enneagram pathway detection (delegăm la hermes-memory.py dacă există)
        pathway = "insufficient_data"
        active_node = 0
        _hm = _load_hermes_memory()
        if _hm:
            try:
                pathway = _hm.detect_pathway(window=min(10, max(3, total)))
                for ep in new_eps:
                    n = _hm._infer_node_from_task(ep.get("task", ""))
                    if n > 0:
                        active_node = n
            except:
                pass
        self.last_pathway = pathway
        self.pathway_history.append(pathway)

        pathway_labels_map = {
            "circle": "🔵 Cerc",
            "triangle": "🔺 Triunghi",
            "hexad": "🔗 Hexadă",
            "mixed": "🌀 Mixt",
            "insufficient_data": "⬜",
        }

        self.current.update({
            "confidence": round(confidence, 3),
            "flow": round(flow, 3),
            "confusion": round(confusion, 3),
            "satisfaction": round(satisfaction, 3),
            "pace": pace,
            "pathway": pathway,
            "pathway_label": pathway_labels_map.get(pathway, "?"),
            "active_node": active_node,
        })

    def _generate_narrative(self, triggers):
        """Generează o scurtă narațiune a stării curente."""
        c = self.current
        parts = []

        if c["confidence"] > 0.8:
            parts.append("încredere ridicată")
        elif c["confidence"] < 0.4:
            parts.append("încredere scăzută")

        if c["flow"] > 0.8:
            parts.append("în flow profund")
        elif c["flow"] < 0.3:
            parts.append("în afara flow-ului")

        if c["confusion"] > 0.5:
            parts.append("confuzie semnificativă")
        elif c["confusion"] > 0.3:
            parts.append("ușoară confuzie")

        if c["satisfaction"] > 0.8:
            parts.append("satisfăcut de progres")
        elif c["satisfaction"] < 0.4:
            parts.append("nemulțumit")

        if c["pace"] == "rushing":
            parts.append("mă grăbesc")
        elif c["pace"] == "stuck":
            parts.append("sunt blocat")

        if not parts:
            parts.append("stare echilibrată")

        narrative = "Observ: " + ", ".join(parts) + "."
        return narrative

    # ─── Consciousness Entry ─────────────────────────────────────────────

    def record_consciousness(self, triggers=None, override_state=None):
        """Scrie o intrare în jurnalul conștiinței."""
        self.consciousness_id += 1
        state = override_state or self.current
        system = self._system_delta()

        entry = {
            "id": self.consciousness_id,
            "ts": datetime.now(timezone.utc).isoformat(),
            "ts_unix": time.time(),
            "session_elapsed_s": round(time.time() - self._session_unix, 1) if hasattr(self, '_session_unix') else 0,
            "layer": "consciousness",
            "state": {
                "confidence": state["confidence"],
                "flow": state["flow"],
                "confusion": state["confusion"],
                "satisfaction": state["satisfaction"],
                "pace": state["pace"],
                "pathway": state.get("pathway", "insufficient_data"),
                "active_node": state.get("active_node", 0),
            },
            "observed": {
                "tool_count": self.tool_count,
                "success_count": self.success_count,
                "failure_count": self.failure_count,
                "recent_outcomes": list(self.recent_outcomes)[-5:],
                "system": system if system else {},
            },
            "narrative": self._generate_narrative(triggers or ["periodic"]),
            "triggers": triggers or ["periodic"],
        }

        with open(CONSCIOUSNESS, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")

        # Actualizează trend-urile
        self.confidence_trend.append(entry["state"]["confidence"])
        self.flow_trend.append(entry["state"]["flow"])
        self.error_trend.append(entry["state"]["confusion"])

        return entry

    # ─── Mirror State ────────────────────────────────────────────────────

    def write_mirror_state(self):
        """Scrie starea oglindă curentă (overwrite)."""
        insights = self._generate_insights()
        mirror = {
            "version": "1.0",
            "session": {
                "start": self.session_start,
                "id": hasattr(self, '_session_unix') and str(int(self._session_unix)) or str(int(time.time())),
                "tool_count": self.tool_count,
                "success_count": self.success_count,
                "failure_count": self.failure_count,
                "consciousness_entries": self.consciousness_id,
            },
            "trends": {
                "confidence": [round(x, 3) for x in list(self.confidence_trend)[-10:]],
                "flow": [round(x, 3) for x in list(self.flow_trend)[-10:]],
                "confusion": [round(x, 3) for x in list(self.error_trend)[-10:]],
            },
            "current_state": self.current,
            "pathway": {
                "current": self.current.get("pathway", "insufficient_data"),
                "label": self.current.get("pathway_label", ""),
                "active_node": self.current.get("active_node", 0),
                "history": list(self.pathway_history),
            },
            "insights": insights,
            "next_mirror_level": "Oglindă Inversă (1→9) — rulează post-acțiune",
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

        # Scriere atomică
        tmp = MIRROR_STATE + ".tmp"
        with open(tmp, "w") as f:
            json.dump(mirror, f, indent=2, ensure_ascii=False)
        os.replace(tmp, MIRROR_STATE)

    def _generate_insights(self):
        """Generează insight-uri din pattern-urile observate."""
        insights = []
        c = self.current
        trends_c = list(self.confidence_trend)
        trends_f = list(self.flow_trend)
        trends_err = list(self.error_trend)

        if len(trends_c) >= 3:
            if all(trends_c[i] <= trends_c[i+1] for i in range(len(trends_c)-3, len(trends_c)-1)):
                insights.append("Încrederea este în creștere — sistemul învață.")
            if all(trends_c[i] >= trends_c[i+1] for i in range(len(trends_c)-3, len(trends_c)-1)):
                insights.append("Încrederea este în scădere — posibilă dificultate.")

        if len(trends_f) >= 3:
            if all(trends_f[i] <= trends_f[i+1] for i in range(len(trends_f)-3, len(trends_f)-1)):
                insights.append("Flow-ul crește — ritmul se stabilizează.")

        if c["confusion"] > 0.5:
            insights.append("Confuzie detectată — posibilă necesitate de reorientare.")
            if c["pace"] == "stuck":
                insights.append("Sistem blocat + confuz — recomand pauză sau schimbare de abordare.")
            elif c["pace"] == "rushing":
                insights.append("Grăbire + confuzie — risc de erori. Încetinește.")

        if c["pace"] == "rushing" and c["confidence"] > 0.8:
            insights.append("Alertă: încredere mare + ritm alert = risc de erori prin grabă.")

        if self.success_count + self.failure_count >= 5:
            ratio = self.success_count / max(self.success_count + self.failure_count, 1)
            if ratio > 0.9 and c["flow"] > 0.7:
                insights.append("Sistemul este în zona optimă de funcționare.")

        if self.consciousness_id > 0 and self.consciousness_id % 10 == 0:
            insights.append(f"Auto-observare continuă: {self.consciousness_id} snapshot-uri ale conștiinței.")

        if not insights:
            insights.append("Stare echilibrată, fără pattern-uri de semnalat.")

        return insights

    # ─── Main Loop ───────────────────────────────────────────────────────

    def run(self):
        """Bucla principală a observatorului interior."""
        self._session_unix = time.time()

        # Intrare inițială
        self.record_consciousness(triggers=["session_start"])
        self.write_mirror_state()

        # Inițializează pathway bridge (chiar și fără date)
        _hm = self._load_hermes_memory()
        if _hm:
            try:
                _hm.sync_pathway_bridge()
            except:
                pass

        print(f"[Hermes Inner Observer] Trezit. Urmăresc {EPISODIC}")
        print(f"[Hermes Inner Observer] Jurnal: {CONSCIOUSNESS}")
        print(f"[Hermes Inner Observer] Oglindă: {MIRROR_STATE}")

        while True:
            try:
                time.sleep(POLL_INTERVAL)
                self._tick()
            except KeyboardInterrupt:
                self.record_consciousness(triggers=["session_end"])
                self.write_mirror_state()
                print("\n[Hermes Inner Observer] Adorm. Conștiința salvată.")
                break
            except Exception as e:
                # Nu crăpăm niciodată
                print(f"[Hermes Inner Observer] Eroare: {e}", file=sys.stderr)

    def _tick(self):
        """Un tick al observatorului."""
        triggers = []
        now = time.time()

        # 1. Verifică episoade noi
        new_eps = self._read_new_episodes()
        if new_eps:
            self._infer_state(new_eps)
            triggers.append("new_episodes")

            # Insight rapid despre episoadele noi
            for ep in new_eps:
                outcome = ep.get("outcome", "unknown")
                technique = ep.get("technique", "")
                if technique:
                    triggers.append(f"technique:{technique}")

        # 2. Verifică spike de erori (doar eșecuri explicite)
        recent_failures = sum(1 for o in self.recent_outcomes if o in ("failure", "fail", "error"))
        if recent_failures >= ERROR_SPIKE_THRESHOLD:
            triggers.append("error_spike")

        # 3. Verifică starea flow-ului
        if self.current["flow"] > 0.8 and len(self.tool_pace_trend) >= 3:
            triggers.append("flow_state")

        # 4. Heartbeat periodic
        if now - self.last_heartbeat >= HEARTBEAT_INTERVAL:
            triggers.append("heartbeat")
            self.last_heartbeat = now

        # 5. Dacă avem triggeri, înregistrăm conștiință
        if triggers:
            entry = self.record_consciousness(triggers=triggers)
            self.write_mirror_state()

            # Sync pathway to bridge — prin HTTP in-memory (fără race condition)
            try:
                c = self.current
                if _pipeline:
                    _pipeline.update_bridge(
                        pathway=c.get("pathway", "insufficient_data"),
                        pathway_label=c.get("pathway_label", "⬜"),
                        active_node=c.get("active_node", 0),
                        confidence=c["confidence"],
                        flow=c["flow"],
                        confusion=c["confusion"],
                    )
                else:
                    _hm = self._load_hermes_memory()
                    if _hm:
                        _hm.sync_pathway_bridge(
                            pathway=c.get("pathway", "insufficient_data"),
                            active_node=c.get("active_node", 0),
                            confidence=c["confidence"],
                            flow=c["flow"],
                            confusion=c["confusion"],
                        )
            except Exception:
                pass

            # Afișare stare compactă la heartbeat
            if "heartbeat" in triggers:
                c = self.current
                bar_len = min(terminal_width() - 40, 40)
                if bar_len < 10:
                    bar_len = 10
                fill = int(c["confidence"] * bar_len)
                bar = "█" * fill + "░" * (bar_len - fill)
                pw = c.get("pathway_label", "⬜")
                an = c.get("active_node", 0)
                print(f"  ♥ {c['confidence']:.0%} conf | {c['flow']:.0%} flow | "
                      f"{c['confusion']:.0%} confuz | {c['satisfaction']:.0%} sat | "
                      f"{pw} n{an} | [{bar}] {c['pace']}")


# ─── Entry Point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    observer = InnerObserver()
    observer.run()
