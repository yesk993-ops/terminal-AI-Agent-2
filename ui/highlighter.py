"""Lightweight syntax highlighter with eye-friendly terminal colors."""
import re

# Soft 256-color palette — good contrast on dark & light backgrounds
_KEY = 74       # soft blue for YAML/JSON keys
_KEYWORD = 68   # muted blue for language keywords
_STRING = 107   # soft green for strings
_NUMBER = 222   # warm yellow for numbers
_BOOL = 104     # lavender for booleans/null
_COMMENT = 243  # dim gray for comments
_FENCE = 136    # muted gold for ``` markers
_CMD = 73       # soft cyan for commands
_FLAG = 221     # warm yellow for command flags/args
_VAR = 188      # light gray for variables/paths
_RESET = 0

_HIGHLIGHTERS = {}

def _highlight_python(code: str) -> str:
    keywords = r'\b(def|class|return|if|else|elif|for|while|import|from|as|try|except|finally|with|yield|lambda|pass|break|continue|and|or|not|in|is|None|True|False|raise|global|nonlocal|del|print|self)\b'
    code = re.sub(keywords, lambda m: f"\033[38;5;{_KEYWORD}m{m.group(1)}\033[0m", code)
    code = re.sub(r'("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')', lambda m: f"\033[38;5;{_STRING}m{m.group(1)}\033[0m", code)
    code = re.sub(r'#.*$', lambda m: f"\033[38;5;{_COMMENT}m{m.group(0)}\033[0m", code)
    return code

def _highlight_json(code: str) -> str:
    code = re.sub(r'("(?:[^"\\]|\\.)*")\s*:', lambda m: f"\033[38;5;{_KEY}m{m.group(1)}\033[0m:", code)
    code = re.sub(r':\s*("(?:[^"\\]|\\.)*")', lambda m: f":\033[38;5;{_STRING}m{m.group(1)}\033[0m", code)
    code = re.sub(r'(:\s*)(\d+\.?\d*)', lambda m: f"{m.group(1)}\033[38;5;{_NUMBER}m{m.group(2)}\033[0m", code)
    code = re.sub(r'(:\s*)(true|false|null)', lambda m: f"{m.group(1)}\033[38;5;{_BOOL}m{m.group(2)}\033[0m", code, flags=re.IGNORECASE)
    return code

def _highlight_yaml(code: str) -> str:
    code = re.sub(r'^(\s*[\w._-]+)(:)', lambda m: f"\033[38;5;{_KEY}m{m.group(1)}\033[38;5;{_COMMENT}m:\033[0m", code, flags=re.MULTILINE)
    code = re.sub(r'(:\s*)("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')', lambda m: f"{m.group(1)}\033[38;5;{_STRING}m{m.group(2)}\033[0m", code)
    code = re.sub(r'(:\s*)(\d+\.?\d*)', lambda m: f"{m.group(1)}\033[38;5;{_NUMBER}m{m.group(2)}\033[0m", code)
    code = re.sub(r'(:\s*)(true|false|null|yes|no|on|off)', lambda m: f"{m.group(1)}\033[38;5;{_BOOL}m{m.group(2)}\033[0m", code, flags=re.IGNORECASE)
    code = re.sub(r'^(\s*#.*)', lambda m: f"\033[38;5;{_COMMENT}m{m.group(1)}\033[0m", code, flags=re.MULTILINE)
    return code

def _highlight_bash(code: str) -> str:
    keywords = r'\b(if|then|else|elif|fi|for|while|do|done|case|esac|function|return|exit|export|source|local|set|unset)\b'
    code = re.sub(keywords, lambda m: f"\033[38;5;{_KEYWORD}m{m.group(1)}\033[0m", code)
    code = re.sub(r'#.*$', lambda m: f"\033[38;5;{_COMMENT}m{m.group(0)}\033[0m", code)
    code = re.sub(r'("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')', lambda m: f"\033[38;5;{_STRING}m{m.group(1)}\033[0m", code)
    return code

def _highlight_generic(code: str) -> str:
    return code

