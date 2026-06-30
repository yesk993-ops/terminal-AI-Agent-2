"""Terminal UI — bordered boxes, themes, color rendering."""
import shutil
import textwrap
import platform
import re
from typing import Dict, Tuple, List

IS_WINDOWS = platform.system() == "Windows"

class TerminalUI:
    """Terminal display — bordered boxes, themes, and color rendering."""
    BORDER_STYLES = {
        "rounded": ("╭", "─", "╮", "│", "╰", "╯"),
        "classic": ("╔", "═", "╗", "║", "╚", "╝"),
        "sharp":   ("┌", "─", "┐", "│", "└", "┘"),
        "thick":   ("┏", "━", "┓", "┃", "┗", "┛"),
        "minimal": ("╭", "─", "╮", " ", "╰", "╯"),
        "clean":   (" ", " ", " ", " ", " ", " "),
    }
    # Standard 16-color ANSI palette — works on Linux, macOS, and Windows terminals
    THEMES = {
        "universal": {"border": 6, "text": 7, "prompt": 3, "accent": 14},
        "eye-friendly": {"border": 6, "text": 7, "prompt": 3, "accent": 14},
        "warm":         {"border": 1, "text": 7, "prompt": 3, "accent": 11},
        "cool":         {"border": 4, "text": 7, "prompt": 6, "accent": 14},
        "default":      {"border": 6, "text": 7, "prompt": 3, "accent": 14},
    }

    def __init__(self, border_style: str = "minimal", theme: str = "eye-friendly"):
        self.border_style = border_style
        self.theme = theme if theme in self.THEMES else "eye-friendly"
        if self.border_style not in self.BORDER_STYLES:
            self.border_style = "minimal"

    def get_terminal_width(self) -> int:
        """Return usable terminal width capped at 240."""
        return min(shutil.get_terminal_size().columns, 240)

    @staticmethod
    def _wrap_ansi(line: str, width: int) -> List[str]:
        """Wrap a line that may contain ANSI codes to a given visible width."""
        # Split the line into segments of plain text and ANSI codes
        parts = re.split(r'(\033\[[0-9;]*m)', line)
        # Plain text chunks: every even index (0,2,4,...) is plain; odd are ANSI codes
        plain_parts = [p for i, p in enumerate(parts) if i % 2 == 0]
        # Build plan text string for measuring
        plain = ''.join(plain_parts)
        if len(plain) <= width:
            return [line]
        # Break plain text at spaces
        words = plain.split(' ')
        wrapped = []
        current_line = ''
        current_ansi = ''
        word_idx = 0
        # Reconstruct with ANSI sequences
        for word in words:
            # Find the original segment for this word (including ANSI)
            pass
        # fallback: simple wrap without considering ANSI properly
        return textwrap.wrap(plain, width)

    def display_box(self, text: str, color: int | None = None) -> None:
        cols = self.get_terminal_width()
        inner = cols - 4
        tl, h, tr, v, bl, br = self.BORDER_STYLES[self.border_style]
        t = self.THEMES[self.theme]
        bc = t["border"] if color is None else color

        if self.border_style == "clean":
            for raw in text.split('\n'):
                for wrapped in textwrap.wrap(raw, cols) or ['']:
                    print(wrapped)
            return

        lines = []
        for raw in text.split('\n'):
            for wrapped in textwrap.wrap(raw, inner) or ['']:
                lines.append(f"\033[38;5;{bc}m{v}\033[38;5;{t['text']}m {wrapped:<{inner}}\033[38;5;{bc}m{v}\033[0m")

        top = f"\033[1;38;5;{bc}m{tl}{h*(cols-2)}{tr}\033[0m"
        bot = f"\033[1;38;5;{bc}m{bl}{h*(cols-2)}{br}\033[0m"

        print(top)
        print('\n'.join(lines))
        print(bot)

    def display_welcome(self) -> None:
        self.display_box("tell - AI Coding Agent")

    def cycle_border_style(self) -> None:
        """Cycle to the next border style."""
        keys = list(self.BORDER_STYLES)
        idx = (keys.index(self.border_style) + 1) % len(keys)
        self.border_style = keys[idx]

    def display_prompt(self, text: str = "❯") -> None:
        t = self.THEMES[self.theme]
        print(f"\033[38;5;{t['prompt']}m{text}\033[0m", end=" ")


