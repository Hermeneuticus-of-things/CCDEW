# Hermes Autonomous Agent

Rulează Hermes ca agent autonom cu loop reflexiv.

## Utilizare

```
node .claude/helpers/hermes-autonomous.cjs "task description"
```

## Cerințe

- Hermes MCP configurat în OpenCode Desktop
- Tool-uri `hermes_*` disponibile în sesiune
- Permisiuni de scriere în `~/.hermes/`

## Cum Funcționează

### 1. Inițializare
- Încarcă memory din `~/.hermes/memories/autonomous.json`
- Incrementează counter sesiuni
- Pregătește contextul cu learnings/patterns anterioare

### 2. Loop Reflexiv
```
while (iteration < 50) {
  if (shouldReflect()) {
    [REFLECT] → evaluează progres
    if (needsCorrection()) {
      [CORRECT] → auto-corectează
    }
  }
  
  [ACT] → execută acțiune Hermes
  
  if ([DONE]) break;
  if ([ERROR]) record & continue;
  
  iteration++;
}
```

### 3. Memory
```javascript
{
  learnings: [{ key, value, ts, iteration }],
  patterns: [{ situation, response, ts }],
  errors: [{ error, ts, iteration }],
  corrections: [{ original, corrected, ts }]
}
```

### 4. Self-Correction
La eroare:
1. Parsează eroarea din output
2. Generează corecție
3. Reîncearcă cu ajustări
4. Stochează lecția

## Configurare OpenCode Desktop

```bash
# În ~/.config/opencode/mcp.json:
{
  "hermes": {
    "command": "/home/think/.local/bin/hermes",
    "args": ["mcp", "serve"],
    "env": {}
  }
}
```

## Exemple

```bash
# Task simplu
node .claude/helpers/hermes-autonomous.cjs "List my Telegram conversations"

# Task complex
node .claude/helpers/hermes-autonomous.cjs "Find the last message from John and reply 'Thanks!'"
```

## Securitate

- Hermes stdio-only via OpenCode Desktop
- Wrapper blochează comenzi non-MCP
- Memory file restricted to user