import type { Plugin } from "@opencode-ai/plugin"

const SENSITIVE_PATHS = [
  /\.env(\.|$)/i,
  /credentials?\.(json|ya?ml)$/i,
  /secrets?\.(json|ya?ml|env)$/i,
  /private[_-]?key/i,
  /id_rsa$/,
  /\.pem$/i,
  /\.pfx$/i,
  /\.p12$/i,
]

const SECRET_PATTERNS = [
  { name: "AWS Access Key", re: /AKIA[0-9A-Z]{16}/ },
  { name: "AWS Secret Key", re: /aws_secret_access_key\s*=\s*['"]?[A-Za-z0-9/+=]{40}['"]?/i },
  { name: "Anthropic API Key", re: /sk-ant-[a-zA-Z0-9_-]{20,}/ },
  { name: "OpenAI API Key", re: /sk-(?!ant-)[a-zA-Z0-9]{20,}/ },
  { name: "GitHub PAT", re: /(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}/ },
  { name: "Google API Key", re: /AIza[0-9A-Za-z_-]{35}/ },
  { name: "Stripe Live Key", re: /sk_live_[0-9a-zA-Z]{24,}/ },
  { name: "Slack Bot Token", re: /xox[baprs]-[0-9]{10,}-[0-9]{10,}-[a-zA-Z0-9]{24,}/ },
  { name: "Generic Bearer Token", re: /bearer\s+[a-zA-Z0-9._-]{32,}/i },
  { name: "Private Key Block", re: /-----BEGIN (RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----/ },
  { name: "Password Assignment", re: /(?:^|\s)(password|passwd|pwd)\s*[:=]\s*['"][^'"\s]{8,}['"]/i },
]

function isSensitivePath(filePath: string): boolean {
  const parts = filePath.split("/")
  const base = parts[parts.length - 1] || ""
  return SENSITIVE_PATHS.some(re => re.test(base))
}

function scanContent(content: string): { pattern: string; sample: string }[] {
  if (!content) return []
  const matches: { pattern: string; sample: string }[] = []
  for (const { name, re } of SECRET_PATTERNS) {
    const m = content.match(re)
    if (m) {
      matches.push({
        pattern: name,
        sample: m[0].slice(0, 20) + (m[0].length > 20 ? "..." : ""),
      })
    }
  }
  return matches
}

export const SecretScanPlugin: Plugin = async () => {
  return {
    "tool.execute.before": async (input, output) => {
      if (input.tool === "write" || input.tool === "edit") {
        const filePath = output.args?.filePath || ""
        const content = output.args?.content || ""

        const reasons: string[] = []
        if (filePath && isSensitivePath(filePath)) {
          const parts = filePath.split("/")
          reasons.push(`sensitive filename: ${parts[parts.length - 1]}`)
        }

        const matches = scanContent(content)
        if (matches.length > 0) {
          reasons.push(
            `${matches.length} secret pattern(s) detected: ${matches.map(m => m.pattern).join(", ")}`
          )
        }

        if (reasons.length > 0) {
          throw new Error(`[CCDEW Secret Scan] BLOCKED: ${reasons.join(" | ")}`)
        }
      }

      if (input.tool === "read") {
        const filePath = output.args?.filePath || ""
        if (isSensitivePath(filePath)) {
          throw new Error(
            `[CCDEW Secret Scan] BLOCKED: reading sensitive file: ${filePath}`
          )
        }
      }
    },
  }
}
