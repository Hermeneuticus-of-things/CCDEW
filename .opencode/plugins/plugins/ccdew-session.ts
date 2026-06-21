import { type Plugin, tool } from "@opencode-ai/plugin"

interface SessionData {
  id: string
  startedAt: string
  endedAt?: string
  duration?: number
  metrics: {
    edits: number
    commands: number
    tasks: number
    errors: number
  }
}

const sessionState: SessionData = {
  id: "",
  startedAt: "",
  metrics: {
    edits: 0,
    commands: 0,
    tasks: 0,
    errors: 0,
  },
}

async function writeSessionSnapshot(data: SessionData) {
  try {
    const { $ } = await import("bun")
    const dir = process.env.OPENCODE_PROJECT_DIR || process.cwd()
    const sessionDir = `${dir}/.claude-flow/sessions`
    await $`mkdir -p ${sessionDir}`
    const archivePath = `${sessionDir}/${data.id}.json`
    await $`echo ${JSON.stringify(data, null, 2)} > ${archivePath}`
  } catch {
    // non-fatal
  }
}

export const SessionPlugin: Plugin = async ({ client }) => {
  return {
    "session.created": async (input, _output) => {
      const event = input as any
      sessionState.id = event.session?.id || `session-${Date.now()}`
      sessionState.startedAt = new Date().toISOString()
      sessionState.metrics = { edits: 0, commands: 0, tasks: 0, errors: 0 }
    },

    "session.updated": async (input, _output) => {
      const event = input as any
      if (event.session?.id) {
        sessionState.id = event.session.id
      }
    },

    "session.idle": async () => {
      await writeSessionSnapshot({ ...sessionState })
    },

    "session.deleted": async () => {
      sessionState.endedAt = new Date().toISOString()
      if (sessionState.startedAt) {
        sessionState.duration = Date.now() - new Date(sessionState.startedAt).getTime()
      }
      await writeSessionSnapshot({ ...sessionState })
    },

    "tool.execute.after": async (input, _output) => {
      if (input.tool === "write" || input.tool === "edit") {
        sessionState.metrics.edits++
      }
      if (input.tool === "bash") {
        sessionState.metrics.commands++
      }
    },

    "session.error": async () => {
      sessionState.metrics.errors++
    },

    tool: {
      ccdew_session: tool({
        description: "Show CCDEW session status (id, duration, metrics, active state)",
        args: {},
        async execute(_args, _ctx) {
          if (!sessionState.startedAt) {
            return "[CCDEW Session] No active session"
          }
          const duration = sessionState.endedAt
            ? sessionState.duration
            : Date.now() - new Date(sessionState.startedAt).getTime()
          const minutes = Math.round(duration / 60000)
          const ended = sessionState.endedAt ? " (ended)" : " (active)"
          const line = `${sessionState.id}${ended} | ${minutes} min | edits:${sessionState.metrics.edits} cmds:${sessionState.metrics.commands} tasks:${sessionState.metrics.tasks} errors:${sessionState.metrics.errors}`
          return `[CCDEW Session] ${line}`
        },
      }),
    },
  }
}
