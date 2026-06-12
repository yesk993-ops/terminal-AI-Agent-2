#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Use venv if it exists
if [ -f "$SCRIPT_DIR/.venv/bin/python3" ]; then
    PYTHON="$SCRIPT_DIR/.venv/bin/python3"
else
    for cmd in python3 python; do
        if command -v "$cmd" &>/dev/null; then
            PYTHON="$cmd"
            break
        fi
    done
fi

if [ -z "$PYTHON" ]; then
    echo "Error: Python not found. Run 'bash install.sh' first."
    exit 1
fi

exec "$PYTHON" "$SCRIPT_DIR/agent.py"
