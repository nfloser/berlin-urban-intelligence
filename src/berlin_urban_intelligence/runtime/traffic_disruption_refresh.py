"""Source refresh and last-known-good handling for official Berlin VIZ disruptions."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from berlin_urban_intelligence.adapters.viz_road_disruptions import (
    VizRoadDisruptionAdapter,
    VizRoadDisruptionClient,
)
from berlin_urban_intelligence.runtime.traffic_disruptions import TrafficDisruptionState
from berlin_urban_intelligence.shared.contracts import FreshnessStatus

SOURCE_ID = "berlin_viz_road_disruptions"


class TrafficDisruptionRefreshCoordinator:
    """Acquire VIZ disruptions outside request handling with strict LKG semantics."""

    def __init__(
        self,
        *,
        client: Any | None = None,
        adapter: VizRoadDisruptionAdapter | None = None,
        now_factory: Callable[[], datetime] | None = None,
    ) -> None:
        self.client = client or VizRoadDisruptionClient()
        self.adapter = adapter or VizRoadDisruptionAdapter()
        self.now_factory = now_factory or (lambda: datetime.now(UTC))

    @staticmethod
    def _error_code(exc: Exception) -> str:
        if isinstance(exc, (ValueError, KeyError, TypeError)):
            return "SCHEMA_CHANGED"
        return "SOURCE_UNAVAILABLE"

    def refresh(
        self,
        *,
        previous_state: TrafficDisruptionState | None = None,
    ) -> TrafficDisruptionState:
        if previous_state is not None and previous_state.source_id != SOURCE_ID:
            raise ValueError("previous traffic disruption source_id does not match VIZ source")
        now = self.now_factory()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("now_factory must produce timezone-aware datetimes")
        now = now.astimezone(UTC)

        try:
            payload = self.client.fetch()
            source_url = getattr(self.client, "source_url", VizRoadDisruptionClient.source_url)
            disruptions = self.adapter.parse(
                payload,
                retrieved_at=now,
                source_url=source_url,
            )
        except Exception as exc:
            return TrafficDisruptionState(
                generated_at=now,
                source_id=SOURCE_ID,
                disruptions=previous_state.disruptions if previous_state else (),
                last_success_at=previous_state.last_success_at if previous_state else None,
                source_error=self._error_code(exc),
                freshness=(
                    FreshnessStatus.STALE
                    if previous_state is not None and previous_state.last_success_at is not None
                    else FreshnessStatus.UNAVAILABLE
                ),
            )

        return TrafficDisruptionState(
            generated_at=now,
            source_id=SOURCE_ID,
            disruptions=disruptions,
            last_success_at=now,
            source_error=None,
            freshness=FreshnessStatus.VALID,
        )
