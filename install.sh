#!/usr/bin/env bash
# Install terminal-AI-Agent-2 globally
set -euo pipefail

REPO_URL="https://github.com/yesk993-ops/terminal-AI-Agent-2.git"
INSTALL_DIR="/opt/terminal-ai-agent"

if [[ "$EUID" -ne 0 ]]; then
    echo "Please run with sudo."
    exit 1
fi

echo "Cloning repository..."
git clone --depth 1 "$REPO_URL" "$INSTALL_DIR"

cd "$INSTALL_DIR"

echo "Creating virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

chmod +x tell
ln -sf "$INSTALL_DIR/tell" /usr/local/bin/tell

echo ""
echo "Done. Set your API key and run:"
echo "  export NVIDIA_API_KEY=\"nvapi-...\""
echo "  tell \"hello\""
echo ""
echo "Or save it in $INSTALL_DIR/.env:"
echo "  NVIDIA_API_KEY=your-key"