"""Tests for commands module."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from commands import LocalCommands


class FakeSecurity:
    def is_dangerous(self, cmd):
        return False
    def is_safe_path(self, path):
        return True
    def safe_execute(self, cmd):
        return cmd, f"executed: {cmd}"


class FakeAPI:
    def generate_response(self, messages, **kw):
        return "AI response"


def test_detect_local_disk():
    lc = LocalCommands(FakeSecurity(), FakeAPI())
    assert lc.detect_local("disk") is not None


def test_detect_local_memory():
    lc = LocalCommands(FakeSecurity(), FakeAPI())
    assert lc.detect_local("do memory") is not None
    result = lc.detect_local("do memory")
    if callable(result):
        out = result()
        assert "RAM" in out or "Mem" in out or "memory" in out.lower()


def test_detect_local_returns_none_for_unknown():
    lc = LocalCommands(FakeSecurity(), FakeAPI())
    assert lc.detect_local("how to use agentshield to scan any directory on linux") is None


def test_detect_local_short_scan():
    lc = LocalCommands(FakeSecurity(), FakeAPI())
    assert lc.detect_local("scan") is not None


def test_detect_local_phrase_disk_usage():
    lc = LocalCommands(FakeSecurity(), FakeAPI())
    assert lc.detect_local("check disk usage") is not None
