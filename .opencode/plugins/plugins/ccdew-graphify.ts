import { type Plugin, tool } from "@opencode-ai/plugin"

const DATA_DIR_SUFFIX = ".claude-flow/data"
const REPORTS_DIR_SUFFIX = ".claude-flow/reports"

function getBase(): string {
  return process.env.OPENCODE_PROJECT_DIR || process.cwd()
}

function getDataDir(): string { return `${getBase()}/${DATA_DIR_SUFFIX}` }
function getReportsDir(): string { return `${getBase()}/${REPORTS_DIR_SUFFIX}` }

async function readJSON(path: string): Promise<any | null> {
  try {
    const { $ } = await import("bun")
    const content = await $`cat ${path}`.text()
    return JSON.parse(content)
  } catch { return null }
}

async function getBurnData(): Promise<{ today_cost: number; month_cost: number; today_calls: number; month_calls: number } | null> {
  const c = await readJSON(`${getDataDir()}/codeburn-cache.json`)
  if (c && c.today_cost !== undefined) return c
  return null
}

async function getSaflaData(): Promise<{ sessions: number; feedbacks: number; nodes: Record<string, { success: number; failure: number; weight_adj: number; last_task?: string }> } | null> {
  const d = await readJSON(`${getDataDir()}/safla.json`)
  if (!d) return null
  return {
    sessions: d.sessions || 0,
    feedbacks: d.total_feedbacks || 0,
    nodes: d.nodes || {},
  }
}

function bar(value: number, max: number, width = 20): string {
  const filled = max > 0 ? Math.round((value / max) * width) : 0
  return "█".repeat(Math.max(0, Math.min(width, filled))) + "░".repeat(Math.max(0, width - filled))
}

async function buildASCIIReport(): Promise<string> {
  const burn = await getBurnData()
  const safla = await getSaflaData()
  const lines: string[] = ["┌─────────────── Graphify Summary ───────────────┐"]

  if (burn) {
    const pct = Math.min(burn.today_cost / 15, 1)
    lines.push(`│ 🔥 Today  ${bar(pct * 20, 20)} $${burn.today_cost.toFixed(2)} / ${burn.today_calls} calls    │`)
  }
  if (safla && safla.feedbacks > 0) {
    const acc = Object.values(safla.nodes).reduce((s, n) => {
      const total = (n.success || 0) + (n.failure || 0)
      return total > 0 ? { s: s.s + (n.success || 0), t: s.t + total } : s
    }, { s: 0, t: 0 })
    const pct = acc.t > 0 ? Math.round((acc.s / acc.t) * 100) : 0
    lines.push(`│ 🤖 SAFLA  ${bar(pct, 100)}  ${pct}% ok           │`)
  }
  lines.push("└────────────────────────────────────────────────┘")
  return lines.join("\n")
}

async function buildMarkdownReport(): Promise<string> {
  const burn = await getBurnData()
  const safla = await getSaflaData()
  const out: string[] = [
    "# Graphify Session Report",
    `**Generated:** ${new Date().toISOString()}`,
    "",
  ]

  out.push("## CodeBurn")
  if (burn) {
    out.push(`- Today: **$${burn.today_cost.toFixed(2)}** (${burn.today_calls} calls)`)
    out.push(`- Month: **$${burn.month_cost.toFixed(2)}** (${burn.month_calls} calls)`)
  } else {
    out.push("_No data_")
  }
  out.push("")

  out.push("## SAFLA — Agent Performance")
  if (safla && safla.feedbacks > 0) {
    out.push(`- Sessions: ${safla.sessions} | Total feedbacks: ${safla.feedbacks}`)
    out.push("")
    out.push("| Tool | Success% | Adj | Last task |")
    out.push("|---|---|---|---|")
    for (const [cat, node] of Object.entries(safla.nodes)) {
      const total = (node.success || 0) + (node.failure || 0)
      if (total === 0) continue
      const rate = Math.round((node.success / total) * 100)
      const adj = (node.weight_adj || 0) >= 0
        ? "+" + (node.weight_adj || 0).toFixed(2)
        : (node.weight_adj || 0).toFixed(2)
      out.push(`| ${cat} | ${rate}% | ${adj} | ${node.last_task || "-"} |`)
    }
  } else {
    out.push("_No feedback recorded yet_")
  }

  return out.join("\n")
}

export const GraphifyPlugin: Plugin = async () => {
  return {
    "session.idle": async () => {
      try {
        const { $ } = await import("bun")
        const ts = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19)
        await $`mkdir -p ${getReportsDir()}`
        const report = await buildMarkdownReport()
        const file = `${getReportsDir()}/session-${ts}.md`
        await $`echo ${report} > ${file}`
      } catch {
        // non-fatal
      }
    },

    tool: {
      ccdew_graphify: tool({
        description: "Show CCDEW Graphify session report (cost, SAFLA performance, stats in ASCII table)",
        args: {
          format: tool.schema.enum(["ascii", "markdown"]).optional().describe("output format (default: ascii)"),
        },
        async execute(args, _ctx) {
          if (args.format === "markdown") {
            return `[CCDEW Graphify]\n${await buildMarkdownReport()}`
          }
          return `[CCDEW Graphify]\n${await buildASCIIReport()}`
        },
      }),
    },
  }
}
