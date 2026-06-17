"""Response cache with TTL-based eviction for repeated queries."""
import json
import time
from pathlib import Path
from typing import Optional, Any


class ResponseCache:
    def __init__(self, config: Any):
        self.config = config
        self._cache_file = Path(".tell_cache.json")

    def get(self, query: str) -> Optional[str]:
        if not self._cache_file.exists():
            return None
        try:
            with open(self._cache_file, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            if query in cache:
                item = cache[query]
                ttl = self.config.get("performance.cache_ttl", 3600)
                if time.time() - item["timestamp"] < ttl:
                    return item["response"]
        except (KeyError, json.JSONDecodeError, OSError):
            pass
        return None

    def set(self, query: str, response: str) -> None:
        try:
            cache_data = {}
            if self._cache_file.exists():
                with open(self._cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
            cache_data[query] = {
                "response": response,
                "timestamp": time.time()
            }
            with open(self._cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)
        except (OSError, json.JSONDecodeError):
            pass

    def evict(self) -> None:
        if not self._cache_file.exists():
            return
        try:
            with open(self._cache_file, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            ttl = self.config.get("performance.cache_ttl", 3600)
            now = time.time()
            expired = [k for k, v in cache.items() if now - v.get("timestamp", 0) > ttl]
            for k in expired:
                del cache[k]
            if expired:
                with open(self._cache_file, 'w', encoding='utf-8') as f:
                    json.dump(cache, f, indent=2)
        except (KeyError, json.JSONDecodeError, OSError):
            pass
