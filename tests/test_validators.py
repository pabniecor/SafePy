"""Tests for validators module."""

import pytest

from app.utils.validators import (
    is_valid_package_name,
    is_valid_version,
    parse_requirement_line,
    is_valid_requirement_line,
)


class TestPackageNameValidation:
    """Test package name validation."""

    def test_valid_simple_name(self):
        """Test valid simple package names."""
        assert is_valid_package_name("requests")
        assert is_valid_package_name("Django")
        assert is_valid_package_name("pytest")

    def test_valid_names_with_hyphens(self):
        """Test valid names with hyphens."""
        assert is_valid_package_name("python-dateutil")
        assert is_valid_package_name("flask-cors")

    def test_valid_names_with_underscores(self):
        """Test valid names with underscores."""
        assert is_valid_package_name("SQL_Alchemy")
        assert is_valid_package_name("Jinja_2")

    def test_valid_names_with_dots(self):
        """Test valid names with dots."""
        assert is_valid_package_name("zope.interface")

    def test_invalid_names(self):
        """Test invalid package names."""
        assert not is_valid_package_name("")
        assert not is_valid_package_name("-invalid")
        assert not is_valid_package_name("invalid-")
        assert not is_valid_package_name("@invalid")


class TestVersionValidation:
    """Test version string validation."""

    def test_valid_versions(self):
        """Test valid version strings."""
        assert is_valid_version("1.0.0")
        assert is_valid_version("2.3")
        assert is_valid_version("0.1.0a1")
        assert is_valid_version("3.0.0.post1")

    def test_invalid_versions(self):
        """Test invalid version strings."""
        assert not is_valid_version("")
        assert not is_valid_version("  ")
        assert not is_valid_version("abc")


class TestParseRequirementLine:
    """Test requirement line parsing."""

    def test_parse_equal_operator(self):
        """Test parsing with == operator."""
        result = parse_requirement_line("requests==2.28.0")
        assert result == ("requests", "==", "2.28.0")

    def test_parse_greater_equal_operator(self):
        """Test parsing with >= operator."""
        result = parse_requirement_line("django>=4.2")
        assert result == ("django", ">=", "4.2")

    def test_parse_tilde_operator(self):
        """Test parsing with ~= operator."""
        result = parse_requirement_line("flask~=2.0")
        assert result == ("flask", "~=", "2.0")

    def test_parse_less_than_operator(self):
        """Test parsing with < operator."""
        result = parse_requirement_line("pytest<8.0")
        assert result == ("pytest", "<", "8.0")

    def test_parse_with_whitespace(self):
        """Test parsing with extra whitespace."""
        result = parse_requirement_line("  requests  ==  2.28.0  ")
        assert result == ("requests", "==", "2.28.0")

    def test_parse_comment_line(self):
        """Test that comment lines return None."""
        result = parse_requirement_line("# This is a comment")
        assert result is None

    def test_parse_empty_line(self):
        """Test that empty lines return None."""
        assert parse_requirement_line("") is None
        assert parse_requirement_line("   ") is None

    def test_parse_invalid_format(self):
        """Test parsing invalid format."""
        assert parse_requirement_line("requests") is None
        assert parse_requirement_line("invalid format") is None
        assert parse_requirement_line("==2.0") is None

    def test_parse_invalid_package_name(self):
        """Test parsing with invalid package name."""
        result = parse_requirement_line("@invalid==1.0.0")
        assert result is None

    def test_parse_invalid_version(self):
        """Test parsing with invalid version."""
        result = parse_requirement_line("requests==invalid")
        assert result is None


class TestIsValidRequirementLine:
    """Test is_valid_requirement_line function."""

    def test_valid_lines(self):
        """Test valid requirement lines."""
        assert is_valid_requirement_line("requests==2.28.0")
        assert is_valid_requirement_line("django>=4.2")
        assert is_valid_requirement_line("  pytest~=7.0  ")

    def test_invalid_lines(self):
        """Test invalid requirement lines."""
        assert not is_valid_requirement_line("# comment")
        assert not is_valid_requirement_line("")
        assert not is_valid_requirement_line("requests")
        assert not is_valid_requirement_line("invalid format")
