#!/usr/bin/env bash
# ------------------------------------------------------------
# Cross‑platform installer for terminal‑AI‑Agent‑2
#   Linux/macOS:   curl -fsSL https://raw.githubusercontent.com/yesk993-ops/terminal-AI-Agent-2/main/install_agent.sh | bash
#   Windows PowerShell: iwr -UseBasicParsing https://raw.githubusercontent.com/yesk993-ops/terminal-AI-Agent-2/main/install_agent.sh | iex
# ------------------------------------------------------------
set -euo pipefail

# ---------- OS detection ----------
if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "darwin"* ]]; then
  PLATFORM="unix"
  INSTALL_DIR="$HOME/.terminal-ai-agent"
elif [[ "$OSTYPE" == "msys"* ]] || [[ "$OSTYPE" == "cygwin"* ]] || [[ "$OSTYPE" == "win32"* ]]; then
  PLATFORM="windows"
  INSTALL_DIR="$USERPROFILE\\.terminal-ai-agent"
else
  echo "Unsupported OS: $OSTYPE"
  exit 1
fi

REPO_URL="https://github.com/yesk993-ops/terminal-AI-Agent-2.git"

# ---------- Helper functions ----------
info() { echo -e "\e[32m[INFO]\e[0m $*"; }
warn() { echo -e "\e[33m[WARN]\e[0m $*"; }
error() { echo -e "\e[31m[ERROR]\e[0m $*" >&2; exit 1; }

# ---------- Clone / update repo ----------
info "Cloning repository..."
if [[ -d "$INSTALL_DIR" ]]; then
  info "Updating existing clone..."
  cd "$INSTALL_DIR"
  git pull --quiet origin main
else
  git clone --quiet "$REPO_URL" "$INSTALL_DIR"
fi
cd "$INSTALL_DIR"

# ---------- Install system dependencies ----------
if [[ "$PLATFORM" == "unix" ]]; then
  if command -v apt-get >/dev/null 2>&1; then
    info "Installing via apt (Debian/Ubuntu)..."
    sudo apt-get update -qq
    sudo apt-get install -y python3 python3-pip git
  elif command -v dnf >/dev/null 2>&1; then
    info "Installing via dnf (Fedora)..."
    sudo dnf install -y python3 python3-pip
  elif command -v yum >/dev/null 2>&1; then
    info "Installing via yum (RHEL/CentOS)..."
    sudo yum install -y python3 python3-pip
  else
    warn "No known package manager found. Please ensure python3, pip, and git are installed."
  fi
elif [[ "$PLATFORM" == "windows" ]]; then
  if command -v choco >/dev/null 2>&1; then
    info "Installing via Chocolatey..."
    choco install -y python git
  else
    warn "Chocolatey not found. Please install Python 3.x and Git manually."
  fi
fi

# ---------- Python virtual environment ----------
if [[ -f "requirements.txt" ]]; then
  info "Setting up Python virtual environment..."
  python3 -m venv venv
  if [[ "$PLATFORM" == "unix" ]]; then
    source venv/bin/activate
  else
    # Git‑Bash/WSL still uses bash‑style activation
    source venv/Scripts/activate
  fi
  pip install --quiet --upgrade pip
  pip install --quiet -r requirements.txt
  deactivate
else
  warn "No requirements.txt found – skipping Python deps."
fi

# ---------- API key configuration ----------
info "Please provide your API keys (leave blank to skip)."
read -rp "NVIDIA API key: " NVIDIA_KEY
read -rp "Azure OpenAI endpoint (optional): " AZURE_ENDPOINT
read -rp "Azure OpenAI key (optional): " AZURE_KEY

CONFIG_FILE="$INSTALL_DIR/config.yaml"
mkdir -p "$(dirname "$CONFIG_FILE")"
cat > "$CONFIG_FILE" <<EOF
nvidia_api_key: "$NVIDIA_KEY"
azure_openai_endpoint: "$AZURE_ENDPOINT"
azure_openai_key: "$AZURE_KEY"
EOF
info "Configuration written to $CONFIG_FILE"

# ---------- Final instructions ----------
info "Installation complete!"
if [[ "$PLATFORM" == "unix" ]]; then
  echo -e "\nTo run the agent:"
  echo "  cd \"$INSTALL_DIR\" && source venv/bin/activate && python -m agent"
else
  echo -e "\nTo run the agent (Git‑Bash/WSL):"
  echo "  cd \"$INSTALL_DIR\" && source venv/Scripts/activate && python -m agent"
  echo -e "\nOr from PowerShell:"
  echo "  & \"$INSTALL_DIR\\\\venv\\\\Scripts\\\\activate.ps1\"; python -m agent"
fi
echo ""
echo "You can now edit $CONFIG_FILE to add/adjust your API keys."