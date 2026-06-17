"""Terminal UI — bordered boxes, themes, color rendering."""
import shutil
import textwrap
import platform
from typing import Dict, Tuple

IS_WINDOWS = platform.system() == "Windows"

class TerminalUI:
    BORDER_STYLES = {
        "rounded": ("╭", "─", "╮", "│", "╰", "╯"),
        "classic": ("╔", "═", "╗", "║", "╚", "╝"),
        "sharp":   ("┌", "─", "┐", "│", "└", "┘"),
        "thick":   ("┏", "━", "┓", "┃", "┗", "┛"),
        "minimal": ("╭", "─", "╮", " ", "╰", "╯"),
        "clean":   (" ", " ", " ", " ", " ", " "),
    }
    THEMES = {
        "eye-friendly": {"border": 37, "text": 188, "prompt": 130, "accent": 107},
        "warm":         {"border": 130, "text": 180, "prompt": 173, "accent": 179},
        "cool":         {"border": 37, "text": 153, "prompt": 39, "accent": 33},
        "default":      {"border": 93, "text": 97, "prompt": 94, "accent": 96},
    }

    def __init__(self, border_style: str = "minimal", theme: str = "eye-friendly"):
        self.border_style = border_style
        self.theme = theme if theme in self.THEMES else "eye-friendly"
        if self.border_style not in self.BORDER_STYLES:
            self.border_style = "minimal"

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 240)

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
        keys = list(self.BORDER_STYLES)
        idx = (keys.index(self.border_style) + 1) % len(keys)
        self.border_style = keys[idx]

    def display_prompt(self, text: str = "❯") -> None:
        t = self.THEMES[self.theme]
        print(f"\033[38;5;{t['prompt']}m{text}\033[0m", end=" ")


