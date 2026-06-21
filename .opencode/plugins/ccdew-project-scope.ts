import { type Plugin, tool } from "@opencode-ai/plugin"

interface ActiveProject {
  name: string
  path: string
  detected_from: string
  ts: string
  structure: string[]
}

const STATE_PATH_SUFFIX = ".claude-flow/data/active-project.json"
const RECENT_TTL = 2 * 60 * 60 * 1000
const CACHE_TTL = 5 * 60 * 1000

function getWorkspace(): string {
  return process.env.OPENCODE_PROJECT_DIR || process.cwd()
}

function getProjectsDir(): string {
  return `${getWorkspace()}/PROJECTS`
}

function getStatePath(): string {
  return `${getWorkspace()}/${STATE_PATH_SUFFIX}`
}

async function listProjects(): Promise<string[]> {
  try {
    const { $ } = await import("bun")
    const result = await $`ls -1 ${getProjectsDir()}`.text()
    return result.trim().split("\n").filter(Boolean).filter(n => !n.startsWith("."))
  } catch {
    return []
  }
}

async function projectStructure(name: string): Promise<string[]> {
  try {
    const { $ } = await import("bun")
    const root = `${getProjectsDir()}/${name}`
    const result = await $`ls -1 ${root}`.text()
    return result.trim().split("\n").filter(Boolean).filter(n => !n.startsWith("."))
  } catch {
    return []
  }
}

function escapeRegExp(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
}

async function loadState(): Promise<ActiveProject | null> {
  try {
    const { $ } = await import("bun")
    const path = getStatePath()
    const content = await $`cat ${path}`.text()
    return JSON.parse(content)
  } catch {
    return null
  }
}

async function saveState(state: ActiveProject) {
  try {
    const { $ } = await import("bun")
    const path = getStatePath()
    await $`mkdir -p ${path.replace(/\/[^/]+$/, "")}`
    await $`echo ${JSON.stringify(state)} > ${path}`
  } catch {
    // non-fatal
  }
}

async function detectActive(prompt: string): Promise<ActiveProject | null> {
  const projects = await listProjects()
  if (projects.length === 0) return null

  for (const proj of projects) {
    const re = new RegExp("\\b" + escapeRegExp(proj) + "\\b", "i")
    if (re.test(prompt)) {
      return {
        name: proj,
        path: `PROJECTS/${proj}`,
        detected_from: "prompt",
        ts: new Date().toISOString(),
        structure: await projectStructure(proj),
      }
    }
  }

  return null
}

let cachedProject: ActiveProject | null = null
let cacheTime = 0

export const ProjectScopePlugin: Plugin = async () => {
  return {
    "tool.execute.before": async (input, output) => {
      if (input.tool !== "write" && input.tool !== "edit") return

      const filePath = output.args?.filePath || ""
      if (!cachedProject) return

      const isInScope = filePath.includes(cachedProject.path)
      if (!isInScope && !filePath.includes("PROJECTS/")) {
        // editing workspace root — warn
      }
    },

    tool: {
      ccdew_project: tool({
        description: "Show CCDEW active project scope detection (name, path, structure, detection method)",
        args: {
          prompt: tool.schema.string().optional().describe("optional prompt to help detect project"),
        },
        async execute(args, _ctx) {
          const prompt = args.prompt || ""
          const active = await detectActive(prompt)
          if (!active) {
            return "[CCDEW Project-Scope] No active project detected"
          }
          const struct = (active.structure || []).slice(0, 6).join(", ")
          const line = `${active.path} (${active.detected_from}) | top: ${struct || "(empty)"}`
          return `[CCDEW Project-Scope] Active: ${line}`
        },
      }),
    },
  }
}
