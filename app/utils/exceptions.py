"""Custom exceptions for SafePy application."""


class SafePyException(Exception):
    """Base exception for SafePy."""
    pass


class FileParseError(SafePyException):
    """Raised when file parsing fails."""
    pass


class InvalidFileError(SafePyException):
    """Raised when file format is invalid."""
    pass


class OSVClientError(SafePyException):
    """Raised when OSV API communication fails."""
    pass


class OSVConnectionError(OSVClientError):
    """Raised when connection to OSV fails."""
    pass


class OSVTimeoutError(OSVClientError):
    """Raised when OSV request times out."""
    pass


class DatabaseError(SafePyException):
    """Raised when database operation fails."""
    pass


class AnalysisError(SafePyException):
    """Raised when analysis execution fails."""
    pass
