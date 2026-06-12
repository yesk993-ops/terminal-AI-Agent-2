#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== tell - AI Agent Installer ==="
echo ""

# --- OS detection ---
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS_ID="$ID"
    OS_LIKE="$ID_LIKE"
else
    echo "Cannot detect OS. Proceeding with generic setup..."
    OS_ID="unknown"
    OS_LIKE=""
fi

# --- Install system packages ---
install_sys_pkgs() {
    if command -v apt &>/dev/null; then
        echo "[apt] Installing python3, python3-pip, python3-venv..."
        sudo apt update -qq && sudo apt install -y python3 python3-pip python3-venv
    elif command -v dnf &>/dev/null; then
        echo "[dnf] Installing python3, python3-pip..."
        sudo dnf install -y python3 python3-pip
    elif command -v yum &>/dev/null; then
        echo "[yum] Installing python3, python3-pip..."
        sudo yum install -y python3 python3-pip
    else
        echo "Warning: No supported package manager found (apt/dnf/yum)."
        echo "Make sure python3 and pip are installed manually."
    fi
}

# Try system packages, fall back to pip --user if sudo unavailable
if sudo -n true 2>/dev/null; then
    install_sys_pkgs
else
    echo "No passwordless sudo. Skipping system packages."
    echo "Ensure python3 and pip are installed, or run install.sh with sudo."
fi

# --- Create venv ---
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
else
    echo "Virtual environment already exists."
fi

# --- Activate and install pip deps ---
echo "Installing Python dependencies..."
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt
deactivate

# --- Make scripts executable ---
chmod +x tell run.sh

echo ""
echo "=== Installation complete! ==="
echo ""
echo "Set your API key:"
echo "  export NVIDIA_API_KEY=\"nvapi-...\""
echo ""
echo "Then use:"
echo "  ./tell \"check disk usage\"          # one-shot mode"
echo "  ./run.sh                             # interactive mode"
echo ""
echo "TIP: Add the export to ~/.bashrc so you don't need to set it every time:"
echo "  echo 'export NVIDIA_API_KEY=\"nvapi-...\"' >> ~/.bashrc"
