"""Deterministic derived products built only from persisted real runtime inputs.

These products intentionally avoid synthetic replacement values and universal/composite scores. A
record is emitted only when its required source-backed inputs exist. Cross-domain context keeps the
source values and timestamps separate so the result remains descriptive rather than causal.
"""

from __future__ import annotations

from pydantic import HttpUrl

from berlin_urban_intelligence.knowledge.derivations import (
    DerivationDefinition,
    DerivationInput,
    DerivationRecord,
)
from berlin_urban_intelligence.runtime.derived import DerivedState
from berlin_urban_intelligence.runtime.state import RuntimeState
from berlin_urban_intelligence.shared.contracts import (
    DerivationStatus,
    FreshnessStatus,
    Observation,
    Provenance,
    QualityFlag,
)

_PROJECT_URL = HttpUrl("https://github.com/nfloser/berlin-urban-intelligence")


class DerivedProductBuilder:
    """Create explainable runtime products without fabricating unavailable domains."""

    definitions = (
        DerivationDefinition(
            id="mobility-delay-share-v1",
            name="VBB delayed trip-update share",
            description=(
                "Share of VBB GTFS-Realtime trip updates containing at least one non-zero delay. "
                "This describes feed contents only and is not a network-wide punctuality rate."
            ),
            producer_agent_id="mobility",
            producer_version="0.1.0",
            algorithm_version="1.0.0",
            output_kind="mobility_delay_share",
        ),
        DerivationDefinition(
            id="heat-air-quality-context-v1",
            name="Latest measured heat and air-quality context",
            description=(
                "Descriptive pairing of the latest measured DWD 2 m air temperature and latest "
                "Berlin LQI grade. Values remain separate; no combined risk score or causal claim "
                "is produced."
            ),
            producer_agent_id="live_state",
            producer_version="0.1.0",
            algorithm_version="1.0.0",
            output_kind="heat_air_quality_context",
        ),
        DerivationDefinition(
            id="mobility-air-quality-context-v1",
            name="Latest mobility and air-quality context",
            description=(
                "Descriptive co-reporting of the VBB GTFS-Realtime delayed trip-update share and "
                "latest Berlin LQI grade. The values retain separate timestamps and source "
                "semantics; no causal relationship, exposure attribution or combined score is "
                "inferred."
            ),
            producer_agent_id="live_state",
            producer_version="0.1.0",
            algorithm_version="1.0.0",
            output_kind="mobility_air_quality_context",
        ),
    )

    @staticmethod
    def _freshness(state: RuntimeState, *source_ids: str) -> FreshnessStatus:
        values = [
            state.source_statuses[source_id].freshness
            for source_id in source_ids
            if source_id in state.source_statuses
        ]
        if len(values) != len(source_ids):
            return FreshnessStatus.UNKNOWN
        if FreshnessStatus.UNAVAILABLE in values:
            return FreshnessStatus.UNAVAILABLE
        if FreshnessStatus.STALE in values:
            return FreshnessStatus.STALE
        if FreshnessStatus.UNKNOWN in values:
            return FreshnessStatus.UNKNOWN
        return FreshnessStatus.VALID

    @staticmethod
    def _quality(*qualities: QualityFlag) -> QualityFlag:
        precedence = (
            QualityFlag.INVALID,
            QualityFlag.SUSPECT,
            QualityFlag.PARTIAL,
            QualityFlag.STALE,
            QualityFlag.UNKNOWN,
            QualityFlag.VALID,
        )
        values = set(qualities)
        return next(flag for flag in precedence if flag in values)

    @classmethod
    def _combined_quality(cls, *observations: Observation) -> QualityFlag:
        return cls._quality(*(item.quality for item in observations))

    @staticmethod
    def _latest(state: RuntimeState, phenomenon: str) -> Observation | None:
        candidates = [item for item in state.observations if item.phenomenon == phenomenon]
        return max(candidates, key=lambda item: item.observed_at) if candidates else None

    def _mobility_record(self, state: RuntimeState) -> DerivationRecord | None:
        snapshot = state.mobility
        if snapshot is None or snapshot.trip_updates == 0:
            return None
        input_id = f"vbb-gtfs-rt:{snapshot.observed_at.isoformat()}"
        return DerivationRecord(
            id="derived:mobility:delay-share:current",
            definition_id="mobility-delay-share-v1",
            entity_id="berlin:public-transport",
            phenomenon="vbb_delayed_trip_update_share",
            value=snapshot.delayed_trip_updates / snapshot.trip_updates,
            unit="1",
            valid_at=snapshot.observed_at,
            computed_at=state.generated_at,
            quality=snapshot.quality,
            freshness=self._freshness(state, "vbb_gtfs_rt"),
            status=DerivationStatus.VALID,
            inputs=(DerivationInput(id=input_id, role="vbb_gtfs_realtime_snapshot"),),
            provenance=Provenance(
                provider="Berlin Urban Intelligence",
                dataset="derived-information",
                source_url=_PROJECT_URL,
                observation_time=snapshot.observed_at,
                retrieved_at=state.generated_at,
                processed_at=state.generated_at,
                processing_method="delayed_trip_updates / trip_updates",
                agent="mobility",
                agent_version="0.1.0",
                model_version="mobility-delay-share-v1",
                quality_note=(
                    "Denominator is the trip updates present in the VBB GTFS-Realtime feed, not "
                    "all scheduled Berlin services."
                ),
                upstream_ids=(input_id,),
            ),
        )

    def _heat_air_quality_record(self, state: RuntimeState) -> DerivationRecord | None:
        temperature = self._latest(state, "air_temperature_2m")
        lqi = self._latest(state, "berlin_lqi_grade")
        if temperature is None or lqi is None:
            return None
        input_ids = (temperature.id, lqi.id)
        valid_at = max(temperature.observed_at, lqi.observed_at)
        return DerivationRecord(
            id="derived:context:heat-air-quality:current",
            definition_id="heat-air-quality-context-v1",
            entity_id="berlin:measured-context",
            phenomenon="heat_air_quality_context",
            value={
                "temperature_c": temperature.value,
                "temperature_entity_id": temperature.entity_id,
                "temperature_observed_at": temperature.observed_at.isoformat(),
                "lqi_grade": lqi.value,
                "lqi_entity_id": lqi.entity_id,
                "lqi_observed_at": lqi.observed_at.isoformat(),
            },
            valid_at=valid_at,
            computed_at=state.generated_at,
            quality=self._combined_quality(temperature, lqi),
            freshness=self._freshness(state, "dwd_open_data", "berlin_air_quality"),
            status=DerivationStatus.VALID,
            inputs=(
                DerivationInput(id=temperature.id, role="measured_air_temperature_2m"),
                DerivationInput(id=lqi.id, role="measured_berlin_lqi_grade"),
            ),
            provenance=Provenance(
                provider="Berlin Urban Intelligence",
                dataset="derived-information",
                source_url=_PROJECT_URL,
                observation_time=valid_at,
                retrieved_at=state.generated_at,
                processed_at=state.generated_at,
                processing_method="latest-value contextual pairing without aggregation",
                agent="live_state",
                agent_version="0.1.0",
                model_version="heat-air-quality-context-v1",
                quality_note=(
                    "Descriptive cross-domain context only; station measurements can represent "
                    "different locations and times and are not a combined exposure/risk score."
                ),
                upstream_ids=input_ids,
            ),
        )

    def _mobility_air_quality_record(self, state: RuntimeState) -> DerivationRecord | None:
        snapshot = state.mobility
        lqi = self._latest(state, "berlin_lqi_grade")
        if snapshot is None or snapshot.trip_updates == 0 or lqi is None:
            return None

        mobility_input = f"vbb-gtfs-rt:{snapshot.observed_at.isoformat()}"
        input_ids = (mobility_input, lqi.id)
        valid_at = max(snapshot.observed_at, lqi.observed_at)
        return DerivationRecord(
            id="derived:context:mobility-air-quality:current",
            definition_id="mobility-air-quality-context-v1",
            entity_id="berlin:operational-context",
            phenomenon="mobility_air_quality_context",
            value={
                "delayed_trip_update_share": snapshot.delayed_trip_updates / snapshot.trip_updates,
                "mobility_trip_updates": snapshot.trip_updates,
                "mobility_delayed_trip_updates": snapshot.delayed_trip_updates,
                "mobility_observed_at": snapshot.observed_at.isoformat(),
                "lqi_grade": lqi.value,
                "lqi_entity_id": lqi.entity_id,
                "lqi_observed_at": lqi.observed_at.isoformat(),
            },
            valid_at=valid_at,
            computed_at=state.generated_at,
            quality=self._quality(snapshot.quality, lqi.quality),
            freshness=self._freshness(state, "vbb_gtfs_rt", "berlin_air_quality"),
            status=DerivationStatus.VALID,
            inputs=(
                DerivationInput(id=mobility_input, role="vbb_gtfs_realtime_snapshot"),
                DerivationInput(id=lqi.id, role="measured_berlin_lqi_grade"),
            ),
            provenance=Provenance(
                provider="Berlin Urban Intelligence",
                dataset="derived-information",
                source_url=_PROJECT_URL,
                observation_time=valid_at,
                retrieved_at=state.generated_at,
                processed_at=state.generated_at,
                processing_method="latest-value contextual co-reporting without aggregation",
                agent="live_state",
                agent_version="0.1.0",
                model_version="mobility-air-quality-context-v1",
                quality_note=(
                    "Descriptive cross-domain context only. The VBB value is a share of trip "
                    "updates present in the realtime feed and the LQI value is station-based; no "
                    "causal relationship, passenger exposure estimate or combined score is inferred."
                ),
                upstream_ids=input_ids,
            ),
        )

    def build(self, state: RuntimeState) -> DerivedState:
        records = [
            record
            for record in (
                self._mobility_record(state),
                self._heat_air_quality_record(state),
                self._mobility_air_quality_record(state),
            )
            if record is not None
        ]
        return DerivedState(
            generated_at=state.generated_at,
            definitions=self.definitions,
            records=tuple(records),
        )
