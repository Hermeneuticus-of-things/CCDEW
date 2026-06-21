import { type Plugin, tool } from "@opencode-ai/plugin"

interface QGCheck {
  check: string
  status: "PASS" | "FAIL" | "WARN" | "SKIP"
  detail: string
}

const GIT_PUSH_RE = /^git\s+push/

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
  try { return require("fs").existsSync(f) } catch { return false }
}

async function runQualityGate(): Promise<{ passed: boolean; results: QGCheck[] }> {
  const results: QGCheck[] = []
  const work = process.env.OPENCODE_PROJECT_DIR || process.cwd()
  const hasNode = hasFile(`${work}/package.json`)

  // Verify
  results.push({ check: "verify (typecheck+test+lint)", status: "SKIP", detail: "run ccdew_verify separately" })

  // npm audit
  if (hasNode) {
    const r = await runBash("npm audit --json --audit-level=high 2>&1 || true")
    let high = 0, critical = 0
    try {
      const j = JSON.parse(r.stdout)
      const v = j.metadata?.vulnerabilities
      if (v) { high = v.high || 0; critical = v.critical || 0 }
    } catch {}
    results.push({
      check: `npm audit (high=${high} critical=${critical})`,
      status: (high === 0 && critical === 0) ? "PASS" : "FAIL",
      detail: (high + critical > 0) ? `${high + critical} vulnerabilities` : "",
    })
  } else {
    results.push({ check: "npm audit", status: "SKIP", detail: "no package.json" })
  }

  // FIXME/XXX in changed files
  const changed = await runBash("git diff --name-only")
  const files = changed.stdout.trim().split("\n").filter(Boolean)
  let fixmeCount = 0
  for (const f of files) {
    try {
      const { $ } = await import("bun")
      const full = f.startsWith("/") ? f : `${work}/${f}`
      const content = await $`cat ${full}`.text()
      const matches = content.match(/\b(FIXME|XXX|HACK)\b/g)
      if (matches) fixmeCount += matches.length
    } catch {}
  }
  results.push({
    check: `fixme/xxx markers (${fixmeCount})`,
    status: fixmeCount === 0 ? "PASS" : "FAIL",
    detail: fixmeCount > 0 ? `${fixmeCount} markers in diff` : "",
  })

  const failed = results.filter(r => r.status === "FAIL").length
  return { passed: failed === 0, results }
}

export const QualityGatePlugin: Plugin = async () => {
  return {
    "tool.execute.before": async (input, output) => {
      if (input.tool !== "bash") return
      const cmd = output.args?.command || ""
      if (GIT_PUSH_RE.test(cmd)) {
        const { passed, results } = await runQualityGate()
        if (!passed) {
          const fails = results.filter(r => r.status === "FAIL").map(r => r.check).join(", ")
          throw new Error(`[CCDEW Quality-Gate] BLOCKED: ${fails} failed — fix before push (set HOOKS_SKIP=1 to bypass)`)
        }
      }
    },

    tool: {
      ccdew_quality_gate: tool({
        description: "Run CCDEW quality gate before merge/deploy (npm audit, FIXME/XXX check). Use before git push.",
        args: {},
        async execute(_args, _ctx) {
          const { passed, results } = await runQualityGate()
          const lines = results.map(r => {
            const sym = r.status === "PASS" ? "✓" : r.status === "FAIL" ? "✗" : "⚠"
            return `  [${sym} ${r.status}] ${r.check}${r.detail ? " — " + r.detail : ""}`
          })
          return `[CCDEW Quality-Gate]\n${lines.join("\n")}\n\n${passed ? "✓ ALL PASS — safe to merge/deploy" : "✗ FAILED — fix before merge"}`
        },
      }),
    },
  }
}
