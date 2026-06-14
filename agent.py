#!/usr/bin/env python3
"""
tell - AI coding & system agent
Security: API key via env var, path validation, dangerous command blocking
"""
import requests, json, os, sys, subprocess, shutil, time, threading, itertools, textwrap, re, random, platform

IS_WINDOWS = platform.system() == "Windows"

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
        "meta/llama-3.1-8b-instruct",
        "deepseek-ai/deepseek-v4-pro",
        "mistralai/mistral-small-4-119b-2603",
    ]
)
_last_model = 0

QUERY_MODELS = (
    [m.strip() for m in _env_models.split(",") if m.strip()]
    if _env_models
    else [
        "meta/llama-3.1-8b-instruct",
        "deepseek-ai/deepseek-v4-pro",
        "mistralai/mistral-small-4-119b-2603",
    ]
)

ALLOWED_WRITE_DIRS = [os.getcwd(), os.path.expanduser("~")]
if IS_WINDOWS:
    ALLOWED_WRITE_DIRS.extend([os.environ.get("TEMP", "C:\\Temp"), os.environ.get("TMP", "C:\\Temp")])
else:
    ALLOWED_WRITE_DIRS.append("/tmp")
MAX_FILE_SIZE = 1024 * 1024
DANGEROUS_CMDS = [
    "rm -rf /", "rm -rf /*", "rm -rf ~", "rm -rf .", "mkfs", "dd if=",
    ":(){", "> /dev/sda", "> /dev/sdb", "format /dev", "mkfs.", "mkswap",
    "shutdown", "reboot", "poweroff", "halt", "init 0", "init 6",
    "chmod 777 /", "chmod 777 /*", "chown ", "passwd", "useradd",
    "userdel", "usermod", "groupadd", "groupdel",
    "format c:", "format c:\\", "del /f /s", "rd /s /q",
    "diskpart", "reg delete", "net user", "sc delete",
    "curl ", "wget ", "eval ", "exec ", "sudo ", "su -",
    "chmod 777", "chmod -R 777", "chmod 000", "chown -R",
    "rm -rf", "rm -r /", "rm -f /", "rmdir /",
    "> /dev/null", "mv /*", "mv /etc", "mv /usr",
    "cat /etc/shadow", "cat /etc/passwd",
    "; rm ", "| rm ", "&& rm ", "|| rm ",
    "`rm ", "$(rm ", "${", "python -c", "python3 -c",
    "perl -e", "ruby -e", "node -e", "bash -c",
    "sh -c", "nc ", "ncat ", "netcat ",
    "base64 ", "xxd ", "openssl ",
    "iptables -F", "iptables -X", "iptables -P",
    "systemctl stop", "systemctl disable",
    "killall", "kill -9", "pkill",
    "mkfifo", "mknod",
    "chattr +i", "chattr -i",
    "export PATH=", "unset PATH",
    "source /etc", ". /etc",
    "cd / &&", "cd /; ",
]

# Patterns to catch encoded/bypassed dangerous commands
DANGEROUS_PATTERNS = [
    r'\brm\s+-[a-z]*r[a-z]*f',  # rm -rf with any flags
    r'\brm\s+-[a-z]*f[a-z]*r',  # rm -fr
    r'\bdd\s+if=',              # dd if=
    r'\bmkfs\b',               # mkfs
    r'>\s*/dev/sd',            # > /dev/sda, > /dev/sdb
    r'>\s*/dev/nvme',          # > /dev/nvme
    r'\bshutdown\b',           # shutdown
    r'\breboot\b',             # reboot
    r'\bpoweroff\b',           # poweroff
    r'\binit\s+[06]',         # init 0 or init 6
    r'\bchmod\s+777',         # chmod 777
    r'\bchmod\s+000',         # chmod 000
    r'\bchown\s+-R',          # chown -R
    r'\bcurl\b.*\|\s*bash',   # curl | bash
    r'\bcurl\b.*\|\s*sh',     # curl | sh
    r'\bwget\b.*\|\s*bash',   # wget | bash
    r'\bwget\b.*\|\s*sh',     # wget | sh
    r'\beval\b',              # eval
    r'\bexec\b',              # exec
    r'\bsudo\b',              # sudo
    r'\bsu\s+-',              # su -
    r';\s*rm\s',              # ; rm
    r'\|\s*rm\s',             # | rm
    r'&&\s*rm\s',             # && rm
    r'\|\|\s*rm\s',           # || rm
    r'`rm\s',                 # `rm
    r'\$\(rm\s',              # $(rm
    r'\bsource\s+/etc',       # source /etc
    r'\.\s+/etc',             # . /etc
    r'\bpython\s+-c',         # python -c
    r'\bpython3\s+-c',        # python3 -c
    r'\bperl\s+-e',           # perl -e
    r'\bruby\s+-e',           # ruby -e
    r'\bnc\s+-',              # nc -
    r'\bncat\s',              # ncat
    r'\bnetcat\s',            # netcat
    r'\bbase64\s+-d',         # base64 -d
    r'\bexport\s+PATH',       # export PATH=
    r'\bunset\s+PATH',        # unset PATH
    r'\bkillall\b',           # killall
    r'\bpkill\b',             # pkill
    r'\bchattr\s+[+-]i',     # chattr +/-i
]

