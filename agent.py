#!/usr/bin/env python3
"""
tell - AI coding & system agent
Security: API key via env var, path validation, dangerous command blocking
"""
import requests, json, os, sys, subprocess, shutil, time, threading, itertools, textwrap, re, random

INVOKE_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
API_KEY = os.environ.get("NVIDIA_API_KEY")
if not API_KEY:
    print("Error: NVIDIA_API_KEY environment variable not set.")
    print("Get a key at: https://build.nvidia.com/explore")
    sys.exit(1)
_env_models = os.environ.get("NVIDIA_MODEL", "").strip()
MODELS = (
    [m.strip() for m in _env_models.split(",") if m.strip()]
    if _env_models
    else [
        "stepfun-ai/step-3.7-flash",
        "minimaxai/minimax-m2.7",
        "deepseek-v4-flash",
        "z-ai/glm4.7",
        "meta/llama-3.1-8b-instruct",
        "microsoft/phi-3-mini-4k-instruct",
    ]
)
_last_model = 0

ALLOWED_WRITE_DIRS = [os.getcwd(), os.path.expanduser("~"), "/tmp"]
MAX_FILE_SIZE = 1024 * 1024
DANGEROUS_CMDS = [
    "rm -rf /", "rm -rf /*", "mkfs", "dd if=", ":(){", "> /dev/sda",
    "> /dev/sdb", "format /dev", "mkfs.", "mkswap", "shutdown",
    "reboot", "poweroff", "halt", "init 0", "init 6", "chmod 777 /",
    "chmod 777 /*", "chown ", "passwd", "useradd", "userdel",
    "usermod", "groupadd", "groupdel",
]

SYS_PROMPT = """You are a system-level AI assistant with full shell and file access.

FORMATTING RULES (strict):
- NEVER use **, *, _, or any markdown formatting
- Use plain text only: labels, dashes, numbers, newlines for structure
- Use backticks `like this` for inline code
- Use ``` for multi-line code blocks (NOT around WRITE:/EXECUTE:)
- NEVER use heredoc (cat > file << EOF) - use WRITE: instead

ACTION DIRECTIVES:
WRITE: relative/path/to/file
<file content here>

EXECUTE: shell command (one line only, no heredocs)

Chain multiple WRITE: and EXECUTE: in any order.
Use WRITE: to create files. Use EXECUTE: only to run commands (not for file creation).

RESPONSE STRUCTURE:
Organize every answer with:

1. Overview - 1-2 sentences explaining what you'll do
2. Steps - Bulleted list of actions
3. Commands - Use EXECUTE: for each
4. Files - Use WRITE: for each
5. Summary - What was done, key results, next steps

TONE:
- Friendly and professional
- Explain why you're doing something
- Use natural conversational flow
- End with a relevant follow-up question or suggestion

CODING:
- Complete, working code. NO placeholders, TODOs, or ...rest
- Multi-file projects: create ALL files (config, source, README, tests)
- Use best practices, error handling, type hints
- After creating files, suggest how to run/test them

SYSTEM TASKS:
- Updates: check package manager, show upgradable count, run update
- Security: check open ports, services, SUID, firewall, failed logins, disk, memory — prioritize risks
- Info: show data clearly with labels, highlight important values
- Install: verify not installed, install, verify
- NEVER run destructive commands: rm -rf /, mkfs, dd, shutdown, etc.

OUTPUT QUALITY:
- Every response must be complete — no partial answers
- Verify by running commands, don't guess
- If something fails, show the error and suggest a fix

EXAMPLES:

User: "check disk space"
Response: I'll check your disk usage right now.
EXECUTE: df -h
Then I'll summarize the findings.

User: "create a flask todo app"
Response:
I'll create a complete Flask todo app with SQLite.

Project structure:
WRITE: app.py
...
WRITE: requirements.txt
...
WRITE: templates/index.html
...
EXECUTE: pip install -r requirements.txt

To run it: python app.py"""

BORDER_STYLES = {
    "rounded": ("╭", "─", "╮", "│", "╰", "╯"),
    "classic": ("╔", "═", "╗", "║", "╚", "╝"),
    "sharp":   ("┌", "─", "┐", "│", "└", "┘"),
    "thick":   ("┏", "━", "┓", "┃", "┗", "┛"),
}
_border_style = os.environ.get("TELL_BORDER", "rounded")
if _border_style not in BORDER_STYLES:
    _border_style = "rounded"

