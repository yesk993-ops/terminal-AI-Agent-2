"""Tests for security module."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from security import SecurityManager


def _sm(**kw):
    return SecurityManager(
        allowed_dirs=kw.get("allowed_dirs", []),
        max_file_size=kw.get("max_file_size", 1024),
        dangerous_commands=kw.get("dangerous_commands", ["rm -rf", "shutdown", "reboot", "mkfs", "dd if="])
    )


def test_is_dangerous_blocks_rm_rf():
    sm = _sm()
    assert sm.is_dangerous("rm -rf /")


def test_is_dangerous_blocks_shutdown():
    sm = _sm()
    assert sm.is_dangerous("shutdown -h now")


def test_is_dangerous_blocks_reboot():
    sm = _sm()
    assert sm.is_dangerous("reboot")


def test_is_dangerous_blocks_mkfs():
    sm = _sm()
    assert sm.is_dangerous("mkfs.ext4 /dev/sda")


def test_is_dangerous_blocks_dd():
    sm = _sm()
    assert sm.is_dangerous("dd if=/dev/zero of=/dev/sda")


def test_is_dangerous_allows_safe():
    sm = _sm()
    assert not sm.is_dangerous("ls -la")
    assert not sm.is_dangerous("echo hello")
    assert not sm.is_dangerous("df -h")


def test_is_safe_path_allows_allowed():
    sm = _sm(allowed_dirs=["/tmp/test"])
    assert sm.is_safe_path("/tmp/test/foo.txt")


def test_is_safe_path_blocks_unauthorized():
    sm = _sm(allowed_dirs=["/tmp/test"])
    assert not sm.is_safe_path("/etc/passwd")
