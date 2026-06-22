# Changelog

## [Unreleased]

## [2026-06-22]

### Added
- Full English translation of all files (README, MCP servers, enneagram_router, hooks)
- Badge section in README (CI, License, Node.js, Python, PRs Welcome)
- MIT LICENSE file
- CONTRIBUTING.md with contribution guidelines
- SECURITY.md with vulnerability reporting policy
- CODE_OF_CONDUCT.md (Contributor Covenant v2.1)
- GitHub Actions CI workflow (tests, syntax checks, spelling)
- Convergent/Divergent feedback loop (`ccdew-feedback-loop.py`)
- NLM auto-cache warmer (`nlm-cache-warmer.py`)
- NLM session hook integrated into `hook-handler.cjs`
- 72 tests (42 convergent-divergent + 30 NLM bridge)
- `nlm-auth` command handler in hook-handler

### Changed
- LLM & Models section rewritten as generic (not tied to specific agents)
- Mermaid diagram: replaced `&`, `→`, `①-⑥` with ASCII-safe equivalents
- Tool descriptions in all MCP servers now in English

## [2026-06-21]

### Added
- Convergent/Divergent Engine MCP server (5 tools)
- NLM Bridge MCP server (7 tools, 10-level async protocol)
- Fractal Enneagram v2 (5 zoom levels, 5 lenses, priority matrix)
- NLM session hook for auth check
- PIN removed from source code (now uses `HERMES_VAULT_PIN` env var)
- Mermaid diagram with agent tree, skill tree, CLI, templates, cron

### Fixed
- Mermaid parse errors: parentheses in node labels
- Large file (OpenCodeDesktop 159MB) removed from history
- PIN 1791 scrubbed from all git history

## [2026-06-20]

### Added
- Initial CCDEW ecosystem deploy
- Enneagram Router with 9 nodes, 27 arcs
- 6 MCP servers (ccdew-mcp, opencode-llm, notebooklm, mission-control)
- 5 bridges (A2A, MCP, External, Claude-OpenCode, Hermes A0)
- 80+ helper engines (Python + CJS)
- Hermes memory pyramid (6 levels)
- 105+ agent profiles, 133 skills