def term_width():
    return min(shutil.get_terminal_size().columns, 240)

def box(text, color=93):
    cols = term_width()
    inner = cols - 4
    tl, h, tr, v, bl, br = BORDER_STYLES[_border_style]
    lines = []
    for raw in text.split('\n'):
        for wrapped in textwrap.wrap(raw, inner) or ['']:
            lines.append(f"\033[{color}m{v} {wrapped:<{inner}}{v}\033[0m")
    top = f"\033[1;{color}m{tl}{h*(cols-2)}{tr}\033[0m"
    bot = f"\033[1;{color}m{bl}{h*(cols-2)}{br}\033[0m"
    return top + '\n' + '\n'.join(lines) + '\n' + bot

def typewrite(text, color=96, delay=0.0003):
    cols = term_width()
    inner = cols - 4
    tl, h, tr, v, bl, br = BORDER_STYLES[_border_style]
    lines_out = []
    for raw in text.split('\n'):
        for wrapped in textwrap.wrap(raw, inner) or ['']:
            lines_out.append(wrapped)
    print(f"\033[1;{color}m{tl}{h*(cols-2)}{tr}\033[0m")
    for wrapped in lines_out:
        sys.stdout.write(f"\033[{color}m{v}\033[0m ")
        for ch in wrapped:
            sys.stdout.write(ch)
            sys.stdout.flush()
            time.sleep(delay)
        sys.stdout.write(f"{' ' * (inner - len(wrapped))}\033[{color}m{v}\033[0m\n")
        sys.stdout.flush()
    print(f"\033[1;{color}m{bl}{h*(cols-2)}{br}\033[0m")

def is_safe_path(path):
    abs_path = os.path.abspath(os.path.expanduser(path))
    for allowed in ALLOWED_WRITE_DIRS:
        if abs_path.startswith(os.path.abspath(allowed)):
            return True
    return False

def is_dangerous(cmd):
    cmd_lower = cmd.lower()
    for d in DANGEROUS_CMDS:
        if d in cmd_lower:
            return True
    return False

def execute(cmd, timeout=120):
    if is_dangerous(cmd):
        return "BLOCKED: dangerous command rejected"
    try:
        r = subprocess.run(
            ["sh", "-c", cmd],
            capture_output=True, text=True, timeout=timeout
        )
        out = r.stdout
        if r.stderr: out += "\n" + r.stderr
        return out.strip()[:5000] or "OK"
    except subprocess.TimeoutExpired:
        return "Command timed out"
    except Exception as e:
        return f"Error: {e}"

def write_file(path, content):
    if not is_safe_path(path):
        return f"BLOCKED: cannot write outside allowed directories: {', '.join(ALLOWED_WRITE_DIRS)}"
    if len(content) > MAX_FILE_SIZE:
        return f"BLOCKED: file too large (max {MAX_FILE_SIZE//1024}KB)"
    abs_path = os.path.abspath(os.path.expanduser(path))
    try:
        os.makedirs(os.path.dirname(abs_path) or '.', exist_ok=True)
        with open(abs_path, 'w') as f:
            f.write(content)
        return f"Created: {os.path.relpath(abs_path, os.getcwd())} ({len(content)} bytes)"
    except Exception as e:
        return f"Error: {e}"

def _clean(text):
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    return text

def extract_content(data):
    msg = data.get("choices", [{}])[0].get("message", {})
    c = msg.get("content")
    if c: return _clean(c)
    r = msg.get("reasoning") or msg.get("reasoning_content")
    return _clean(r or str(data)[:200])

class Spinner:
    def __init__(self):
        self._running = False
        self._thread = None

    def _spin(self):
        chars = '⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
        i = 0
        try:
            while self._running:
                sys.stdout.write(f'\033[96m{chars[i]}\033[0m')
                sys.stdout.flush()
                time.sleep(0.1)
                sys.stdout.write('\b \b')
                sys.stdout.flush()
                i = (i + 1) % len(chars)
        except Exception:
            pass

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1)

_session = requests.Session()

def _guess_tokens(messages):
    total = sum(len(m.get("content", "")) for m in messages if m.get("role") == "user")
    if total < 100: return 256
    if total < 300: return 1024
    return 4096

