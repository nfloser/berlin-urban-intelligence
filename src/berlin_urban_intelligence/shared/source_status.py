"""Runtime source status kept separately from static source metadata."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict, model_validator

from berlin_urban_intelligence.shared.contracts import AvailabilityStatus, FreshnessStatus
from berlin_urban_intelligence.shared.temporal import classify_freshness


class SourceRuntimeStatus(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    source_id: str
    availability: AvailabilityStatus
    freshness: FreshnessStatus
    last_retrieval_attempt: datetime | None = None
    last_successful_retrieval: datetime | None = None
    latest_observation_time: datetime | None = None
    error_code: str | None = None

    @model_validator(mode="after")
    def normalise_times(self) -> "SourceRuntimeStatus":
        for field in ("last_retrieval_attempt", "last_successful_retrieval", "latest_observation_time"):
            value = getattr(self, field)
            if value is None:
                continue
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError(f"{field} must be timezone-aware")
            object.__setattr__(self, field, value.astimezone(UTC))
        return self


class SourceStatusStore:
    def __init__(self, initial: Mapping[str, SourceRuntimeStatus] | None = None) -> None:
        self._state: dict[str, dict[str, Any]] = {}
        for source_id, status in (initial or {}).items():
            self._state[source_id] = {
                "availability": status.availability,
                "last_retrieval_attempt": status.last_retrieval_attempt,
                "last_successful_retrieval": status.last_successful_retrieval,
                "latest_observation_time": status.latest_observation_time,
                "error_code": status.error_code,
            }

    @staticmethod
    def _utc(value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("source status timestamps must be timezone-aware")
        return value.astimezone(UTC)

    def record_success(self, source_id: str, *, retrieved_at: datetime, observation_time: datetime | None) -> None:
        retrieved = self._utc(retrieved_at)
        observed = self._utc(observation_time) if observation_time is not None else None
        self._state[source_id] = {
            "availability": AvailabilityStatus.AVAILABLE,
            "last_retrieval_attempt": retrieved,
            "last_successful_retrieval": retrieved,
            "latest_observation_time": observed,
            "error_code": None,
        }

    def record_failure(self, source_id: str, *, checked_at: datetime, error_code: str) -> None:
        checked = self._utc(checked_at)
        current = self._state.setdefault(source_id, {"last_successful_retrieval": None, "latest_observation_time": None})
        current.update(availability=AvailabilityStatus.UNAVAILABLE, last_retrieval_attempt=checked, error_code=error_code)

    def get(self, source_id: str, *, now: datetime, freshness_threshold: timedelta) -> SourceRuntimeStatus:
        current = self._state.get(source_id)
        if current is None:
            return SourceRuntimeStatus(source_id=source_id, availability=AvailabilityStatus.UNKNOWN, freshness=FreshnessStatus.UNKNOWN)
        observed = current.get("latest_observation_time")
        freshness = classify_freshness(observed, now=now, threshold=freshness_threshold) if isinstance(observed, datetime) else FreshnessStatus.UNKNOWN
        return SourceRuntimeStatus(
            source_id=source_id,
            availability=current.get("availability", AvailabilityStatus.UNKNOWN),
            freshness=freshness,
            last_retrieval_attempt=current.get("last_retrieval_attempt"),
            last_successful_retrieval=current.get("last_successful_retrieval"),
            latest_observation_time=observed,
            error_code=current.get("error_code"),
        )
