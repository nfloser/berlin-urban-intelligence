"""Mobility agent with explicit realtime absence semantics."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta

from pydantic import BaseModel, ConfigDict, Field

from berlin_urban_intelligence.agents.base import BaseAgent
from berlin_urban_intelligence.shared.contracts import (
    AgentDescriptor,
    AgentHealth,
    AvailabilityStatus,
    FreshnessStatus,
    QualityFlag,
)
from berlin_urban_intelligence.shared.temporal import classify_freshness, ensure_utc


class TransitUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    trip_id: str
    delays_s: list[int] = Field(default_factory=list)


class MobilitySnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    observed_at: datetime
    retrieved_at: datetime
    trip_updates: int = Field(ge=0)
    delayed_trip_updates: int = Field(ge=0)
    max_abs_delay_s: int | None
    quality: QualityFlag
    note: str
    source: str = "VBB GTFS-Realtime"


class MobilityAgent(BaseAgent):
    descriptor = AgentDescriptor(
        id="mobility",
        version="0.1.0",
        description="Berlin mobility state from verified VBB sources with explicit realtime coverage semantics.",
        capabilities=("gtfs_realtime_summary", "mobility_state"),
        input_contracts=("TransitUpdate",),
        output_contracts=("MobilitySnapshot",),
        source_dependencies=("vbb_gtfs_rt", "vbb_gtfs_static"),
    )

    def __init__(
        self,
        snapshot: MobilitySnapshot | None = None,
        *,
        now_factory: Callable[[], datetime] | None = None,
    ) -> None:
        super().__init__(now_factory=now_factory)
        self._snapshot: MobilitySnapshot | None = snapshot

    @staticmethod
    def from_decoded_records(records: list[dict[str, object]]) -> list[TransitUpdate]:
        updates: list[TransitUpdate] = []
        for record in records:
            trip_id = str(record.get("trip_id") or "").strip()
            if not trip_id:
                continue
            delays_raw = record.get("delays_s")
            delays = [int(value) for value in delays_raw] if isinstance(delays_raw, list) else []
            updates.append(TransitUpdate(trip_id=trip_id, delays_s=delays))
        return updates

    def summarise_updates(
        self,
        updates: list[TransitUpdate],
        feed_timestamp: datetime,
        retrieved_at: datetime | None = None,
    ) -> MobilitySnapshot:
        observed = ensure_utc(feed_timestamp)
        retrieved = ensure_utc(retrieved_at or self.now())
        delayed = 0
        all_delays: list[int] = []
        for update in updates:
            nonzero = [delay for delay in update.delays_s if delay != 0]
            if nonzero:
                delayed += 1
                all_delays.extend(nonzero)
        if updates:
            quality = QualityFlag.VALID
            note = "Summary reflects trip updates present in the VBB GTFS-Realtime feed only."
        else:
            quality = QualityFlag.UNKNOWN
            note = "No trip updates were present; absence of realtime updates is not evidence of normal operation."
        snapshot = MobilitySnapshot(
            observed_at=observed,
            retrieved_at=retrieved,
            trip_updates=len(updates),
            delayed_trip_updates=delayed,
            max_abs_delay_s=max((abs(value) for value in all_delays), default=None),
            quality=quality,
            note=note,
        )
        self._snapshot = snapshot
        return snapshot

    def snapshot(self) -> MobilitySnapshot | None:
        return self._snapshot

    def health(self) -> AgentHealth:
        now = self.now()
        if self._snapshot is None:
            return self.unavailable_health("No VBB GTFS-Realtime snapshot has been ingested.")
        freshness = classify_freshness(self._snapshot.observed_at, now, timedelta(minutes=15))
        status = AvailabilityStatus.AVAILABLE
        if freshness != FreshnessStatus.VALID or self._snapshot.quality != QualityFlag.VALID:
            status = AvailabilityStatus.DEGRADED
        return AgentHealth(
            agent_id=self.descriptor.id,
            status=status,
            checked_at=now,
            freshness=freshness,
            quality=self._snapshot.quality,
            detail=self._snapshot.note,
        )
