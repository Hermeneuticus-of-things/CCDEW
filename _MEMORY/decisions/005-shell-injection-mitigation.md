---
name: Shell injection mitigation via lib/path-safe
severity: HIGH
version: v3.2
date: 2026-05-10
status: applied
tags: [security, shell, windows, exec]
---

# Shell injection mitigation via lib/path-safe

## Context
Node 22 received CVE-2024-27980 patch: `execFileSync` refuses `.cmd`/`.bat` without `shell: true`. Workaround: set `shell: true` only for these extensions. **But:** `shell: true` with a dynamically detected path (from `where codeburn`) is potential injection if PATH is attacker-controlled and returns something like `C:\evil & calc.exe`.

## Options

**A. Status quo v3.0 (no validation)**
- MEDIUM risk: PATH manipulation → injection

**B. Whitelist path (full canonical)**
- Pro: max safety
- Contra: rigid, breaks if codeburn is installed at an unexpected path

**C. Reject shell metacharacters in path**
- Pro: simple, blocks most attacks
- Contra: doesn't block `..` traversal etc.

## Decision
**C — `lib/path-safe.cjs::isSafeBinaryPath()`** verifies the path doesn't contain `& ; | $ ( ) ' " ! * ? \r \n` (excluding `\` which is a valid Windows separator).

## Rationale
- Defensive programming at the `shell: true` boundary
- Backslash excluded from metachars (false-positive blocking on Windows)
- 10 tests with malicious input (all rejected)

## Consequences
- `codeburn.cjs::fetchRealStatus()` validates `bin` before `execFileSync`
- Error logged to `error-log.cjs` if unsafe path detected
- 4 modules using `shell:true` (codeburn, verify, quality-gate, review) protected at the path level
- `lib/path-safe.test.cjs` 10/10 PASS

## Bug found while testing this fix
Initially the regex included `\\` (backslash) as metachar → blocked valid Windows path `C:\nodejs\node.exe`. The path-safe.test.cjs test caught the false-pos at "safe Windows path passes" → fix: removed `\\` from the pattern.
