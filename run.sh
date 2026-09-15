#!/usr/bin/env bash
# ==============================================================================
# Universal Starter for Cachy-Sched-Pilot
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Wenn venv vorhanden, aktivieren
if [ -d "$SCRIPT_DIR/venv" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
elif [ -d "$SCRIPT_DIR/.venv" ]; then
    source "$SCRIPT_DIR/.venv/bin/activate"
fi

exec python3 "$SCRIPT_DIR/app.py" "$@"