SYS_PROMPT = """You are a system-level AI assistant with full shell and file access.

FORMATTING RULES (strict):
- NEVER use **, *, _, or any markdown formatting
- Use plain text only: labels, dashes, numbers, newlines for structure
- Use backticks `like this` for inline code
- NEVER use heredoc (cat > file << EOF) - use WRITE: instead

ACTION DIRECTIVES:
WRITE: relative/path/to/file
<file content here>

EXECUTE: shell command (one line only, no heredocs)

Chain multiple WRITE: and EXECUTE: in any order.
Use WRITE: to create files. Use EXECUTE: only to run commands (not for file creation).

CRITICAL RULES:
- When user asks to CHECK, RUN, SHOW, or GET something, ALWAYS use EXECUTE: with the actual command
- When user asks to CREATE or WRITE something, use WRITE: to create the file
- Never give generic advice when you can run actual commands
- Always run the command first, then analyze the results
- Detect the user's OS (Linux/Mac/Windows) and use appropriate commands
- For "do" tasks: ALWAYS execute real commands, never just describe how to do it

RESPONSE STRUCTURE:
1. Brief intro (1 sentence)
2. Commands to run (use EXECUTE:)
3. Analysis of results
4. Recommendations

EXAMPLE for "do check disk space":
Response:
EXECUTE: df -h
Based on the disk usage above, here are recommendations for freeing space...

CRITICAL: Output only the answer. Never include your internal reasoning process.

TONE:
- Friendly and professional
- Run commands, don't just describe them
- Show actual results, not generic advice
- Give specific, actionable recommendations

SYSTEM TASKS:
- Always execute real commands, never give generic instructions
- Detect OS and use appropriate commands (Linux: df, du, apt | Windows: dir, winget)
- Show actual results from commands
- Analyze results and give specific recommendations
- NEVER run destructive commands: rm -rf /, mkfs, dd, shutdown, etc.

OUTPUT QUALITY:
- Every response must be complete — no partial answers
- Run commands to get real data, don't guess
- If something fails, show the error and suggest a fix"""

