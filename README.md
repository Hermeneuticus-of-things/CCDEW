# Hermes Autonomous Agent

A self-contained Hermes agent that runs with a reflexive loop, self-evolution, and full tool autonomy. Integrates with OpenCode Desktop to overcome MCP limitations.

## Features

- **Reflexive Loop**: THINK → ACT → OBSERVE → REFLECT → CORRECT
- **Self-Evolution**: Pattern detection, learning, and memory
- **Tool Autonomy**: Uses Hermes MCP tools + OpenCode bash for full terminal access
- **Agent Zero Compliant**: Full Agent Zero patterns implemented
- **No MCP Limitations**: Can execute shell commands via OpenCode

## Installation

1. Save the script to `/home/think/CCDEW/.claude/helpers/hermes-autonomous.cjs`
2. Make it executable: `chmod +x /home/think/CCDEW/.claude/helpers/hermes-autonomous.cjs`
3. Ensure OpenCode Desktop is running with Hermes MCP configured

## Usage

```bash
# Run a task
node /home/think/CCDEW/.claude/helpers/hermes-autonomous.cjs "Your task description"

# Example tasks:
# - "List my Telegram conversations"
# - "Send 'Hello!' to my Telegram chat"
# - "Check last 5 messages and reply 'OK'"
```

## How It Works

1. Hermes runs in a loop (up to 50 iterations)
2. Each iteration: THINK → ACT → OBSERVE → REFLECT (every 3 steps) → CORRECT
3. Uses Hermes MCP tools for messaging
4. Uses OpenCode bash for shell execution
5. Stores learnings in `~/.hermes/memories/autonomous.json`
6. Detects patterns from past sessions
7. Auto-corrects based on errors

## Security

- Runs within OpenCode Desktop sandbox
- No external network access beyond Hermes MCP
- All operations logged in memory file
- Can be stopped anytime with Ctrl+C

## Customization

Edit the script to:
- Add more tools
- Change loop parameters
- Modify system prompt
- Integrate with other services

## Requirements

- OpenCode Desktop installed and running
- Hermes MCP configured in OpenCode
- Python 3.6+

## Testing

Run the test script:
```bash
python /home/think/CCDEW/.claude/helpers/test-hermes-autonomous.py
```

## Support

For issues, check:
- OpenCode Desktop logs
- Hermes MCP configuration
- Script permissions
- Network connectivity

---

*Hermes Autonomous Agent - Full autonomy with Agent Zero patterns*