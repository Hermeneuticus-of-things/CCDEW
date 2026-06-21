import { type Plugin, tool } from "@opencode-ai/plugin"

interface InstinctEntry {
  ts: string
  fp: string
  tool: string
  success: boolean
}

interface InstinctPattern {
  count: number
  success_rate: number
  dominant_tool: string
  node_confidence: number
}

const DATA_DIR_SUFFIX = ".claude-flow/data"
const INSTINCTS_LOG = "instincts.jsonl"
const PATTERNS_FILE = "instincts-patterns.json"
const MAX_LINES = 5000
const MIN_OCCURRENCES = 3

const STOP_WORDS = new Set([
  "this", "that", "these", "those", "with", "from", "into", "about",
  "have", "should", "would", "could", "please", "thanks",
])

function getDataDir(): string {
  const base = process.env.OPENCODE_PROJECT_DIR || process.cwd()
  return `${base}/${DATA_DIR_SUFFIX}`
}

function fingerprint(text: string): string {
  if (!text) return ""
  return text.toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ")
    .split(/\s+/)
    .filter(w => w.length >= 4 && !STOP_WORDS.has(w))
    .sort()
    .slice(0, 8)
    .join(" ")
}

async function ensureDir() {
  const { $ } = await import("bun")
  await $`mkdir -p ${getDataDir()}`
}

async function appendLog(entry: InstinctEntry) {
  try {
    await ensureDir()
    const { $ } = await import("bun")
    const line = JSON.stringify(entry) + "\n"
    await $`echo ${line} >> ${getDataDir()}/${INSTINCTS_LOG}`
  } catch {
    // non-fatal
  }
}

async function buildPatterns(): Promise<Record<string, InstinctPattern>> {
  try {
    const { $ } = await import("bun")
    const filePath = `${getDataDir()}/${INSTINCTS_LOG}`
    const content = await $`cat ${filePath}`.text()
    const lines = content.trim().split("\n").filter(Boolean)
    if (lines.length === 0) return {}

    const byFp: Record<string, { count: number; success: number; tools: Record<string, number> }> = {}
    for (const line of lines) {
      let e: InstinctEntry
      try { e = JSON.parse(line) } catch { continue }
      if (!e.fp || !e.tool) continue
      byFp[e.fp] = byFp[e.fp] || { count: 0, success: 0, tools: {} }
      byFp[e.fp].count++
      if (e.success) byFp[e.fp].success++
      byFp[e.fp].tools[e.tool] = (byFp[e.fp].tools[e.tool] || 0) + 1
    }

    const patterns: Record<string, InstinctPattern> = {}
    for (const [fp, data] of Object.entries(byFp)) {
      if (data.count < MIN_OCCURRENCES) continue
      const dominantTool = Object.entries(data.tools).sort((a, b) => b[1] - a[1])[0]
      patterns[fp] = {
        count: data.count,
        success_rate: +(data.success / data.count).toFixed(2),
        dominant_tool: dominantTool[0],
        node_confidence: +(dominantTool[1] / data.count).toFixed(2),
      }
    }

    await $`echo ${JSON.stringify(patterns)} > ${getDataDir()}/${PATTERNS_FILE}`
    return patterns
  } catch {
    return {}
  }
}

async function loadPatterns(): Promise<Record<string, InstinctPattern>> {
  try {
    const { $ } = await import("bun")
    const content = await $`cat ${getDataDir()}/${PATTERNS_FILE}`.text()
    return JSON.parse(content)
  } catch {
    return {}
  }
}

let lastPrompt = ""

export const InstinctsPlugin: Plugin = async () => {
  return {
    "tool.execute.before": async (input, output) => {
      if (input.tool === "bash" || input.tool === "write" || input.tool === "edit") {
        lastPrompt = output.args?.command || output.args?.filePath || ""
      }
    },

    "tool.execute.after": async (input, _output) => {
      const fp = fingerprint(lastPrompt || input.tool)
      if (!fp) return

      const entry: InstinctEntry = {
        ts: new Date().toISOString(),
        fp,
        tool: input.tool,
        success: true,
      }
      await appendLog(entry)
    },

    "session.idle": async () => {
      await buildPatterns()
    },

    tool: {
      ccdew_instincts: tool({
        description: "Show CCDEW Instincts pattern recognition (learned patterns from tool usage, confidence, success rates)",
        args: {
          prompt: tool.schema.string().optional().describe("optional prompt to check for matching pattern"),
        },
        async execute(args, _ctx) {
          const patterns = await loadPatterns()
          const count = Object.keys(patterns).length

          if (args.prompt) {
            const fp = fingerprint(args.prompt)
            const match = patterns[fp]
            if (match && match.success_rate >= 0.5) {
              return `[CCDEW Instincts] Match: "${fp}" → tool ${match.dominant_tool} (${Math.round(match.node_confidence * 100)}% confidence over ${match.count} samples, ${Math.round(match.success_rate * 100)}% success rate)`
            }
            return `[CCDEW Instincts] No matching pattern for "${fp}" (${count} known patterns)`
          }

          const lines = [`Patterns: ${count}`]
          for (const [fp, p] of Object.entries(patterns).slice(0, 10)) {
            lines.push(`  "${fp.slice(0, 40)}" → ${p.dominant_tool} (${Math.round(p.success_rate * 100)}% of ${p.count})`)
          }
          return `[CCDEW Instincts]\n${lines.join("\n")}`
        },
      }),
    },
  }
}
