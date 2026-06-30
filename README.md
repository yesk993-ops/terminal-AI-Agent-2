# tell – Terminal AI Agent

**tell** is a powerful, terminal-based AI coding and productivity agent built for corporate environments. It combines a ChatGPT‑style natural‑language interface with safe local command execution, document generation, and cross‑session memory — all inside your terminal.

---

## Features

| Feature | Description |
|---------|-------------|
| **General Q&A** | Ask any question and receive well-structured, bold‑formatted answers with terminal colour highlighting. |
| **Coding tasks** | Use `do` to generate, write, and execute code automatically (supports any language). |
| **Document generation** | Ask for a document or SOP and it will be auto‑saved as a Markdown file. |
| **Conversation memory** | Chat history persists across sessions via `.tell_history.json`. |
| **Response completeness** | Automatic continuation loop ensures no answer is cut off. |
| **Local command detection** | Commands like `date`, `df`, `ps` are intercepted and executed safely. |
| **Security** | Dangerous commands are blocked; file writes are restricted to allowed directories. |
| **Syntax highlighting** | Code blocks, inline commands, and file paths are coloured for readability. |
| **Cross‑platform colours** | Uses the standard 16‑colour ANSI palette — identical appearance on Linux, macOS, and Windows terminals. |

---

## Installation

### Prerequisites

- **Python 3.10+**
- **NVIDIA API key** (free tier available at https://build.nvidia.com/explore)

### Quick start

```bash
# 1. Clone the repository
git clone https://github.com/yesk993-ops/terminal-AI-Agent-2.git
cd terminal-AI-Agent-2

# 2. (Optional) Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set your NVIDIA API key
export NVIDIA_API_KEY="your-key-here"

# 5. Run it
python main.py --inline "what is python"
```

### Platform‑specific notes

| Platform | Notes |
|----------|-------|
| **Linux** | Works out of the box. Unicode (box‑drawing) characters may need a modern terminal (GNOME Terminal, Konsole, iTerm2, Windows Terminal). |
| **macOS** | Works out of the box. iTerm2 recommended. |
| **Windows** | Use Windows Terminal or PowerShell 7+. The colour palette uses basic 16‑colour ANSI codes that render identically to Linux/macOS. |

---

## Configuration

Configuration is read from `.tellrc` (JSON format) in the current directory. Key options:

```json
{
  "ui": {
    "border_style": "minimal",
    "theme": "universal"
  },
  "security": {
    "allowed_write_dirs": ["/path/to/allowed"],
    "max_file_size": 10485760,
    "dangerous_commands": ["rm -rf", "mkfs", "dd if="]
  },
  "performance": {
    "enable_caching": true,
    "cache_ttl": 3600,
    "timeout": 45
  },
  "models": {
    "system": "nvidia/nemotron-4-340b-instruct"
  },
  "behavior": {
    "enable_command_history": true,
    "max_history_size": 100
  }
}
```

### Environment variables

| Variable | Purpose |
|----------|---------|
| `NVIDIA_API_KEY` | API key for the NVIDIA LLM backend (required). |
| `TELL_BORDER` | Override border style (e.g. `rounded`, `classic`, `clean`). |

---

## Usage

### Inline mode (single query)

```bash
# General question
python main.py --inline "how does docker work"

# Coding task (auto‑write and execute)
python main.py --inline "do write a python script that prints hello world"

# Document creation (auto‑saves to Markdown)
python main.py --inline "create a document about docker images"

# System command
python main.py --inline "show disk usage"
```

### Interactive mode

```bash
python main.py
```

You will see a prompt (`❯`). Type naturally:

- Type any question to get an answer.
- Prefix with `do ` to run a coding or system task.
- Type `help` to see built‑in commands.
- Type `border` to cycle the box style.
- Type `reset` to clear conversation history.
- Type `history` to see recent commands.

---

## Architecture

```
main.py                  – Entry point, argument parsing, UI routing
├── core/
│   ├── __init__.py      – TellAgent orchestrator (prompt, API, commands)
│   ├── prompts.py       – System prompts (Q&A, coding, document)
│   ├── analyzer.py      – Query complexity analysis, token limits
│   ├── cache.py         – Response caching with TTL
│   ├── command_history.py – Recent‑command tracking
├── api/                 – NVIDIA API client (generate, stream)
├── commands/            – Local command detection & execution
├── ui/
│   ├── __init__.py      – TerminalUI (bordered boxes, themes)
│   ├── highlighter.py   – Syntax highlighting (cross‑platform ANSI)
├── config/              – JSON/ENV config loader
├── security/            – Path validation, dangerous‑command blocking
└── logger/              – File‑based logging
```

### Prompt selection

| Trigger | Prompt used |
|---------|-------------|
| `do <task>` | `CODING_PROMPT` (file‑write + execution directives) |
| `create document …` | `DOCUMENT_PROMPT` (auto‑save to Markdown) |
| Any other query | `QUERY_PROMPT` (ChatGPT‑style, markdown‑friendly) |

---

## Corporate readiness

- **Answer completeness** – Automatic continuation loop if the model stops early.
- **Full conversation memory** – Both user and assistant messages are persisted to `.tell_history.json`.
- **Error handling** – All API calls wrapped in try/except; graceful degradation.
- **Security** – File writes restricted to allowed directories; dangerous commands blocked; permissions set to `0o600`.
- **Cross‑platform** – Uses the standard 16‑colour ANSI palette (codes 30–37, 90–97) that renders identically on Linux, macOS, and Windows.
- **No markdown leakage** – Bold markers (`**`) are converted to ANSI bold so raw markdown never appears in terminal output.
- **Extensible** – Modular architecture makes it easy to swap backends, add commands, or change themes.

---

## Example output

```
╭─────────────────────────────────────────────────────────────────╮
│ **Docker Overview**                                              │
│                                                                   │
│ Docker is a containerization platform that allows developers to  │
│ package, ship, and run applications in containers. Containers    │
│ are lightweight and portable.                                    │
│                                                                   │
│ **Key Components**                                                │
│                                                                   │
│ 1. **Images**: Templates containing application code and deps.   │
│ 2. **Containers**: Running instances of images.                  │
│ 3. **Docker Daemon**: Background process that manages containers.│
│ 4. **Docker Client**: CLI to interact with the daemon.           │
╰─────────────────────────────────────────────────────────────────╯
```

(Colours appear as bold headings, cyan for inline commands, green for strings, etc.)

---

## Roadmap

- [ ] Unit tests with pytest
- [ ] CI pipeline (GitHub Actions)
- [ ] Retrieval‑Augmented Generation (RAG) for local docs
- [ ] Streaming responses for inline mode
- [ ] Dockerised deployment

---

## License

MIT
