# tell - AI System & Coding Agent

Terminal-based AI assistant powered by NVIDIA NIM. Executes shell commands, manages files, monitors systems, and writes code — all from natural language.

## Requirements

- Python 3.8+
- NVIDIA API key ([get one free](https://build.nvidia.com/explore))

## Installation

One command for both Ubuntu and RHEL:

```bash
bash install.sh
```

This will:
1. Detect your OS and install `python3`, `pip`, and `venv` via `apt`, `dnf`, or `yum`
2. Create a virtual environment (`.venv`) in the project directory
3. Install all Python dependencies

No need to activate a venv manually — `tell` and `run.sh` auto-detect it.

## Quick Start

Set your API key and run:

```bash
export NVIDIA_API_KEY="nvapi-..."
./tell "check disk usage"
```

Or use interactive mode:

```bash
./run.sh
```

## Usage

### Command line (one-shot)

```bash
./tell "show me running processes"
./tell "create a python web server"
./tell "check disk space"
./tell "install nginx"
```

### Interactive mode

```bash
./run.sh
```

Then type commands naturally:
- `check disk usage`
- `what ports are open?`
- `create a flask todo app`
- `run ls -la`
- `read /etc/os-release`

### Built-in quick commands

| Command | Description |
|---------|-------------|
| `disk` | Disk usage summary |
| `memory` | RAM usage |
| `procs` | Top processes by CPU |
| `sysinfo` | Kernel and OS info |
| `ports` | Open listening ports |
| `services` | Running systemd services |
| `updates` | Available package updates |
| `fw` / `firewall` | Firewall status |
| `users` | Logged-in users |
| `security` | Full security overview |
| `whoami` | Current user |
| `uptime` | System uptime |
| `ip` | IP addresses |
| `date` | Current date/time |

### Agent commands

- `quit` / `exit` — Exit
- `clear` — Clear screen
- `reset` — Reset conversation
- `help` — Show help
- `border` — Cycle border styles

## Cross-platform Support

This agent works on both **Debian/Ubuntu** (apt) and **RHEL/Fedora/CentOS** (dnf/yum) systems. Package manager detection is automatic.

## API Key

Get your free NVIDIA API key at [build.nvidia.com](https://build.nvidia.com/explore).

Set it as an environment variable:

```bash
export NVIDIA_API_KEY="nvapi-..."
```

Or add to your `~/.bashrc` / `~/.zshrc` to make it permanent:

```bash
echo 'export NVIDIA_API_KEY="nvapi-..."' >> ~/.bashrc
source ~/.bashrc
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NVIDIA_API_KEY` | — | **Required.** Your NVIDIA NIM API key |
| `NVIDIA_MODEL` | (multi-model) | Comma-separated model list to override defaults |
| `TELL_BORDER` | `rounded` | Border style: `rounded`, `classic`, `sharp`, `thick` |
