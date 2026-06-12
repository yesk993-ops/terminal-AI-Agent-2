# NVIDIA System Agent

Terminal-based system administrator and coding agent powered by Kimi K2.6.

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
python3 agent.py
# or
./run.sh
```

## Commands

### Quick Commands
| Command | Description |
|---------|-------------|
| `run <cmd>` | Execute shell command |
| `read <file>` | Read file contents |
| `write <file>` | Write to file |
| `disk` | Disk usage |
| `mem` | Memory info |
| `procs` | Top processes |
| `sysinfo` | System info |
| `net` | Network info |
| `install <pkg>` | Install package |
| `service <act> <name>` | Manage service |

### Natural Language
Just ask in plain English:
- "show me running processes"
- "create a python web server"
- "check disk space"
- "install docker"
- "restart nginx"
- "what's using the most memory?"

### Agent Commands
- `quit` / `exit` - Exit
- `clear` - Clear screen
- `reset` - Reset conversation
- `help` - Show help

## Features

- Execute any shell command
- Read/write/copy/delete files
- System monitoring (CPU, RAM, disk)
- Process management
- Package installation
- Service management (systemd)
- Network information
- Dangerous command protection
- Streaming AI responses
