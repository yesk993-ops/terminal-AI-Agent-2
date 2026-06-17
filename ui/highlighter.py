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
    """Apply syntax highlighting to code blocks in markdown text."""
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
    return text
