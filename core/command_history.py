import time
from typing import List, Dict, Optional, Any

class CommandHistory:
    def __init__(self, max_size: int = 100):
        self.history: List[Dict[str, Any]] = []
        self.max_size = max_size
        
    def add(self, command: str, result: str, timestamp: Optional[float] = None) -> None:
        if timestamp is None:
            timestamp = time.time()
            
        entry = {
            "command": command,
            "result": result,
            "timestamp": timestamp,
            "type": self._detect_type(command)
        }
        
        self.history.append(entry)
        
        if len(self.history) > self.max_size:
            self.history.pop(0)
            
    def get_last(self, n: int = 10) -> List[Dict[str, Any]]:
        return self.history[-n:]
        
    def search(self, query: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        query = query.lower() if not case_sensitive else query
        results = []
        
        for entry in self.history:
            if (query in entry["command"].lower() if not case_sensitive else query in entry["command"]):
                results.append(entry)
                
        return results
        
    def clear(self) -> None:
        self.history.clear()
        
    def get_count_by_type(self) -> Dict[str, int]:
        counts = {}
        for entry in self.history:
            entry_type = entry["type"]
            counts[entry_type] = counts.get(entry_type, 0) + 1
        return counts
        
    def get_recent_commands(self) -> List[str]:
        return [entry["command"] for entry in self.history[-10:]]
        
    def _detect_type(self, command: str) -> str:
        command_lower = command.lower()
        if command_lower.startswith("do "):
            return "system_command"
        elif command_lower.startswith("help"):
            return "help"
        elif command_lower.startswith("clear"):
            return "clear"
        elif command_lower.startswith("reset"):
            return "reset"
        elif command_lower.startswith("border"):
            return "ui"
        else:
            return "query"

    def export_to_file(self, filepath: str) -> bool:
        try:
            with open(filepath, 'w') as f:
                for entry in self.history:
                    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(entry['timestamp']))
                    f.write(f"[{timestamp}] {entry['type'].upper()}: {entry['command']}\n")
                    f.write(f"Result: {entry['result'][:200]}{'...' if len(entry['result']) > 200 else ''}\n\n")
            return True
        except Exception:
            return False