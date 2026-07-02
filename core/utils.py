"""Utility functions shared across modules."""

import re
import sys
import textwrap
import shutil
import time
import re as _re

def _auto_bold(text: str) -> str:
    """Add bold styling to headings and certain lines for better readability."""
    lines = text.split('\n')
    result = []
    for line in lines:
        stripped = line.strip()
        if (len(stripped) < 60 and len(stripped) > 3
                and '**' not in stripped and stripped.count(' ') >= 1
                and not stripped.startswith('-') and '.' not in stripped):
            if stripped[0].isupper():
                line = line.replace(stripped, f'**{stripped}**')
        elif _re.match(r'^\d+\.\s+[A-Z][^:]+:\s', stripped) and '**' not in stripped:
            match = _re.match(r'^(\d+\.\s+[^:]+:)(.*)', stripped)
            if match:
                keyword_part = match.group(1)
                rest = match.group(2)
                line = line.replace(stripped, f'**{keyword_part}**{rest}')
        elif _re.match(r'^[A-Z][a-zA-Z\s]+:\s', stripped) and '**' not in stripped and len(stripped) < 80:
            colon_idx = stripped.index(':')
            keyword = stripped[:colon_idx+1]
            rest = stripped[colon_idx+1:]
            line = line.replace(stripped, f'**{keyword}**{rest}')
        result.append(line)
    return '\n'.join(result)


def _visible_len(text: str) -> int:
    """Return visible length of string stripping ANSI escape sequences."""
    return len(_re.sub(r'\033\[[0-9;]*m', '', text))


def _pad_ansi(text: str, width: int) -> str:
    """Pad ANSI-colored text to given width."""
    visible = _visible_len(text)
    pad = max(0, width - visible)
    return text + ' ' * pad


def _wrap_text(text: str, width: int) -> list:
    """Wrap text to width, returning list of lines."""
    return textwrap.wrap(text, width) or ['']


def _strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from text."""
    return _re.sub(r'\033\[[0-9;]*m', '', text)


def _render_bold(text: str, ef_clr: int, bold_clr: int, text_clr: int) -> str:
    """Render **bold** text with ANSI colors."""
    def replace_bold(match):
        return f"\033[1;{ef_clr}{bold_clr}m{match.group(1)}\033[0m\033[{ef_clr}{text_clr}m"
    return _re.sub(r'\*\*(.+?)\*\*', replace_bold, text)


def get_terminal_width() -> int:
    """Return terminal width capped at 240."""
    return min(shutil.get_terminal_size().columns, 240)