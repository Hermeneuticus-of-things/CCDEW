import { type Plugin, tool } from "@opencode-ai/plugin"

const DATA_DIR_SUFFIX = ".claude-flow/data"

function getBase(): string { return process.env.OPENCODE_PROJECT_DIR || process.cwd() }
function getDataDir(): string { return `${getBase()}/${DATA_DIR_SUFFIX}` }

async function readJSON(path: string): Promise<any | null> {
  try {
    const { $ } = await import("bun")
    const content = await $`cat ${path}`.text()
    return JSON.parse(content)
  } catch { return null }
}

async function buildStatusLine(): Promise<string> {
  const parts: string[] = []

  // CodeBurn cost
  const burn = await readJSON(`${getDataDir()}/codeburn-cache.json`)
  if (burn && burn.today_cost !== undefined) {
    const cpc = burn.today_calls > 0 ? burn.today_cost / burn.today_calls : 0
    const flag = cpc > 0.05 ? " ⚠" : ""
    parts.push(`💰 $${burn.today_cost.toFixed(2)}/d · ${burn.today_calls}c${flag}`)
  } else {
    parts.push("💰 n/a")
  }

  // SAFLA stats
  const safla = await readJSON(`${getDataDir()}/safla.json`)
  if (safla && safla.total_feedbacks > 0) {
    const validRates = Object.values(safla.nodes || {}).filter((n: any) => ((n.success || 0) + (n.failure || 0)) >= 3)
    if (validRates.length > 0) {
      const avgRate = validRates.reduce((sum: number, n: any) => sum + ((n.success || 0) / Math.max(1, (n.success || 0) + (n.failure || 0))), 0) / validRates.length
      parts.push(`🤖 ${Math.round(avgRate * 100)}% ok·${safla.total_feedbacks}fb`)
    }
  }

  // Auto-optimize
  try {
    const { $ } = await import("bun")
    const optContent = await $`cat ${getDataDir()}/auto-optimize.jsonl`.text()
    const lines = optContent.trim().split("\n").filter(Boolean)
    if (lines.length > 0) {
      parts.push(`⚡ ${lines.length}opt`)
    }
  } catch {}

  return parts.length > 0 ? parts.join(" │ ") : "🔧 CCDEW v3"
}

export const StatuslinePlugin: Plugin = async () => {
  return {
    tool: {
      ccdew_status: tool({
        description: "Show CCDEW full status line (cost today, SAFLA learning rate, optimization stats, active project)",
        args: {},
        async execute(_args, _ctx) {
          const line = await buildStatusLine()
          return `[CCDEW Status] ${line}`
        },
      }),
    },
  }
}
