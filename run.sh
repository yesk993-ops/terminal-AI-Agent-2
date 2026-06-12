#!/bin/bash
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
    DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
    SOURCE="$(readlink "$SOURCE")"
    [[ "$SOURCE" != /* ]] && SOURCE="$DIR/$SOURCE"
done
SCRIPT_DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"

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
