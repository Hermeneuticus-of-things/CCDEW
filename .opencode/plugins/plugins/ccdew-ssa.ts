import { type Plugin, tool } from "@opencode-ai/plugin"

interface MemoryEntry {
  id: string
  content: string
  title: string
  tags: string[]
  pinned: boolean
  timestamp?: string
  related?: string[]
}

const AVG_CHARS_PER_TOKEN = 4
const STOP_WORDS = new Set([
  "the", "a", "an", "is", "are", "was", "were", "have", "has", "do", "does", "did",
  "to", "of", "in", "for", "on", "with", "at", "by", "and", "but", "or", "not",
  "this", "that", "it", "its", "i", "we", "you", "they", "he", "she",
  "ca", "la", "de", "si", "cu", "din", "pe", "un", "o", "sa", "se", "nu",
])

let _stats = {
  total_entries: 0,
  saved_entries: 0,
  total_chars: 0,
  saved_chars: 0,
  total_tokens: 0,
  saved_tokens: 0,
  calls: 0,
}

function tokenize(text: string): string[] {
  if (!text) return []
  return String(text).toLowerCase()
    .replace(/[^a-z0-9\s\-_]/g, " ")
    .split(/\s+/)
    .filter(w => w.length > 2 && !STOP_WORDS.has(w))
}

function trigrams(words: string[]): Set<string> {
  const t = new Set<string>()
  for (const w of words) {
    for (let i = 0; i <= w.length - 3; i++) t.add(w.slice(i, i + 3))
  }
  return t
}

function jaccard(a: Set<string>, b: Set<string>): number {
  if (a.size === 0 && b.size === 0) return 0
  let inter = 0
  for (const x of a) { if (b.has(x)) inter++ }
  return inter / (a.size + b.size - inter)
}

function getRecencyBonus(entry: MemoryEntry): number {
  if (!entry.timestamp) return 0
  const ageMs = Date.now() - new Date(entry.timestamp).getTime()
  const ageHours = ageMs / 3600000
  if (ageHours < 1) return 0.1
  if (ageHours < 4) return 0.05
  if (ageHours < 24) return 0.02
  return 0
}

function getPinnedScore(entry: MemoryEntry): number {
  return entry.pinned ? 0.5 : 0
}

function scoreEntry(promptT: Set<string>, entry: MemoryEntry): number {
  const text = [entry.content, entry.title, entry.tags.join(" ")].join(" ")
  const entryT = trigrams(tokenize(text))
  return jaccard(promptT, entryT)
}

function multiScore(promptT: Set<string>, entry: MemoryEntry, _all: MemoryEntry[]): number {
  const semantic = scoreEntry(promptT, entry)
  const recency = getRecencyBonus(entry)
  const pinned = getPinnedScore(entry)
  const weights = { semantic: 0.8, recency: 0.1, pinned: 0.1 }
  const raw = (semantic * weights.semantic) + (recency * weights.recency) + (pinned * weights.pinned)
  return Math.max(0, Math.min(1, raw))
}

function filterContext(prompt: string, entries: MemoryEntry[], topK = 12, minScore = 0.15): MemoryEntry[] {
  if (!Array.isArray(entries) || entries.length === 0) return entries

  const promptT = trigrams(tokenize(prompt))
  const scored = entries.map(entry => ({ entry, score: multiScore(promptT, entry, entries) }))
  scored.sort((a, b) => b.score - a.score)

  const filtered = scored.filter(s => s.score >= minScore).slice(0, topK).map(s => s.entry)
  const pinned = entries.filter(e => e.pinned)
  const pinnedIds = new Set(pinned.map(e => e.id).filter(Boolean))
  const merged = [...pinned, ...filtered.filter(e => !e.id || !pinnedIds.has(e.id))]

  const result = merged.slice(0, Math.max(topK, pinned.length))

  const totalIn = entries.reduce((sum, e) => sum + e.content.length + e.title.length, 0)
  const totalOut = result.reduce((sum, e) => sum + e.content.length + e.title.length, 0)

  _stats.total_entries += entries.length
  _stats.saved_entries += (entries.length - result.length)
  _stats.total_chars += totalIn
  _stats.saved_chars += (totalIn - totalOut)
  _stats.total_tokens += Math.round(totalIn / AVG_CHARS_PER_TOKEN)
  _stats.saved_tokens += Math.round((totalIn - totalOut) / AVG_CHARS_PER_TOKEN)
  _stats.calls++

  return result
}

async function loadMemoryEntries(): Promise<MemoryEntry[]> {
  try {
    const { $ } = await import("bun")
    const dir = process.env.OPENCODE_PROJECT_DIR || process.cwd()
    const indexFile = `${dir}/.claude-flow/data/session-critical-index.json`

    const result = await $`cat ${indexFile}`.text()
    const idx = JSON.parse(result)
    const source = idx.all || Object.values(idx.by_project || {}).flat()

    return source.map((e: any) => ({
      id: e.file || e.path || "",
      content: e.content || e.body || e.summary || e.compact || "",
      title: e.title || e.name || e.file || "",
      tags: e.tags || [],
      pinned: e.priority === "critical" || e.tags?.includes("session-critical"),
      timestamp: e.timestamp,
      related: e.related,
    }))
  } catch {
    return []
  }
}

export const SsaPlugin: Plugin = async () => {
  return {
    "experimental.session.compacting": async (input, output) => {
      const prompt = (input as any).prompt || ""

      try {
        const entries = await loadMemoryEntries()
        if (entries.length === 0) return

        const filtered = filterContext(prompt, entries)
        const pct = Math.round((1 - filtered.length / entries.length) * 100)

        const memoryBlock = filtered.map(e => {
          const parts = [`[${e.id}]`]
          if (e.title) parts.push(e.title)
          parts.push(e.content.slice(0, 500))
          if (e.tags.length) parts.push(`tags: ${e.tags.join(",")}`)
          return parts.join(" | ")
        }).join("\n---\n")

        output.context.push(
          `## CCDEW SSA Memory (${pct}% reduction from ${entries.length} to ${filtered.length} entries)\n${memoryBlock}`
        )
      } catch {
        // non-fatal: SSA is advisory
      }
    },

    tool: {
      ccdew_memory: tool({
        description: "Search CCDEW memory entries using SSA (Jaccard trigram similarity). Provide a prompt to find relevant context.",
        args: {
          prompt: tool.schema.string().describe("search query to match against memory entries"),
          topK: tool.schema.number().optional().describe("max results (default 12)"),
        },
        async execute(args, _ctx) {
          const prompt = args.prompt || ""
          const topK = args.topK || 12
          const entries = await loadMemoryEntries()
          const filtered = filterContext(prompt, entries, topK)
          const pct = Math.round((1 - filtered.length / entries.length) * 100)

          if (filtered.length === 0) return "[CCDEW SSA] No matching memory entries found"

          const results = filtered.map((e, i) => {
            return `${i + 1}. [${e.id}] ${e.title}\n   ${e.content.slice(0, 300)}${e.content.length > 300 ? "..." : ""}`
          })

          return `[CCDEW SSA] ${entries.length} → ${filtered.length} entries (${pct}% reduction)\n\n${results.join("\n")}`
        },
      }),
    },
  }
}
