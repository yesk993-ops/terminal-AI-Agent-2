#!/usr/bin/env bash
# Global installer for terminal‑AI‑Agent‑2
set -euo pipefail

REPO_URL="https://github.com/yesk993-ops/terminal-AI-Agent-2.git"
INSTALL_DIR="/opt/terminal-ai-agent"
BIN_LINK="/usr/local/bin/tell"

# ----- Clone or update repo -----
if [[ -d "$INSTALL_DIR" ]]; then
    echo "Updating existing installation at $INSTALL_DIR ..."
    git -C "$INSTALL_DIR" fetch --depth=1 origin
    git -C "$INSTALL_DIR" reset --hard origin/main
else
    echo "Cloning repository into $INSTALL_DIR ..."
    git clone --depth 1 "$REPO_URL" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# ----- Verify Python 3 -----
if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: python3 is not installed. Please install it first."
    exit 1
fi

# ----- Create virtual environment -----
if [[ ! -d ".venv" ]]; then
    echo "Creating Python virtual environment ..."
    python3 -m venv .venv
fi

# Activate venv
source .venv/bin/activate

# Upgrade pip and install setuptools wheel (needed for building if any)
echo "Upgrading pip and installing build essentials ..."
pip install --upgrade pip setuptools wheel

# Install dependencies from requirements.txt (fallback to pyproject)
if [[ -f "requirements.txt" ]]; then
    echo "Installing dependencies from requirements.txt ..."
    pip install -r requirements.txt
elif [[ -f "pyproject.toml" ]]; then
    echo "Installing dependencies from pyproject.toml ..."
    pip install .
else
    echo "Error: No requirements.txt or pyproject.toml found."
    exit 1
fi

# Make entry point executable and create system-wide symlink
chmod +x tell
if [[ -L "$BIN_LINK" ]]; then
    sudo rm -f "$BIN_LINK"
fi
sudo ln -sf "$INSTALL_DIR/tell" "$BIN_LINK"

echo ""
echo "Installation complete!"
echo "You can now run the agent with:"
echo "  tell"
echo "(or directly via $INSTALL_DIR/tell)"