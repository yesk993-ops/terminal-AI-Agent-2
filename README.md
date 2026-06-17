# 🤖 Tell — AI Terminal Assistant

> **Your AI co-pilot for the terminal.** Ask questions, run system tasks, automate coding — all without leaving the command line.

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/pylint-8.59/10-brightgreen" alt="Pylint">
  <img src="https://img.shields.io/badge/mypy-2_errors-yellow" alt="Mypy">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/Platform-Linux%20%7C%20Windows%20%7C%20macOS-lightgrey" alt="Platform">
  <img src="https://img.shields.io/badge/NVIDIA-NIM-76B900?logo=nvidia" alt="NVIDIA NIM">
  <img src="https://img.shields.io/badge/PRs-welcome-brightgreen" alt="PRs Welcome">
</p>

---

## 🎯 Why Tell?

| Instead of typing… | Just type… |
|---|---|
| `docker ps \| awk '{print $1}' \| xargs docker inspect...` | `tell "check which containers are using too much memory"` |
| `python3 -c "import psutil; print(psutil.disk_usage('/'))"` | `tell "do check disk space"` |
| Googling "how to find large files in linux" | `tell "find all files over 100MB in this directory"` |

**Tell understands natural language** — it routes simple queries to local commands and complex ones to the NVIDIA NIM AI. No context switching, no browser tabs, no memorizing obscure flags.

---

## ✨ Features at a Glance

| Category | Capabilities |
|----------|-------------|
| 🧠 **AI-Powered** | Answers questions, writes code, explains concepts via NVIDIA NIM |
| 💻 **System Control** | Disk, memory, processes, ports, network, firewall, uptime, users |
| 🔐 **Security-First** | Dangerous commands blocked, path traversal protected, permissive file mode 0o600 |
| 📦 **File Operations** | Create, read, write files; auto-install pip/npm dependencies |
| 🎨 **Beautiful UI** | Colorful bordered boxes, typewriter animation, multiple border themes |
| 📊 **Audit Trail** | Full logging, command history with search, response caching |
| 🌍 **Multi-language** | English (default), Marathi, Hindi support |
| ⚡ **Fast** | Response caching with TTL eviction, streaming output |

---

## 🚀 Quick Start

```bash
# One-liner install
git clone https://github.com/yesk993-ops/terminal-AI-Agent-2.git
cd terminal-AI-Agent-2
bash install.sh

# Set your API key (free at https://build.nvidia.com/explore)
export NVIDIA_API_KEY="nvapi-..."

# Start using it!
tell "what is docker?"
tell "do check disk usage"
```

---

## 📖 Usage Examples

### 💬 Ask Questions
```bash
tell "explain how kubernetes networking works"
tell "what's the difference between git merge and rebase?"
tell "write a python script to monitor CPU temperature"
```

### ⚡ Run System Tasks
```bash
tell "do disk"         # Check disk usage
tell "do memory"       # Check memory usage
tell "do ports"        # Show open ports
tell "do scan"         # Full security scan
tell "do services"     # List running services
tell "do uptime"       # System uptime
```

### 🌐 Natural Language File Browsing
```bash
tell "what are files in current folder"
tell "show me all python files"
tell "list files larger than 10MB"
```

### 🎮 Interactive Mode
```bash
./run.sh              # Rich interactive session with history
python3 main.py       # Same, any platform
```

---

## ⚙️ Built-in Commands

```
disk  memory  procs  ports  ip  network  sysinfo  uptime
whoami  date  pwd  services  fw  updates  users  logins
scan  suid  security  ls  dir  files
```

Type `help` or `commands` inside Tell to see them all.

---

## 🔒 Security Architecture

```
User Input → SecurityManager → LocalCommands / NVIDIAAgent → Sanitized Output
                │
                ├─ is_dangerous() — blocks rm -rf, mkfs, dd, shutdown, reboot
                ├─ is_safe_path() — prevents path traversal outside allowed dirs
                └─ safe_execute() — sanitized env, timeout, output capped at 2000 chars
```

---

## 📁 Modular Architecture

```
tell/
├── core/              # Agent orchestration, prompt selection, command dispatch
│   ├── __init__.py    # TellAgent — the main controller (528 lines)
│   ├── analyzer.py    # 3-tier query complexity classifier
│   ├── prompts.py     # Shared system prompts (coding + Q&A)
│   └── command_history.py  # In-memory history with file export
├── api/               # NVIDIA NIM client (streaming + batch)
├── commands/          # 20+ local system commands
├── security/          # Dangerous command + path traversal detection
├── ui/                # Terminal box rendering with themes
├── config/            # .tellrc JSON config loader
├── logger/            # Structured file + console logging
├── main.py            # Entry point (inline + interactive)
└── agent.py           # Legacy wrapper (delegates to core)
```

---

## 📊 Code Quality

| Metric | Score |
|--------|-------|
| Pylint | **8.59/10** |
| Mypy | **2 errors** (3rd-party stubs only) |
| Bandit | **0 high, 0 medium** |
| Type coverage | ~85% annotated |
| Executable lines | ~1,950 |

---

## 📦 Requirements

- Python 3.8+
- NVIDIA API Key ([free tier available](https://build.nvidia.com/explore))

Dependencies: `requests`, `psutil` (installed automatically by `install.sh`)

---

## 🤝 Contributing

Contributions are welcome! Here's how to help:

1. **⭐ Star the repo** — helps others discover it
2. **🐛 Report bugs** — open an issue
3. **💡 Suggest features** — open a discussion
4. **🔧 Submit PRs** — fork, branch, commit, push, PR

---

## 📄 License

MIT — see [LICENSE](LICENSE)

---

## ⭐ Support

If Tell saves you time or helps you learn, **star the repo** and share it with a friend!

---

<p align="center">
  <sub>Built with ❤️ and NVIDIA NIM</sub>
</p>
