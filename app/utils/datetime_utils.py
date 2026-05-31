"""Datetime utilities for formatting and parsing."""

from datetime import datetime, timedelta


def format_datetime(dt: datetime) -> str:
    """
    Format datetime to readable string (ISO format with time).

    Args:
        dt: Datetime to format

    Returns:
        Formatted string like "2026-05-31 14:30:45"
    """
    if dt is None:
        return ""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_date_only(dt: datetime) -> str:
    """
    Format datetime to date only.

    Args:
        dt: Datetime to format

    Returns:
        Formatted string like "2026-05-31"
    """
    if dt is None:
        return ""
    return dt.strftime("%Y-%m-%d")


def time_since(dt: datetime) -> str:
    """
    Calculate human-readable time since datetime (e.g., "2 hours ago").

    Args:
        dt: Datetime to compare to now

    Returns:
        String like "2 hours ago", "just now", "3 days ago"
    """
    if dt is None:
        return ""

    now = datetime.now()
    diff = now - dt

    if diff < timedelta(seconds=60):
        return "just now"
    elif diff < timedelta(minutes=60):
        mins = int(diff.total_seconds() / 60)
        return f"{mins} minute{'s' if mins != 1 else ''} ago"
    elif diff < timedelta(hours=24):
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff < timedelta(days=30):
        days = diff.days
        return f"{days} day{'s' if days != 1 else ''} ago"
    else:
        weeks = diff.days // 7
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"


def parse_datetime(dt_str: str) -> datetime:
    """
    Parse datetime string in ISO format.

    Args:
        dt_str: String like "2026-05-31 14:30:45"

    Returns:
        Parsed datetime object

    Raises:
        ValueError: If string format is invalid
    """
    try:
        return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    except ValueError as e:
        raise ValueError(f"Invalid datetime format: {dt_str}") from e