QUERY_PROMPT = """You are a world-class AI assistant — respond like the best AI models (Claude, Gemini, GPT-4). Give exceptional, insightful, and expert-level answers.

FORMATTING RULES (STRICT):
- NEVER use markdown: no **, no *, no ##, no ```, no |, no ---
- Use PLAIN TEXT ONLY
- Use simple dashes - for lists
- Use numbers 1. 2. 3. for ordered lists
- Use backticks only for actual code commands
- Keep it clean and readable
- No special characters, no formatting symbols

RESPONSE STYLE:
- Sound like a knowledgeable friend, not a textbook
- Be conversational yet authoritative
- Use natural flow, not robotic structure
- Mix short and long sentences for rhythm
- Use real-world analogies to explain complex ideas
- Be specific with examples, not vague generalizations

CORE RULES:
- Start with a direct, confident answer (1-2 sentences)
- Then expand with depth and context
- Use "Think of it like..." analogies for complex topics
- Include practical "why this matters" explanations
- Be honest about limitations and unknowns
- End with something useful: next steps, a tip, or a question

LANGUAGE:
- Match the language of the user's question EXACTLY
- If user asks in English, respond in English
- If user asks in Hindi, respond in Hindi
- If user asks in Marathi, respond in Marathi
- If user asks in Spanish, respond in Spanish
- If user asks in any other language, respond in that same language
- Never mix languages in same response
- Use natural, fluent, grammatically correct language

RESPONSE STRUCTURE:
1. Opening — Direct answer that immediately satisfies the question
2. Explanation — Deeper dive with clear, logical flow
3. Example — Real-world analogy or practical use case
4. Tips — Actionable advice or common pitfalls to avoid
5. Closing — Suggest what to explore next

EXAMPLE for "What is Python?":

Python is a high-level programming language created by Guido van Rossum in 1991. Think of it as the Swiss Army knife of programming — versatile, beginner-friendly, and used everywhere from web apps to AI research.

Why Python stands out:
- Easy to read and write — the code looks almost like English
- Huge ecosystem — over 400,000 packages on PyPI for every possible task
- Cross-platform — runs on Windows, Mac, and Linux without changes

Where Python shines:
- Web development (Django, Flask power sites like Instagram and Spotify)
- Data science and AI (NumPy, pandas, TensorFlow are industry standards)
- Automation (scripting, scraping, task automation)
- Education (the most popular language for teaching programming)

Common pitfalls:
- Speed — Python is slower than C++ or Java, so avoid it for real-time games
- Mobile apps — not ideal for iOS/Android development
- Indentation matters — spaces vs tabs can cause errors

What to learn next:
- Start with Python.org's official tutorial
- Try building a simple web scraper or calculator
- Explore frameworks like FastAPI for web development

Want me to dive deeper into any specific Python topic?"""

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

def box(text, color=97):
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

def animated_box(text, color=97, delay=0.02):
    """Display text in a box with typewriter animation"""
    cols = term_width()
    inner = cols - 4
    tl, h, tr, v, bl, br = BORDER_STYLES[_border_style]
    lines = []
    for raw in text.split('\n'):
        for wrapped in textwrap.wrap(raw, inner) or ['']:
            lines.append(wrapped)
    print(f"\033[1;{color}m{tl}{h*(cols-2)}{tr}\033[0m")
    for line in lines:
        sys.stdout.write(f"\033[{color}m{v}\033[0m ")
        sys.stdout.write(line)
        sys.stdout.write(f"{' ' * (inner - len(line))}\033[{color}m{v}\033[0m\n")
        sys.stdout.flush()
        time.sleep(delay)
    print(f"\033[1;{color}m{bl}{h*(cols-2)}{br}\033[0m")

def is_safe_path(path):
    try:
        abs_path = os.path.abspath(os.path.expanduser(path))
        # Resolve symlinks to prevent symlink attacks
        real_path = os.path.realpath(abs_path)
        for allowed in ALLOWED_WRITE_DIRS:
            allowed_real = os.path.realpath(os.path.abspath(allowed))
            if real_path.startswith(allowed_real + os.sep) or real_path == allowed_real:
                return True
        return False
    except (OSError, ValueError):
        return False

def is_dangerous(cmd):
    cmd_lower = cmd.lower().strip()
    # Remove whitespace variations to prevent bypass
    cmd_normalized = re.sub(r'\s+', ' ', cmd_lower)
    # Check substring matches
    for d in DANGEROUS_CMDS:
        if d in cmd_normalized:
            return True
    # Check regex patterns
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, cmd_normalized):
            return True
    return False

