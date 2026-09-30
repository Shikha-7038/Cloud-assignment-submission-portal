"""
Time helpers. RULE: all timestamps are stored and compared in UTC, and the
"now" used for deadline decisions ALWAYS comes from the server clock,
never from the browser (a student could change their computer's clock to
dodge a late flag).

Timestamps are stored as fixed-width ISO-8601 UTC strings, so they also sort
correctly as plain text in both SQLite and PostgreSQL.
"""
from datetime import datetime, timezone

ISO_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:               # naive value -> assume it is already UTC
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def to_iso(dt: datetime) -> str:
    return ensure_utc(dt).strftime(ISO_FMT)


def parse_dt(value) -> datetime:
    if isinstance(value, datetime):
        return ensure_utc(value)
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    return ensure_utc(datetime.fromisoformat(text))


def is_late(submitted_at, deadline) -> bool:
    """Deadline rule: on time if submitted_at <= deadline, else late."""
    return parse_dt(submitted_at) > parse_dt(deadline)
