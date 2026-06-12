#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        PYTHON="$cmd"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo "Error: Python not found. Install Python 3 from your package manager:"
    echo "  Ubuntu/Debian: sudo apt install python3"
    echo "  RHEL/Fedora:   sudo dnf install python3"
    exit 1
fi

exec "$PYTHON" "$SCRIPT_DIR/agent.py"
