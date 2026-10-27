"""Timezone and datetime utilities for DST-safe London / UTC operations."""

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

LONDON_TZ = ZoneInfo("Europe/London")
UTC_TZ = UTC


def parse_iso_utc(iso_str: str) -> datetime:
    """Parse an ISO-8601 timestamp string into a timezone-aware UTC datetime."""
    clean_str = iso_str.strip().replace("Z", "+00:00")
    dt = datetime.fromisoformat(clean_str)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC_TZ)
    return dt.astimezone(UTC_TZ)


def format_iso_utc(dt: datetime) -> str:
    """Format a datetime to standard ISO-8601 UTC string ending in 'Z'."""
    utc_dt = dt.astimezone(UTC_TZ) if dt.tzinfo else dt.replace(tzinfo=UTC_TZ)
    return utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_cutoff_time(cutoff_str: str) -> tuple[int, int]:
    """Parse 'HH:MM' string into hour and minute integers with validation."""
    parts = cutoff_str.strip().split(":")
    if len(parts) != 2:
        raise ValueError(f"Invalid cutoff format '{cutoff_str}'. Expected 'HH:MM'.")
    hour = int(parts[0])
    minute = int(parts[1])
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError(f"Cutoff '{cutoff_str}' out of range [00:00 - 23:59].")
    return hour, minute


def get_decision_cutoff_utc(delivery_date: date, cutoff_str: str = "09:00") -> datetime:
    """
    Calculate the exact decision cutoff moment in UTC for a given delivery date.
    
    The decision day is D-1. The cutoff time (e.g., 09:00) is specified in Europe/London time.
    This function handles GMT and BST transitions safely and returns the equivalent UTC datetime.
    """
    decision_date = delivery_date - timedelta(days=1)
    hour, minute = parse_cutoff_time(cutoff_str)
    
    # Construct naive time on D-1, localize to Europe/London
    naive_dt = datetime.combine(decision_date, time(hour, minute, 0))
    london_dt = naive_dt.replace(tzinfo=LONDON_TZ)
    
    # Convert directly to UTC
    return london_dt.astimezone(UTC_TZ)


def to_london_display(utc_dt: datetime) -> str:
    """Convert a UTC datetime to a formatted string in Europe/London time."""
    london_dt = utc_dt.astimezone(LONDON_TZ)
    return london_dt.strftime("%Y-%m-%d %H:%M %Z")
