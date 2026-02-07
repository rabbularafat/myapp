"""
Tests for version utilities
"""
import pytest
from myapp.version_utils import (
    parse_version,
    compare_versions,
    is_update_available,
    format_version,
)


class TestParseVersion:
    """Tests for parse_version function."""
    
    def test_simple_version(self):
        assert parse_version("1.0.0") == (1, 0, 0, 0)
    
    def test_version_with_release(self):
        assert parse_version("1.0.0-1") == (1, 0, 0, 1)
        assert parse_version("1.2.3-10") == (1, 2, 3, 10)
    
    def test_version_with_v_prefix(self):
        assert parse_version("v1.0.0") == (1, 0, 0, 0)
        assert parse_version("v1.0.0-1") == (1, 0, 0, 1)
    
    def test_version_with_whitespace(self):
        assert parse_version("  1.0.0  ") == (1, 0, 0, 0)
        assert parse_version("\n1.0.0-1\n") == (1, 0, 0, 1)


class TestCompareVersions:
    """Tests for compare_versions function."""
    
    def test_equal_versions(self):
        assert compare_versions("1.0.0", "1.0.0") == 0
        assert compare_versions("1.0.0-1", "1.0.0-1") == 0
    
    def test_current_less_than_latest(self):
        assert compare_versions("1.0.0", "1.0.1") == -1
        assert compare_versions("1.0.0", "1.1.0") == -1
        assert compare_versions("1.0.0", "2.0.0") == -1
        assert compare_versions("1.0.0", "1.0.0-1") == -1
    
    def test_current_greater_than_latest(self):
        assert compare_versions("1.0.1", "1.0.0") == 1
        assert compare_versions("1.1.0", "1.0.0") == 1
        assert compare_versions("2.0.0", "1.0.0") == 1
        assert compare_versions("1.0.0-2", "1.0.0-1") == 1


class TestIsUpdateAvailable:
    """Tests for is_update_available function."""
    
    def test_update_available(self):
        assert is_update_available("1.0.0", "1.0.1") is True
        assert is_update_available("1.0.0", "2.0.0") is True
        assert is_update_available("1.0.0-1", "1.0.0-2") is True
    
    def test_no_update(self):
        assert is_update_available("1.0.0", "1.0.0") is False
        assert is_update_available("1.0.1", "1.0.0") is False
        assert is_update_available("2.0.0", "1.9.9") is False


class TestFormatVersion:
    """Tests for format_version function."""
    
    def test_simple_format(self):
        assert format_version(1, 0, 0) == "1.0.0"
        assert format_version(1, 2, 3) == "1.2.3"
    
    def test_format_with_release(self):
        assert format_version(1, 0, 0, 1) == "1.0.0-1"
        assert format_version(1, 2, 3, 10) == "1.2.3-10"
