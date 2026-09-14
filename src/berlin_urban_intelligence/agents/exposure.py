"""Environmental exposure agent."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta

from pydantic import HttpUrl

from berlin_urban_intelligence.adapters.berlin_air_quality import LqiRecord
from berlin_urban_intelligence.agents.base import BaseAgent
from berlin_urban_intelligence.shared.contracts import (
    AgentDescriptor,
    AgentHealth,
    AvailabilityStatus,
    DataState,
    FreshnessStatus,
    Observation,
    Provenance,
    QualityFlag,
)
from berlin_urban_intelligence.shared.temporal import classify_freshness, ensure_utc


class ExposureAgent(BaseAgent):
    descriptor = AgentDescriptor(
        id="exposure",
        version="0.1.0",
        description="Environmental observations and transparent exposure-state handling.",
        capabilities=("ingest_berlin_lqi", "exposure_state"),
        input_contracts=("LqiRecord",),
        output_contracts=("Observation",),
        source_dependencies=("berlin_air_quality",),
    )

    def __init__(
        self,
        observations: list[Observation] | tuple[Observation, ...] | None = None,
        *,
        now_factory: Callable[[], datetime] | None = None,
    ) -> None:
        super().__init__(now_factory=now_factory)
        self._observations: tuple[Observation, ...] = tuple(observations or ())

    def ingest_lqi_records(
        self, records: list[LqiRecord], retrieved_at: datetime | None = None
    ) -> list[Observation]:
        retrieved = ensure_utc(retrieved_at or self.now())
        output: list[Observation] = []
        for record in records:
            provenance = Provenance(
                provider="Berliner Luftgütemessnetz",
                dataset="Luftqualitätsindex (LQI)",
                source_url=HttpUrl("https://luftdaten.berlin.de/api/lqis/data"),
                original_identifier=record.station_code,
                observation_time=record.observed_at,
                retrieved_at=retrieved,
                processed_at=self.now(),
                processing_method="official LQI REST payload normalisation",
                agent=self.descriptor.id,
                agent_version=self.descriptor.version,
                source_licence="Datenlizenz Deutschland - Namensnennung - Version 2.0",
                quality_note=(
                    "Current LQI uses automatic measurements that remain subject "
                    "to quality control."
                ),
            )
            output.append(
                Observation(
                    id=f"lqi:{record.station_code}:{record.observed_at.isoformat()}",
                    entity_id=f"air-quality-station:{record.station_code}",
                    phenomenon="berlin_lqi_grade",
                    value=record.grade,
                    unit="1",
                    observed_at=record.observed_at,
                    state=DataState.OBSERVED,
                    quality=QualityFlag.SUSPECT,
                    provenance=provenance,
                )
            )
            for component, grade in sorted(record.component_grades.items()):
                output.append(
                    Observation(
                        id=f"lqi:{record.station_code}:{component}:{record.observed_at.isoformat()}",
                        entity_id=f"air-quality-station:{record.station_code}",
                        phenomenon=f"berlin_lqi_component_{component.lower().replace('.', '_')}",
                        value=grade,
                        unit="1",
                        observed_at=record.observed_at,
                        state=DataState.OBSERVED,
                        quality=QualityFlag.SUSPECT,
                        provenance=provenance,
                    )
                )
        self._observations = tuple(output)
        return output

    def observations(self) -> list[Observation]:
        return list(self._observations)

    def health(self) -> AgentHealth:
        now = self.now()
        if not self._observations:
            return self.unavailable_health("No Berlin air-quality snapshot has been ingested.")
        newest = max(item.observed_at for item in self._observations)
        freshness = classify_freshness(newest, now, timedelta(hours=2))
        status = (
            AvailabilityStatus.AVAILABLE
            if freshness == FreshnessStatus.VALID
            else AvailabilityStatus.DEGRADED
        )
        return AgentHealth(
            agent_id=self.descriptor.id,
            status=status,
            checked_at=now,
            freshness=freshness,
            quality=QualityFlag.SUSPECT,
            detail=f"{len(self._observations)} LQI observations; source values are provisional.",
        )
