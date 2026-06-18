"""Configuration loader for .tellrc with env var overrides."""
import os
import json
from typing import Dict, Any, List, Optional

from api import PROVIDER_REGISTRY

class TellConfig:
    """Configuration loader for .tellrc with env var overrides."""

    def __init__(self, config_path: str = ".tellrc"):
        self.config_path = os.path.expanduser(config_path)
        self.data = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        models = {}
        for pname, pconf in PROVIDER_REGISTRY.items():
            models[pname] = {
                "query": list(pconf.get("default_models", [])),
                "system": list(pconf.get("default_models", [])),
            }
        return {
            "providers": ["nvidia"],
            "models": models,
            "security": {
                "allowed_write_dirs": [os.getcwd()],
                "max_file_size": 1024 * 1024,
                "dangerous_commands": [
                    "rm -rf /", "rm -rf /*", "mkfs", "dd if=", ":(){", "> /dev/sda",
                    "> /dev/sdb", "format /dev", "mkfs.", "mkswap", "shutdown",
                    "reboot", "poweroff", "halt", "init 0", "init 6", "chmod 777 /",
                    "chmod 777 /*", "chown ", "passwd", "useradd", "userdel",
                    "usermod", "groupadd", "groupdel",
                    "format c:", "format c:\\", "del /f /s", "rd /s /q",
                    "diskpart", "reg delete", "net user", "sc delete",
                ]
            },
            "ui": {
                "border_style": "minimal",
                "theme": "eye-friendly",
                "themes": {
                    "eye-friendly": {
                        "border": 102,
                        "text": 188,
                        "prompt": 130,
                        "accent": 107,
                        "bold": 107
                    },
                    "warm": {
                        "border": 130,
                        "text": 180,
                        "prompt": 173,
                        "accent": 179,
                        "bold": 179
                    },
                    "cool": {
                        "border": 37,
                        "text": 153,
                        "prompt": 39,
                        "accent": 33,
                        "bold": 39
                    },
                    "default": {
                        "border": 93,
                        "text": 97,
                        "prompt": 94,
                        "accent": 96,
                        "bold": 96
                    }
                }
            },
            "performance": {
                "enable_caching": True,
                "cache_ttl": 3600,
                "max_retries": 2,
                "timeout": 15
            },
            "behavior": {
                "enable_command_history": True,
                "max_history_size": 100,
                "auto_install_deps": True
            }
        }

    def save(self) -> bool:
        """Write config to disk. Returns True on success."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2)
            return True
        except OSError:
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """Get config value by dot-separated key with optional default."""
        keys = key.split('.')
        value = self.data
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: Any) -> None:
        keys = key.split('.')
        target = self.data
        for _, k in enumerate(keys[:-1]):
            if k not in target:
                target[k] = {}
            target = target[k]
        target[keys[-1]] = value

    def update_from_env(self) -> None:
        for pname, pconf in PROVIDER_REGISTRY.items():
            env_val = os.environ.get(pconf["env_model"])
            if env_val:
                models = [m.strip() for m in env_val.split(",") if m.strip()]
                self.set(f"models.{pname}.query", models)
                self.set(f"models.{pname}.system", models)

        tell_border = os.environ.get("TELL_BORDER")
        if tell_border:
            self.set("ui.border_style", tell_border)
