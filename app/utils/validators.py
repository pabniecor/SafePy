"""Validation utilities for requirements parsing."""

import re
from typing import Optional, Tuple


def is_valid_package_name(name: str) -> bool:
    """Check if package name is valid (PEP 508)."""
    pattern = r"^[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?$"
    return bool(re.match(pattern, name.strip()))


def is_valid_version(version: str) -> bool:
    """Check if version string is valid."""
    if not version or not version.strip():
        return False
    pattern = r"^[0-9]+(\.[0-9]+)*([a-zA-Z0-9._\-]*)?$"
    return bool(re.match(pattern, version.strip()))


def parse_requirement_line(line: str) -> Optional[Tuple[str, str, str]]:
    """Parse requirement line into (name, operator, version).

    Returns None if line is invalid or empty.
    Supports operators: ==, >=, <=, ~=, >, <, !=
    Default operator: == if not specified
    """
    line = line.strip()

    if not line or line.startswith("#"):
        return None

    operators = ["~=", "==", ">=", "<=", "!=", ">", "<"]
    operator = "=="
    name = None
    version = None

    for op in operators:
        if op in line:
            parts = line.split(op, 1)
            if len(parts) == 2:
                name = parts[0].strip()
                version = parts[1].strip()
                operator = op
                break

    if not name or not version:
        return None

    if not is_valid_package_name(name):
        return None

    if not is_valid_version(version):
        return None

    return (name, operator, version)


def is_valid_requirement_line(line: str) -> bool:
    """Check if line is a valid requirement (not comment, not empty)."""
    return parse_requirement_line(line) is not None
