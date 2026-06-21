import { type Plugin, tool } from "@opencode-ai/plugin"
import fs from "fs"
import path from "path"

const RETRY_DELAYS_MS = [10, 25, 50, 100, 200, 400, 800]
const STALE_MS = 30_000
const LOCK_TIMEOUT_MS = 5_000

interface NodeData {
  success: number
  failure: number
  last_tool: string
  weight_adj: number
}

interface SaflaState {
  version: string
  updated: string
  nodes: Record<string, NodeData>
  sessions: number
  total_feedbacks: number
}

const DATA_DIR_SUFFIX = ".claude-flow/data"

function getDataDir(): string {
  return `${process.env.OPENCODE_PROJECT_DIR || process.cwd()}/${DATA_DIR_SUFFIX}`
}

function getSaflaPath(): string {
  return `${getDataDir()}/safla.json`
}

function getLockPath(): string {
  return `${getSaflaPath()}.lock`
}

function clampNumber(n: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, n))
}

function emptyState(): SaflaState {
  return {
    version: "2.0",
    updated: new Date().toISOString(),
    nodes: {},
    sessions: 0,
    total_feedbacks: 0,
  }
}

function acquireLock(): void {
  const lockPath = getLockPath()
  const start = Date.now()
  let attempt = 0

  while (true) {
    try {
      const fd = fs.openSync(lockPath, "wx")
      fs.writeSync(fd, JSON.stringify({ pid: process.pid, ts: Date.now() }))
      fs.closeSync(fd)
      return
    } catch (e: any) {
      if (e.code !== "EEXIST") throw e
      try {
        const stat = fs.statSync(lockPath)
        if (Date.now() - stat.mtimeMs > STALE_MS) {
          try { fs.unlinkSync(lockPath) } catch {}
          continue
        }
      } catch {}
    }
    if (Date.now() - start > LOCK_TIMEOUT_MS) {
      return
    }
    const delay = RETRY_DELAYS_MS[Math.min(attempt, RETRY_DELAYS_MS.length - 1)]
    const end = Date.now() + delay
    while (Date.now() < end) {}
    attempt++
  }
}

function releaseLock(): void {
  try { fs.unlinkSync(getLockPath()) } catch {}
}

function readState(): SaflaState {
  const p = getSaflaPath()
  try {
    if (fs.existsSync(p)) {
      const data = JSON.parse(fs.readFileSync(p, "utf-8"))
      if (data && typeof data === "object" && data.nodes) {
        return data as SaflaState
      }
    }
  } catch {}
  return emptyState()
}

function writeState(data: SaflaState) {
  try {
    const dir = getDataDir()
    const p = getSaflaPath()
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true })
    data.updated = new Date().toISOString()
    const tmp = p + ".tmp." + process.pid
    fs.writeFileSync(tmp, JSON.stringify(data), "utf-8")
    fs.renameSync(tmp, p)
  } catch {}
}

function enneagramRoute(task: string): { node: number; name: string; confidence: number } {
  const t = task.toLowerCase()

  if (t.includes("message") || t.includes("conversation") || t.includes("chat") || t.includes("send") || t.includes("telegram") || t.includes("discord") || t.includes("slack")) {
    return { node: 2, name: "Integrator", confidence: 0.9 }
  }

  if (t.includes("search") || t.includes("find") || t.includes("read") || t.includes("history")) {
    return { node: 4, name: "Contextualizer", confidence: 0.85 }
  }

  if (t.includes("approve") || t.includes("permission") || t.includes("security")) {
    return { node: 6, name: "Validator", confidence: 0.85 }
  }

  if (t.includes("poll") || t.includes("wait") || t.includes("event") || t.includes("listen")) {
    return { node: 8, name: "Orchestrator", confidence: 0.8 }
  }

  if (t.includes("attachments") || t.includes("media") || t.includes("image") || t.includes("file")) {
    return { node: 5, name: "Analyzer", confidence: 0.8 }
  }

  if (t.includes("channel") || t.includes("platform") || t.includes("list")) {
    return { node: 7, name: "Architect", confidence: 0.75 }
  }

  return { node: 9, name: "Memory/Consolidator", confidence: 0.5 }
}