# Commands to detect on bare lines (not inside backticks)
_CMDS = (
    "kubectl", "docker", "helm", "git", "pip", "pip3", "npm", "yarn",
    "apt", "apt-get", "dnf", "yum", "brew", "zypper", "pacman",
    "systemctl", "service", "journalctl",
    "pvcreate", "vgcreate", "lvcreate", "pvremove", "vgremove", "lvremove",
    "pvextend", "vgextend", "lvextend", "pvreduce", "vgreduce", "lvreduce",
    "pvdisplay", "vgdisplay", "lvdisplay", "pvscan", "vgscan", "lvscan",
    "pvchange", "vgchange", "lvchange", "lvresize", "mkfs", "mount", "umount",
    "ssh", "scp", "sftp", "rsync",
    "curl", "wget", "python", "python3", "node", "go", "rustc", "cargo",
    "make", "cmake", "terraform", "ansible", "kustomize", "minikube", "kind",
    "vagrant", "echo", "cat", "grep", "awk", "sed",
    "ls", "cd", "rm", "cp", "mv", "chmod", "chown", "find",
    "df", "du", "free", "ps", "top", "htop",
    "ping", "traceroute", "nslookup", "dig",
    "netstat", "ss", "ip", "ifconfig", "iwconfig",
    "fdisk", "parted", "lsblk", "blkid", "dd",
    "adduser", "useradd", "usermod", "passwd",
    "crontab", "at", "systemd", "timedatectl",
    "sudo", "su", "chroot", "env", "export",
    "nano", "vim", "vi", "emacs", "code",
    "gcc", "g++", "clang", "javac", "java",
    "mysql", "psql", "redis-cli", "mongosh",
)

# Single commands that always indicate a command line
_SINGLE_CMDS = ("sudo", "doctl", "gcloud", "az", "aws", "oc", "istioctl", "linkerd")


def _highlight_inline_code(text: str) -> str:
    """Highlight inline backtick content: `kubectl get pods`"""
    return re.sub(r'`([^`]+)`', lambda m: f"\033[38;5;{_CMD}m{m.group(1)}\033[0m", text)


def _color_rest(rest: str) -> str:
    """Color flags and paths in the remainder of a command line."""
    rest = re.sub(r'(\s+)(--?[\w-]+)', lambda n: f"{n.group(1)}\033[38;5;{_FLAG}m{n.group(2)}\033[0m", rest)
    rest = re.sub(r'(\s+)(\.?/?[\w./_-]+)', lambda n: f"{n.group(1)}\033[38;5;{_STRING}m{n.group(2)}\033[0m", rest)
    return rest


def _highlight_cmd_lines(text: str) -> str:
    """Highlight bare lines starting with a known command."""
    cmd_pattern = r'^(\s*(?:\d+\.\s*)?(?:\$\s*|#\s*)?)((?:sudo\s+)?(?:(' + '|'.join(_CMDS) + r')\b)).*$'
    def _replace(m):
        prefix = m.group(1)
        cmd = m.group(2)
        rest_line = m.group(0)[len(m.group(1)) + len(cmd):]
        rest_colored = _color_rest(rest_line)
        return f"{prefix}\033[38;5;{_CMD}m{cmd}\033[0m{rest_colored}"
    return re.sub(cmd_pattern, _replace, text, flags=re.MULTILINE)


def _highlight_cmd_single(text: str) -> str:
    """Highlight lines starting with sudo/su etc followed by subcommands."""
    pattern = r'^(\s*(?:\d+\.\s*)?)((?:' + '|'.join(_SINGLE_CMDS) + r')\b)(.*)$'
    def _replace(m):
        prefix = m.group(1)
        cmd = m.group(2)
        rest = m.group(3)
        rest_colored = _color_rest(rest)
        return f"{prefix}\033[38;5;{_CMD}m{cmd}\033[0m{rest_colored}"
    return re.sub(pattern, _replace, text, flags=re.MULTILINE)


_HIGHLIGHTERS = {
    "python": _highlight_python,
    "py": _highlight_python,
    "json": _highlight_json,
    "yaml": _highlight_yaml,
    "yml": _highlight_yaml,
    "bash": _highlight_bash,
    "sh": _highlight_bash,
    "shell": _highlight_bash,
    "dockerfile": _highlight_generic,
    "text": _highlight_generic,
}


def highlight_code_block(lang: str, code: str) -> str:
    fn = _HIGHLIGHTERS.get(lang.lower(), _highlight_generic)
    return fn(code)


def highlight_response(text: str) -> str:
    """Apply syntax highlighting to code blocks, inline commands, and bare command lines."""
    def _replace_block(m):
        lang = m.group(1).strip() or ""
        code = m.group(2)
        highlighted = highlight_code_block(lang, code)
        return f"\033[38;5;{_FENCE}m```{lang}\033[0m\n{highlighted}\n\033[38;5;{_FENCE}m```\033[0m"

    text = re.sub(
        r'```(\w*)\n(.*?)```',
        _replace_block,
        text,
        flags=re.DOTALL
    )
    text = _highlight_inline_code(text)
    text = _highlight_cmd_lines(text)
    text = _highlight_cmd_single(text)

    return text
