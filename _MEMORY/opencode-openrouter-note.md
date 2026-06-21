# OpenCode + OpenRouter - Solutie Finala

## Problema: "No endpoints found that support tool use"

**Cauza**: Eroarea vine de la **OpenRouter**, nu de la OpenCode.
- OpenCode trimite requests cu `tools` (bash, edit, read, write, etc.)
- OpenRouter filtrează provider-ele care suportă tool use
- Dacă niciun provider endpoint nu suportă tool use → eroare

## Solutia Aplicata

1. Adaugat `"tool_call": true` explicit la fiecare model în `opencode.json`
2. Adaugat provider routing options cu fallbacks
3. Adaugat `tool_call: true` la modelele Ollama (backup sigur)

## Config Final

```json
"model": "openrouter/qwen/qwen3-coder:free"
```

Cu `tool_call: true` explicit pentru toate modelele.

## Modele Gratuite cu Tool Use Confirmat

| Model | tool_call | Status |
|-------|-----------|--------|
| qwen/qwen3-coder:free | true | ✅ |
| deepseek/deepseek-v4-flash:free | true | ✅ |
| meta-llama/llama-3.3-70b-instruct:free | true | ✅ |
| nousresearch/hermes-3-llama-3.1-405b:free | true | ✅ |

## Backup: Ollama Local

Dacă OpenRouter nu merge, comută la:
```json
"model": "ollama/qwen2.5-coder"
```

Ollama rulează local, tool_call garantat.

## Limbă: Română
## User: think
## Hermes: helper activ