def execute(cmd, timeout=120):
    if is_dangerous(cmd):
        return "BLOCKED: dangerous command rejected"
    try:
        shell = ["cmd", "/c", cmd] if IS_WINDOWS else ["sh", "-c", cmd]
        # Sanitize environment - remove dangerous vars that could enable injection
        safe_env = {k: v for k, v in os.environ.items()
                    if k not in ("LD_PRELOAD", "LD_LIBRARY_PATH", "DYLD_INSERT_LIBRARIES",
                                 "DYLD_LIBRARY_PATH", "PYTHONPATH", "BASH_ENV", "ENV")}
        r = subprocess.run(
            shell,
            capture_output=True, text=True, timeout=timeout,
            env={**safe_env, "PATH": os.environ.get("PATH", "/usr/bin:/bin")}
        )
        out = r.stdout
        if r.stderr: out += "\n" + r.stderr
        result = out.strip()[:20000] or "OK"
        if r.returncode != 0:
            result += f"\n[Exit code: {r.returncode}]"
        return result
    except subprocess.TimeoutExpired:
        return "Command timed out [Exit code: -1]"
    except Exception as e:
        err_str = str(e)
        # Sanitize error messages
        if "No such file" in err_str:
            return "Command not found [Exit code: -2]"
        return f"Error: {err_str} [Exit code: -2]"

def write_file(path, content):
    if not is_safe_path(path):
        return f"BLOCKED: cannot write outside allowed directories: {', '.join(ALLOWED_WRITE_DIRS)}"
    if len(content) > MAX_FILE_SIZE:
        return f"BLOCKED: file too large (max {MAX_FILE_SIZE//1024}KB)"
    abs_path = os.path.abspath(os.path.expanduser(path))
    try:
        os.makedirs(os.path.dirname(abs_path) or '.', exist_ok=True)
        # Write with restrictive permissions (owner read/write only)
        fd = os.open(abs_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, 'w') as f:
            f.write(content)
        return f"Created: {os.path.relpath(abs_path, os.getcwd())} ({len(content)} bytes)"
    except Exception as e:
        return f"Error: {e}"

def _clean(text):
    if not text:
        return text
    # Remove markdown bold **text**
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    # Remove markdown italic *text*
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    # Remove markdown headers ## Header
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    # Remove inline code `code`
    text = re.sub(r'`([^`]+)`', r'\1', text)
    # Remove code blocks ```code```
    text = re.sub(r'```[\s\S]*?```', '', text)
    # Remove horizontal rules ---
    text = re.sub(r'^-{3,}$', '', text, flags=re.MULTILINE)
    # Remove markdown links [text](url)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # Remove blockquotes > text
    text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)
    # Remove table pipes |text|
    text = re.sub(r'\|', ' ', text)
    # Clean up multiple spaces
    text = re.sub(r'  +', ' ', text)
    # Clean up multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def _strip_reasoning(text):
    lower = text.lower()
    if not any(p in lower for p in ('wait,', 'let me', 'oh right', "that's", "first let's", "first step should", 'make sure')):
        return text
    lines = text.split('\n')
    split_markers = ('wait', 'let me', 'oh right', 'okay, let', 'now let')
    segments = []
    current = []
    for line in lines:
        lower = line.strip().lower()
        is_marker = any(lower.startswith(m) for m in split_markers)
        if is_marker and current:
            segments.append(current)
            current = [line]
        else:
            current.append(line)
    if current:
        segments.append(current)
    best = segments[-1] if segments else lines
    skip_start = ('got ', 'let ', 'first,', 'first step', 'second step', 'third step',
                  'wait,', 'okay,', "i'll", "let's", 'hmm,', 'oh ', 'make sure',
                  'then,', 'first,', 'now let', 'also,')
    result = []
    started = False
    for line in best:
        lower = line.strip().lower()
        if not started:
            if not line.strip():
                continue
            if any(lower.startswith(s) for s in skip_start):
                continue
            started = True
        if lower.startswith(('wait,', 'let me', 'oh right', "that's", 'make sure', 'also, from an')):
            break
        result.append(line)
    return '\n'.join(result).strip()

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
    combined = " ".join(m.get("content", "") for m in messages if m.get("role") == "user")
    code_kw = ["create", "build", "write", "make", "app", "code", "file",
               "implement", "generate", "script", "program", "project"]
    is_code = any(kw in combined.lower() for kw in code_kw)
    if is_code:
        if total < 100: return 4096
        if total < 500: return 8192
        return 16384
    if total < 100: return 512
    if total < 500: return 1024
    return 2048

