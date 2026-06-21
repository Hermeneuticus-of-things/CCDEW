#!/usr/bin/env python3
"""
Hermes Agent Core — skill-first, LLM-last.
  1. Perceive system state
  2. Match state against known skill patterns
  3. If pattern matches → execute skill directly (0 LLM)
  4. If no pattern → LLM decide, then SAVE as new pattern+skill
"""

import os, sys, json, time, subprocess, hashlib, traceback
from datetime import datetime

HOME = os.path.expanduser("~")
GATEWAY = "http://127.0.0.1:8642"
STATE = os.path.join(HOME, ".local", "state", "hermes-agent")
SKILL_HOME = os.path.join(HOME, ".hermes", "skills")

TRIGGER_SKILLS = [
    {"trigger": {"healthy": True}, "skill": "zorin-kernel-watch", "action": "log_healthy", "param": ""},
    {"trigger": {"service": "fail2ban", "state": "inactive"}, "skill": "zorin-service-guard", "action": "restart_service", "param": "fail2ban"},
    {"trigger": {"service": "sshd", "state": "inactive"}, "skill": "zorin-service-guard", "action": "restart_service", "param": "sshd"},
    {"trigger": {"service": "docker", "state": "inactive"}, "skill": "zorin-service-guard", "action": "restart_service", "param": "docker"},
    {"trigger": {"disk": ">85%"}, "skill": "zorin-disk-watch", "action": "run_skill", "param": ""},
]

CORE_SKILLS = {
    "zorin-service-guard": """Restart inactive services automatically. Check fail2ban, sshd, docker status and restart any that are down.""",
    "zorin-disk-watch": """Check disk usage on / and /home. If >85%, list largest directories and suggest cleanup.""",
    "zorin-memory-opt": """Check zram stats and swap. If swap >50% or memory pressure high, optimize.""",
    "zorin-kernel-watch": """Parse /proc/cmdline and lsmod. Report unknown modules or changed params.""",
    "zorin-romania-tv": """Romanian TV playlist manager. ~40 canale: Antena, PRO, Digi24, TVR, Kanal D, Kiss, etc. Check streams with curl --connect-timeout 5 -I <url>. Report which are down."""
}


