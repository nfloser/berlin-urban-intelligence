"""Best-effort live refresh across independent authoritative sources.

A failure in one source is recorded and does not turn another domain's valid observation into
missing or synthetic data. When a previous canonical runtime state is supplied, failed sources keep
their last-known-good observations/snapshot while source transport status becomes unavailable and
freshness continues to age explicitly.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from berlin_urban_intelligence.adapters.berlin_air_quality import BerlinAirQualityClient, extract_lqi_records, parse_lqi_record
from berlin_urban_intelligence.adapters.dwd import DwdTenMinuteAirTemperatureClient
from berlin_urban_intelligence.adapters.vbb import VbbGtfsRealtimeClient, decode_gtfs_realtime
from berlin_urban_intelligence.agents.exposure import ExposureAgent
from berlin_urban_intelligence.agents.heat import HeatAgent
from berlin_urban_intelligence.agents.mobility import MobilityAgent, MobilitySnapshot
from berlin_urban_intelligence.runtime.state import RuntimeState
from berlin_urban_intelligence.shared.contracts import Observation
from berlin_urban_intelligence.shared.source_status import SourceRuntimeStatus, SourceStatusStore


class RefreshCoordinator:
    def __init__(self, *, air_client: Any | None = None, dwd_client: Any | None = None, vbb_client: Any | None = None, vbb_decoder: Callable[[bytes], tuple[datetime | None, list[dict[str, object]]]] = decode_gtfs_realtime, now_factory: Callable[[], datetime] | None = None) -> None:
        self.air_client = air_client or BerlinAirQualityClient()
        self.dwd_client = dwd_client or DwdTenMinuteAirTemperatureClient()
        self.vbb_client = vbb_client or VbbGtfsRealtimeClient()
        self.vbb_decoder = vbb_decoder
        self.now_factory = now_factory or (lambda: datetime.now(UTC))

    @staticmethod
    def _error_code(exc: Exception) -> str:
        if isinstance(exc, RuntimeError):
            return "MODEL_UNAVAILABLE" if "GTFS-Realtime" not in str(exc) else "DECODER_UNAVAILABLE"
        if isinstance(exc, (ValueError, KeyError, TypeError)):
            return "SCHEMA_CHANGED"
        return "SOURCE_UNAVAILABLE"

    @staticmethod
    def _replace_agent_observations(existing: list[Observation], agent_id: str, replacement: list[Observation]) -> list[Observation]:
        retained = [item for item in existing if item.provenance.agent != agent_id]
        return [*retained, *replacement]

    def refresh(self, *, previous_state: RuntimeState | None = None) -> RuntimeState:
        now = self.now_factory()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("now_factory must produce timezone-aware datetimes")
        now = now.astimezone(UTC)
        status_store = SourceStatusStore(previous_state.source_statuses if previous_state else None)
        exposure = ExposureAgent()
        heat = HeatAgent()
        observations = list(previous_state.observations if previous_state else ())
        mobility_snapshot: MobilitySnapshot | None = previous_state.mobility if previous_state else None
        errors: dict[str, str] = {}

        try:
            payload = self.air_client.get_lqi_data()
            records = [parse_lqi_record(item) for item in extract_lqi_records(payload)]
            if not records:
                raise ValueError("Berlin LQI response contains no usable records")
            current = exposure.ingest_lqi_records(records, retrieved_at=now)
            observations = self._replace_agent_observations(observations, "exposure", current)
            status_store.record_success("berlin_air_quality", retrieved_at=now, observation_time=max(record.observed_at for record in records))
        except Exception as exc:
            code = self._error_code(exc)
            status_store.record_failure("berlin_air_quality", checked_at=now, error_code=code)
            errors["berlin_air_quality"] = code

        try:
            record = self.dwd_client.fetch()
            current = heat.ingest_dwd_record(record, retrieved_at=now)
            observations = self._replace_agent_observations(observations, "heat", current)
            status_store.record_success("dwd_open_data", retrieved_at=now, observation_time=record.observed_at)
        except Exception as exc:
            code = self._error_code(exc)
            status_store.record_failure("dwd_open_data", checked_at=now, error_code=code)
            errors["dwd_open_data"] = code

        try:
            raw = self.vbb_client.fetch()
            feed_timestamp, decoded = self.vbb_decoder(raw)
            if feed_timestamp is None:
                raise ValueError("VBB feed has no source timestamp")
            mobility = MobilityAgent()
            updates = mobility.from_decoded_records(decoded)
            mobility_snapshot = mobility.summarise_updates(updates, feed_timestamp=feed_timestamp, retrieved_at=now)
            status_store.record_success("vbb_gtfs_rt", retrieved_at=now, observation_time=feed_timestamp)
        except Exception as exc:
            code = self._error_code(exc)
            status_store.record_failure("vbb_gtfs_rt", checked_at=now, error_code=code)
            errors["vbb_gtfs_rt"] = code

        thresholds = {
            "berlin_air_quality": timedelta(hours=2),
            "dwd_open_data": timedelta(hours=1),
            "vbb_gtfs_rt": timedelta(minutes=15),
        }
        statuses: dict[str, SourceRuntimeStatus] = {
            source_id: status_store.get(source_id, now=now, freshness_threshold=threshold)
            for source_id, threshold in thresholds.items()
        }
        return RuntimeState(
            generated_at=now,
            observations=tuple(sorted(observations, key=lambda item: item.id)),
            mobility=mobility_snapshot,
            source_statuses=statuses,
            errors=errors,
        )
