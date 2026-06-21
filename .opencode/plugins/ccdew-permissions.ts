import type { Plugin } from "@opencode-ai/plugin"

const DENY_PATTERNS: { pattern: RegExp; reason: string }[] = [
  { pattern: /rm\s+-rf\s+\/\s*/i, reason: "rm -rf / is destructive" },
  { pattern: /rm\s+-rf\s+~\//, reason: "rm -rf ~/ is destructive" },
  { pattern: /:\(\)\s*\{/, reason: "fork bomb detected" },
  { pattern: /mkfs\./, reason: "filesystem creation blocked" },
  { pattern: /dd\s+if=.*of=\/dev\/sd/i, reason: "raw disk write blocked" },
  { pattern: /format\s+c:\//i, reason: "format command blocked" },
  { pattern: /del\s+\/s\s+\/q/i, reason: "recursive delete blocked" },
  { pattern: />\s*\/dev\/sd/i, reason: "raw disk write blocked" },
]

const DENY_FILE_READS = [
  /\.env$/,
  /\.env\./,
  /credentials\.json/,
  /credentials\.yaml/,
  /secrets\.json/,
  /secrets\.yaml/,
  /\.kube\/config/,
  /id_rsa$/,
  /id_ed25519$/,
  /\.pem$/,
  /\.pfx$/,
  /\.p12$/,
  /service-account-key/,
  /google-app-credentials/,
  /aws-credentials/,
]

export const PermissionsPlugin: Plugin = async () => {
  return {
    "tool.execute.before": async (input, output) => {
      if (input.tool === "bash") {
        const cmd = output.args?.command || ""
        for (const { pattern, reason } of DENY_PATTERNS) {
          if (pattern.test(cmd)) {
            throw new Error(`[CCDEW Permissions] BLOCKED: ${reason}`)
          }
        }
      }

      if (input.tool === "read") {
        const filePath = output.args?.filePath || ""
        for (const deny of DENY_FILE_READS) {
          if (deny.test(filePath)) {
            throw new Error(
              `[CCDEW Permissions] BLOCKED: reading sensitive file: ${filePath}`
            )
          }
        }
      }
    },
  }
}