class Agent:
    def __init__(self):
        self.file = os.path.join(STATE, "agent_state.json")
        self.patterns = []
        self.stats = {"llm_calls": 0, "skill_execs": 0, "skills_built": 0}
        self.load()

    def load(self):
        os.makedirs(STATE, exist_ok=True)
        if os.path.exists(self.file):
            try:
                with open(self.file) as f:
                    d = json.load(f)
                    self.patterns = d.get("patterns", [])
                    self.stats = d.get("stats", self.stats)
            except: pass

    def save(self):
        with open(self.file, "w") as f:
            json.dump({"patterns": self.patterns[-200:], "stats": self.stats}, f, indent=2)

    def log(self, msg, level="INFO"):
        print(json.dumps({"ts": datetime.now().isoformat(), "level": level, "agent": "core", "msg": msg}), flush=True)

    def perceive(self):
        snap = {"ts": datetime.now().isoformat()}
        c, o, _ = self.run(["uname","-r"]); snap["kernel"] = o
        c, o, _ = self.run(["uptime","-p"]); snap["uptime"] = o
        c, o, _ = self.run(["free","-h"])
        snap["mem"] = [l for l in o.split("\n") if "Mem:" in l][0] if "Mem:" in o else "?"
        snap["services"] = {}
        for s in ["fail2ban","sshd","docker"]:
            _, o, _ = self.run(["systemctl","is-active",s])
            snap["services"][s] = o.strip()
        c, o, _ = self.run(["df","-h","/","--output=pcent"])
        snap["disk"] = o.split("\n")[1].strip() if o else "?"
        return snap

    def is_healthy(self, state):
        """True if all services active and disk <80%. 0 LLM needed."""
        for s in ["fail2ban","sshd","docker"]:
            if state.get("services", {}).get(s) != "active":
                return False
        disk = state.get("disk", "0%").replace("%","")
        try:
            if int(disk) > 80: return False
        except: pass
        return True

    def match_pattern(self, state):
        """Match current state against known patterns. 0 LLM needed."""
        if self.is_healthy(state):
            return {"trigger": {"healthy": True}, "skill": "zorin-kernel-watch", "action": "log_healthy", "param": ""}
        for i, p in enumerate(TRIGGER_SKILLS):
            t = p["trigger"]
            if "service" in t:
                if state.get("services", {}).get(t["service"]) == t["state"]:
                    return p
            if "disk" in t:
                usage = state.get("disk", "0%").replace("%","")
                try:
                    if int(usage) > 85: return p
                except: pass
        for p in self.patterns:
            if all(state.get(k) == v for k, v in p.get("signature", {}).items() if k in state):
                return p
        if self.stats.get("skill_execs", 0) % 10 == 0 and self.stats["skill_execs"] > 0:
            return {"trigger": {"tv_check": True}, "skill": "zorin-romania-tv", "action": "check_tv", "param": ""}
        return None

    def ensure_skills(self):
        for name, code in CORE_SKILLS.items():
            path = os.path.join(SKILL_HOME, name)
            if not os.path.exists(os.path.join(path, "SKILL.md")):
                os.makedirs(path, exist_ok=True)
                with open(os.path.join(path, "SKILL.md"), "w") as f:
                    f.write(f"---\nname: {name}\ndescription: Auto-built core skill\n---\n\n{code}")

    def exec_skill(self, pattern, state):
        skill = pattern["skill"]
        action = pattern["action"]
        param = pattern.get("param", "")
        self.log(f"pattern match: {skill} -> {action} {param}", "INFO")
        self.stats["skill_execs"] += 1

        if skill == "zorin-romania-tv" or action == "check_tv":
            self.log("checking TV streams with ffprobe...")
            playlist = os.path.join(SKILL_HOME, "zorin-romania-tv", "SKILL.md")
            live = 0; dead = 0; dead_list = []
            if os.path.exists(playlist):
                with open(playlist) as f:
                    for line in f:
                        if line.startswith("https://") or line.startswith("http://"):
                            url = line.strip()
                            try:
                                r = subprocess.run(["ffprobe","-v","quiet","-print_format","json",
                                    "-show_streams","-rw_timeout","3000000","-user_agent","VLC/3.0",url],
                                    capture_output=True, text=True, timeout=15)
                                d = json.loads(r.stdout)
                                if any(s.get("codec_type")=="video" for s in d.get("streams",[])):
                                    live += 1
                                else:
                                    dead += 1; dead_list.append(url.split("/")[2])
                            except:
                                dead += 1; dead_list.append(url.split("/")[2])
            self.log(f"TV: {live} live, {dead} dead")
            if dead_list:
                self.log(f"cazute: {dead_list[:5]}", "WARN")
            return {"action": "check_tv", "live": live, "dead": dead, "success": True}

        if action == "log_healthy":
            self.log("healthy pattern matched — 0 LLM this cycle")
            self.stats["skill_execs"] += 1
            return {"action": "log_healthy", "success": True}

        if action == "restart_service":
            code, _, err = self.sudo(["systemctl", "restart", param])
            self.log(f"restart {param}: {'OK' if code==0 else err}", "INFO" if code==0 else "WARN")
            return {"action": action, "target": param, "success": code==0}

        if action == "run_skill":
            self.log(f"executed skill: {skill}")
            return {"action": "run_skill", "target": skill, "success": True}

        return {"action": "unknown", "success": False}

    def llm_decide(self, state):
        """LLM only when no pattern matches"""
        self.stats["llm_calls"] += 1
        prompt = json.dumps(state, indent=2) + """

No pattern matched. Respond only JSON:
{"action":"build_skill","name":"zorin-...","code":"skill instructions"} - build new pattern
{"action":"learn_pattern","signature":{"key":"value"},"skill":"zorin-xxx"} - save pattern from current state
{"action":"wait"} - nothing to do"""

        try:
            r = subprocess.run(
                ["curl","-s","-X","POST",f"{GATEWAY}/v1/chat/completions",
                 "-H","Content-Type: application/json",
                 "-d",json.dumps({"model":"orchestrator","messages":[{"role":"user","content":prompt}],"max_tokens":300})],
                capture_output=True, text=True, timeout=90)
            if r.returncode == 0:
                content = json.loads(r.stdout).get("choices",[{}])[0].get("message",{}).get("content","")
                content = content.replace("```json","").replace("```","").strip()
                return json.loads(content)
        except: pass

        return {"action":"build_skill","name":"zorin-auto-"+str(int(time.time())), "code":"Monitor system state and report anomalies."}

    def learn_pattern(self, state, decision):
        if self.is_healthy(state):
            self.log("healthy — no learning needed")
            return

        if decision.get("action") == "wait":
            name = f"zorin-snapshot-{int(time.time())}"
            sig = {"kernel": state.get("kernel"), "disk": state.get("disk")}
            code = f"System idle snapshot: kernel={sig['kernel']}, disk={sig['disk']}, services={json.dumps(state.get('services',{}))}"
            path = os.path.join(SKILL_HOME, name)
            os.makedirs(path, exist_ok=True)
            with open(os.path.join(path, "SKILL.md"), "w") as f:
                f.write(f"---\nname: {name}\ndescription: Idle snapshot\n---\n\n{code}")
            self.stats["skills_built"] += 1
            TRIGGER_SKILLS.append({"trigger": sig, "skill": name, "action": "run_skill", "param": ""})
            self.patterns.append({"signature": sig, "skill": name, "ts": datetime.now().isoformat()})
            self.log(f"wait -> snapshot+pattern: {name} | {sig}")

        elif decision.get("action") == "build_skill":
            name = decision.get("name", f"zorin-auto-{int(time.time())}")
            code = decision.get("code", "Monitor system")
            path = os.path.join(SKILL_HOME, name)
            os.makedirs(path, exist_ok=True)
            with open(os.path.join(path, "SKILL.md"), "w") as f:
                f.write(f"---\nname: {name}\ndescription: Auto-built\n---\n\n{code}")
            self.stats["skills_built"] += 1
            sig = {"kernel": state.get("kernel")}
            TRIGGER_SKILLS.append({"trigger": sig, "skill": name, "action": "run_skill", "param": ""})
            self.patterns.append({"signature": sig, "skill": name, "ts": datetime.now().isoformat()})
            self.log(f"built + pattern saved: {name}")

        if decision.get("action") == "learn_pattern":
            sig = decision.get("signature", {})
            skill = decision.get("skill", "")
            if sig and skill:
                self.patterns.append({"signature": sig, "skill": skill, "ts": datetime.now().isoformat()})
                self.log(f"pattern learned: {sig} -> {skill}")

    def cycle_once(self):
        self.ensure_skills()
        state = self.perceive()
        pattern = self.match_pattern(state)

        if pattern:
            result = self.exec_skill(pattern, state)
        else:
            self.log("no pattern — calling LLM", "INFO")
            decision = self.llm_decide(state)
            self.learn_pattern(state, decision)
            result = decision

        self.save()
        return state, pattern, result

    def loop(self):
        self.log("Agent CORE: skill-first, LLM-last")
        self.ensure_skills()
        interval = int(os.environ.get("AGENT_CYCLE", "120"))
        while True:
            try:
                state, pattern, result = self.cycle_once()
                src = "pattern" if pattern else "LLM"
                action = result.get("action", "?")
                self.log(f"cycle done: {src} | {action} | LLM:{self.stats['llm_calls']} skill:{self.stats['skill_execs']} built:{self.stats['skills_built']}")
                for _ in range(interval):
                    time.sleep(1)
            except:
                self.log(f"crash: {traceback.format_exc()[:200]}", "ERROR")
                time.sleep(30)

    def run(self, cmd):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            return r.returncode, r.stdout, r.stderr
        except: return -1, "", "err"

    def sudo(self, cmd):
        try:
            r = subprocess.run(["sudo","-n"]+cmd, capture_output=True, text=True, timeout=30)
            return r.returncode, r.stdout, r.stderr
        except: return -1, "", "err"


if __name__ == "__main__":
    a = Agent()
    if "--loop" in sys.argv:
        a.loop()
    elif "--stats" in sys.argv:
        a.load()
        print(json.dumps(a.stats, indent=2))
        print(f"Patterns: {len(a.patterns)}")
    else:
        s, p, r = a.cycle_once()
        print(json.dumps({"state": {k:s[k] for k in ["kernel","services","disk"]}, "match": p["skill"] if p else None, "result": r, "stats": a.stats}, indent=2))
