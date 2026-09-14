"""Temporal utilities with explicit timezone and freshness semantics."""

from datetime import UTC, datetime, timedelta

from berlin_urban_intelligence.shared.contracts import FreshnessStatus


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("datetime must be timezone-aware")
    return value.astimezone(UTC)


def classify_freshness(
    observed_at: datetime | None, now: datetime, threshold: timedelta
) -> FreshnessStatus:
    if observed_at is None:
        return FreshnessStatus.UNAVAILABLE
    observed = ensure_utc(observed_at)
    current = ensure_utc(now)
    if observed > current:
        return FreshnessStatus.UNKNOWN
    return FreshnessStatus.VALID if current - observed <= threshold else FreshnessStatus.STALE
