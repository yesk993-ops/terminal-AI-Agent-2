#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/yesk993-ops/terminal-AI-Agent-2.git"
INSTALL_DIR="/opt/terminal-ai-agent"

if [[ "$EUID" -ne 0 ]]; then
    echo "Please run with sudo."
    exit 1
fi

if [[ -d "$INSTALL_DIR" ]]; then
    echo "Updating existing installation..."
    git -C "$INSTALL_DIR" pull --ff-only origin main
else
    echo "Cloning repository..."
    git clone --depth 1 "$REPO_URL" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

if [[ ! -d ".venv" ]]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

chmod +x tell
ln -sf "$INSTALL_DIR/tell" /usr/local/bin/tell

echo ""
echo "Installation complete."
echo ""
echo "Set your API key:"
echo "  export NVIDIA_API_KEY=\"nvapi-...\""
echo "  tell \"hello\""
echo ""
echo "Or create $INSTALL_DIR/.env with:"
echo "  NVIDIA_API_KEY=your-key"