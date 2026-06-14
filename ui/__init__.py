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
    }

    def __init__(self, border_style: str = "rounded"):
        self.border_style = border_style
        if self.border_style not in self.BORDER_STYLES:
            self.border_style = "rounded"

    def get_terminal_width(self) -> int:
        return min(shutil.get_terminal_size().columns, 240)

    def display_box(self, text: str, color: int = 93) -> None:
        cols = self.get_terminal_width()
        inner = cols - 4
        tl, h, tr, v, bl, br = self.BORDER_STYLES[self.border_style]
        
        lines = []
        for raw in text.split('\n'):
            for wrapped in textwrap.wrap(raw, inner) or ['']:
                lines.append(f"\033[{color}m{v} {wrapped:<{inner}}{v}\033[0m")
                
        top = f"\033[1;{color}m{tl}{h*(cols-2)}{tr}\033[0m"
        bot = f"\033[1;{color}m{bl}{h*(cols-2)}{br}\033[0m"
        
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
        print(f"\033[94m{text}\033[0m", end=" ")