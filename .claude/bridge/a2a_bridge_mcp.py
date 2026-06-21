#!/usr/bin/env python3
"""
a2a_bridge_mcp.py — A2A MCP Bridge: Claude Code (Think/Linux) <-> OpenCode (Honor/Windows)

Ruleaza pe Think (100.74.102.89), port 9130, accesibil via Tailscale.
OpenCode pe Honor se conecteaza la http://100.74.102.89:9130/sse

Arhitectura:
  Claude Code (NAS/Linux) ──→ tool send_to_honor ──→ queue ──→ OpenCode (Honor)
  OpenCode (Honor) ──→ tool send_to_think ──→ queue ──→ Claude Code (NAS/Linux)
"""
import json
from datetime import datetime
from pathlib import Path
from mcp.server.fastmcp import FastMCP

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
TASKS_FILE  = DATA_DIR / "a2a_tasks.json"
RESULTS_FILE = DATA_DIR / "a2a_results.json"

mcp = FastMCP("a2a-bridge", host="0.0.0.0", port=9130)


def _read(path: Path, default):
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        pass
    return default


def _write(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))


# ── Tools expuse catre OpenCode pe Honor ────────────────────────────────────

@mcp.tool()
def queue_apk_build(
    project_path: str = r"D:\Cloude Code\PROJECTS\QnapGX+GX\PhoneGX",
    java_home: str = r"C:\Program Files\Android\Android Studio\jbr",
    adb_serial: str = "10AF5G1L3A002LD",
    adb_path: str = r"C:\temp\pt\platform-tools\adb.exe",
) -> str:
    """Claude apeleaza asta ca sa ceara lui OpenCode pe Honor sa buildeze si sa instaleze APK-ul.
    OpenCode va rula: gradlew.bat assembleDebug + adb install -r pe serial dat.
    """
    import uuid
    tasks = _read(TASKS_FILE, [])
    task = {
        "id": str(uuid.uuid4())[:8],
        "type": "build_and_install_apk",
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "params": {
            "project_path": project_path,
            "java_home": java_home,
            "adb_serial": adb_serial,
            "adb_path": adb_path,
            "apk_output": project_path + r"\app\build\outputs\apk\debug\app-debug.apk",
            "instructions": (
                "1. taskkill /F /IM java.exe (curata procese vechi)\n"
                "2. set JAVA_HOME=<java_home> && cd /d <project_path> && gradlew.bat assembleDebug --no-daemon\n"
                "3. Daca BUILD SUCCESSFUL: <adb_path> -s <adb_serial> install -r <apk_output>\n"
                "4. report_result cu succes/eroare"
            ),
        },
    }
    tasks.append(task)
    _write(TASKS_FILE, tasks)
    return f"Task queued: id={task['id']} — OpenCode pe Honor trebuie sa apeleze get_pending_task() si sa execute."


@mcp.tool()
def get_pending_task() -> str:
    """OpenCode pe Honor apeleaza asta pentru a prelua urmatorul task de la Claude."""
    tasks = _read(TASKS_FILE, [])
    pending = [t for t in tasks if t.get("status") == "pending"]
    if not pending:
        return "Niciun task pending."
    task = pending[0]
    task["status"] = "in_progress"
    task["started_at"] = datetime.now().isoformat()
    _write(TASKS_FILE, tasks)
    return json.dumps(task, ensure_ascii=False, indent=2)


@mcp.tool()
def report_result(task_id: str, result: str, success: bool = True) -> str:
    """OpenCode pe Honor raporteaza rezultatul unui task finalizat."""
    results = _read(RESULTS_FILE, [])
    entry = {
        "task_id": task_id,
        "result": result,
        "success": success,
        "timestamp": datetime.now().isoformat(),
    }
    results.append(entry)
    _write(RESULTS_FILE, results)
    # Marcheaza task ca done
    tasks = _read(TASKS_FILE, [])
    for t in tasks:
        if t.get("id") == task_id:
            t["status"] = "done"
            t["completed_at"] = datetime.now().isoformat()
    _write(TASKS_FILE, tasks)
    return f"Rezultat inregistrat pentru task {task_id}."


@mcp.tool()
def ping(message: str = "ping") -> str:
    """Test conectivitate A2A bridge."""
    return f"pong — A2A bridge activ pe 9130 | {datetime.now().isoformat()} | msg={message}"


@mcp.tool()
def list_tasks(status: str = "all") -> str:
    """Listeaza task-urile din coada (all / pending / done / in_progress)."""
    tasks = _read(TASKS_FILE, [])
    if status != "all":
        tasks = [t for t in tasks if t.get("status") == status]
    return json.dumps(tasks, ensure_ascii=False, indent=2) if tasks else "Nicio inregistrare."


# ── Functii apelate de Claude Code (acest session) ─────────────────────────
# Claude Code nu mai are nevoie de MCP stdio — apeleaza direct REST sau
# prin tool-urile MCP din bridge-mcp-server.js (care sunt wrappers peste HTTP)

if __name__ == "__main__":
    print("[A2A] Bridge pornit pe 0.0.0.0:9130 — Claude Code se conecteaza la /mcp")
    mcp.run(transport="streamable-http")
