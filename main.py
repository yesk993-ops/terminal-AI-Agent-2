#!/usr/bin/env python3
"""
Tell - Modular AI Coding Agent

This is the entry point for the tell AI agent. It uses a modular structure:
- core/agent.py: Main orchestration and agent logic
- commands/: Local system commands
- ui/: Display and interaction
- security/: Validation and blocking
- api/: NVIDIA API handling
- config/: Configuration management
- logger/: Logging system
"""
import os
import sys
import time
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from core import TellAgent
from logger import get_logger

class AnimatedUI:
    def __init__(self):
        self.log = get_logger(__name__)
        self.border_styles = {
            "rounded": ("╭", "─", "╮", "│", "╰", "╯"),
            "classic": ("╔", "═", "╗", "║", "╚", "╝"),
            "sharp":   ("┌", "─", "┐", "│", "└", "┘"),
            "thick":   ("┏", "━", "┓", "┃", "┗", "┛"),
        }
        self.current_style = "rounded"
        self.ef = lambda c: f"38;5;{c}"
        self.border_clr = 37
        self.text_clr = 188
        self.bold_clr = 107
        self.vbar_clr = 37
        
    def get_terminal_width(self) -> int:
        import shutil
        return min(shutil.get_terminal_size().columns, 240)
    
    def _render_bold(self, text: str) -> str:
        import re
        def replace_bold(match):
            return f"\033[1;{self.ef(self.bold_clr)}m{match.group(1)}\033[0m\033[{self.ef(self.text_clr)}m"
        return re.sub(r'\*\*(.+?)\*\*', replace_bold, text)

    def _visible_len(self, text: str) -> int:
        import re
        return len(re.sub(r'\033\[[0-9;]*m', '', text))

    def _pad_ansi(self, text: str, width: int) -> str:
        visible = self._visible_len(text)
        pad = max(0, width - visible)
        return text + ' ' * pad

    def animate_box(self, text: str, color: int = None, delay: float = 0.005) -> None:
        cols = self.get_terminal_width()
        inner = cols - 4
        tl, h, tr, v, bl, br = self.border_styles[self.current_style]
        bc = self.border_clr if color is None else color
        
        lines = []
        for raw in text.split('\n'):
            for wrapped_raw in self._wrap_text(raw, inner) or ['']:
                rendered = self._render_bold(wrapped_raw)
                lines.append(rendered)
        
        border_color = f"1;{self.ef(bc)}"
        print(f"\033[{border_color}m{tl}{h*(cols-2)}{tr}\033[0m")
        for line in lines:
            sys.stdout.write(f"\033[{self.ef(self.vbar_clr)}m{v}\033[{self.ef(self.text_clr)}m ")
            visible_len = self._visible_len(line)
            padding = inner - visible_len
            if padding < 0:
                padding = 0
            import re as _re
            segments = _re.split(r'(\033\[[0-9;]*m)', line)
            for seg in segments:
                if _re.match(r'\033\[', seg):
                    sys.stdout.write(seg)
                else:
                    for ch in seg:
                        sys.stdout.write(ch)
                        sys.stdout.flush()
                        if delay > 0:
                            time.sleep(delay * 0.3)
            sys.stdout.write(f"{' ' * padding}\033[{self.ef(self.vbar_clr)}m{v}\033[0m\n")
            if delay > 0:
                time.sleep(delay)
        print(f"\033[{border_color}m{bl}{h*(cols-2)}{br}\033[0m")
        
    def _wrap_text(self, text: str, width: int) -> list:
        import textwrap
        return textwrap.wrap(text, width) or ['']
    
    def cycle_border_style(self) -> None:
        styles = list(self.border_styles.keys())
        idx = (styles.index(self.current_style) + 1) % len(styles)
        self.current_style = styles[idx]
        self.log.info(f"Border style changed to: {self.current_style}")

def main():
    """Main entry point"""
    log = get_logger(__name__)
    animated_ui = AnimatedUI()
    
    if len(sys.argv) > 2 and sys.argv[1] == "--inline":
        # Inline mode - direct execution
        from core import TellAgent
        agent = TellAgent()
        
        query = sys.argv[2].lower()
        
        if query.startswith("do "):
            task = sys.argv[2][3:].strip()
            action, value = agent.commands.execute(task)
            
            if action != "ai":
                animated_ui.animate_box(value)
                print()
                return
                
            agent.add_message("user", task)
            # Use coding-specific system prompt
            coding_prompt = [{"role": "system", "content": "You are a coding agent. ALWAYS use these directives:\n\nWRITE: filename\n<file content here>\n\nEXECUTE: command\n\nCRITICAL: Start with WRITE: then filename. Then code. Then EXECUTE:.\nDo NOT use markdown or code blocks."}]
            messages = coding_prompt + [{"role": "user", "content": task}]
            response = agent.api.generate_response(messages)
            
            # Parse and execute WRITE: and EXECUTE: directives
            results = agent._run_commands(response)
            if results:
                animated_ui.animate_box(results)
                print()
            else:
                animated_ui.animate_box(response)
                print()
            
            agent.add_message("assistant", response)
            
        elif query in ("history", "hist", "help", "commands", "border", "reset", "clear"):
            if query == "help" or query == "commands":
                help_text = agent.get_help()
                animated_ui.animate_box(help_text)
                print()
            elif query == "history" or query == "hist":
                hist_text = agent.show_history(10)
                animated_ui.animate_box(hist_text)
                print()
            elif query == "border":
                agent.ui.cycle_border_style()
                animated_ui.animate_box(f"Border style: {agent.ui.border_style}")
                print()
            elif query == "reset":
                agent.clear_history()
                animated_ui.animate_box("Conversation reset")
                print()
            elif query == "clear":
                animated_ui.animate_box("Cleared screen")
                print()
            
        else:
            agent.add_message("user", sys.argv[2])
            response = agent.process_query(sys.argv[2])
            animated_ui.animate_box(response)
            print()
        
        return
    
    # Full interactive mode
    agent = TellAgent()
    agent.run()
if __name__ == "__main__":
    import time
    main()