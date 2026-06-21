import { type Plugin, tool } from "@opencode-ai/plugin"

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

function emptyState(): SaflaState {
  return {
    version: "2.0",
    updated: new Date().toISOString(),
    nodes: {},
    sessions: 0,
    total_feedbacks: 0,
  }
}

function clampNumber(n: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, n))
}

async function readState(): Promise<SaflaState> {
  try {
    const { $ } = await import("bun")
    const path = getSaflaPath()
    const result = await $`cat ${path}`.text()
    const data = JSON.parse(result)
    if (data && typeof data === "object" && data.nodes) {
      return data as SaflaState
    }
  } catch {
    // state file doesn't exist yet
  }
  return emptyState()
}

async function writeState(data: SaflaState) {
  try {
    const { $ } = await import("bun")
    const dir = getDataDir()
    const path = getSaflaPath()
    data.updated = new Date().toISOString()
    await $`mkdir -p ${dir}`
    await $`echo ${JSON.stringify(data)} > ${path}`
  } catch {
    // non-fatal
  }
}

function toolCategory(toolName: string): string {
  if (toolName === "write" || toolName === "edit") return "edit"
  if (toolName === "bash") return "bash"
  if (toolName === "read") return "read"
  if (toolName === "search" || toolName === "grep") return "search"
  return "other"
}

export const SaflaPlugin: Plugin = async () => {
  return {
    "tool.execute.after": async (input, _output) => {
      const cat = toolCategory(input.tool)
      const state = await readState()

      if (!state.nodes[cat]) {
        state.nodes[cat] = { success: 0, failure: 0, last_tool: "", weight_adj: 0 }
      }

      const node = state.nodes[cat]
      const exitCode = (input as any).exit_code ?? 0
      if (exitCode === 0) {
        node.success++
        node.weight_adj = clampNumber(node.weight_adj + 0.05, -0.5, 0.5)
      } else {
        node.failure++
        node.weight_adj = clampNumber(node.weight_adj - 0.1, -0.5, 0.5)
      }
      node.last_tool = input.tool
      state.total_feedbacks++

      await writeState(state)
    },

    "session.created": async () => {
      const state = await readState()
      state.sessions++
      await writeState(state)
    },

    tool: {
      ccdew_safla: tool({
        description: "Show CCDEW SAFLA adaptive learning stats (success rates per tool type, feedback count, weight adjustments)",
        args: {},
        async execute(_args, _ctx) {
          const state = await readState()
          const lines: string[] = [
            `Sessions: ${state.sessions} | Total feedbacks: ${state.total_feedbacks}`,
          ]

          for (const [cat, node] of Object.entries(state.nodes)) {
            const total = node.success + node.failure
            const rate = total > 0 ? Math.round((node.success / total) * 100) : 0
            const adj = node.weight_adj >= 0
              ? `+${node.weight_adj.toFixed(2)}`
              : node.weight_adj.toFixed(2)
            lines.push(`  ${cat}: ${rate}% ok (${node.success}/${total}) | adj ${adj} | last: ${node.last_tool}`)
          }

          return `[CCDEW SAFLA]\n${lines.join("\n")}`
        },
      }),
    },
  }
}