def ask(messages, max_tokens=None, max_retries=1, models=None, temperature=0.5):
    """Non-streaming fallback (for conversation history in interactive mode)."""
    global _last_model
    if max_tokens is None:
        max_tokens = _guess_tokens(messages)
    model_list = models or MODELS
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    model_idx = _last_model
    for mi in range(len(model_list)):
        idx = (model_idx + mi) % len(model_list)
        model = model_list[idx]
        payload = {
            "model": model, "messages": messages,
            "max_tokens": max_tokens, "temperature": temperature,
        }
        for attempt in range(max_retries):
            try:
                r = _session.post(INVOKE_URL, headers=headers, json=payload, timeout=(15, 45))
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
                # Sanitize error to prevent API key leak
                err_str = str(e)
                if API_KEY and API_KEY in err_str:
                    err_str = err_str.replace(API_KEY, "[REDACTED]")
                return f"API Error: {err_str}"
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
                r = _session.post(INVOKE_URL, headers=headers, json=payload, timeout=(15, 45), stream=True)
                if r.status_code == 429:
                    time.sleep(0.5)
                    continue
                if r.status_code != 200:
                    yield f"API Error {r.status_code}: {r.text[:100]}"
                    return
                _last_model = idx
                for line in r.iter_lines(decode_unicode=True):
                    if line is None:
                        continue
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
                # Sanitize error to prevent API key leak
                err_str = str(e)
                if API_KEY and API_KEY in err_str:
                    err_str = err_str.replace(API_KEY, "[REDACTED]")
                yield f"Error: {err_str}"
                return
    yield "All models failed"


def stream_response(messages, color=97):
    """Streams tokens into a live-bordered box. Returns the full collected text."""
    cols = term_width()
    inner = cols - 4
    tl, h, tr, v, bl, br = BORDER_STYLES[_border_style]
    full_text = ""
    current_line = ""
    started = False
    deadline = time.time() + 120
    buf = []

    for chunk in ask_stream(messages):
        if time.time() > deadline:
            break
        if not started:
            print(f"\033[1;{color}m{tl}{h*(cols-2)}{tr}\033[0m")
            sys.stdout.write(f"\033[{color}m{v} ")
            sys.stdout.flush()
            started = True
        full_text += chunk
        for ch in chunk:
            if ch == '\n':
                buf.append(' ' * (inner - len(current_line)))
                buf.append(f"{v}\033[0m\n")
                buf.append(f"\033[{color}m{v} ")
                current_line = ""
            elif len(current_line) >= inner:
                buf.append(f"{v}\033[0m\n")
                buf.append(f"\033[{color}m{v} ")
                buf.append(ch)
                current_line = ch
            else:
                buf.append(ch)
                current_line += ch
        sys.stdout.write(''.join(buf))
        sys.stdout.flush()
        buf.clear()

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
    created_files = []
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        raw = lines[i]
        l = _strip_fences(raw).strip()
        if l.startswith("EXECUTE:"):
            cmd = l[8:].strip()
            for fence in ('```', '`', '~~~', '~'):
                cmd = cmd.rstrip(fence)
            # Sanitize command - remove dangerous patterns
            if '<<' in cmd:
                # Block heredoc to prevent injection
                results.append("  BLOCKED: heredoc not allowed for security")
                i += 1
                continue
            if is_dangerous(cmd):
                results.append(f"  BLOCKED: {cmd[:50]}... is dangerous")
            else:
                results.append(f"  $ {cmd}\n{execute(cmd)}")
        elif l.startswith("WRITE:"):
            path = l[6:].strip()
            for fence in ('```', '`', '~~~', '~'):
                path = path.rstrip(fence)
            # Validate path before processing
            if not is_safe_path(path):
                results.append(f"  BLOCKED: cannot write to {path}")
                i += 1
                continue
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
                abs_path = os.path.abspath(os.path.expanduser(path))
                if os.path.exists(abs_path):
                    created_files.append(abs_path)
            i -= 1
        i += 1
    deps_result = _auto_install_deps(created_files)
    if deps_result:
        results.append(deps_result)
    for f in created_files:
        v = _validate_syntax(f)
        if v:
            results.append(v)
    return '\n'.join(results), created_files


