import { type Plugin, tool } from "@opencode-ai/plugin"

const ARCH_KEYWORDS = [
  "arhitectur", "architect", "design", "refactor", "migrat", "rewrit", "integrat",
  "implementeaz", "implement", "creaz", "create", "build", "sistem", "system",
  "deploy", "produc", "release", "optimi",
]

const RISK_TEMPLATES = [
  "What tacit assumptions does this solution rely on?",
  "What are the 2 ways this can fail in production?",
  "Is there a simpler approach with ≤50% of the complexity?",
  "What unexpected side effect could appear within 30 days?",
  "If this decision is wrong, how costly is it to roll back?",
  "What data or edge cases are we not considering?",
  "How will this interact with existing systems?",
  "What monitoring or observability do we need?",
]

function pickRisks(prompt: string, count = 2): string[] {
  const seed = prompt.length % RISK_TEMPLATES.length
  const result: string[] = []
  for (let i = 0; i < count; i++) {
    result.push(RISK_TEMPLATES[(seed + i) % RISK_TEMPLATES.length])
  }
  return result
}

function isArchTask(prompt: string): boolean {
  const lower = prompt.toLowerCase()
  return ARCH_KEYWORDS.some(kw => lower.includes(kw))
}

function evaluate(prompt: string): { questions: string[]; isArch: boolean } | null {
  const words = prompt.trim().split(/\s+/)
  if (words.length < 10) return null

  const arch = isArchTask(prompt)
  if (!arch && (prompt.length % 5) >= 2) return null

  const questions = pickRisks(prompt, arch ? 3 : 2)
  return { questions, isArch: arch }
}

export const RedHatEvaluatorPlugin: Plugin = async () => {
  return {
    "chat.message": async (input, output) => {
      const msgText = output.message?.content || ""
      if (typeof msgText !== "string") return

      const result = evaluate(msgText)
      if (!result) return

      const lines = [
        "[CCDEW Red-Hat] Critical evaluation before execution:",
        ...result.questions.map((q, i) => `  ${i + 1}. ${q}`),
        result.isArch ? "  → Answer these questions BEFORE writing code." : "",
      ].filter(Boolean)

      const existing = output.parts || []
      existing.push({
        type: "text",
        text: lines.join("\n"),
      } as any)
    },

    tool: {
      ccdew_evaluate: tool({
        description: "Run CCDEW Red-Hat critical evaluator on a prompt (surface risks, assumptions, failure modes before starting work)",
        args: {
          prompt: tool.schema.string().describe("the task or prompt to evaluate"),
        },
        async execute(args, _ctx) {
          const prompt = args.prompt || ""
          const result = evaluate(prompt)
          if (!result) {
            return "[CCDEW Red-Hat] Prompt too short or not selected for evaluation"
          }
          const lines = [
            "Critical evaluation:",
            ...result.questions.map((q, i) => `  ${i + 1}. ${q}`),
            result.isArch ? "  → Architecture task: answer before writing code." : "",
          ].filter(Boolean)
          return `[CCDEW Red-Hat]\n${lines.join("\n")}`
        },
      }),
    },
  }
}
