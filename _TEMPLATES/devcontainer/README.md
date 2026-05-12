# CCDEW Dev Container Template

## Purpose

Dev container for running CCDEW workspace in a consistent development environment.

## Usage

```bash
# Open in VS Code
code --folder-uri . → Ctrl+Shift+P → "Dev Containers: Open Folder in Container"

# Or with Remote Containers extension
devcontainer open .
```

## What's included

- Node.js 20 LTS
- Python 3 (for obs.py, enneagram_router.py, auto_learn scripts)
- Git (for version control)
- npm (for Node packages)

## Post-create setup

After container creation, `codeburn@0.9.7` is installed globally for cost tracking.

## Customization

Edit `devcontainer.json` to add:
- Additional VS Code extensions
- Port forwarding for preview servers
- Volume mounts for persistent data
- Environment variables