def _strip_code_fences(text):
    lines = text.split('\n')
    return '\n'.join(l for l in lines if not l.strip().startswith('```'))

_DEPENDENCY_FILES = {
    "requirements.txt": "pip install -r requirements.txt",
    "package.json": "npm install",
    "Cargo.toml": "cargo build",
    "go.mod": "go mod download",
    "Gemfile": "bundle install",
    "composer.json": "composer install",
    "setup.py": "pip install -e .",
    "Pipfile": "pipenv install",
    "yarn.lock": "yarn install",
    "pnpm-lock.yaml": "pnpm install",
    "Cargo.lock": "cargo build",
}

def _auto_install_deps(created_files):
    detected = set()
    for f in created_files:
        basename = os.path.basename(f)
        if basename in _DEPENDENCY_FILES and basename not in detected:
            detected.add(basename)
    if not detected:
        return ""
    cmds = [_DEPENDENCY_FILES[d] for d in detected]
    parts = []
    for cmd in cmds:
        out = execute(cmd, timeout=120)
        parts.append(f"  $ {cmd}\n{out}")
    return "Dependencies:\n" + "\n".join(parts)

_SYNTAX_CHECKERS = {
    ".py": "python3 -m py_compile {path}",
    ".js": "node --check {path}",
    ".ts": "npx tsc --noEmit --lib es6 --strict {path}",
    ".json": "python3 -c \"import json; json.load(open({path}))\"",
    ".yaml": "python3 -c \"import yaml; yaml.safe_load(open({path}))\"",
    ".yml": "python3 -c \"import yaml; yaml.safe_load(open({path}))\"",
    ".sh": "bash -n {path}",
}

def _validate_syntax(path):
    ext = os.path.splitext(path)[1]
    if ext not in _SYNTAX_CHECKERS:
        return ""
    # Validate path is safe before using in command
    if not is_safe_path(path):
        return "  Syntax check blocked: path outside allowed directories"
    # Quote path to prevent injection - use shlex for proper escaping
    import shlex
    safe_path = shlex.quote(path)
    cmd = _SYNTAX_CHECKERS[ext].format(path=safe_path)
    out = execute(cmd, timeout=30)
    if out.strip() in ("", "OK"):
        return ""
    if "error" in out.lower() or "traceback" in out.lower():
        return f"  Syntax check ({os.path.basename(path)}):\n{out}"
    return ""

_DISK_ROOT = '/' if not IS_WINDOWS else os.getenv('SystemDrive', 'C:') + '\\'

def _cmd_disk():
    u = shutil.disk_usage(_DISK_ROOT)
    return f"Disk Used: {u.used//(1024**3)}GB / {u.total//(1024**3)}GB ({u.used/u.total*100:.1f}%)"

def _cmd_memory():
    m = __import__('psutil').virtual_memory()
    return f"RAM: {m.used//(1024**2)}MB / {m.total//(1024**2)}MB ({m.percent}%)"

def _cmd_procs():
    if IS_WINDOWS:
        return execute("tasklist")
    return execute("ps aux --sort=-%cpu | head -10")

def _cmd_uptime():
    if IS_WINDOWS:
        try:
            import psutil, datetime
            b = datetime.datetime.fromtimestamp(psutil.boot_time())
            d = datetime.datetime.now() - b
            return f"Up {d.days}d {d.seconds//3600}h {(d.seconds//60)%60}m"
        except Exception:
            return execute("wmic os get lastbootuptime")
    return execute("uptime")

def _cmd_date():
    if IS_WINDOWS:
        return execute("echo %date% %time%")
    return execute("date")

def _cmd_pwd():
    if IS_WINDOWS:
        return os.getcwd()
    return execute("pwd")

def _cmd_ip():
    if IS_WINDOWS:
        return execute("ipconfig | findstr IPv4")
    return execute("ip addr | grep inet")

def _cmd_network():
    if IS_WINDOWS:
        return execute("ipconfig /all")
    return execute("ip addr")

