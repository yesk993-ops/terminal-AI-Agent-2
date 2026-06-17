"""Tests for response cache."""
import sys
import os
import json
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.cache import ResponseCache


class FakeConfig:
    def get(self, key, default=None):
        if key == "performance.cache_ttl":
            return 1  # 1 second TTL for testing
        return default


def test_cache_set_and_get():
    cache = ResponseCache(FakeConfig())
    cache.set("test query", "test response")
    result = cache.get("test query")
    assert result == "test response"
    # cleanup
    if cache._cache_file.exists():
        cache._cache_file.unlink()


def test_cache_expiry():
    cache = ResponseCache(FakeConfig())
    cache.set("expire query", "expire response")
    time.sleep(1.1)
    result = cache.get("expire query")
    assert result is None
    # cleanup
    if cache._cache_file.exists():
        cache._cache_file.unlink()


def test_cache_evict():
    cache = ResponseCache(FakeConfig())
    cache.set("evict query", "evict response")
    cache.evict()
    result = cache.get("evict query")
    # Should be evicted since TTL is 1s and it was just set... actually
    # evict() removes expired entries and the entry was just set, so it shouldn't be expired yet.
    assert result == "evict response"
    # cleanup
    if cache._cache_file.exists():
        cache._cache_file.unlink()
