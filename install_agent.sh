#!/usr/bin/env bash
# Global installer for terminal-AI-Agent-2
set -euo pipefail

REPO_URL="https://github.com/yesk993-ops/terminal-AI-Agent-2.git"
INSTALL_DIR="/opt/terminal-ai-agent"

echo "Cloning repository..."
if [[ -d "$INSTALL_DIR" ]]; then
    echo "Updating existing installation..."
    git -C "$INSTALL_DIR" pull origin main
else
    git clone --depth 1 "$REPO_URL" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# Ensure we have a Python interpreter
if ! command -v python3 &>/dev/null; then
    echo "Error: python3 not found. Please install python3."
    exit 1
fi

# Create virtual environment if not exists
if [[ ! -d ".venv" ]]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate venv
source .venv/bin/activate

# Install/upgrade pip
pip install --upgrade pip

# Install dependencies from pyproject.toml (preferred) or requirements.txt
if [[ -f "pyproject.toml" ]]; then
    pip install .
else
    if [[ -f "requirements.txt" ]]; then
        pip install -r requirements.txt
    fi
fi

# Make the entrypoint script executable and create a symlink in /usr/local/bin
chmod +x tell