def _cmd_ports():
    if IS_WINDOWS:
        return execute("netstat -ano")
    return execute("ss -tlnp")

def _cmd_sysinfo():
    if IS_WINDOWS:
        return execute("systeminfo | findstr /B /C:OS")
    return execute("uname -a")

def _cmd_services():
    if IS_WINDOWS:
        return execute("sc query state= all")
    return execute("systemctl list-units --type=service --state=running 2>/dev/null | head -20")

def _cmd_fw():
    if IS_WINDOWS:
        return execute("netsh advfirewall show allprofiles")
    return execute("(ufw status verbose 2>/dev/null || firewall-cmd --list-all 2>/dev/null); iptables -L -n 2>/dev/null | head -20; echo '---'")

def _cmd_updates():
    if IS_WINDOWS:
        return execute("winget upgrade 2>nul || echo 'winget not available'")
    return execute("apt list --upgradable 2>/dev/null | head -20 || dnf check-update 2>/dev/null | head -20 || yum list updates 2>/dev/null | head -20 || echo 'no package manager found'")

def _cmd_users():
    if IS_WINDOWS:
        return execute("query user 2>nul || echo 'query user not available'")
    return execute("who -u")

def _cmd_logins():
    if IS_WINDOWS:
        # Use safe command without user input
        return execute("wevtutil qe Security /rd:true /f:text /c:5 2>nul || echo 'Event log access not available'")
    return execute("last -10 2>/dev/null")

def _cmd_scan():
    if IS_WINDOWS:
        return execute("echo --- PORTS --- && netstat -ano && echo --- PROCS --- && tasklist && echo --- DISK --- && wmic logicaldisk get size,freespace,caption && echo --- MEM --- && wmic os get TotalVisibleMemorySize,FreePhysicalMemory")
    return execute("echo '--- PORTS ---' && ss -tlnp 2>/dev/null && echo '--- TOP PROCS ---' && ps aux --sort=-%cpu | head -10 && echo '--- DISK ---' && df -h && echo '--- MEM ---' && free -h")

def _cmd_suid():
    if IS_WINDOWS:
        return "N/A (not applicable on Windows)"
    return execute("find /usr/bin /usr/sbin -perm -4000 -type f 2>/dev/null")

def _security_scan():
    r = []
    if IS_WINDOWS:
        r.append("=== Open Ports ===")
        r.append(execute("netstat -ano"))
        r.append("=== Running Services ===")
        r.append(execute("sc query state= all | findstr SERVICE_NAME"))
        r.append("=== Firewall ===")
        r.append(execute("netsh advfirewall show allprofiles"))
        r.append("=== Disk ===")
        r.append(execute("wmic logicaldisk get size,freespace,caption"))
        r.append("=== Memory ===")
        r.append(execute("wmic os get TotalVisibleMemorySize,FreePhysicalMemory"))
    else:
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
    "disk": _cmd_disk,
    "memory": _cmd_memory,
    "procs": _cmd_procs,
    "ps": _cmd_procs,
    "uptime": _cmd_uptime,
    "whoami": lambda: execute("whoami"),
    "date": _cmd_date,
    "pwd": _cmd_pwd,
    "ip": _cmd_ip,
    "network": _cmd_network,
    "netstat": _cmd_ports,
    "ports": _cmd_ports,
    "sysinfo": _cmd_sysinfo,
    "services": _cmd_services,
    "fw": _cmd_fw,
    "firewall": _cmd_fw,
    "updates": _cmd_updates,
    "upgradable": _cmd_updates,
    "users": _cmd_users,
    "logins": _cmd_logins,
    "scan": _cmd_scan,
    "suid": _cmd_suid,
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
    # Check for direct keyword matches (even in long queries)
    for kw in LOCAL:
        if kw in words:
            return LOCAL[kw]
    # Check for phrase matches (even in long queries)
    for phrase, key in PHRASES:
        if phrase in q:
            return LOCAL[key]
    return None

def handle_do(query):
    """Universal dispatcher: local commands → shell execution → AI fallback."""
    q = query.strip()
    local = detect_local(q)
    if local:
        return ("local", local())
    result = execute(q)
    if "BLOCKED" not in result and "[Exit code:" not in result:
        return ("shell", result)
    return ("ai", q)

