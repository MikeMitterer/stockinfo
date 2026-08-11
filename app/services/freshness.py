"""Geteilte TTL-Frische-Prüfung für cachende Dienste."""

from datetime import datetime, timezone


def is_fresh(fetched_at: str, ttl_hours: int) -> bool:
    """Prüft, ob ein ISO-Zeitstempel jünger als die TTL (in Stunden) ist."""
    try:
        timestamp = datetime.fromisoformat(fetched_at)
    except ValueError:
        return False
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    age_seconds = (datetime.now(timezone.utc) - timestamp).total_seconds()
    return age_seconds < ttl_hours * 3600
