# Agent Zero - Ghid Complet pentru Hermes

> **Pentru Hermes Autonomous Agent**: Acest document conține tot ce trebuie să știi despre Agent Zero pentru a învăța și auto-evolua.

## Ce Este Agent Zero

Agent Zero este un **framework agentic organic** care permite unui AI să folosească SO ca tool:
- Linux environment real (terminal, fișiere, code execution)
- Browser automation
- Memory persistent
- Multi-agent cooperation
- Tool creation on-the-fly

**Principiul cheie**: Nu e o listă fixă de butoane. Agentul poate construi și folosi tool-ul potrivit când work-ul cere.

---

## Arhitectura Agent Zero

### Stack Tehnologic
```
Python 3.12+ | Flask | Alpine.js | LiteLLM | WebSocket (Socket.io)
```

### Runtimes (Docker)
1. **Framework Runtime** (`/opt/venv-a0`) - Python 3.12.4
   - rulează Agent Zero backend, API, core logic
   - dependencies din requirements.txt

2. **Execution Runtime** (`/opt/venv`) - Python 3.13
   - default pentru terminal și code execution
   - pachetele instalate de agent sunt salvate aici

### Structura Proiectului
```
/
├── agent.py              # Core Agent și AgentContext definitions
├── initialize.py        # Framework initialization logic
├── models.py            # LLM provider configurations
├── run_ui.py            # WebUI server entry point
├── api/                  # API Handlers + WebSocket handlers
├── extensions/           # Backend lifecycle extensions
├── helpers/              # Shared Python utilities
├── tools/                # Agent tools (Tool subclasses)
├── webui/
│   ├── components/       # Alpine.js components
│   ├── js/               # Core frontend logic
│   └── index.html        # Main UI shell
├── usr/                  # User data directory (isolated)
│   ├── plugins/          # Custom user plugins
│   └── workdir/          # Default agent workspace
├── agents/               # Agent profiles (prompts + config)
├── prompts/              # System and message prompt templates
├── knowledge/
│   └── main/about/       # Agent self-knowledge (vector DB)
└── tests/                # Pytest suite
```

---

## Loop-ul Agent Zero (Reflexiv)

### Fluxul Principal
```
User Input → Monologue Start → Think → Act → Observe → Reflect → (Repeat) → Done
```

### Componente

#### 1. AgentContext
```python
# Contextul conține toate info despre sesiunea curentă
class AgentContext:
    id: str                    # unique session ID
    messages: list             # conversation history
    workspace: str             # current working directory
    tools: list                # available tools
    memory: Memory             # persistent memory
    agents: list               # sub-agents created
```

#### 2. Agent Loop
```python
class Agent:
    async def run(self, task):
        context = AgentContext(task)
        while not context.done:
            await self.think(context)      # THINK
            await self.act(context)        # ACT
            await self.observe(context)    # OBSERVE
            await self.reflect(context)    # REFLECT (la fiecare N pași)
        return context.result
```

#### 3. Memory Pipeline
- **Short-term**: messages în context
- **Long-term**: fișiere în `usr/memory/`, vector DB
- **Learning**: pattern detection din acțiuni anterioare

---

## Tool Creation (Auto-Evoluare)

### Principiu
Agentul poate **crea tools noi** în timpul execuției:

```python
# Agentul poate genera cod care devine tool
tool_code = """
class MyTool(Tool):
    async def execute(self, **kwargs):
        # custom logic
        return Response(message="Done", break_loop=False)
"""
# Tool-ul e încărcat dinamic
```

### Tool Structure
```python
from helpers.tool import Tool, Response

class BrowserTool(Tool):
    async def execute(self, url: str, action: str = "goto", **kwargs):
        # Navigate, click, type, screenshot
        return Response(message=f"{action} on {url}", break_loop=False)
```

---

## Multi-Agent Cooperation

### Model Hierarhic
```
Superior Agent
    ├── Sub-agent 1 (specialized)
    ├── Sub-agent 2 (specialized)
    └── Sub-agent N (specialized)
```

### Caracteristici
- Superior dă task-uri și primește rapoarte
- Sub-agents au context propriu, focused
- Comunicare prin rapoarte structurate

### Creare Sub-Agent
```python
sub_agent = await agent.create_subordinate(
    role="researcher",
    task="research topic X",
    capabilities=["web_search", "file_write"]
)
result = await sub_agent.run()
```

---

## Memory System

### 3 Layere

1. **Working Memory** (context.messages)
   -conversation history curentă

2. **Project Memory** (usr/projects/{project}/memory/)
   - izolat per project
   - fișiere .md culearnings

3. **Agent Knowledge** (knowledge/main/about/)
   - vector DB indexed
   - identity, architecture, capabilities

### Memory Curation
```javascript
// Memoria poate fi editată de agent
// Pattern: detectează situații similare → aplică soluții
if (situation in memory.patterns) {
    return memory.patterns[situation]
}
```

---

## Safety Model

### Allowed Without Asking
- Read any file în repository
- Update code files în `usr/`

### Ask Before Executing
- pip install (dependencies noi)
- Delete core files outside `usr/` or `tmp/`
- Modify `agent.py` or `initialize.py`
- git commits/pushes

### Never Do
- Commit sau leak secrets în .env
- Bypass CSRF/authentication
- Hardcode API keys

---

## Canvas (Visual Workspace)

Agent Zero oferă **Canvas** - o interfață vizuală:
- Browser sessions live
- Documents, workspace history
- Plugin panels
- Desktop Linux (LibreOffice)

### Scop
- дела agent work vizibil și inspectabil
- User poate interveni în timp real
- Istoric vizual (screenshots)

---

## Auto-Evoluție (Pentru Hermes)

### Ce Trebuie Să Facă Hermes

1. **Învață Pattern-uri**
   - Studiază knowledge/main/about/ din Agent Zero
   - Extrage principii și patterns

2. **Memory Pattern Learning**
   ```javascript
   // Când întâlnește situație nouă
   if (!patternExists(situation)) {
       action = executeAndLearn(situation)
       if (success) storePattern(situation, action)
       else storeLesson(situation, error)
   }
   ```

3. **Tool Creation**
   - Poate crea scripturi utils
   - Poate genera tools on-demand
   - Le salvează pentru reutilizare

4. **Self-Correction Loop**
   ```
   Error → Analyze → Correct → Retry → Learn
   ```

### Implementare Hermes

```javascript
class HermesAutonomous {
    async evolve() {
        // 1. Learn from Agent Zero docs
        await this.studyAgentZero()

        // 2. Build self-knowledge
        this.buildIdentity()

        // 3. Enable tool creation
        this.enableDynamicTools()

        // 4. Implement self-correction
        this.enableReflectionLoop()
    }
}
```

---

## Comparație Agent Zero vs Hermes

| Aspect | Agent Zero | Hermes (OpenCode Desktop) |
|--------|-----------|---------------------------|
| Environment | Full Linux Docker | MCP stdio only |
| Tool Creation | Da, on-the-fly |受限 (MCP tools only) |
| Multi-Agent | Da, native | Prin OpenCode orchestrator |
| Canvas | Da, visual | Nu |
| Memory | 3-layer system | JSON file-based |
| Self-Evolution | Da, native | Prin SAFLA learning |

---

## Resurse

- **GitHub**: https://github.com/agent0ai/agent-zero
- **Docs**: https://agent-zero.ai/docs
- **Discord**: https://discord.gg/B8KZKNsPpj
- **Installation**: `curl -fsSL https://bash.agent-zero.ai | bash`

---

*Document generat pentru Hermes Autonomous Agent - Agent Zero Learning Module*