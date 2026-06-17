"""Tests for query analyzer."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.analyzer import analyze, get_max_tokens


def test_analyze_simple_query():
    result = analyze("what is the weather")
    assert result["level"] == "simple"
    assert result["score"] <= 3


def test_analyze_coding_query():
    result = analyze("write a python script to sort files")
    assert result["level"] in ("medium", "complex")
    assert result["score"] > 0


def test_analyze_complex_query():
    result = analyze("compare the time complexity of quicksort vs mergesort and implement both in python with test cases")
    assert result["level"] == "complex"


def test_analyze_technical():
    result = analyze("compare the cap theorem with acid properties in distributed database design")
    assert result["level"] == "complex"


def test_get_max_tokens():
    assert get_max_tokens("simple") > 0
    assert get_max_tokens("medium") > get_max_tokens("simple")
    assert get_max_tokens("complex") > get_max_tokens("medium")
