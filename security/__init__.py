import os
import re
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
            real_path = os.path.realpath(abs_path)
            for allowed in self.allowed_dirs:
                allowed_real = os.path.realpath(os.path.abspath(allowed))
                if real_path.startswith(allowed_real + os.sep) or real_path == allowed_real:
                    return True
            return False
        except Exception:
            return False

    def is_dangerous(self, cmd: str) -> bool:
        cmd_lower = cmd.lower().strip()
        # Normalize whitespace to prevent bypass
        cmd_normalized = re.sub(r'\s+', ' ', cmd_lower)
        # Check substring matches
        for d in self.dangerous_commands:
            if d in cmd_normalized:
                return True
        # Check regex patterns for encoded/bypassed commands
        dangerous_patterns = [
            r'\brm\s+-[a-z]*r[a-z]*f',  # rm -rf
            r'\brm\s+-[a-z]*f[a-z]*r',  # rm -fr
            r'\bdd\s+if=',              # dd if=
            r'\bmkfs\b',               # mkfs
            r'>\s*/dev/sd',            # > /dev/sda
            r'\bshutdown\b',           # shutdown
            r'\breboot\b',             # reboot
            r'\bchmod\s+777',         # chmod 777
            r'\bcurl\b.*\|\s*bash',   # curl | bash
            r'\bwget\b.*\|\s*bash',   # wget | bash
            r'\beval\b',              # eval
            r'\bexec\b',              # exec
            r'\bsudo\b',              # sudo
            r'\bpython\s+-c',         # python -c
            r'\bpython3\s+-c',        # python3 -c
        ]
        for pattern in dangerous_patterns:
            if re.search(pattern, cmd_normalized):
                return True
        return False

    def safe_write(self, path: str, content: str) -> str:
        if not self.is_safe_path(path):
            return f"BLOCKED: cannot write outside allowed directories: {', '.join(self.allowed_dirs)}"
        # Input length validation
        if len(path) > 1000:
            return "BLOCKED: path too long (max 1000 characters)"
        if len(content) > self.max_file_size:
            return f"BLOCKED: file too large (max {self.max_file_size//1024}KB)"
            
        abs_path = os.path.abspath(os.path.expanduser(path))
        try:
            os.makedirs(os.path.dirname(abs_path) or '.', exist_ok=True)
            # Write with restrictive permissions (owner read/write only)
            fd = os.open(abs_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, 'w') as f:
                f.write(content)
            return f"Created: {os.path.relpath(abs_path, os.getcwd())} ({len(content)} bytes)"
        except Exception as e:
            return f"Error: {e}"

    def safe_execute(self, cmd: str, timeout: int = 120) -> str:
        if self.is_dangerous(cmd):
            return "BLOCKED: dangerous command rejected"
        # Input length validation to prevent DoS
        if len(cmd) > 10000:
            return "BLOCKED: command too long (max 10000 characters)"
            
        try:
            shell = ["cmd", "/c", cmd] if IS_WINDOWS else ["sh", "-c", cmd]
            import subprocess
            # Sanitize environment - remove dangerous vars
            safe_env = {k: v for k, v in os.environ.items()
                        if k not in ("LD_PRELOAD", "LD_LIBRARY_PATH", "DYLD_INSERT_LIBRARIES",
                                     "DYLD_LIBRARY_PATH", "PYTHONPATH", "BASH_ENV", "ENV")}
            r = subprocess.run(
                shell,
                capture_output=True, text=True, timeout=timeout,
                env={**safe_env, "PATH": os.environ.get("PATH", "/usr/bin:/bin")}
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