# 🤖 Tell — AI Terminal Assistant

> A powerful terminal-based AI assistant powered by NVIDIA NIM. Get instant answers, run system tasks, and automate coding — all from your command line.

[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows-lightgrey.svg)]()
[![NVIDIA NIM](https://img.shields.io/badge/NVIDIA-NIM-76B900.svg)](https://build.nvidia.com)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🧠 **Smart Queries** | Ask anything — get structured, expert-level answers |
| 💻 **System Tasks** | Run shell commands, check disk, memory, processes |
| 🔐 **Security** | Dangerous commands blocked, path traversal protected |
| 📝 **Command History** | Track and repeat previous commands |
| 🎨 **Animated UI** | Beautiful terminal boxes with typewriter effect |
| 🌍 **Multi-language** | English (default), Marathi, Hindi support |
| ⚡ **Fast** | Response caching for repeated queries |
| 📊 **Logging** | Full audit trail of all actions |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- NVIDIA API Key ([Get one free](https://build.nvidia.com/explore))

### Installation

**Linux/macOS:**
```bash
git clone https://github.com/yesk993-ops/terminal-AI-Agent-2.git
cd terminal-AI-Agent-2
bash install.sh
```

**Windows:**
```powershell
git clone https://github.com/yesk993-ops/terminal-AI-Agent-2.git
cd terminal-AI-Agent-2
.\install.ps1
```

### Set API Key

```bash
# Linux/macOS
export NVIDIA_API_KEY="nvapi-..."

# Windows
set NVIDIA_API_KEY="nvapi-..."
```

---

## 📖 Usage

### Query Mode (`tell`)

Ask questions and get expert answers:

```bash
tell "what is docker?"
tell "how does kubernetes work?"
tell "explain python decorators"
```

### Task Mode (`do`)

Run system and coding tasks:

```bash
tell "do check disk usage"
tell "do create a flask app"
tell "do list running processes"
tell "do scan for security issues"
```

### Interactive Mode

```bash
./run.sh                          # Linux
python agent.py                   # Any platform
```

---

## 🎯 Built-in Commands

### System Monitoring

| Command | Description |
|---------|-------------|
| `do disk` | Check disk usage |
| `do memory` | Check memory usage |
| `do procs` | List running processes |
| `do ports` | Show open ports |
| `do ip` | Show IP addresses |
| `do sysinfo` | System information |
| `do uptime` | System uptime |

### Security

| Command | Description |
|---------|-------------|
| `do security` | Run security scan |
| `do fw` | Check firewall status |

### Agent Controls

| Command | Description |
|---------|-------------|
| `help` | Show help |
| `history` | Show command history |
| `border` | Cycle border styles |
| `reset` | Reset conversation |
| `clear` | Clear screen |
| `quit` | Exit |

---

## ⚙️ Configuration

Edit `.tellrc` to customize:

```json
{
  "default_api_key": "",
  "model": "meta/llama-3.3-70b-instruct",
  "max_tokens": 4096,
  "theme": "default",
  "border": "rounded",
  "typing_animation": true,
  "sound_enabled": false
}
```

---

## 🔒 Security Features

- **Command Blocking**: Dangerous commands (rm -rf, fork bombs, etc.) are blocked
- **Path Traversal Protection**: Cannot access files outside allowed directories
- **Input Validation**: Length limits and sanitization
- **API Key Protection**: Never logged or exposed in error messages
- **File Permissions**: Created files have restrictive permissions (0o600)

---

## 📁 Project Structure

```
terminal-AI-Agent-2/
├── agent.py           # Main agent (all logic)
├── install.sh         # Linux installer
├── install.ps1        # Windows installer
├── run.sh             # Linux entry point
├── tell               # Bash script entry
├── tell.bat           # Windows batch entry
├── requirements.txt   # Python dependencies
├── .tellrc            # Configuration file
└── README.md          # This file
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [NVIDIA NIM](https://build.nvidia.com) for API access
- Python community for amazing libraries

---

## 📧 Contact

**yesk993-ops** — [GitHub](https://github.com/yesk993-ops)

⭐ Star this repo if you find it useful!
