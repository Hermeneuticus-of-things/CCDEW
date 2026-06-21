import { type Plugin, tool } from "@opencode-ai/plugin"

interface CostData {
  today_cost: number
  today_calls: number
  month_cost: number
  month_calls: number
  source: string
}

const costState: CostData = {
  today_cost: 0,
  today_calls: 0,
  month_cost: 0,
  month_calls: 0,
  source: "session",
}

const MODEL_COST_PER_CALL: Record<string, number> = {
  "claude-opus-4": 0.015,
  "claude-sonnet-4": 0.003,
  "claude-haiku-3.5": 0.0008,
  "gpt-4o": 0.0025,
  "gpt-4o-mini": 0.00015,
  default: 0.001,
}

function getModelCost(model: string): number {
  for (const [key, cost] of Object.entries(MODEL_COST_PER_CALL)) {
    if (model.includes(key)) return cost
  }
  return MODEL_COST_PER_CALL.default
}

export const CodeBurnPlugin: Plugin = async ({ client }) => {
  return {
    "tool.execute.after": async (input, _output) => {
      costState.today_calls++
      costState.month_calls++
      const model = process.env.OPENCODE_MODEL || "default"
      const cost = getModelCost(model)
      costState.today_cost += cost
      costState.month_cost += cost
    },

    "session.idle": async () => {
      const burnData = {
        ...costState,
        ts: new Date().toISOString(),
      }
      try {
        const { $ } = await import("bun")
        const dir = process.env.OPENCODE_PROJECT_DIR || process.cwd()
        const dataDir = `${dir}/.claude-flow/data`
        await $`mkdir -p ${dataDir}`
        await $`echo ${JSON.stringify(burnData)} > ${dataDir}/codeburn-cache.json`
      } catch {
        // non-fatal: cost caching is advisory
      }
    },

    tool: {
      ccdew_burn: tool({
        description: "Show CCDEW CodeBurn cost tracking data (today cost, calls, month total)",
        args: {},
        async execute(_args, _ctx) {
          const flag = costState.today_calls > 0 && costState.today_cost / costState.today_calls > 0.05
          const line = `$${costState.today_cost.toFixed(2)} today | $${costState.month_cost.toFixed(2)} month | ${costState.today_calls} calls${flag ? " ⚠" : ""}`
          return `[CCDEW CodeBurn] ${line}`
        },
      }),
    },
  }
}
