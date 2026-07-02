#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/yesk993-ops/terminal-AI-Agent-2.git"

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

if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: python3 not found."
    exit 1
fi

if [[ ! -d ".venv" ]]; then
    echo "Creating Python virtual environment ..."
    python3 -m venv .venv
fi

source .venv/bin/activate

pip install --upgrade pip

if [[ -f "requirements.txt" ]]; then
    echo "Installing dependencies from requirements.txt ..."
    pip install -r requirements.txt
else
    echo "Error: requirements.txt not found."
    exit 1
fi

chmod +x tell
ln -sf "$INSTALL_DIR/tell" "$BIN_LINK"

# Prompt for API key only if running interactively and no key/.env exists
if [[ -t 0 ]] && [[ ! -f "$INSTALL_DIR/.env" ]] && [[ -z "${NVIDIA_API_KEY:-}" ]] && [[ -z "${OPENROUTER_API_KEY:-}" ]]; then
    echo ""
    echo "No API key detected."
    echo "You can get a free key at https://build.nvidia.com/explore"
    echo ""
    read -r -p "Enter your NVIDIA API key (or press Enter to skip): " API_KEY
    if [[ -n "$API_KEY" ]]; then
        echo "NVIDIA_API_KEY=$API_KEY" > "$INSTALL_DIR/.env"
        chmod 600 "$INSTALL_DIR/.env"
        echo "Saved to $INSTALL_DIR/.env"
    fi
fi

echo ""
echo "Installation complete!"
echo ""
echo "Set your API key and run:"
echo "  export NVIDIA_API_KEY=\"nvapi-...\""
echo "  tell \"what is python?\""
echo ""
echo "Or create $INSTALL_DIR/.env with:"
echo "  NVIDIA_API_KEY=your-key-here"
echo ""
if [[ "$EUID" -ne 0 ]]; then
    echo "Make sure $BIN_DIR is in your PATH."
fi