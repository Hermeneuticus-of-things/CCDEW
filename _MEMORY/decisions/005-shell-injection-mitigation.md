---
name: Shell injection mitigation cu lib/path-safe
severity: HIGH
version: v3.2
date: 2026-05-10
status: applied
tags: [security, shell, windows, exec]
---

# Shell injection mitigation cu lib/path-safe

## Context
Node 22 a primit patch CVE-2024-27980: `execFileSync` refuză `.cmd`/`.bat` fără `shell: true`. Workaround: setăm `shell: true` doar pentru aceste extensii. **Dar:** `shell: true` cu path detectat dynamic (din `where codeburn`) e potențial injection dacă PATH-ul e atacator-controlled și returnează ceva ca `C:\evil & calc.exe`.

## Opțiuni

**A. Status quo v3.0 (no validation)**
- Risk MEDIUM: PATH manipulation → injection

**B. Whitelisting path (full canonical)**
- Pro: max safety
- Contra: rigid, break dacă codeburn instalat la path neașteptat

**C. Reject shell metacharacters în path**
- Pro: simplu, bloacă majoritatea atacurilor
- Contra: nu blochează `..` traversal etc.

## Decizie
**C — `lib/path-safe.cjs::isSafeBinaryPath()`** verifică path nu conține `& ; | $ ( ) ' " ! * ? \r \n` (excluding `\` care e separator Windows valid).

## Motiv
- Defensive programming la `shell: true` boundary
- Backslash exclus din metachars (false-positive blocking pe Windows)
- 10 teste cu input malicious (toate respinse)

## Consecințe
- `codeburn.cjs::fetchRealStatus()` validează `bin` înainte de `execFileSync`
- Eroare logged la `error-log.cjs` dacă unsafe path detectat
- 4 module care folosesc `shell:true` (codeburn, verify, quality-gate, review) protejate la nivel de path
- `lib/path-safe.test.cjs` 10/10 PASS

## Bug găsit chiar în testarea acestui fix
Inițial regex includea `\\` (backslash) ca metachar → blocat path Windows valid `C:\nodejs\node.exe`. Test path-safe.test.cjs a prins false-pos la "safe Windows path passes" → fix: scos `\\` din pattern.
