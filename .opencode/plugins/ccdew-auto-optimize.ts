import { type Plugin, tool } from "@opencode-ai/plugin"

const DATA_DIR_SUFFIX = ".claude-flow/data"
const OPT_LOG = "auto-optimize.jsonl"

function getDataDir(): string {
  const base = process.env.OPENCODE_PROJECT_DIR || process.cwd()
  return `${base}/${DATA_DIR_SUFFIX}`
}

const BLOAT_PATTERNS = [
  { re: /\bte rog\b/gi, replace: "" },
  { re: /\bpoti sa\b/gi, replace: "" },
  { re: /\bvrei sa\b/gi, replace: "" },
  { re: /\bam nevoie sa\b/gi, replace: "" },
  { re: /\bplease\b/gi, replace: "" },
  { re: /\bcould you\b/gi, replace: "" },
  { re: /\bi would like\b/gi, replace: "" },
  { re: /\bcan you\b/gi, replace: "" },
  { re: /\bi want to\b/gi, replace: "" },
  { re: /\bi need to\b/gi, replace: "" },
]

function estimateTokens(text: string): number {
  return Math.ceil((text || "").length / 4)
}

function analyzePrompt(prompt: string): { originalTokens: number; strippedTokens: number; savedPct: number } | null {
  const originalTokens = estimateTokens(prompt)
  if (originalTokens < 20) return null

  let stripped = prompt
  for (const { re, replace } of BLOAT_PATTERNS) {
    stripped = stripped.replace(re, replace)
  }
  stripped = stripped.replace(/\s{2,}/g, " ").trim()

  const strippedTokens = estimateTokens(stripped)
  const savedPct = Math.round(((originalTokens - strippedTokens) / originalTokens) * 100)

  if (savedPct < 5) return null

  return { originalTokens, strippedTokens, savedPct }
}

async function logOptimization(data: { originalTokens: number; strippedTokens: number; savedPct: number }) {
  try {
    const { $ } = await import("bun")
    const dir = getDataDir()
    await $`mkdir -p ${dir}`
    const entry = JSON.stringify({ ts: new Date().toISOString(), ...data }) + "\n"
    await $`echo ${entry} >> ${dir}/${OPT_LOG}`
  } catch {
    // non-fatal
  }
}

async function getStats(): Promise<{ prompts: number; avgSaved: number }> {
  try {
    const { $ } = await import("bun")
    const content = await $`cat ${getDataDir()}/${OPT_LOG}`.text()
    const lines = content.trim().split("\n").filter(Boolean)
    if (lines.length === 0) return { prompts: 0, avgSaved: 0 }

    const entries = lines.map(l => {
      try { return JSON.parse(l) } catch { return null }
    }).filter(Boolean)

    const avg = Math.round(entries.reduce((s: number, e: any) => s + e.savedPct, 0) / entries.length)
    return { prompts: entries.length, avgSaved: avg }
  } catch {
    return { prompts: 0, avgSaved: 0 }
  }
}

export const AutoOptimizePlugin: Plugin = async ({ client }) => {
  return {
    "chat.message": async (input, output) => {
      const msgText = output.message?.content || ""
      if (typeof msgText !== "string") return

      const result = analyzePrompt(msgText)
      if (!result) return

      await logOptimization(result)

      // Append optimization hint as a new message part
      const hint = `[CCDEW Auto-Optimize] Prompt ${result.originalTokens} → ~${result.strippedTokens} tokens (${result.savedPct}% estimated savings)`
      const existing = output.parts || []
      existing.push({
        type: "text",
        text: hint,
      } as any)
    },

    tool: {
      ccdew_optimize: tool({
        description: "Show CCDEW Auto-Optimize stats (prompts analyzed, average token savings)",
        args: {},
        async execute(_args, _ctx) {
          const stats = await getStats()
          if (stats.prompts === 0) {
            return "[CCDEW Auto-Optimize] No data yet"
          }
          return `[CCDEW Auto-Optimize] ${stats.prompts} prompts analyzed | avg savings ${stats.avgSaved}%`
        },
      }),
    },
  }
}
