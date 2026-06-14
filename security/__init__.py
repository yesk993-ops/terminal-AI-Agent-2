import os
import platform
from typing import List, Dict, Any
from pathlib import Path

IS_WINDOWS = platform.system() == "Windows"

class SecurityManager:
    def __init__(self, allowed_dirs: List[str], max_file_size: int, dangerous_commands: List[str]):
        self.allowed_dirs = [os.path.abspath(d) for d in allowed_dirs]
        self.max_file_size = max_file_size
        self.dangerous_commands = dangerous_commands

    def is_safe_path(self, path: str) -> bool:
        try:
            abs_path = os.path.abspath(os.path.expanduser(path))
            for allowed in self.allowed_dirs:
                if abs_path.startswith(allowed):
                    return True
            return False
        except Exception:
            return False

    def is_dangerous(self, cmd: str) -> bool:
        cmd_lower = cmd.lower()
        for d in self.dangerous_commands:
            if d in cmd_lower:
                return True
        return False

    def safe_write(self, path: str, content: str) -> str:
        if not self.is_safe_path(path):
            return f"BLOCKED: cannot write outside allowed directories: {', '.join(self.allowed_dirs)}"
            
        if len(content) > self.max_file_size:
            return f"BLOCKED: file too large (max {self.max_file_size//1024}KB)"
            
        abs_path = os.path.abspath(os.path.expanduser(path))
        try:
            os.makedirs(os.path.dirname(abs_path) or '.', exist_ok=True)
            with open(abs_path, 'w') as f:
                f.write(content)
            return f"Created: {os.path.relpath(abs_path, os.getcwd())} ({len(content)} bytes)"
        except Exception as e:
            return f"Error: {e}"

    def safe_execute(self, cmd: str, timeout: int = 120) -> str:
        if self.is_dangerous(cmd):
            return "BLOCKED: dangerous command rejected"
            
        try:
            shell = ["cmd", "/c", cmd] if IS_WINDOWS else ["sh", "-c", cmd]
            import subprocess
            r = subprocess.run(
                shell,
                capture_output=True, text=True, timeout=timeout
            )
            out = r.stdout
            if r.stderr:
                out += "\n" + r.stderr
            result = out.strip()[:20000] or "OK"
            if r.returncode != 0:
                result += f"\n[Exit code: {r.returncode}]"
            return result
        except subprocess.TimeoutExpired:
            return "Command timed out [Exit code: -1]"
        except Exception as e:
            return f"Error: {e} [Exit code: -2]"