---
name: PII redaction obligatorie în logs
severity: MED
version: v3.3
date: 2026-05-10
status: applied
tags: [security, privacy, logging, gdpr]
---

# PII redaction obligatorie în logs

## Context
`error-log.cjs` scria mesaje + extra obj direct în `errors.jsonl` fără filtrare. Risc:
- prompt user content cu emails/PII
- API keys leakat în message
- home paths absolute (`C:\Users\Alice\...`) → identifică userul
- JWT-uri în error stacks

## Decizie
**`lib/redact.cjs` integrat automat în `error-log.cjs::logError()`.**

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

## Consecințe
- Toate erorile loguite trec prin `redact()` automat
- `redactObject` recursiv (depth ≤5) pentru nested fields
- 10 teste regression (`redact.test.cjs`)
- **Nu blochează debugging real** — semnătura erorii (code, stack lines) păstrată

## Trade-off
Pierdem ~5ms per error log (negligibil). În schimb, logs sunt safe-to-share (suport tickets, GitHub issues).
