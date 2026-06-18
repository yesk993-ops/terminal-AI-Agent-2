"""Security manager — path validation, dangerous command detection, safe execution."""
import os
import re
import subprocess
import platform
from typing import List, Dict, Any
from pathlib import Path

IS_WINDOWS = platform.system() == "Windows"

class SecurityManager:
    """Path validation, dangerous command blocking, safe execution."""

    def __init__(self, allowed_dirs: List[str], max_file_size: int, dangerous_commands: List[str]):
        self.allowed_dirs = [os.path.abspath(d) for d in allowed_dirs]
        self.max_file_size = max_file_size
        self.dangerous_commands = dangerous_commands

    def is_safe_path(self, path: str) -> bool:
        """Check if path is within allowed write directories."""
        try:
            abs_path = os.path.abspath(os.path.expanduser(path))
            real_path = os.path.realpath(abs_path)
            for allowed in self.allowed_dirs:
                allowed_real = os.path.realpath(os.path.abspath(allowed))
                if real_path.startswith(allowed_real + os.sep) or real_path == allowed_real:
                    return True
            return False
        except (OSError, AttributeError):
            return False

    def is_dangerous(self, cmd: str) -> bool:
        cmd_lower = cmd.lower().strip()
        cmd_normalized = re.sub(r'\s+', ' ', cmd_lower)

        for d in self.dangerous_commands:
            if d in cmd_normalized:
                return True

        dangerous_patterns = [
            r'\brm\s+-[a-z]*r[a-z]*f',
            r'\brm\s+-[a-z]*f[a-z]*r',
            r'\bdd\s+if=',
            r'\bmkfs\b',
            r'>\s*/dev/sd',
            r'\bshutdown\b',
            r'\breboot\b',
            r'\bchmod\s+777',
            r'\bcurl\b.*\|\s*bash',
            r'\bwget\b.*\|\s*bash',
            r'\beval\b',
            r'\bexec\b',
            r'\bsudo\b',
            r'\bpython\s+-c',
            r'\bpython3\s+-c',
            r'base64\s+-d',
            r'openssl\s+enc',
            r'\\x[0-9a-f]{2}.*\\x[0-9a-f]{2}',
            r'\$\(.*\)',
            r'`.*`',
        ]
        for pattern in dangerous_patterns:
            if re.search(pattern, cmd_normalized):
                return True
        return False

    def safe_write(self, path: str, content: str) -> str:
        abs_path = os.path.realpath(os.path.abspath(os.path.expanduser(path)))
        if not self.is_safe_path(abs_path):
            return f"BLOCKED: cannot write outside allowed directories"
        if len(path) > 1000:
            return "BLOCKED: path too long (max 1000 characters)"
        if len(content) > self.max_file_size:
            return f"BLOCKED: file too large (max {self.max_file_size//1024}KB)"

        try:
            os.makedirs(os.path.dirname(abs_path) or '.', exist_ok=True)
            fd = os.open(abs_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, 'w') as f:
                f.write(content)
            return f"Created: {os.path.relpath(abs_path, os.getcwd())} ({len(content)} bytes)"
        except OSError:
            return "Error: write failed"

    SENSITIVE_PATTERNS = [
        (r'(?i)-----BEGIN\s+(?:RSA\s+)?(?:DSA\s+)?(?:EC\s+)?(?:OPENSSH\s+)?(?:PRIVATE\s+)?KEY-----', '-----BEGIN PRIVATE KEY-----'),
        (r'(nvapi-[a-zA-Z0-9_-]{20,})', 'nvapi-***'),
        (r'(sk-or-v1-[a-zA-Z0-9]{20,})', 'sk-or-v1-***'),
        (r'(ghp_[a-zA-Z0-9]{20,})', 'ghp_***'),
        (r'(gho_[a-zA-Z0-9]{20,})', 'gho_***'),
        (r'(ghu_[a-zA-Z0-9]{20,})', 'ghu_***'),
        (r'(ghs_[a-zA-Z0-9]{20,})', 'ghs_***'),
        (r'(ghr_[a-zA-Z0-9]{20,})', 'ghr_***'),
        (r'(AKIA[0-9A-Z]{16})', 'AKIA***'),
        (r'(sk-[a-zA-Z0-9]{20,})', 'sk-***'),
    ]

    @staticmethod
    def sanitize_output(text: str) -> str:
        for pattern, replacement in SecurityManager.SENSITIVE_PATTERNS:
            text = re.sub(pattern, replacement, text)
        return text

    def safe_execute(self, cmd: str, timeout: int = 120) -> str:
        if self.is_dangerous(cmd):
            return "BLOCKED: dangerous command rejected"
        # Input length validation to prevent DoS
        if len(cmd) > 10000:
            return "BLOCKED: command too long (max 10000 characters)"

        try:
            shell = ["cmd", "/c", cmd] if IS_WINDOWS else ["sh", "-c", cmd]
            # Sanitize environment - remove dangerous vars
            safe_env = {k: v for k, v in os.environ.items()
                        if k not in ("LD_PRELOAD", "LD_LIBRARY_PATH", "DYLD_INSERT_LIBRARIES",
                                     "DYLD_LIBRARY_PATH", "PYTHONPATH", "BASH_ENV", "ENV")}
            r = subprocess.run(
                shell,
                capture_output=True, text=True, timeout=timeout,
                env={**safe_env, "PATH": os.environ.get("PATH", "/usr/bin:/bin")},
                check=False
            )
            out = r.stdout
            if r.stderr:
                out += "\n" + r.stderr
            result = self.sanitize_output(out.strip()[:20000]) or "OK"
            if r.returncode != 0:
                result += f"\n[Exit code: {r.returncode}]"
            return result
        except subprocess.TimeoutExpired:
            return "Command timed out [Exit code: -1]"
        except OSError as e:
            return f"Error: {e} [Exit code: -2]"