def ask(messages, max_tokens=None, max_retries=2):
    """Non-streaming fallback (for conversation history in interactive mode)."""
    global _last_model
    if max_tokens is None:
        max_tokens = _guess_tokens(messages)
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    model_idx = _last_model
    for mi in range(len(MODELS)):
        idx = (model_idx + mi) % len(MODELS)
        model = MODELS[idx]
        payload = {
            "model": model, "messages": messages,
            "max_tokens": max_tokens, "temperature": 0.5,
            "top_p": 0.95, "stream": False
        }
        for attempt in range(max_retries):
            try:
                r = _session.post(INVOKE_URL, headers=headers, json=payload, timeout=15)
                if r.status_code == 429:
                    time.sleep(0.5)
                    continue
                if r.status_code != 200:
                    break
                _last_model = idx
                return _clean(extract_content(r.json()))
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                time.sleep(0.3)
                continue
            except Exception as e:
                return f"API Error: {e}"
    return "All models failed"


def ask_stream(messages, max_tokens=None, max_retries=2):
    """Streaming generator — yields content tokens as they arrive from the API."""
    global _last_model
    if max_tokens is None:
        max_tokens = _guess_tokens(messages)
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "text/event-stream",
        "Content-Type": "application/json"
    }
    model_idx = _last_model
    for mi in range(len(MODELS)):
        idx = (model_idx + mi) % len(MODELS)
        model = MODELS[idx]
        payload = {
            "model": model, "messages": messages,
            "max_tokens": max_tokens, "temperature": 0.5,
            "top_p": 0.95, "stream": True
        }
        for attempt in range(max_retries):
            try:
                r = _session.post(INVOKE_URL, headers=headers, json=payload, timeout=15, stream=True)
                if r.status_code == 429:
                    time.sleep(0.5)
                    continue
                if r.status_code != 200:
                    yield f"API Error {r.status_code}: {r.text[:100]}"
                    return
                _last_model = idx
                for line in r.iter_lines(decode_unicode=True):
                    if not line:
                        continue
                    if line.startswith('data: '):
                        data = line[6:]
                        if data == '[DONE]':
                            return
                        try:
                            chunk = json.loads(data)
                            choices = chunk.get('choices')
                            if choices and len(choices) > 0:
                                delta = choices[0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    yield _clean(content)
                        except json.JSONDecodeError:
                            pass
                return
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                time.sleep(0.3)
                continue
            except Exception as e:
                yield f"Error: {e}"
                return
    yield "All models failed"


def stream_response(messages, color=93):
    """Streams tokens into a live-bordered box. Returns the full collected text."""
    cols = term_width()
    inner = cols - 4
    tl, h, tr, v, bl, br = BORDER_STYLES[_border_style]
    full_text = ""
    current_line = ""
    started = False

    for chunk in ask_stream(messages):
        if not started:
            print(f"\033[1;{color}m{tl}{h*(cols-2)}{tr}\033[0m")
            sys.stdout.write(f"\033[{color}m{v} ")
            sys.stdout.flush()
            started = True
        full_text += chunk
        for ch in chunk:
            if ch == '\n':
                sys.stdout.write(' ' * (inner - len(current_line)))
                sys.stdout.write(f"{v}\033[0m\n")
                sys.stdout.write(f"\033[{color}m{v} ")
                current_line = ""
            elif len(current_line) >= inner:
                sys.stdout.write(f"{v}\033[0m\n")
                sys.stdout.write(f"\033[{color}m{v} ")
                sys.stdout.write(ch)
                current_line = ch
            else:
                sys.stdout.write(ch)
                current_line += ch
            sys.stdout.flush()

    if started:
        sys.stdout.write(' ' * (inner - len(current_line)))
        sys.stdout.write(f"{v}\033[0m\n")
        print(f"\033[1;{color}m{bl}{h*(cols-2)}{br}\033[0m")

    cleaned = _clean(full_text)
    if not cleaned:
        cleaned = _clean(ask(messages) or "No response")
        if cleaned:
            print()
            print(box(cleaned, color))
            print()

    return cleaned

def _strip_fences(l):
    return l.lstrip('`').lstrip()

def run_commands(text):
    results = []
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        raw = lines[i]
        l = _strip_fences(raw).strip()
        if l.startswith("EXECUTE:"):
            cmd = l[8:].strip()
            for fence in ('```', '`', '~~~', '~'):
                cmd = cmd.rstrip(fence)
            if '<<' in cmd:
                term = cmd.split('<<')[1].strip().split()[-1]
                heredoc_lines = []
                i += 1
                while i < len(lines):
                    raw = lines[i]
                    stripped = _strip_fences(raw).strip()
                    if stripped.startswith("EXECUTE:") or stripped.startswith("WRITE:"):
                        break
                    if stripped == term:
                        i += 1
                        break
                    heredoc_lines.append(raw)
                    i += 1
                if heredoc_lines:
                    cmd += '\n' + '\n'.join(heredoc_lines)
                i -= 1
            results.append(f"  $ {cmd}\n{execute(cmd)}")
        elif l.startswith("WRITE:"):
            path = l[6:].strip()
            for fence in ('```', '`', '~~~', '~'):
                path = path.rstrip(fence)
            content_lines = []
            i += 1
            opened = False
            while i < len(lines):
                rc = lines[i].strip()
                if rc in ('```', '~~~', '`', '```python', '```bash', '```sh', '```py', '```bash'):
                    if not opened:
                        opened = True
                        i += 1
                        continue
                    else:
                        i += 1
                        break
                stripped = _strip_fences(lines[i]).strip()
                if stripped.startswith("EXECUTE:") or stripped.startswith("WRITE:"):
                    break
                content_lines.append(lines[i])
                i += 1
            if content_lines:
                content = '\n'.join(content_lines)
                content = _strip_code_fences(content)
                result = write_file(path, content)
                results.append(f"  {result}")
            i -= 1
        i += 1
    return '\n'.join(results)


def _strip_code_fences(text):
    lines = text.split('\n')
    return '\n'.join(l for l in lines if not l.strip().startswith('```'))

def _security_scan():
    r = []
    r.append("=== Open Ports ===")
    r.append(execute("ss -tlnp 2>/dev/null"))
    r.append("=== Running Services ===")
    r.append(execute("systemctl list-units --type=service --state=running 2>/dev/null | head -15"))
    r.append("=== SUID Files ===")
    r.append(execute("find /usr/bin /usr/sbin -perm -4000 -type f 2>/dev/null"))
    r.append("=== Firewall ===")
    r.append(execute("ufw status 2>/dev/null || firewall-cmd --list-all 2>/dev/null || echo 'no firewall frontend'; iptables -L -n 2>/dev/null | head -10; echo '--- done ---'"))
    r.append("=== Failed Logins ===")
    r.append(execute("lastb 2>/dev/null | head -5 || echo 'none'"))
    r.append("=== Disk ===")
    r.append(execute("df -h /"))
    r.append("=== Memory ===")
    r.append(execute("free -h"))
    return '\n'.join(r)

LOCAL = {
    "disk": lambda: f"Disk Used: {shutil.disk_usage('/').used//(1024**3)}GB / {shutil.disk_usage('/').total//(1024**3)}GB ({shutil.disk_usage('/').used/shutil.disk_usage('/').total*100:.1f}%)",
    "memory": lambda: (m := __import__('psutil').virtual_memory()) and f"RAM: {m.used//(1024**2)}MB / {m.total//(1024**2)}MB ({m.percent}%)",
    "procs": lambda: execute("ps aux --sort=-%cpu | head -10"),
    "ps": lambda: execute("ps aux --sort=-%cpu | head -10"),
    "uptime": lambda: execute("uptime"),
    "whoami": lambda: execute("whoami"),
    "date": lambda: execute("date"),
    "pwd": lambda: execute("pwd"),
    "ip": lambda: execute("ip addr | grep inet"),
    "network": lambda: execute("ip addr"),
    "netstat": lambda: execute("ss -tlnp"),
    "ports": lambda: execute("ss -tlnp"),
    "sysinfo": lambda: execute("uname -a"),
    "services": lambda: execute("systemctl list-units --type=service --state=running 2>/dev/null | head -20"),
    "fw": lambda: execute("(ufw status verbose 2>/dev/null || firewall-cmd --list-all 2>/dev/null); iptables -L -n 2>/dev/null | head -20; echo '---'"),
    "firewall": lambda: execute("(ufw status verbose 2>/dev/null || firewall-cmd --list-all 2>/dev/null); iptables -L -n 2>/dev/null | head -20; echo '---'"),
    "updates": lambda: execute("apt list --upgradable 2>/dev/null | head -20 || dnf check-update 2>/dev/null | head -20 || yum list updates 2>/dev/null | head -20 || echo 'no package manager found'"),
    "upgradable": lambda: execute("apt list --upgradable 2>/dev/null | head -20 || dnf check-update 2>/dev/null | head -20 || yum list updates 2>/dev/null | head -20 || echo 'no package manager found'"),
    "users": lambda: execute("who -u"),
    "logins": lambda: execute("last -10 2>/dev/null"),
    "scan": lambda: execute("echo '--- PORTS ---' && ss -tlnp 2>/dev/null && echo '--- TOP PROCS ---' && ps aux --sort=-%cpu | head -10 && echo '--- DISK ---' && df -h && echo '--- MEM ---' && free -h"),
    "suid": lambda: execute("find /usr/bin /usr/sbin -perm -4000 -type f 2>/dev/null"),
    "security": _security_scan,
}

PHRASES = [
    ("disk usage","disk"), ("disk space","disk"), ("free space","disk"),
    ("memory usage","memory"), ("free memory","memory"),
    ("running processes","procs"), ("top processes","procs"),
    ("system info","sysinfo"),
    ("open ports","ports"), ("listening ports","ports"),
    ("running services","services"), ("active services","services"),
    ("firewall status","fw"), ("firewall rules","fw"),
    ("available updates","updates"), ("pending updates","updates"),
    ("logged in users","users"), ("who is logged in","users"),
    ("security scan","security"), ("security check","security"),
    ("suid files","suid"), ("setuid files","suid"),
    ("quick scan","scan"), ("system scan","scan"),
]

def detect_local(q):
    q = q.lower().strip().strip("?.")
    if q in LOCAL:
        return LOCAL[q]
    if q in ("exit", "quit", "clear", "reset", ""):
        return None
    words = set(q.split())
    for kw in LOCAL:
        if kw in words and len(words) <= 3:
            return LOCAL[kw]
    if len(words) <= 4:
        for phrase, key in PHRASES:
            if phrase in q:
                return LOCAL[key]
    return None

def inline_mode(query):
    local = detect_local(query)
    if local:
        result = local()
        print(f"\n{box(result, 92)}\n")
        return

    print()
    resp = stream_response([
        {"role": "system", "content": SYS_PROMPT},
        {"role": "user", "content": query}
    ])
    print()

    if "EXECUTE:" in resp or "WRITE:" in resp:
        r = run_commands(resp)
        if r:
            print(box(r, 93))
            print()

def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--inline":
        inline_mode(' '.join(sys.argv[2:]))
        return

    print(box("tell - AI Coding Agent"))
    print()

    msgs = [{"role": "system", "content": SYS_PROMPT}]

    while True:
        try:
            u = input("\033[94m❯\033[0m ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!"); break

        if not u: continue
        if u.lower() in ("quit","exit"): break
        if u.lower() == "clear": print("\033[2J\033[H", end=""); continue
        if u.lower() in ("help","commands"):
            cmds = "\n".join(f"  {k}" for k in sorted(LOCAL))
            print(f"\n{box(f'Local commands:\\n{cmds}', 92)}")
            print(f"\n{box('Also: run <cmd>, read <file>, border, reset, clear', 92)}\n")
            continue
        if u.lower() == "border":
            global _border_style
            keys = list(BORDER_STYLES)
            idx = (keys.index(_border_style) + 1) % len(keys)
            _border_style = keys[idx]
            print(f"\n{box(f'Border style: {_border_style}', 93)}\n")
            continue
        if u.lower() == "reset":
            msgs = [{"role":"system","content":SYS_PROMPT}]
            print(box("Conversation reset", 92)); print(); continue

        local = detect_local(u)
        if local:
            print(f"\n{box(local(), 92)}\n")
            continue

        if u.startswith("run "):
            print(f"\n{box(execute(u[4:]), 92)}\n")
            continue

        if u.startswith("read "):
            path = u[5:].strip()
            if not is_safe_path(path):
                print(f"\n{box('BLOCKED: cannot read outside allowed directories', 91)}\n")
                continue
            try:
                with open(os.path.abspath(os.path.expanduser(path))) as f:
                    print(f"\n{box(f.read(), 92)}\n")
            except Exception as e:
                print(box(f"Error: {e}", 91))
            continue

        msgs.append({"role": "user", "content": u})

        print()
        resp = stream_response(msgs)
        print()

        if "EXECUTE:" in resp or "WRITE:" in resp:
            r = run_commands(resp)
            if r:
                print(box(r, 93))
                print()
        msgs.append({"role": "assistant", "content": resp})

        if len(msgs) > 40:
            msgs = [msgs[0]] + msgs[-20:]

if __name__ == "__main__":
    main()
