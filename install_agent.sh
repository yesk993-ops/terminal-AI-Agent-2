#!/usr/bin/env bash
# Global installer for terminal-AI-Agent-2
set -euo pipefail

REPO_URL="https://github.com/yesk993-ops/terminal-AI-Agent-2.git"

# Determine install location: if running as root, use /opt, else user local
if [[ "$EUID" -eq 0 ]]; then
    INSTALL_DIR="/opt/terminal-ai-agent"
    BIN_DIR="/usr/local/bin"
else
    INSTALL_DIR="$HOME/.terminal-ai-agent"
    BIN_DIR="$HOME/.local/bin"
    mkdir -p "$BIN_DIR"
fi

BIN_LINK="$BIN_DIR/tell"

echo "Cloning repository..."
if [[ -d "$INSTALL_DIR" ]]; then
    echo "Updating existing installation at $INSTALL_DIR ..."
    git -C "$INSTALL_DIR" fetch --depth=1 origin
    git -C "$INSTALL_DIR" reset --hard origin/main
else
    echo "Cloning repository into $INSTALL_DIR ..."
    git clone --depth 1 "$REPO_URL" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# Verify Python 3
if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: python3 not found. Please install python3."
    exit 1
fi

# Create virtual environment if not exists
if [[ ! -d ".venv" ]]; then
    echo "Creating Python virtual environment ..."
    python3 -m venv .venv
fi

# Activate venv
source .venv/bin/activate

# Upgrade pip and install build dependencies
echo "Upgrading pip ..."
pip install --upgrade pip
pip install --upgrade setuptools wheel

# Install dependencies
if [[ -f "pyproject.toml" ]]; then
    echo "Installing package from pyproject.toml ..."
    pip install .
elif [[ -f "requirements.txt" ]]; then
    echo "Installing from requirements.txt ..."
    pip install -r requirements.txt
else
    echo "Error: No pyproject.toml or requirements.txt found."
    exit 1
fi

# Make entry point available
chmod +x tell
if [[ -L "$BIN_LINK" ]]; then
    rm -f "$BIN_LINK"
fi
ln -sf "$INSTALL_DIR/tell" "$BIN_LINK"

echo ""
echo "Installation complete!"
echo "You can now run the agent with:"
echo "  tell"
if [[ "$EUID" -ne 0 ]]; then
    echo "Make sure $BIN_DIR is in your PATH is set (usually it is for $HOME/.local/bin)."
fi
echo ""