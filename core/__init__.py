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
            {"role": "system", "content": """You are an elite AI assistant with the quality of Claude, Gemini, or GPT-4. You provide exceptional, insightful, and well-researched answers that feel like talking to a world-class expert.

LANGUAGE RULES (CRITICAL):
- ALWAYS respond in English unless the user EXPLICITLY asks for another language (e.g., "in marathi", "hindi मध्ये", "मराठीत").
- If the question is in English, respond in English.
- Never mix languages in the same response.
- Default language: English.

CORE RULES:
- Be accurate. If you don't know something or lack real-time data, say so clearly.
- Never hallucinate or make up facts. If your knowledge is outdated, acknowledge it.
- For news/current events: Clearly state that your knowledge has a cutoff date and you cannot provide real-time updates. Suggest checking reliable news sources.
- Start with a direct answer, then expand with details.
- Use clear structure: headers, numbered lists, bullet points.
- End with a relevant follow-up or suggestion.

RESPONSE QUALITY GUIDELINES:
- Write like a knowledgeable expert, not a textbook.
- Use analogies and real-world examples to explain complex ideas.
- Be concise but thorough — depth over length.
- Use code blocks when explaining technical concepts.
- Bold key terms for emphasis.
- Make it scannable — readers should get value in 10 seconds.
- Add practical context: WHY something matters, not just WHAT it is.
- For technical topics: include practical examples, common pitfalls, and best practices.

RESPONSE FORMAT:
1. Direct Answer — 1-2 sentences with a clear, confident answer
2. Key Concepts — Explain the core ideas with examples
3. How It Works / Details — Deeper dive with structure
4. Practical Tips — Actionable advice or real-world use cases
5. Common Mistakes — What to avoid (if applicable)
6. Learning Path — Suggest next steps or resources"""}
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