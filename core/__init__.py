import os
import sys
import json
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
            border_style=self.config.get("ui.border_style", "rounded")
        )
        
        self.commands = LocalCommands(self.security, self.api)
        
        self.message_history: List[Dict[str, str]] = []
        
        if self.config.get("behavior.enable_command_history"):
            from .command_history import CommandHistory
            self.history = CommandHistory(max_size=self.config.get("behavior.max_history_size", 100))
        else:
            self.history = None
            
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

    def process_query(self, query: str) -> str:
        messages = self.get_messages()
        
        if self.config.get("performance.enable_caching"):
            cached_response = self._check_cache(query)
            if cached_response:
                return cached_response
                
        response = self.api.generate_response(messages)
        
        if self.config.get("performance.enable_caching"):
            self._cache_response(query, response)
            
        return response
        
    def _check_cache(self, query: str) -> Optional[str]:
        cache_file = Path(".tell_cache.json")
        if not cache_file.exists():
            return None
            
        try:
            with open(cache_file, 'r') as f:
                cache = json.load(f)
                
            if query in cache:
                item = cache[query]
                if time.time() - item["timestamp"] < self.config.get("performance.cache_ttl", 3600):
                    return item["response"]
        except Exception:
            pass
            
        return None
        
    def _cache_response(self, query: str, response: str) -> None:
        cache_file = Path(".tell_cache.json")
        
        try:
            cache_data = {}
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                    
            cache_data[query] = {
                "response": response,
                "timestamp": time.time()
            }
            
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception:
            pass
        
    def get_help(self) -> str:
        commands = sorted(list(self.commands.get_command_map().keys()))
        help_text = "Built-in commands:\n"
        for cmd in commands:
            help_text += f"  {cmd}\n"
            
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
        
        query_prompt = [
            {"role": "system", "content": """You are a world-class AI assistant — respond like the best AI models (Claude, Gemini, GPT-4). Give exceptional, insightful, and expert-level answers.

FORMATTING RULES (STRICT):
- NEVER use markdown: no **, no *, no ##, no ```, no |, no ---
- Use PLAIN TEXT ONLY
- Use simple dashes - for lists
- Use numbers 1. 2. 3. for ordered lists
- Use backticks only for actual code commands
- Keep it clean and readable
- No special characters, no formatting symbols

RESPONSE STYLE:
- Sound like a knowledgeable friend, not a textbook
- Be conversational yet authoritative
- Use natural flow, not robotic structure
- Mix short and long sentences for rhythm
- Use real-world analogies to explain complex ideas
- Be specific with examples, not vague generalizations

CORE RULES:
- Start with a direct, confident answer (1-2 sentences)
- Then expand with depth and context
- Use "Think of it like..." analogies for complex topics
- Include practical "why this matters" explanations
- Be honest about limitations and unknowns
- End with something useful: next steps, a tip, or a question

LANGUAGE:
- Match the language of the user's question EXACTLY
- If user asks in English, respond in English
- If user asks in Hindi, respond in Hindi
- If user asks in Marathi, respond in Marathi
- If user asks in Spanish, respond in Spanish
- If user asks in any other language, respond in that same language
- Never mix languages in same response
- Use natural, fluent, grammatically correct language

RESPONSE STRUCTURE:
1. Opening — Direct answer that immediately satisfies the question
2. Explanation — Deeper dive with clear, logical flow
3. Example — Real-world analogy or practical use case
4. Tips — Actionable advice or common pitfalls to avoid
5. Closing — Suggest what to explore next"""}
        ]
        
        self.message_history = query_prompt
        
        while True:
            try:
                user_input = input("\033[94m❯\033[0m ").strip()
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
                # Use subprocess instead of os.system to prevent command injection
                import subprocess
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
                    self.add_message("user", task)
                    response = self.api.generate_response(self.get_messages())
                    self.add_message("assistant", response)
                    
                    self.ui.display_box(response)
                    print()
                else:
                    action, value = result
                    self.ui.display_box(value)
                    print()
            else:
                response = self.process_query(user_input)
                self.add_message("user", user_input)
                self.add_message("assistant", response)
                
                self.ui.display_box(response)
                print()

# Keep for backward compatibility
def main():
    agent = TellAgent()
    agent.run()