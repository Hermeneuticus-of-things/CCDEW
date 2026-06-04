#!/usr/bin/env bash
# Hermes Full — bypass security wrapper, apeleaza binary-ul real din venv
REAL_HERMES="$HOME/.hermes/hermes-agent/venv/bin/hermes"
exec "$REAL_HERMES" "$@"
