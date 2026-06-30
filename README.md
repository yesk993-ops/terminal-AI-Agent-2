# 🤖 Tell — AI Terminal Assistant

A terminal-based AI assistant powered by **OpenRouter** and **NVIDIA NIM**. Ask questions, run system tasks, and automate coding — all from your command line. Automatically falls back between providers and models for maximum uptime.

[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows-lightgrey.svg)]()
[![OpenRouter](https://img.shields.io/badge/OpenRouter-Free-FF6B6B.svg)](https://openrouter.ai)
[![NVIDIA NIM](https://img.shields.io/badge/NVIDIA-NIM-76B900.svg)](https://build.nvidia.com)

---

## Quick Start

```bash
git clone https://github.com/yesk993-ops/terminal-AI-Agent-2.git
cd terminal-AI-Agent-2
bash install.sh
export OPENROUTER_API_KEY="sk-or-..."
tell "what is docker?"
```

Get a free API key at [openrouter.ai/keys](https://openrouter.ai/keys) — no credit card required.

### Using NVIDIA instead

```bash
export NVIDIA_API_KEY="nvapi-..."
# Key at https://build.nvidia.com/explore
```

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

## Multi-Provider Architecture

Tell supports both OpenRouter and NVIDIA simultaneously:

1. **OpenRouter** — top free models tried in order:
   - `qwen/qwen3-coder:free` (1M context)
   - `google/gemma-4-26b-a4b-it:free` (262K)
   - `openrouter/owl-alpha` (1M context)
2. **NVIDIA NIM** — 3 models as fallback
3. **Zero-delay failover** — on any error, instantly tries the next model
4. **Fast streaming** — raw tokens delivered without heavy post-processing
5. **Speed mode** — enable `"speed_mode": true` in `.tellrc` for optimized performance

Configure which providers and models to use in `.tellrc`:

```json
{
  "speed_mode": true,
  "providers": ["openrouter", "nvidia"],
  "models": {
    "openrouter": {
      "query": ["qwen/qwen3-coder:free", "google/gemma-4-26b-a4b-it:free", "openrouter/owl-alpha"],
      "system": ["qwen/qwen3-coder:free", "google/gemma-4-26b-a4b-it:free", "openrouter/owl-alpha"]
    },
    "nvidia": {
      "query": ["meta/llama-3.1-8b-instruct", "mistralai/mistral-small-4-119b-2603", "deepseek-ai/deepseek-v4-pro"],
      "system": ["meta/llama-3.1-8b-instruct", "mistralai/mistral-small-4-119b-2603", "deepseek-ai/deepseek-v4-pro"]
    }
  },
  "ui": {
    "border_style": "clean",
    "theme": "eye-friendly",
    "themes": {
      "eye-friendly": { "border": 102, "text": 188, "prompt": 130, "accent": 107, "bold": 107 },
      "warm":        { "border": 130, "text": 180, "prompt": 173, "accent": 179, "bold": 179 },
      "cool":        { "border": 37,  "text": 153, "prompt": 39,  "accent": 33,  "bold": 39 },
      "default":     { "border": 93,  "text": 97,  "prompt": 94,  "accent": 96,  "bold": 96 }
    }
  },
  "performance": {
    "enable_caching": true,
    "cache_ttl": 7200,
    "max_retries": 2,
    "timeout": 5
  }
}
```

---

## Features

- **AI-powered** — natural language queries routed to OpenRouter or NVIDIA
- **Multi-provider** — automatically falls back between providers and models
- **Zero-delay failover** — no retry sleeps, instant model switching
- **Speed mode** — optimized performance with reduced model lists
- **System commands** — disk, memory, processes, ports, network, firewall, services, users
- **Security** — dangerous commands blocked, path traversal protected
- **File operations** — create, read, write files
- **Command history** — track and repeat commands
- **Response caching** — TTL-based eviction for repeated queries (sub-second cached responses)
- **Animated UI** — bordered boxes with typewriter effect, 4 built-in themes (eye-friendly, warm, cool, default)

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
├── api/                 # Multi-provider API client (OpenRouter, NVIDIA)
├── commands/            # Local system commands
├── security/            # Command + path validation
├── ui/                  # Terminal rendering
├── config/              # Configuration loader
└── logger/              # Audit logging
```

---

## Requirements

- Python 3.8+
- At least one API key:
  - [OpenRouter](https://openrouter.ai/keys) (free, recommended)
  - [NVIDIA NIM](https://build.nvidia.com/explore) (free)

---

## License

MIT
