# tell - AI System & Coding Agent

Terminal-based AI assistant powered by NVIDIA NIM. Two modes:

- **`tell <question>`** — Answer queries (no system actions)
- **`do <task>`** — System/coding tasks (shell, files, code generation)

Works on **Linux** and **Windows**.

## Requirements

- Python 3.8+
- NVIDIA API key ([get one free](https://build.nvidia.com/explore))

## Installation

### Linux

```bash
bash install.sh
```

This will:
1. Detect your OS and install `python3`, `pip`, and `venv` via `apt`, `dnf`, or `yum`
2. Create a virtual environment (`.venv`) in the project directory
3. Install all Python dependencies

No need to activate a venv manually — `tell` and `run.sh` auto-detect it.

### Windows

```powershell
.\install.ps1
```

Or manually:

```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

## Quick Start

Set your API key and run:

### Linux

```bash
export NVIDIA_API_KEY="nvapi-..."
tell "what is python?"
tell "do check disk usage"
```

### Windows

```cmd
set NVIDIA_API_KEY="nvapi-..."
tell.bat "what is python?"
tell.bat "do check disk usage"
```

Or use interactive mode:

```bash
bash run.sh        # Linux
python agent.py    # Any platform
```

## Usage

### tell — Answer queries only

```bash
tell "what is python?"
tell "how does memory management work?"
```

### do — System and coding tasks

```bash
tell "do check disk usage"
tell "do create a flask app"
tell "do ls -la"
tell "do update my system"
```

### Interactive mode

```bash
./run.sh                          # Linux
python agent.py                   # Any platform
```

| Input | Behavior |
|-------|----------|
| `what is python?` | Query-only answer |
| `do check disk` | System/coding task |
| `clear` | Clear screen |
| `reset` | Reset conversation |
| `help` | Show help |
| `border` | Cycle border styles |

### Built-in quick commands (use with `do`)

| Command | Linux | Windows |
|---------|-------|---------|
| `do disk` | `df -h` | `shutil.disk_usage` |
| `do memory` | `free -h` | `psutil.virtual_memory` |
| `do procs` / `do ps` | `ps aux` | `tasklist` |
| `do ports` | `ss -tlnp` | `netstat -ano` |
| `do services` | `systemctl` | `sc query` |
| `do ip` | `ip addr` | `ipconfig` |
| `do sysinfo` | `uname -a` | `systeminfo` |
| `do users` | `who -u` | `query user` |
| `do fw` / `do firewall` | `ufw` / `iptables` | `netsh advfirewall` |
| `do updates` | `apt` / `dnf` / `yum` | `winget` |
| `do security` | Full scan | Windows equivalent |
| `do uptime` | `uptime` | `psutil.boot_time` |

### Agent commands

- `do <task>` — Universal dispatcher: local commands, shell, or AI fallback
- `quit` / `exit` — Exit
- `clear` — Clear screen
- `reset` — Reset conversation
- `help` — Show help
- `border` — Cycle border styles

## API Key

Get your free NVIDIA API key at [build.nvidia.com](https://build.nvidia.com/explore).

### Linux (persist)

```bash
echo 'export NVIDIA_API_KEY="nvapi-..."' >> ~/.bashrc
source ~/.bashrc
```

### Windows (persist)

```powershell
[Environment]::SetEnvironmentVariable("NVIDIA_API_KEY", "nvapi-...", "User")
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NVIDIA_API_KEY` | — | **Required.** Your NVIDIA NIM API key |
| `NVIDIA_MODEL` | (multi-model) | Comma-separated model list to override defaults |
| `TELL_BORDER` | `rounded` | Border style: `rounded`, `classic`, `sharp`, `thick` |
