#!/usr/bin/env python3
"""tell - AI coding & system agent (legacy wrapper)."""
import os
import sys
import re
import shutil
import textwrap
import time

API_KEY = os.environ.get("NVIDIA_API_KEY")
if not API_KEY:
    print("Error: NVIDIA_API_KEY environment variable not set.")
    print("Get a key at: https://build.nvidia.com/explore")
    sys.exit(1)

from core import TellAgent
from core.prompts import CODING_PROMPT, QUERY_PROMPT
from ui import TerminalUI

ui = TerminalUI()
IS_WINDOWS = __import__('platform').system() == "Windows"


def box(text, color=96):
    return ui.display_box(text, color)


def typewrite(text, color=96, delay=0.0003):
    cols = min(shutil.get_terminal_size().columns, 240)
    inner = cols - 4
    tl, h, tr, v, bl, br = ui.BORDER_STYLES[ui.border_style]
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


def animated_box(text, color=96, delay=0.02):
    cols = min(shutil.get_terminal_size().columns, 240)
    inner = cols - 4
    tl, h, tr, v, bl, br = ui.BORDER_STYLES[ui.border_style]
    lines = []
    for raw in text.split('\n'):
        for wrapped in textwrap.wrap(raw, inner) or ['']:
            lines.append(wrapped)
    print(f"\033[1;{color}m{tl}{h*(cols-2)}{tr}\033[0m")
    for line in lines:
        sys.stdout.write(f"\033[{color}m{v}\033[97m ")
        rendered = re.sub(r'\*\*(.*?)\*\*', r'\033[1;96m\1\033[0m\033[97m', line)
        visible_len = len(re.sub(r'\033\[[0-9;]*m', '', line))
        padding = inner - visible_len
        if padding < 0:
            padding = 0
        sys.stdout.write(rendered)
        sys.stdout.write(f"{' ' * padding}\033[{color}m{v}\033[0m\n")
        sys.stdout.flush()
        time.sleep(delay)
    print(f"\033[1;{color}m{bl}{h*(cols-2)}{br}\033[0m")


def _auto_bold(text):
    lines = text.split('\n')
    result = []
    for line in lines:
        stripped = line.strip()
        if (stripped.endswith(':') and len(stripped) < 80
            and not stripped.startswith('-') and not stripped.startswith(tuple(str(i) for i in range(10)))
            and '**' not in stripped and stripped.count(' ') >= 1):
            if stripped[0].isupper() and '.' not in stripped:
                line = line.replace(stripped, f'**{stripped}**')
        result.append(line)
    return '\n'.join(result)


def inline_mode(query):
    if len(query) > 10000:
        print(box("Input too long (max 10000 characters)", 91))
        return

    agent = TellAgent()

    if query.lower().startswith("do "):
        task = query[3:].strip()
        action, value = agent.commands.execute(task)
        if action != "ai":
            print(f"\n{box(value, 92)}\n")
            return

        coding_prompt = [{"role": "system", "content": CODING_PROMPT}]
        messages = coding_prompt + [{"role": "user", "content": task}]
        print()
        response = agent.api.generate_response(messages)

        results = agent._run_commands(response)
        if results:
            print(box(results, 97))
            print()
        else:
            print(box(response, 97))
            print()
    else:
        messages = [
            {"role": "system", "content": QUERY_PROMPT},
            {"role": "user", "content": query}
        ]
        response = agent.api.generate_response(messages, max_tokens=16384)
        response = _auto_bold(response)
        if response:
            print()
            animated_box(response, 97, delay=0.0003)
            print()
        else:
            print(box("No response generated", 91))


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--inline":
        inline_mode(' '.join(sys.argv[2:]))
        return

    print(box("tell - AI Coding Agent"))
    print()

    agent = TellAgent()

    msgs = [{"role": "system", "content": QUERY_PROMPT}]
    while True:
        try:
            u = input("\033[94m\u276f\033[0m ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!"); break

        if not u: continue
        if len(u) > 10000:
            print(box("Input too long (max 10000 characters)", 91))
            continue
        if u.lower() in ("quit","exit"): break
        if u.lower() == "clear": print("\033[2J\033[H", end=""); continue
        if u.lower() in ("help","commands"):
            cmds = "\n".join(f"  {k}" for k in sorted(agent.commands.get_command_map()))
            print(f"\n{box(f'Built-in commands:\n{cmds}', 92)}")
            print(f"\n{box('do <task> - coding/system tasks  |  border  |  reset  |  clear  |  help', 92)}\n")
            continue
        if u.lower() == "border":
            ui.cycle_border_style()
            print(f"\n{box(f'Border style: {ui.border_style}', 97)}\n")
            continue
        if u.lower() == "reset":
            msgs = [{"role":"system","content":QUERY_PROMPT}]
            print(box("Conversation reset", 92)); print(); continue

        if u.lower().startswith("do "):
            msgs[0] = {"role": "system", "content": CODING_PROMPT}
            task = u[3:].strip()
            action, value = agent.commands.execute(task)
            if action != "ai":
                print(f"\n{box(value, 92)}\n")
                continue
            msgs.append({"role": "user", "content": task})
            print()
            response = agent.api.generate_response(msgs)
            print(box(response, 97))
            print()
            cmd_results = ""
            if "EXECUTE:" in response or "WRITE:" in response:
                r, _ = agent._run_commands_with_files(response)
                if r:
                    print(box(r, 97))
                    print()
                    cmd_results = r
            msgs.append({"role": "assistant", "content": response})
            if cmd_results:
                msgs.append({"role": "system", "content": f"[Command results from previous turn:\n{cmd_results}\n]"})
        else:
            if msgs[0]["content"] != QUERY_PROMPT:
                msgs[0] = {"role": "system", "content": QUERY_PROMPT}
            msgs.append({"role": "user", "content": u})
            response = agent.api.generate_response(msgs, max_tokens=16384)
            response = _auto_bold(response)
            if response:
                print()
                animated_box(response, 97, delay=0.0003)
                print()
            if not response:
                response = "No response"
            msgs.append({"role": "assistant", "content": response})

        if len(msgs) > 60:
            msgs = [msgs[0]] + msgs[-40:]

        for m in msgs:
            if m.get("role") == "system":
                content = m.get("content", "")
                if len(content) > 50000:
                    m["content"] = content[:50000] + "\n[Truncated]"


if __name__ == "__main__":
    main()
