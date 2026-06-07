"""Tests for datetime utility functions."""

import pytest
from datetime import datetime, timedelta
from app.utils.datetime_utils import (
    format_datetime,
    format_date_only,
    time_since,
    parse_datetime,
)


class TestFormatDatetime:
    """Tests for format_datetime function."""

    def test_format_datetime_valid(self):
        """Test formatting valid datetime."""
        dt = datetime(2026, 5, 31, 14, 30, 45)
        result = format_datetime(dt)
        assert result == "2026-05-31 14:30:45"

    def test_format_datetime_midnight(self):
        """Test formatting datetime at midnight."""
        dt = datetime(2026, 1, 1, 0, 0, 0)
        result = format_datetime(dt)
        assert result == "2026-01-01 00:00:00"

    def test_format_datetime_none(self):
        """Test formatting None returns empty string."""
        result = format_datetime(None) # type: ignore
        assert result == ""

    def test_format_datetime_preserves_all_info(self):
        """Test that formatting preserves date and time."""
        dt = datetime(2025, 12, 25, 23, 59, 59)
        result = format_datetime(dt)
        assert "2025-12-25" in result
        assert "23:59:59" in result


class TestFormatDateOnly:
    """Tests for format_date_only function."""

    def test_format_date_only_valid(self):
        """Test formatting date only."""
        dt = datetime(2026, 5, 31, 14, 30, 45)
        result = format_date_only(dt)
        assert result == "2026-05-31"

    def test_format_date_only_ignores_time(self):
        """Test that time is ignored."""
        dt1 = datetime(2026, 5, 31, 0, 0, 0)
        dt2 = datetime(2026, 5, 31, 23, 59, 59)
        assert format_date_only(dt1) == format_date_only(dt2)

    def test_format_date_only_none(self):
        """Test formatting None returns empty string."""
        result = format_date_only(None) # type: ignore
        assert result == ""

    def test_format_date_only_various_dates(self):
        """Test various dates."""
        dates = [
            (datetime(2026, 1, 1), "2026-01-01"),
            (datetime(2026, 12, 31), "2026-12-31"),
            (datetime(2000, 2, 29), "2000-02-29"),  # Leap year
        ]
        for dt, expected in dates:
            assert format_date_only(dt) == expected


class TestTimeSince:
    """Tests for time_since function."""

    def test_time_since_none(self):
        """Test with None returns empty string."""
        result = time_since(None) # type: ignore
        assert result == ""

    def test_time_since_just_now(self):
        """Test very recent datetime (< 1 minute)."""
        dt = datetime.now() - timedelta(seconds=30)
        result = time_since(dt)
        assert result == "just now"

    def test_time_since_one_minute_ago(self):
        """Test 1 minute ago."""
        dt = datetime.now() - timedelta(minutes=1)
        result = time_since(dt)
        assert "minute" in result

    def test_time_since_multiple_minutes_ago(self):
        """Test multiple minutes ago."""
        dt = datetime.now() - timedelta(minutes=30)
        result = time_since(dt)
        assert "30 minutes ago" == result

    def test_time_since_one_hour_ago(self):
        """Test 1 hour ago."""
        dt = datetime.now() - timedelta(hours=1)
        result = time_since(dt)
        assert result == "1 hour ago"

    def test_time_since_multiple_hours_ago(self):
        """Test multiple hours ago."""
        dt = datetime.now() - timedelta(hours=5)
        result = time_since(dt)
        assert "5 hours ago" == result

    def test_time_since_one_day_ago(self):
        """Test 1 day ago."""
        dt = datetime.now() - timedelta(days=1)
        result = time_since(dt)
        assert result == "1 day ago"

    def test_time_since_multiple_days_ago(self):
        """Test multiple days ago."""
        dt = datetime.now() - timedelta(days=5)
        result = time_since(dt)
        assert "5 days ago" == result

    def test_time_since_one_week_ago(self):
        """Test 7 days ago."""
        dt = datetime.now() - timedelta(days=7)
        result = time_since(dt)
        assert result == "7 days ago" or "1 week ago"

    def test_time_since_multiple_weeks_ago(self):
        """Test multiple weeks ago."""
        dt = datetime.now() - timedelta(days=30)
        result = time_since(dt)
        assert "week" in result

    def test_time_since_plural_forms(self):
        """Test plural forms are correct."""
        # 1 minute (singular)
        dt1 = datetime.now() - timedelta(minutes=1)
        result1 = time_since(dt1)
        assert "1 minute ago" == result1

        # 2 minutes (plural)
        dt2 = datetime.now() - timedelta(minutes=2)
        result2 = time_since(dt2)
        assert "2 minutes ago" == result2

    def test_time_since_edge_cases(self):
        """Test edge case timings."""
        # 59 seconds (should be "just now")
        dt = datetime.now() - timedelta(seconds=59)
        result = time_since(dt)
        assert "just now" == result

        # 60 seconds (should be 1 minute)
        dt = datetime.now() - timedelta(seconds=60)
        result = time_since(dt)
        assert "1 minute ago" == result


class TestParseDatetime:
    """Tests for parse_datetime function."""

    def test_parse_datetime_valid(self):
        """Test parsing valid datetime string."""
        result = parse_datetime("2026-05-31 14:30:45")
        assert result.year == 2026
        assert result.month == 5
        assert result.day == 31
        assert result.hour == 14
        assert result.minute == 30
        assert result.second == 45

    def test_parse_datetime_valid_midnight(self):
        """Test parsing midnight."""
        result = parse_datetime("2026-01-01 00:00:00")
        assert result == datetime(2026, 1, 1, 0, 0, 0)

    def test_parse_datetime_invalid_format(self):
        """Test parsing invalid format raises ValueError."""
        with pytest.raises(ValueError):
            parse_datetime("2026/05/31 14:30:45")

    def test_parse_datetime_invalid_date(self):
        """Test parsing invalid date raises ValueError."""
        with pytest.raises(ValueError):
            parse_datetime("2026-13-01 14:30:45")  # Month 13

    def test_parse_datetime_missing_time(self):
        """Test parsing without time raises ValueError."""
        with pytest.raises(ValueError):
            parse_datetime("2026-05-31")

    def test_parse_datetime_roundtrip(self):
        """Test format and parse roundtrip."""
        original = datetime(2026, 5, 31, 14, 30, 45)
        formatted = format_datetime(original)
        parsed = parse_datetime(formatted)
        assert parsed == original

    def test_parse_datetime_error_message(self):
        """Test error message includes invalid string."""
        with pytest.raises(ValueError) as exc_info:
            parse_datetime("invalid")
        assert "invalid" in str(exc_info.value)


class TestDatetimeIntegration:
    """Integration tests combining multiple functions."""

    def test_format_and_parse_roundtrip(self):
        """Test complete roundtrip: datetime -> format -> parse -> datetime."""
        original = datetime(2026, 3, 15, 10, 45, 30)

        formatted = format_datetime(original)
        parsed = parse_datetime(formatted)

        assert parsed == original

    def test_time_since_consistent_with_now(self):
        """Test time_since is consistent with current time."""
        now = datetime.now()
        result = time_since(now)
        assert result == "just now"

    def test_multiple_format_functions(self):
        """Test using multiple format functions on same datetime."""
        dt = datetime(2026, 5, 31, 14, 30, 45)

        full = format_datetime(dt)
        date_only = format_date_only(dt)

        assert "14:30:45" in full
        assert "14:30:45" not in date_only
        assert full.startswith(date_only)
