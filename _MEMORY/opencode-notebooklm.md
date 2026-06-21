# OpenCode + NotebookLM Integration

> Last updated: 2026-05-11

## MCP Servers (6 total)

| Name | Command | Purpose |
|---|---|---|
| `github` | mcp-server-github | GitHub API |
| `context7` | context7-mcp | Library docs |
| `tavily` | tavily-mcp | Web search |
| `ccdew` | node ccdew-notebooklm-mcp.cjs | CCDEW tools |
| `opencode-llm` | node opencode-llm-mcp.cjs | LLM gateway (17+ models) |
| `notebooklm` | /home/think/.local/bin/notebooklm-mcp | NotebookLM API |

Config: `~/.config/opencode/mcp.json`

## NotebookLM Notebooks (11 total)

| Notebook | ID | Sources |
|---|---|---|
| Build Your AI OS | 67477efb-c2c1-4886-9c31-cbd82fd0b3cb | 261 |
| Cercetare | 669ee18c-e98a-417f-b546-6655fe41ccb0 | 235 |
| Karma BooK | 6696523d-23cf-4176-86f3-1935a7cb3431 | 211 |
| Clasificarea Tulburărilor | d270d7cb-7b78-473a-a669-e97450ffdf85 | 166 |
| Tik Tok | a1883356-b3f5-4f99-97b4-5af786c4b9cc | 87 |
| Carte | 0c8d9752-77e6-4e47-a5f9-013c15f3373c | 71 |
| Termeni Glosar | 6acbbc90-9fe7-4263-be1a-15ae11d61503 | 30 |
| 108 Lanțuri Vii | e2912672-51cb-4c4d-9758-61c44d73359a | 25 |
| Cele Șapte Praguri | 00f4b0f0-e01d-457b-a1f5-2f5ee2a86095 | 47 |
| Cele Cinci Kosha | 8eddc0c7-eaa3-4323-b21f-575ab323dfcf | 8 |
| Beyond the Visible | 73ad43f7-49f5-4bea-8ed4-64c7f3f0c5d7 | 8 |

Total: 1,163 sources

Auth: thingsofinternet2018@gmail.com — valid

## Audio Generation Status

### Completed (2026-05-11 22:27)
| Notebook | Artifact ID | Status |
|---|---|---|
| Carte | 804a16de-c1a6-4693-ada8-480fc8bfa084 | Done |
| 108 Lanțuri Vii | 299558aa-0573-4660-9a8e-fe9e7050c97d | Done |
| Cercetare | 9259cd92-4311-451a-b82e-206df2ce2473 | Done |
| Karma BooK | 75741c5c-e810-4bf8-9d71-fa9658c9c75b | Done |
| Tik Tok | ff241b8a-2c22-4adb-9ab0-7418f8c5a25f | Done |
| Termeni Glosar | 20e2eaa1-9768-4cc2-8cff-c234dd050d99 | Done |
| Build Your AI OS | e1d59337-3366-4a02-a217-cd2fa3b984fc | Done |
| Beyond the Visible | 72776006-c98c-4ae8-92d1-f95b74382ba0 | Done |

### Pending (needing check)
- Clasificarea Tulburărilor — ID needed
- Cele Șapte Praguri — ID needed
- Cele Cinci Kosha — ID needed

## CCDEW Commands

```bash
opencode status      # Cost tracking
opencode safla       # Learning system
opencode audit       # Architecture audit
opencode graphify    # ASCII report
opencode dashboard   # Web dashboard
opencode mcp         # MCP management
```

## Key Decisions

- No official OpenCode MCP LLM provider (searched GitHub)
- Created opencode-llm-mcp.cjs as workaround gateway (17+ models)
- NotebookLM audio generation: 4 formats (deep_dive, brief, critique, debate)
- Audio generation takes 1-5 minutes — poll with `nlm studio status <notebook_id>`