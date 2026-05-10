---
name: Mandatory PII redaction in logs
severity: MED
version: v3.3
date: 2026-05-10
status: applied
tags: [security, privacy, logging, gdpr]
---

# Mandatory PII redaction in logs

## Context
`error-log.cjs` was writing messages + extra obj directly into `errors.jsonl` without filtering. Risk:
- user prompt content with emails/PII
- API keys leaking in messages
- absolute home paths (`C:\Users\Alice\...`) → identifies the user
- JWTs in error stacks

## Decision
**`lib/redact.cjs` integrated automatically into `error-log.cjs::logError()`.**

## Patterns redacted
```js
emails    → <email>
phones    → <phone?>
JWT       → <jwt>
hex>40    → <hex>
sk-ant-*  → <api-key>
sk-*      → <api-key>
AKIA[A-Z]{16} → <aws-key>
$HOME     → ~
```

## Consequences
- All logged errors pass through `redact()` automatically
- `redactObject` recursive (depth ≤5) for nested fields
- 10 regression tests (`redact.test.cjs`)
- **Does not block real debugging** — error signature (code, stack lines) preserved

## Trade-off
~5ms lost per error log (negligible). In return, logs are safe-to-share (support tickets, GitHub issues).
