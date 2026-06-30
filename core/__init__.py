"""Core agent orchestration — TellAgent, prompt selection, command dispatch."""
import os
import re
import sys
import json
import subprocess
import time
import itertools
import platform
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# Import modules from parent directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import TellConfig
from api import PROVIDER_REGISTRY, MultiProviderAgent, create_agent
from commands import LocalCommands
from ui import TerminalUI
from ui.highlighter import highlight_response
from security import SecurityManager
from logger import get_logger
from . import analyzer
from .prompts import CODING_PROMPT, DOCUMENT_PROMPT, QUERY_PROMPT
from .cache import ResponseCache

IS_WINDOWS = platform.system() == "Windows"

class TellAgent:
    """Core orchestrator for the Tell AI agent.

    Handles configuration, prompt selection, API communication, command
    execution, and response post‑processing. The implementation now includes
    comprehensive docstrings, type hints, and small refactors to improve
    readability, maintainability, and suitability for corporate environments.
    """

    def __init__(self, config_path: str = ".tellrc"):
        self.log = get_logger("TellAgent")
        self.log.info(f"Initializing TellAgent with config: {config_path}")

        self.config = TellConfig(config_path)
        self.config.update_from_env()

        providers = self.config.get("providers", [self.config.get("provider", "nvidia")])
        agent_configs = []
        for name in providers:
            pconf = PROVIDER_REGISTRY.get(name)
            if not pconf:
                continue
            api_key = os.environ.get(pconf["env_key"], "")
            if not api_key:
                continue
            models = self.config.get(f"models.{name}.system") or self.config.get("models.system", [])
            if not models:
                continue
            agent_configs.append({"class": pconf["class"], "api_key": api_key, "models": models})

        if not agent_configs:
            agent_configs.append({"class": PROVIDER_REGISTRY["nvidia"]["class"], "api_key": "", "models": []})

        if len(agent_configs) == 1:
            c = agent_configs[0]
            self.api = c["class"](api_key=c["api_key"], models=c["models"],
                                   timeout=self.config.get("performance.timeout", 45))
            self.log.info(f"Using single provider: {c['class'].__name__} with model: {c['models'][0] if c['models'] else 'unknown'}")
        else:
            self.api = MultiProviderAgent(agent_configs, timeout=self.config.get("performance.timeout", 45))
            provider_names = [c["class"].__name__ for c in agent_configs]
            self.log.info(f"Using multiple providers: {', '.join(provider_names)}; will try in order")

        self.security = SecurityManager(
            allowed_dirs=self.config.get("security.allowed_write_dirs"),
            max_file_size=self.config.get("security.max_file_size"),
            dangerous_commands=self.config.get("security.dangerous_commands")
        )

        self.ui = TerminalUI(
            border_style=self.config.get("ui.border_style", "minimal"),
            theme=self.config.get("ui.theme", "eye-friendly")
        )

        self.commands = LocalCommands(self.security, self.api)

        self.message_history: List[Dict[str, str]] = []
        self.history: Optional[CommandHistory] = None
        # Path for persisting chat history across sessions
        self._history_path = Path('.tell_history.json')
        # Load existing history if present
        if self._history_path.is_file():
            try:
                self.message_history = json.load(self._history_path.open())
                self.log.info('Loaded persisted chat history')
            except Exception as e:
                self.log.warning(f'Failed to load chat history: {e}')
                self.message_history = []
        self.cache = ResponseCache(self.config)

        if self.config.get("behavior.enable_command_history"):
            from .command_history import CommandHistory
            self.history = CommandHistory(max_size=self.config.get("behavior.max_history_size", 100))

        # Evict expired cache entries on startup
        self.cache.evict()
        self.log.info("TellAgent initialized successfully")

    def add_message(self, role: str, content: str) -> None:
        """Record a message in the internal chat history and persist it.

        Args:
            role: ``"user"`` or ``"assistant"`` indicating the speaker.
            content: The raw text of the message.
        """
        self.message_history.append({"role": role, "content": content})
        # Persist the updated history to disk for cross‑session memory
        try:
            self._history_path.write_text(json.dumps(self.message_history, ensure_ascii=False, indent=2))
        except Exception as e:
            self.log.error(f"Failed to persist chat history: {e}")

    def get_messages(self) -> List[Dict[str, str]]:
        """Return the full list of stored chat messages.

        This includes both user and assistant entries in chronological order.
        """
        return self.message_history

    def clear_history(self) -> None:
        """Reset the internal chat history, delete persisted file, and clear command history buffer.

        All stored messages are discarded, the ``.tell_history.json`` file is removed,
        and the optional ``CommandHistory`` instance is cleared.
        """
        self.message_history = []
        # Delete persisted history file if it exists
        try:
            if self._history_path.is_file():
                self._history_path.unlink()
        except Exception as e:
            self.log.error(f"Failed to delete history file: {e}")
        if self.history:
            self.history.clear()

    def execute_command(self, query: str) -> Tuple[str, Any]:
        """Run a user‑issued command through ``LocalCommands`` and record it.

        The method forwards the ``query`` to ``LocalCommands.execute`` which
        returns a tuple ``(action, value)``. ``action`` indicates the type of
        operation (e.g., ``"local"``, ``"shell"``, ``"ai"``) and ``value``
        contains the result string or a callable.

        If command‑history tracking is enabled, the call is logged in the
        ``CommandHistory`` buffer.
        """
        action, value = self.commands.execute(query)

        # ``action`` determines how ``value`` should be interpreted; for now we
        # simply forward the result unchanged.
        result = value

        if self.history and self.config.get("behavior.enable_command_history"):
            self.history.add(query, str(result))

        return action, value

    def _get_dynamic_system_prompt(self, query: str) -> dict:
        """Generate a system prompt based on query complexity.

        The original implementation selected one of the predefined ``SYSTEM_PROMPTS``
        (simple/medium/complex) after analysing the query. Although the main
        workflow now prefers ``QUERY_PROMPT``, this helper remains for backward
        compatibility or specialised internal uses.
        """
        result = analyzer.analyze(query)
        level = result["level"]
        content = analyzer.SYSTEM_PROMPTS[level]
        self.log.info(
            f"Query complexity: {level} (score={result['score']}, factors={result['factors']})"
        )
        return {"role": "system", "content": content}

    def process_query(self, query: str) -> str:
        """Handle a user query, choose the appropriate system prompt, and
        return the final assistant response.

        The method performs:
        1️⃣ Document‑creation detection (auto‑saves as Markdown).
        2️⃣ Prompt selection (now using ``QUERY_PROMPT`` for standard Q&A).
        3️⃣ Caching based on query text.
        4️⃣ Post‑processing for ``WRITE:`` / ``EXECUTE:`` directives.
        """
        messages = self.get_messages()
        result_analysis = analyzer.analyze(query)
        level = result_analysis["level"]

        # Detect document/SOP creation intent
        doc_keywords = [
            "create document", "create doc", "create sop",
            "write document", "write doc", "write sop",
            "generate document", "generate doc", "generate sop",
            "make a document", "make a doc", "make an sop",
            "document about", "sop for", "sop on",
            "create a report", "write a report",
        ]
        is_doc_request = any(kw in query.lower() for kw in doc_keywords)

        if is_doc_request:
            messages = [m for m in messages if m.get("role") != "system"]
            messages.insert(0, {"role": "system", "content": DOCUMENT_PROMPT})
            try:
                raw_response = self.api.generate_response(messages)
            except Exception as e:
                self.log.error(f"Doc generation failed: {e}")
                raw_response = f"Failed to generate document: {e}"
            # Persist conversation
            self.add_message("user", query)
            self.add_message("assistant", raw_response)
            # Check if AI used WRITE: directives
            if re.search(r'^WRITE:', raw_response, re.MULTILINE):
                results = self._run_commands(raw_response)
                if results:
                    return results
            # Auto-save as markdown if AI didn't use WRITE: directive
            topic = query.lower()
            for prefix in ["create document", "create doc", "create sop",
                           "write document", "write doc", "write sop",
                           "generate document", "generate doc", "generate sop",
                           "make a document", "make a doc", "make an sop",
                           "create a report", "write a report",
                           "document about", "sop for", "sop on"]:
                topic = topic.replace(prefix, "").strip()
            topic = re.sub(r'[^a-z0-9]+', '-', topic).strip('-')[:50]
            filename = f"{topic or 'document'}-guide.md"
            save_result = self.security.safe_write(filename, raw_response)
            return f"{save_result}\n\n{raw_response}"

        if level == "complex":
            self.log.info("Using complex prompt for query (%s pts): %s", result_analysis['score'], result_analysis['factors'])

        # Use the richer QUERY_PROMPT for general Q&A instead of the simple dynamic prompt
        from .prompts import QUERY_PROMPT
        system_prompt = {"role": "system", "content": QUERY_PROMPT}
        # Remove any existing system prompt and insert the new one
        messages = [m for m in messages if m.get("role") != "system"]
        messages.insert(0, system_prompt)

        if self.config.get("performance.enable_caching"):
            cached_response = self.cache.get(query)
            if cached_response:
                raw_response = cached_response
            else:
                try:
                    max_tokens = analyzer.get_max_tokens(level)
                    raw_response = self.api.generate_response(messages, max_tokens=max_tokens)
                    self.cache.set(query, raw_response)
                except Exception as e:
                    self.log.error(f"API call failed: {e}")
                    raw_response = f"I encountered an error while processing your request. Please try again later.\n\nDetails: {e}"
        else:
            try:
                max_tokens = analyzer.get_max_tokens(level)
                raw_response = self.api.generate_response(messages, max_tokens=max_tokens)
            except Exception as e:
                self.log.error(f"API call failed: {e}")
                raw_response = f"I encountered an error while processing your request. Please try again later.\n\nDetails: {e}"

        # --- Continuation loop for incomplete responses ---
        max_continue = 2
        for _ in range(max_continue):
            lines = [l for l in raw_response.split('\n') if l.strip()]
            if not lines:
                break
            last_line = lines[-1].rstrip()
            # End-of-sentence punctuation → consider complete
            if last_line and last_line[-1] in ('.', '!', '?', ')', '"', "'", '`'):
                break
            self.log.info("Response may be incomplete (ends %r), fetching continuation", last_line[-60:])
            messages.append({"role": "assistant", "content": raw_response})
            messages.append({"role": "user", "content": "Continue exactly from where the previous assistant message left off. Do NOT repeat anything, just continue the explanation."})
            try:
                continuation = self.api.generate_response(messages, max_tokens=4096)
            except Exception as e:
                self.log.error(f"Continuation failed: {e}")
                break
            if not continuation or len(continuation) < 10:
                break
            raw_response += "\n" + continuation

        # Check for WRITE: directives in any response and execute them
        write_results = self._run_commands(raw_response)
        if write_results:
            self.add_message("user", query)
            self.add_message("assistant", raw_response)
            return write_results

        # Convert markdown bold (**text**) to ANSI bold and keep colors for code/commands
        formatted = re.sub(r'\*\*(.*?)\*\*', r'\033[1m\1\033[0m', raw_response)
        response = highlight_response(formatted)

        # Persist assistant response so conversation memory is complete
        self.add_message("user", query)
        self.add_message("assistant", raw_response)

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
        Also auto-detect code blocks and create files from them.
        Returns empty string if no directives found (caller should fall back to raw response)."""
        results = []
        created_files = []
        step_num = 0
        found_directive = False
        lines = text.split('\n')
        i = 0

        def add_step(msg):
            nonlocal step_num
            step_num += 1
            results.append(f"\n  Step {step_num}: {msg}")

        while i < len(lines):
            line = lines[i].strip()
            # Remove <code> tags
            line = re.sub(r'</?code>', '', line).strip()

            if line.startswith('WRITE:'):
                found_directive = True
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
                allowed_no_ext = {'Makefile', 'Dockerfile', 'LICENSE', 'README', 'Procfile', '.gitignore', '.dockerignore'}
                if '.' not in basename and basename not in allowed_no_ext:
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
                    result = self.security.safe_write(path, content)
                    results.append(result)
                    if result.startswith("Created:"):
                        created_files.append(os.path.abspath(path))
                i -= 1

            elif line.startswith('EXECUTE:'):
                found_directive = True
                cmd = line[8:].strip()
                cmd = cmd.strip('`')

                result = self.security.safe_execute(cmd, timeout=120)
                add_step(f"Running: {cmd}")
                results.append(f"$ {cmd}\n{result[:2000]}")
                i += 1
                continue

            i += 1

        if not found_directive:
            return ''

        add_step(f"Created {len(created_files)} file(s)")

        if not self.config.get("behavior.auto_install_deps", True):
            return '\n'.join(results) if results else ''

        for f in created_files:
            basename = os.path.basename(f)
            if basename == 'requirements.txt':
                try:
                    r = subprocess.run(
                        ['pip', 'install', '--break-system-packages', '-r', f],
                        capture_output=True, text=True, timeout=120,
                        check=False
                    )
                    results.append(f"$ pip install --break-system-packages -r {f}\n{self.security.sanitize_output(r.stdout[:500])}")
                except (OSError, ValueError) as e:
                    results.append(f"Error installing deps")
            elif basename == 'package.json':
                try:
                    r = subprocess.run(
                        ['npm', 'install'],
                        capture_output=True, text=True, timeout=120,
                        check=False
                    )
                    results.append(f"$ npm install\n{self.security.sanitize_output(r.stdout[:500])}")
                except (OSError, ValueError) as e:
                    results.append(f"Error installing deps")

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
        """Return help text listing available commands."""
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
        """Return formatted command history."""
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
        """Main interactive loop — processes user input and dispatches responses."""
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
                subprocess.run(["cls" if os.name == "nt" else "clear"], shell=False, check=False)
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
                    # Detect document/SOP creation intent
                    doc_keywords = [
                        "create document", "create doc", "create sop",
                        "write document", "write doc", "write sop",
                        "generate document", "generate doc", "generate sop",
                        "make a document", "make a doc", "make an sop",
                        "document about", "sop for", "sop on",
                        "create a report", "write a report",
                    ]
                    is_doc_request = any(kw in user_input.lower() for kw in doc_keywords)

                    if is_doc_request:
                        doc_prompt = [{"role": "system", "content": DOCUMENT_PROMPT}]
                        messages = doc_prompt + [{"role": "user", "content": user_input}]

                        spinner = itertools.cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])
                        sys.stdout.write("\033[?25l")
                        spinner_color = self.ui.THEMES[self.ui.theme]['prompt']
                        sys.stdout.write(f"\033[38;5;{spinner_color}m{next(spinner)} Generating document...\033[0m")
                        sys.stdout.flush()
                        response = self.api.generate_response(messages)
                        sys.stdout.write("\r\033[K\033[?25h")

                        # Check if AI used WRITE: directives
                        if re.search(r'^WRITE:', response, re.MULTILINE):
                            results = self._run_commands(response)
                            self.add_message("user", user_input)
                            self.add_message("assistant", response)
                            print()
                            self.ui.display_box(results or response)
                        else:
                            # Auto-save as markdown if AI didn't use WRITE:
                            topic = user_input.lower()
                            for prefix in ["create document", "create doc", "create sop",
                                           "write document", "write doc", "write sop",
                                           "generate document", "generate doc", "generate sop",
                                           "make a document", "make a doc", "make an sop",
                                           "create a report", "write a report",
                                           "document about", "sop for", "sop on"]:
                                topic = topic.replace(prefix, "").strip()
                            topic = re.sub(r'[^a-z0-9]+', '-', topic).strip('-')[:50]
                            filename = f"{topic or 'document'}-guide.md"
                            save_result = self.security.safe_write(filename, response)
                            self.add_message("user", user_input)
                            self.add_message("assistant", response)
                            print()
                            self.ui.display_box(f"{save_result}\n\n{response}")
                    else:
                        self.add_message("user", user_input)
                        # Show animated spinner while waiting for response
                        spinner = itertools.cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])
                        sys.stdout.write("\033[?25l")  # hide cursor
                        spinner_color = self.ui.THEMES[self.ui.theme]['prompt']
                        sys.stdout.write(f"\033[38;5;{spinner_color}m{next(spinner)} Thinking...\033[0m")
                        sys.stdout.flush()
                        full = ""
                        for partial in self.process_query_stream(user_input):
                            full = partial
                        sys.stdout.write(f"\r\033[K\033[?25h")  # clear spinner, show cursor
                        self.add_message("assistant", full)
                        print()
                        self.ui.display_box(full)

# Keep for backward compatibility
def main():
    agent = TellAgent()
    agent.run()
