"""Local system commands — disk, memory, processes, file listing, and more."""
import os
import platform
import shutil
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, Tuple, Callable

import psutil

IS_WINDOWS = platform.system() == "Windows"

class LocalCommands:
    def __init__(self, security_manager, api_agent):
        self.security = security_manager
        self.api = api_agent
        self.command_map = self._initialize_commands()
        self.phrase_map = self._initialize_phrases()

    def _initialize_commands(self) -> Dict[str, Callable[[], str]]:
        return {
            "disk": self._cmd_disk,
            "memory": self._cmd_memory,
            "procs": self._cmd_procs,
            "ps": self._cmd_procs,
            "uptime": self._cmd_uptime,
            "whoami": lambda: self._safe_execute("whoami"),
            "date": self._cmd_date,
            "pwd": self._cmd_pwd,
            "ip": self._cmd_ip,
            "network": self._cmd_network,
            "netstat": self._cmd_ports,
            "ports": self._cmd_ports,
            "sysinfo": self._cmd_sysinfo,
            "services": self._cmd_services,
            "fw": self._cmd_fw,
            "firewall": self._cmd_fw,
            "updates": self._cmd_updates,
            "upgradable": self._cmd_updates,
            "users": self._cmd_users,
            "logins": self._cmd_logins,
            "scan": self._cmd_scan,
            "suid": self._cmd_suid,
            "security": self._cmd_security_scan,
            "ls": self._cmd_ls,
            "dir": self._cmd_ls,
            "files": self._cmd_ls,
        }

    def _initialize_phrases(self) -> Dict[str, str]:
        return {
            "disk usage": "disk",
            "disk space": "disk",
            "free space": "disk",
            "memory usage": "memory",
            "free memory": "memory",
            "running processes": "procs",
            "top processes": "procs",
            "system info": "sysinfo",
            "open ports": "ports",
            "listening ports": "ports",
            "running services": "services",
            "active services": "services",
            "firewall status": "fw",
            "firewall rules": "fw",
            "available updates": "updates",
            "pending updates": "updates",
            "logged in users": "users",
            "who is logged in": "users",
            "security scan": "security",
            "security check": "security",
            "suid files": "suid",
            "setuid files": "suid",
            "quick scan": "scan",
            "system scan": "scan",
            "list files": "ls",
            "files in": "ls",
            "current folder": "ls",
            "current directory": "ls",
            "directory listing": "ls",
            "what's here": "ls",
            "what is here": "ls",
            "show files": "ls",
            "folder contents": "ls",
        }

    def detect_local(self, query: str) -> Any:
        q = query.lower().strip().strip("?.")
        if q in self.command_map:
            return self.command_map[q]

        if q in ("exit", "quit", "clear", "reset", ""):
            return None

        words = set(q.split())

        # Check phrase matches first (more specific, safe for any query length)
        for phrase, key in self.phrase_map.items():
            if phrase in q:
                return self.command_map[key]

        # Keyword matches only for short queries (likely direct commands, not natural language)
        if len(words) <= 3:
            for kw, fn in self.command_map.items():
                if kw in words:
                    return fn

        return None

    def execute(self, query: str) -> Tuple[str, Any]:
        local = self.detect_local(query)
        if local:
            return ("local", local())

        result = self._safe_execute(query)
        if "BLOCKED" not in result and "[Exit code:" not in result:
            return ("shell", result)
        return ("ai", query)

    def _safe_execute(self, cmd: str, timeout: int = 120) -> str:
        return self.security.safe_execute(cmd, timeout)

    def _cmd_disk(self) -> str:
        if IS_WINDOWS:
            u = shutil.disk_usage("C:\\")
            return f"Disk Used: {u.used//(1024**3)}GB / {u.total//(1024**3)}GB ({u.used/u.total*100:.1f}%)"
        return self._safe_execute("df -h /")

    def _cmd_memory(self) -> str:
        m = psutil.virtual_memory()
        return f"RAM: {m.used//(1024**2)}MB / {m.total//(1024**2)}MB ({m.percent}%)"

    def _cmd_procs(self) -> str:
        if IS_WINDOWS:
            return self._safe_execute("tasklist")
        return self._safe_execute("ps aux --sort=-%cpu | head -10")

    def _cmd_uptime(self) -> str:
        if IS_WINDOWS:
            try:
                import datetime
                b = datetime.datetime.fromtimestamp(psutil.boot_time())
                d = datetime.datetime.now() - b
                return f"Up {d.days}d {d.seconds//3600}h {(d.seconds//60)%60}m"
            except (AttributeError, ImportError, ValueError):
                return self._safe_execute("wmic os get lastbootuptime")
        return self._safe_execute("uptime")

    def _cmd_date(self) -> str:
        if IS_WINDOWS:
            return self._safe_execute("echo %date% %time%")
        return self._safe_execute("date")

    def _cmd_ls(self) -> str:
        if IS_WINDOWS:
            return self._safe_execute("dir")
        return self._safe_execute("ls -la --color=never")

    def _cmd_pwd(self) -> str:
        if IS_WINDOWS:
            return os.getcwd()
        return self._safe_execute("pwd")

    def _cmd_ip(self) -> str:
        if IS_WINDOWS:
            return self._safe_execute("ipconfig | findstr IPv4")
        return self._safe_execute("ip addr | grep inet")

    def _cmd_network(self) -> str:
        if IS_WINDOWS:
            return self._safe_execute("ipconfig /all")
        return self._safe_execute("ip addr")

    def _cmd_ports(self) -> str:
        if IS_WINDOWS:
            return self._safe_execute("netstat -ano")
        return self._safe_execute("ss -tlnp")

    def _cmd_sysinfo(self) -> str:
        if IS_WINDOWS:
            return self._safe_execute("systeminfo | findstr /B /C:OS")
        return self._safe_execute("uname -a")

    def _cmd_services(self) -> str:
        if IS_WINDOWS:
            return self._safe_execute("sc query state= all | findstr SERVICE_NAME")
        return self._safe_execute("systemctl list-units --type=service --state=running 2>/dev/null | head -20")

    def _cmd_fw(self) -> str:
        if IS_WINDOWS:
            return self._safe_execute("netsh advfirewall show allprofiles")
        return self._safe_execute("(ufw status verbose 2>/dev/null || firewall-cmd --list-all 2>/dev/null); iptables -L -n 2>/dev/null | head -20; echo '---'")

    def _cmd_updates(self) -> str:
        if IS_WINDOWS:
            return self._safe_execute("winget upgrade 2>nul || echo 'winget not available'")
        return self._safe_execute("apt list --upgradable 2>/dev/null | head -20 || dnf check-update 2>/dev/null | head -20 || yum list updates 2>/dev/null | head -20 || echo 'no package manager found'")

    def _cmd_users(self) -> str:
        if IS_WINDOWS:
            return self._safe_execute("query user 2>nul || echo 'query user not available'")
        return self._safe_execute("who -u")

    def _cmd_logins(self) -> str:
        if IS_WINDOWS:
            return self._safe_execute("wevtutil qe Security /rd:true /f:text /c:5 /q:\"*[System[EventID=4624]]\" 2>nul || echo 'Event log access not available'")
        return self._safe_execute("last -10 2>/dev/null")

    def _cmd_scan(self) -> str:
        if IS_WINDOWS:
            return self._safe_execute("echo --- PORTS --- && netstat -ano && echo --- PROCS --- && tasklist && echo --- DISK --- && wmic logicaldisk get size,freespace,caption && echo --- MEM --- && wmic os get TotalVisibleMemorySize,FreePhysicalMemory")
        return self._safe_execute("echo '--- PORTS ---' && ss -tlnp 2>/dev/null && echo '--- TOP PROCS ---' && ps aux --sort=-%cpu | head -10 && echo '--- DISK ---' && df -h && echo '--- MEM ---' && free -h")

    def _cmd_suid(self) -> str:
        if IS_WINDOWS:
            return "N/A (not applicable on Windows)"
        return self._safe_execute("find /usr/bin /usr/sbin -perm -4000 -type f 2>/dev/null")

    def _cmd_security_scan(self) -> str:
        r = []
        if IS_WINDOWS:
            r.append("=== Open Ports ===")
            r.append(self._safe_execute("netstat -ano"))
            r.append("=== Running Services ===")
            r.append(self._safe_execute("sc query state= all | findstr SERVICE_NAME"))
            r.append("=== Firewall ===")
            r.append(self._safe_execute("netsh advfirewall show allprofiles"))
            r.append("=== Disk ===")
            r.append(self._safe_execute("wmic logicaldisk get size,freespace,caption"))
            r.append("=== Memory ===")
            r.append(self._safe_execute("wmic os get TotalVisibleMemorySize,FreePhysicalMemory"))
        else:
            r.append("=== Open Ports ===")
            r.append(self._safe_execute("ss -tlnp 2>/dev/null"))
            r.append("=== Running Services ===")
            r.append(self._safe_execute("systemctl list-units --type=service --state=running 2>/dev/null | head -15"))
            r.append("=== SUID Files ===")
            r.append(self._safe_execute("find /usr/bin /usr/sbin -perm -4000 -type f 2>/dev/null"))
            r.append("=== Firewall ===")
            r.append(self._safe_execute("ufw status 2>/dev/null || firewall-cmd --list-all 2>/dev/null || echo 'no firewall frontend'; iptables -L -n 2>/dev/null | head -10; echo '--- done ---'"))
            r.append("=== Failed Logins ===")
            r.append(self._safe_execute("lastb 2>/dev/null | head -5 || echo 'none'"))
            r.append("=== Disk ===")
            r.append(self._safe_execute("df -h /"))
            r.append("=== Memory ===")
            r.append(self._safe_execute("free -h"))
        return '\n'.join(r)

    def get_command_map(self) -> Dict[str, Callable]:
        return self.command_map