def inline_mode(query):
    # Input length validation
    if len(query) > 10000:
        print(box("Input too long (max 10000 characters)", 91))
        return
    if query.lower().startswith("do "):
        action, value = handle_do(query[3:])
        if action != "ai":
            print(f"\n{box(value, 92)}\n")
            return
        query = value
        print()
        resp = stream_response([
            {"role": "system", "content": SYS_PROMPT},
            {"role": "user", "content": query}
        ])
        print()
        if "EXECUTE:" in resp or "WRITE:" in resp:
            r, created = run_commands(resp)
            if r:
                print(box(r, 97))
                print()
    else:
        resp = ask([
            {"role": "system", "content": QUERY_PROMPT},
            {"role": "user", "content": query}
        ], max_tokens=16384, models=QUERY_MODELS, temperature=0.6)
        resp = _strip_reasoning(resp)
        if resp:
            print()
            animated_box(resp, 97, delay=0.0003)
            print()
        else:
            print(box("No response generated", 91))

def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--inline":
        inline_mode(' '.join(sys.argv[2:]))
        return

    print(box("tell - AI Coding Agent"))
    print()

    msgs = [{"role": "system", "content": QUERY_PROMPT}]

    while True:
        try:
            u = input("\033[94m❯\033[0m ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!"); break

        if not u: continue
        # Input length validation to prevent DoS
        if len(u) > 10000:
            print(box("Input too long (max 10000 characters)", 91))
            continue
        if u.lower() in ("quit","exit"): break
        if u.lower() == "clear": print("\033[2J\033[H", end=""); continue
        if u.lower() in ("help","commands"):
            cmds = "\n".join(f"  {k}" for k in sorted(LOCAL))
            print(f"\n{box(f'Built-in commands:\\n{cmds}', 92)}")
            print(f"\n{box('do <task> - coding/system tasks  |  border  |  reset  |  clear  |  help', 92)}\n")
            continue
        if u.lower() == "border":
            global _border_style
            keys = list(BORDER_STYLES)
            idx = (keys.index(_border_style) + 1) % len(keys)
            _border_style = keys[idx]
            print(f"\n{box(f'Border style: {_border_style}', 97)}\n")
            continue
        if u.lower() == "reset":
            msgs = [{"role":"system","content":QUERY_PROMPT}]
            print(box("Conversation reset", 92)); print(); continue

        if u.lower().startswith("do "):
            msgs[0] = {"role": "system", "content": SYS_PROMPT}
            action, value = handle_do(u[3:])
            if action != "ai":
                print(f"\n{box(value, 92)}\n")
                continue
            u = value
            msgs.append({"role": "user", "content": u})
            print()
            resp = stream_response(msgs)
            print()
            cmd_results = ""
            if "EXECUTE:" in resp or "WRITE:" in resp:
                r, created = run_commands(resp)
                if r:
                    print(box(r, 97))
                    print()
                    cmd_results = r
            msgs.append({"role": "assistant", "content": resp})
            if cmd_results:
                msgs.append({"role": "system", "content": f"[Command results from previous turn:\n{cmd_results}\n]"})
        else:
            if msgs[0]["content"] != QUERY_PROMPT:
                msgs[0] = {"role": "system", "content": QUERY_PROMPT}
            msgs.append({"role": "user", "content": u})
            resp = ask(msgs, max_tokens=16384, models=QUERY_MODELS, temperature=0.6)
            resp = _strip_reasoning(resp)
            if resp:
                print()
                animated_box(resp, 97, delay=0.0003)
                print()
            if not resp:
                resp = "No response"
            msgs.append({"role": "assistant", "content": resp})

        if len(msgs) > 60:
            msgs = [msgs[0]] + msgs[-40:]

        # Sanitize message history to prevent context injection
        for m in msgs:
            if m.get("role") == "system":
                content = m.get("content", "")
                if len(content) > 50000:
                    m["content"] = content[:50000] + "\n[Truncated for security]"

if __name__ == "__main__":
    main()