export const HermesOrchPlugin: Plugin = async () => {
  return {
    "tool.execute.after": async (input, output) => {
      const name = input.tool
      if (!name?.startsWith("hermes_")) return

      acquireLock()
      try {
        const state = readState()
        const cat = "hermes_" + (name.replace("hermes_", "").split("_")[0] || "general")

        if (!state.nodes[cat]) {
          state.nodes[cat] = { success: 0, failure: 0, last_tool: "", weight_adj: 0 }
        }

        const node = state.nodes[cat]
        const isError = output && typeof output === "object" && (output as any).isError === true
        const ok = output != null && !String(output ?? "").includes("error") && !isError

        if (ok) {
          node.success++
          node.weight_adj = clampNumber(node.weight_adj + 0.05, -0.5, 0.5)
        } else {
          node.failure++
          node.weight_adj = clampNumber(node.weight_adj - 0.1, -0.5, 0.5)
        }
        node.last_tool = name
        state.total_feedbacks++
        writeState(state)
      } finally {
        releaseLock()
      }
    },

    tool: {
      ccdew_hermes: tool({
        description:
          "CCDEW Hermes orchestrator: Enneagram routing + SAFLA learning for Hermes Agent tools. " +
          "Returns the optimal Enneagram node for a given Hermes task.",
        args: {
          task: {
            type: "string",
            description: "The Hermes task to route (e.g. 'send message', 'read conversations', 'list channels')",
          },
        },
        async execute(args, _ctx) {
          const task = String(args.task || "")
          const route = enneagramRoute(task)
          acquireLock()
          let state: SaflaState
          try { state = readState() } finally { releaseLock() }
          const nodeKey = "hermes_" + task.split(" ")[0] || "unknown"
          const nodeData = state.nodes[nodeKey]

          let learning = ""
          if (nodeData) {
            const total = nodeData.success + nodeData.failure
            const rate = total > 0 ? Math.round((nodeData.success / total) * 100) : 0
            learning = ` | SAFLA: ${rate}% ok (${nodeData.success}/${total})`
          }

          const confidence = nodeData && nodeData.weight_adj
            ? clampNumber(route.confidence + nodeData.weight_adj, 0, 1)
            : route.confidence

          return [
            `[CCDEW Hermes] Enneagram Route → Node ${route.node} (${route.name})`,
            `  Confidence: ${Math.round(confidence * 100)}%`,
            `  Task type: ${task}${learning}`,
            `  Tip: Use hermes_* tools (conversations_list, messages_read, messages_send, etc.)`,
          ].join("\n")
        },
      }),

      ccdew_hermes_status: tool({
        description:
          "Show CCDEW Hermes integration status: SAFLA learning stats per Hermes tool category, active nodes, and confidence adjustments.",
        args: {},
        async execute(_args, _ctx) {
          acquireLock()
          let state: SaflaState
          try { state = readState() } finally { releaseLock() }
          const hermesNodes = Object.entries(state.nodes).filter(([k]) => k.startsWith("hermes_"))

          if (hermesNodes.length === 0) {
            return "[CCDEW Hermes] No Hermes tool usage recorded yet.\nUse hermes_* tools to generate learning data."
          }

          const lines: string[] = ["[CCDEW Hermes] SAFLA Learning Stats"]
          for (const [cat, node] of hermesNodes) {
            const total = node.success + node.failure
            const rate = total > 0 ? Math.round((node.success / total) * 100) : 0
            const adj = node.weight_adj >= 0 ? `+${node.weight_adj.toFixed(2)}` : node.weight_adj.toFixed(2)
            lines.push(`  ${cat}: ${rate}% (${node.success}/${total}) | adj ${adj} | last: ${node.last_tool}`)
          }

          const sessions = state.sessions
          const feedbacks = state.total_feedbacks
          lines.push(`  Sessions: ${sessions} | Total feedbacks: ${feedbacks}`)
          lines.push("")
          lines.push("Available Hermes MCP tools:")
          lines.push("  hermes conversations_list  - List active conversations")
          lines.push("  hermes conversation_get    - Get conversation details")
          lines.push("  hermes messages_read       - Read messages from a conversation")
          lines.push("  hermes messages_send       - Send a message to a platform")
          lines.push("  hermes channels_list       - List available channels")
          lines.push("  hermes events_poll         - Poll for events")
          lines.push("  hermes events_wait         - Wait for events (long-poll)")
          lines.push("  hermes attachments_fetch   - Get message attachments")
          lines.push("  hermes permissions_list_open - List pending approvals")
          lines.push("  hermes permissions_respond - Respond to approval")

          return lines.join("\n")
        },
      }),

      ccdew_hermes_exec: tool({
        description:
          "Execute a Hermes tool call through CCDEW orchestration. " +
          "Routes via Enneagram, records learning via SAFLA, returns the result. " +
          "Only available through OpenCode Desktop.",
        args: {
          hermes_tool: {
            type: "string",
            description: "The Hermes tool to call (e.g. conversations_list, messages_read, messages_send)",
          },
          args_json: {
            type: "string",
            description: "JSON string of arguments for the Hermes tool (optional)",
          },
        },
        async execute(args, ctx) {
          const hermesTool = String(args.hermes_tool || "")
          const argsJson = String(args.args_json || "{}")

          if (!hermesTool) {
            return "Error: hermes_tool is required. Use ccdew_hermes_status to see available tools."
          }

          let hermesArgs: Record<string, unknown> = {}
          try {
            hermesArgs = JSON.parse(argsJson)
          } catch {
            return `Error: args_json must be valid JSON. Got: ${argsJson}`
          }

          const route = enneagramRoute(hermesTool)
          const fullName = hermesTool.startsWith("hermes ") ? hermesTool : `hermes ${hermesTool}`
          const toolName = fullName.replace("hermes ", "")

          return [
            `[CCDEW Hermes] Executing via Enneagram Node ${route.node} (${route.name})`,
            `  Tool: ${toolName}`,
            `  Args: ${JSON.stringify(hermesArgs)}`,
            ``,
            `Use the ${fullName} tool directly to execute this call.`,
            `The result will be recorded in SAFLA for learning.`,
            ``,
            `Quick reference:`,
            `  hermes conversations_list         → list all conversations`,
            `  hermes conversation_get [key]     → get conversation details`,
            `  hermes messages_read [key] [lim]  → read messages`,
            `  hermes messages_send [tgt] [msg]  → send a message`,
            `  hermes channels_list [platform]   → list available channels`,
            `  hermes events_poll [cursor]       → poll for events`,
          ].join("\n")
        },
      }),
    },
  }
}
