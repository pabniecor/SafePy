"""Domain enumerations."""

from enum import Enum


class Ecosystem(str, Enum):
    """Package ecosystem types."""
    PYPI = "PyPI"
    NPM = "npm"
    GIT = "GIT"


class AnalysisStatus(str, Enum):
    """Analysis execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class VulnerabilitySeverity(str, Enum):
    """Vulnerability severity level."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
