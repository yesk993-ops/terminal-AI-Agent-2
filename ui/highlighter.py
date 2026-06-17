"""Lightweight syntax highlighter for terminal output."""
import re

# ANSI 256-color palette (eye-friendly)
_BLUE = 39
_GREEN = 71
_YELLOW = 221
_CYAN = 80
_MAGENTA = 177
_RED = 167
_DIM = 242
_ORANGE = 173
_WHITE = 188

_HIGHLIGHTERS = {}

def _highlight_python(code: str) -> str:
    keywords = r'\b(def|class|return|if|else|elif|for|while|import|from|as|try|except|finally|with|yield|lambda|pass|break|continue|and|or|not|in|is|None|True|False|raise|global|nonlocal|del|print|self)\b'
    code = re.sub(keywords, lambda m: f"\033[38;5;{_BLUE}m{m.group(1)}\033[0m", code)
    code = re.sub(r'("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')', lambda m: f"\033[38;5;{_GREEN}m{m.group(1)}\033[0m", code)
    code = re.sub(r'#.*$', lambda m: f"\033[38;5;{_DIM}m{m.group(0)}\033[0m", code)
    return code

def _highlight_json(code: str) -> str:
    code = re.sub(r'("(?:[^"\\]|\\.)*")\s*:', lambda m: f"\033[38;5;{_CYAN}m{m.group(1)}\033[0m:", code)
    code = re.sub(r':\s*("(?:[^"\\]|\\.)*")', lambda m: f":\033[38;5;{_GREEN}m{m.group(1)}\033[0m", code)
    code = re.sub(r'(:\s*)(\d+\.?\d*)', lambda m: f"{m.group(1)}\033[38;5;{_YELLOW}m{m.group(2)}\033[0m", code)
    code = re.sub(r'(:\s*)(true|false|null)', lambda m: f"{m.group(1)}\033[38;5;{_BLUE}m{m.group(2)}\033[0m", code, flags=re.IGNORECASE)
    return code

def _highlight_yaml(code: str) -> str:
    code = re.sub(r'^(\s*[\w._-]+)(:)', lambda m: f"\033[38;5;{_CYAN}m{m.group(1)}\033[0m{_ORANGE}:{_WHITE}", code)
    code = re.sub(r'(:\s*)("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')', lambda m: f"{m.group(1)}\033[38;5;{_GREEN}m{m.group(2)}\033[0m", code)
    code = re.sub(r'^(\s*#.*)', lambda m: f"\033[38;5;{_DIM}m{m.group(1)}\033[0m", code)
    return code

def _highlight_bash(code: str) -> str:
    keywords = r'\b(if|then|else|elif|fi|for|while|do|done|case|esac|function|return|exit|export|source|local|set|unset)\b'
    code = re.sub(keywords, lambda m: f"\033[38;5;{_BLUE}m{m.group(1)}\033[0m", code)
    code = re.sub(r'#.*$', lambda m: f"\033[38;5;{_DIM}m{m.group(0)}\033[0m", code)
    code = re.sub(r'("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')', lambda m: f"\033[38;5;{_GREEN}m{m.group(1)}\033[0m", code)
    return code

def _highlight_generic(code: str) -> str:
    return f"\033[38;5;{_DIM}m{code}\033[0m"

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
    """Process markdown text and apply syntax highlighting to code blocks."""
    def _replace_block(m):
        lang = m.group(1).strip() or ""
        code = m.group(2)
        highlighted = highlight_code_block(lang, code)
        return f"\033[38;5;{_ORANGE}m```{lang}\033[0m\n{highlighted}\n\033[38;5;{_ORANGE}m```\033[0m"

    text = re.sub(
        r'```(\w*)\n(.*?)```',
        _replace_block,
        text,
        flags=re.DOTALL
    )
    return text
