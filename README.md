# 🤖 Tell — AI Terminal Assistant

A terminal-based AI assistant powered by NVIDIA NIM. Ask questions, run system tasks, and automate coding — all from your command line.

[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows-lightgrey.svg)]()
[![NVIDIA NIM](https://img.shields.io/badge/NVIDIA-NIM-76B900.svg)](https://build.nvidia.com)

---

## Quick Start

```bash
git clone https://github.com/yesk993-ops/terminal-AI-Agent-2.git
cd terminal-AI-Agent-2
bash install.sh
export NVIDIA_API_KEY="nvapi-..."
tell "what is docker?"
```

Get a free API key at [build.nvidia.com/explore](https://build.nvidia.com/explore).

---

## Usage

### Ask Questions
```bash
tell "explain kubernetes networking"
tell "how does git rebase work?"
tell "write a script to monitor CPU temperature"
```

### Run System Tasks
```bash
tell "do disk"          # Disk usage
tell "do memory"        # RAM usage
tell "do ports"         # Open ports
tell "do scan"          # Security scan
tell "what are files"   # List files
```

### Interactive Mode
```bash
./run.sh
```

---

## Features

- **AI-powered** — natural language queries routed to NVIDIA NIM
- **System commands** — disk, memory, processes, ports, network, firewall, services, users
- **Security** — dangerous commands blocked, path traversal protected
- **File operations** — create, read, write files; auto-install dependencies
- **Command history** — track and repeat commands
- **Response caching** — TTL-based eviction for repeated queries
- **Animated UI** — bordered boxes with typewriter effect, multiple themes

---

## Built-in Commands

```
disk    memory    procs    ports    ip    network    sysinfo
uptime  whoami    date     pwd      services  fw    updates
users   logins    scan     suid     security  ls    dir    files
```

Type `help` or `commands` for the full list.

---

## Project Structure

```
tell/
├── main.py              # Entry point
├── agent.py             # Legacy wrapper
├── core/                # Agent orchestration, query analysis
├── api/                 # NVIDIA NIM API client
├── commands/            # Local system commands
├── security/            # Command + path validation
├── ui/                  # Terminal rendering
├── config/              # Configuration loader
└── logger/              # Audit logging
```

---

## Requirements

- Python 3.8+
- NVIDIA API Key ([free tier](https://build.nvidia.com/explore))

---

## License

MIT
