"""Core agent orchestration — TellAgent, prompt selection, command dispatch."""
import os
import re
import sys
import json
import socket
import subprocess
import time
import platform
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# Import modules from parent directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import TellConfig
from api import NVIDIAAgent
from commands import LocalCommands
from ui import TerminalUI
from security import SecurityManager
from logger import get_logger
from . import analyzer
from .prompts import CODING_PROMPT
from .cache import ResponseCache

IS_WINDOWS = platform.system() == "Windows"

class TellAgent:
    def __init__(self, config_path: str = ".tellrc"):
        self.log = get_logger("TellAgent")
        self.log.info(f"Initializing TellAgent with config: {config_path}")

        self.config = TellConfig(config_path)
        self.config.update_from_env()

        self.api = NVIDIAAgent(
            api_key=os.environ.get("NVIDIA_API_KEY", ""),
            models=self.config.get("models.system"),
            timeout=self.config.get("performance.timeout", 45)
        )

        self.security = SecurityManager(
            allowed_dirs=self.config.get("security.allowed_write_dirs"),
            max_file_size=self.config.get("security.max_file_size"),
            dangerous_commands=self.config.get("security.dangerous_commands")
        )

        self.ui = TerminalUI(
            border_style=self.config.get("ui.border_style", "rounded"),
            theme=self.config.get("ui.theme", "eye-friendly")
        )

        self.commands = LocalCommands(self.security, self.api)

        self.message_history: List[Dict[str, str]] = []
        self.history: Optional[CommandHistory] = None
        self.cache = ResponseCache(self.config)

        if self.config.get("behavior.enable_command_history"):
            from .command_history import CommandHistory
            self.history = CommandHistory(max_size=self.config.get("behavior.max_history_size", 100))

        # Evict expired cache entries on startup
        self.cache.evict()
        self.log.info("TellAgent initialized successfully")

    def add_message(self, role: str, content: str) -> None:
        self.message_history.append({"role": role, "content": content})

    def get_messages(self) -> List[Dict[str, str]]:
        return self.message_history

    def clear_history(self) -> None:
        self.message_history = []
        if self.history:
            self.history.clear()

    def execute_command(self, query: str) -> Tuple[str, Any]:
        action, value = self.commands.execute(query)

        if action in ("local", "shell"):
            result = value
        else:
            result = value

        if self.history and self.config.get("behavior.enable_command_history"):
            self.history.add(query, str(result))

        return action, value

    def _get_dynamic_system_prompt(self, query: str) -> dict:
        result = analyzer.analyze(query)
        level = result["level"]
        content = analyzer.SYSTEM_PROMPTS[level]
        self.log.info(f"Query complexity: {level} (score={result['score']}, factors={result['factors']})")
        return {"role": "system", "content": content}

    def process_query(self, query: str) -> str:
        messages = self.get_messages()
        result = analyzer.analyze(query)
        level = result["level"]

        if level == "complex":
            self.log.info(f"Using complex prompt for query ({result['score']} pts): {result['factors']}")

        system_prompt = self._get_dynamic_system_prompt(query)

        # Remove old system prompt, insert fresh one based on this query
        messages = [m for m in messages if m.get("role") != "system"]
        messages.insert(0, system_prompt)

        if self.config.get("performance.enable_caching"):
            cached_response = self.cache.get(query)
            if cached_response:
                raw_response = cached_response
            else:
                max_tokens = analyzer.get_max_tokens(level)
                raw_response = self.api.generate_response(messages, max_tokens=max_tokens)
                self.cache.set(query, raw_response)
        else:
            max_tokens = analyzer.get_max_tokens(level)
            raw_response = self.api.generate_response(messages, max_tokens=max_tokens)

        def _auto_bold(text):
            lines = text.split('\n')
            result = []
            for line in lines:
                stripped = line.strip()
                if (len(stripped) < 60 and len(stripped) > 3
                    and '**' not in stripped and stripped.count(' ') >= 1
                    and not stripped.startswith('-') and '.' not in stripped):
                    if stripped[0].isupper():
                        line = line.replace(stripped, f'**{stripped}**')
                elif re.match(r'^\d+\.\s+[A-Z][^:]+:\s', stripped) and '**' not in stripped:
                    match = re.match(r'^(\d+\.\s+[^:]+:)(.*)', stripped)
                    if match:
                        keyword_part = match.group(1)
                        rest = match.group(2)
                        line = line.replace(stripped, f'**{keyword_part}**{rest}')
                elif re.match(r'^[A-Z][a-zA-Z\s]+:\s', stripped) and '**' not in stripped and len(stripped) < 80:
                    colon_idx = stripped.index(':')
                    keyword = stripped[:colon_idx+1]
                    rest = stripped[colon_idx+1:]
                    line = line.replace(stripped, f'**{keyword}**{rest}')
                result.append(line)
            return '\n'.join(result)
        response = _auto_bold(raw_response)

        return response

    def process_query_stream(self, query: str):
        """Process query with streaming response generator.
        Yields progressively larger text chunks as they arrive."""
        messages = self.get_messages()
        result = analyzer.analyze(query)
        level = result["level"]
        system_prompt = self._get_dynamic_system_prompt(query)
        messages = [m for m in messages if m.get("role") != "system"]
        messages.insert(0, system_prompt)
        max_tokens = analyzer.get_max_tokens(level)

        full_text = ""
        for chunk in self.api.generate_stream(messages, max_tokens=max_tokens):
            full_text += chunk
            yield full_text

    def _run_commands(self, text: str) -> str:
        """Parse and execute WRITE: and EXECUTE: directives from AI response.
        Also auto-detect code blocks and create files from them."""
        results = []
        created_files = []
        step_num = 0
        lines = text.split('\n')
        i = 0

        def add_step(msg):
            nonlocal step_num
            step_num += 1
            results.append(f"\n  Step {step_num}: {msg}")

        add_step("Parsing response for directives")

        while i < len(lines):
            line = lines[i].strip()
            # Remove <code> tags
            line = re.sub(r'</?code>', '', line).strip()

            if line.startswith('WRITE:'):
                # Parse file path
                path = line[6:].strip()
                path = path.strip('`')
                # Remove <code> tags from path
                path = re.sub(r'</?code>', '', path).strip()

                # Skip paths ending with / (directories)
                if path.endswith('/'):
                    i += 1
                    continue
                # Skip paths that are just directory names
                basename = os.path.basename(path.rstrip('/'))
                ALLOWED_NO_EXT = {'Makefile', 'Dockerfile', 'LICENSE', 'README', 'Procfile', '.gitignore', '.dockerignore'}
                if '.' not in basename and basename not in ALLOWED_NO_EXT:
                    i += 1
                    continue

                # Collect content until next WRITE: or EXECUTE: or end
                content_lines = []
                seen_lines = set()
                i += 1
                opened = False
                while i < len(lines):
                    next_line = lines[i].strip()
                    # Remove <code> tags
                    next_line = re.sub(r'</?code>', '', next_line).strip()
                    if next_line.startswith('WRITE:') or next_line.startswith('EXECUTE:'):
                        break
                    if next_line.startswith('```') or next_line == '`':
                        if not opened:
                            opened = True
                            i += 1
                            continue
                        i += 1
                        break
                    # Deduplicate lines
                    if next_line and next_line in seen_lines:
                        i += 1
                        continue
                    if next_line:
                        seen_lines.add(next_line)
                    content_lines.append(lines[i])
                    i += 1

                if content_lines:
                    content = '\n'.join(content_lines)
                    # Remove code fences
                    content_lines_clean = []
                    for cl in content.split('\n'):
                        if not cl.strip().startswith('```'):
                            content_lines_clean.append(cl)
                    content = '\n'.join(content_lines_clean)

                    add_step(f"Creating file: {path} ({len(content)} bytes)")
                    # Write the file
                    try:
                        os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
                        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
                        with os.fdopen(fd, 'w') as fh:
                            fh.write(content)
                        results.append(f"Created: {path} ({len(content)} bytes)")
                        created_files.append(os.path.abspath(path))
                    except Exception as e:
                        results.append(f"Error creating {path}: {e}")
                i -= 1

            elif line.startswith('EXECUTE:'):
                cmd = line[8:].strip()
                cmd = cmd.strip('`')

                # Fix port conflicts
                if 'http.server' in cmd:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    try:
                        s.bind(('', 8000))
                        s.close()
                    except OSError:
                        cmd = "python3 -m http.server 8080"
                    finally:
                        try:
                            s.close()
                        except:
                            pass

                # Skip dangerous commands
                dangerous = ['rm -rf', 'mkfs', 'dd if=', 'shutdown', 'reboot', '> /dev/']
                if any(d in cmd.lower() for d in dangerous):
                    add_step(f"BLOCKED: {cmd[:50]}... is dangerous")
                else:
                    add_step(f"Running: {cmd}")
                    try:
                        r = subprocess.run(
                            ['sh', '-c', cmd],
                            capture_output=True, text=True, timeout=120,
                            env={k: v for k, v in os.environ.items()
                                 if k not in ("LD_PRELOAD", "LD_LIBRARY_PATH", "BASH_ENV")}
                        )
                        output = r.stdout.strip()
                        if r.stderr:
                            output += "\n" + r.stderr.strip() if output else r.stderr.strip()
                        results.append(f"$ {cmd}\n{output[:2000]}")
                    except subprocess.TimeoutExpired:
                        results.append(f"$ {cmd}\nCommand timed out")
                    except Exception as e:
                        results.append(f"$ {cmd}\nError: {e}")
                i += 1
                continue

            i += 1

        add_step(f"Created {len(created_files)} file(s)")

        # Auto-install dependencies if requirements.txt or package.json was created
        for f in created_files:
            basename = os.path.basename(f)
            if basename == 'requirements.txt':
                try:
                    r = subprocess.run(
                        ['pip', 'install', '--break-system-packages', '-r', f],
                        capture_output=True, text=True, timeout=120
                    )
                    results.append(f"$ pip install --break-system-packages -r {f}\n{r.stdout[:500]}")
                except Exception as e:
                    results.append(f"Error installing deps: {e}")
            elif basename == 'package.json':
                try:
                    r = subprocess.run(
                        ['npm', 'install'],
                        capture_output=True, text=True, timeout=120
                    )
                    results.append(f"$ npm install\n{r.stdout[:500]}")
                except Exception as e:
                    results.append(f"Error installing deps: {e}")

        return '\n'.join(results) if results else ''

    def _run_commands_with_files(self, text: str):
        """Run commands and return (results_str, created_files_list)."""
        results = self._run_commands(text)
        created_files = []
        for line in results.split('\n'):
            if line.strip().startswith('Created:'):
                path = line.strip()[8:].strip()
                if path:
                    created_files.append(os.path.abspath(path))
        return results, created_files

    def get_help(self) -> str:
        commands = sorted(list(self.commands.get_command_map().keys()))
        help_text = "Built-in commands:\n"
        help_text += "".join(f"  {cmd}\n" for cmd in commands)

        help_text += "\ndo <task> - coding/system tasks  |  border  |  reset  |  clear  |  help"

        if self.history:
            help_text += "  |  history <n> - show last n commands"
            help_text += "  |  hist <n> - show last n commands"
            help_text += "  |  history - show recent commands"

        help_text += "\n"
        return help_text

    def show_history(self, count: int = 10) -> str:
        if not self.history:
            return "Command history is disabled."

        recent = self.history.get_last(count)
        if not recent:
            return "No commands in history."

        result = f"Last {len(recent)} commands:\n"

        for i, entry in enumerate(recent, 1):
            timestamp = time.strftime('%H:%M:%S', time.localtime(entry['timestamp']))
            result += f"{i}. [{timestamp}] {entry['command']}\n"

        return result

    def run(self) -> None:
        self.ui.display_welcome()

        self.message_history = []

        while True:
            try:
                self.ui.display_prompt()
                user_input = input().strip()
            except (EOFError, KeyboardInterrupt):
                print("\nBye!")
                break

            if not user_input:
                continue

            # Input length validation to prevent DoS
            if len(user_input) > 10000:
                self.ui.display_box("Input too long (max 10000 characters)")
                print()
                continue

            if user_input.lower() in ("quit", "exit"):
                break

            if user_input.lower() == "clear":
                subprocess.run(["cls" if os.name == "nt" else "clear"], shell=False)
                continue

            if user_input.lower() in ("help", "commands"):
                help_text = self.get_help()
                self.ui.display_box(help_text)
                print()
                continue

            if user_input.lower() == "border":
                self.ui.cycle_border_style()
                self.ui.display_box(f"Border style: {self.ui.border_style}")
                print()
                continue

            if user_input.lower() == "reset":
                self.clear_history()
                self.ui.display_box("Conversation reset")
                print()
                continue

            if user_input.lower() == "history" or user_input.lower() == "hist":
                hist_text = self.show_history(10)
                self.ui.display_box(hist_text)
                print()
                continue

            if user_input.lower().startswith("do "):
                task = user_input[3:].strip()
                result = self.commands.execute(task)

                if result and "ai" in result:
                    # Use coding-specific system prompt for "do" tasks
                    coding_prompt = [{"role": "system", "content": CODING_PROMPT}]
                    messages = coding_prompt + [{"role": "user", "content": task}]
                    response = self.api.generate_response(messages)

                    # Parse and execute WRITE: and EXECUTE: directives
                    results = self._run_commands(response)
                    if results:
                        self.ui.display_box(results)
                        print()
                    else:
                        self.ui.display_box(response)
                        print()

                    self.add_message("user", task)
                    self.add_message("assistant", response)
                else:
                    _, value = result
                    self.ui.display_box(value)
                    print()
            else:
                # Try local command detection first
                local_fn = self.commands.detect_local(user_input)
                if local_fn:
                    self.ui.display_box(local_fn())
                    print()
                else:
                    self.add_message("user", user_input)
                    full = ""
                    for partial in self.process_query_stream(user_input):
                        full = partial
                    self.add_message("assistant", full)
                    self.ui.display_box(full)
                    print()

# Keep for backward compatibility
def main():
    agent = TellAgent()
    agent.run()