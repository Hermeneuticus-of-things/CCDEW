import { type Plugin, tool } from "@opencode-ai/plugin"

interface CheckResult {
  check: string
  status: "PASS" | "FAIL" | "WARN" | "SKIP" | "INFO"
  detail: string
  ms: number
}

const GIT_COMMIT_RE = /^git\s+commit/

async function runBash(cmd: string): Promise<{ code: number; stdout: string; stderr: string }> {
  try {
    const { $ } = await import("bun")
    const result = await $`bash -c ${cmd}`.quiet()
    return { code: result.exitCode, stdout: result.stdout.toString(), stderr: result.stderr.toString() }
  } catch (e: any) {
    return { code: 1, stdout: "", stderr: String(e) }
  }
}

function hasFile(f: string): boolean {
  try {
    const fs = require("fs")
    return fs.existsSync(f)
  } catch { return false }
}

async function listChangedFiles(): Promise<string[]> {
  const r = await runBash("git diff --name-only")
  return r.stdout.trim().split("\n").filter(Boolean)
}

async function runVerify(): Promise<{ passed: boolean; results: CheckResult[] }> {
  const results: CheckResult[] = []
  const work = process.env.OPENCODE_PROJECT_DIR || process.cwd()

  const changed = await listChangedFiles()
  const hasTS = hasFile(`${work}/tsconfig.json`)
  const hasNode = hasFile(`${work}/package.json`)

  // Typecheck
  if (hasTS) {
    const r = await runBash("npx --no-install tsc --noEmit 2>&1 || true")
    const failed = r.stdout.includes("error TS")
    results.push({
      check: "typecheck (tsc)",
      status: failed ? "FAIL" : "PASS",
      detail: failed ? r.stdout.split("\n").slice(0, 3).join(" | ") : "",
      ms: 0,
    })
  } else {
    results.push({ check: "typecheck", status: "SKIP", detail: "no tsconfig.json", ms: 0 })
  }

  // Tests
  if (hasNode && changed.length > 0) {
    const r = await runBash("npm test --silent 2>&1 || true")
    const failed = r.code !== 0
    results.push({
      check: "tests (npm test)",
      status: failed ? "FAIL" : "PASS",
      detail: failed ? r.stdout.split("\n").slice(-3).join(" | ") : "",
      ms: 0,
    })
  } else {
    results.push({ check: "tests", status: "SKIP", detail: "no changed files", ms: 0 })
  }

  // Lint
  if (hasNode && changed.length > 0) {
    const codeFiles = changed.filter(f => /\.(js|cjs|mjs|ts|tsx|jsx)$/i.test(f))
    if (codeFiles.length > 0) {
      const r = await runBash(`npx eslint ${codeFiles.join(" ")} 2>&1 || true`)
      results.push({
        check: "lint (eslint)",
        status: r.code === 0 ? "PASS" : "WARN",
        detail: `${codeFiles.length} files`,
        ms: 0,
      })
    } else {
      results.push({ check: "lint", status: "SKIP", detail: "no JS/TS files", ms: 0 })
    }
  } else {
    results.push({ check: "lint", status: "SKIP", detail: "no linter", ms: 0 })
  }

  // Diff stats
  if (changed.length > 0) {
    const r = await runBash("git diff --shortstat")
    results.push({ check: "diff stats", status: "INFO", detail: r.stdout.trim().slice(0, 100), ms: 0 })
  }

  const failed = results.filter(r => r.status === "FAIL").length
  return { passed: failed === 0, results }
}

export const VerifyPlugin: Plugin = async () => {
  return {
    "tool.execute.before": async (input, output) => {
      if (input.tool !== "bash") return
      const cmd = output.args?.command || ""
      if (GIT_COMMIT_RE.test(cmd)) {
        const { passed, results } = await runVerify()
        if (!passed) {
          const fails = results.filter(r => r.status === "FAIL").map(r => r.check).join(", ")
          throw new Error(`[CCDEW Verify] BLOCKED: ${fails} failed — fix before commit (set HOOKS_SKIP=1 to bypass)`)
        }
      }
    },

    tool: {
      ccdew_verify: tool({
        description: "Run CCDEW pre-commit verification (typecheck, tests, lint, diff stats). Use before git commit.",
        args: {},
        async execute(_args, _ctx) {
          const { passed, results } = await runVerify()
          const lines = results.map(r => {
            const sym = r.status === "PASS" ? "✓" : r.status === "FAIL" ? "✗" : r.status === "WARN" ? "⚠" : "·"
            return `  [${sym} ${r.status}] ${r.check}${r.detail ? " — " + r.detail : ""}`
          })
          const passedCount = results.filter(r => r.status === "PASS").length
          const failedCount = results.filter(r => r.status === "FAIL").length
          const summary = passed ? `ALL PASS (${passedCount}/${results.length})` : `${failedCount} FAILED`
          return `[CCDEW Verify]\n${lines.join("\n")}\n\nResult: ${summary}`
        },
      }),
    },
  }
}
