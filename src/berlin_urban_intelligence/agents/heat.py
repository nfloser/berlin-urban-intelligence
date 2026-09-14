"""Urban heat agent combining measured meteorology with separately identified modelled layers."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

from pydantic import HttpUrl

from berlin_urban_intelligence.adapters.dwd import DwdTemperatureRecord
from berlin_urban_intelligence.agents.base import BaseAgent
from berlin_urban_intelligence.shared.contracts import (
    AgentDescriptor,
    AgentHealth,
    AvailabilityStatus,
    DataState,
    FreshnessStatus,
    Observation,
    OfficialModelFeature,
    Provenance,
    QualityFlag,
    SpatialReference,
)
from berlin_urban_intelligence.shared.temporal import classify_freshness, ensure_utc


class HeatAgent(BaseAgent):
    descriptor = AgentDescriptor(
        id="heat",
        version="0.1.0",
        description=(
            "Measured meteorology and official urban-climate information with "
            "explicit state semantics."
        ),
        capabilities=("ingest_dwd_temperature", "ingest_official_climate_features", "heat_state"),
        input_contracts=("DwdTemperatureRecord",),
        output_contracts=("Observation",),
        source_dependencies=("dwd_open_data", "berlin_climate_analysis_2022"),
    )

    def __init__(
        self,
        observations: list[Observation] | tuple[Observation, ...] | None = None,
        *,
        now_factory: Callable[[], datetime] | None = None,
    ) -> None:
        super().__init__(now_factory=now_factory)
        self._observations: tuple[Observation, ...] = tuple(observations or ())

    def ingest_dwd_record(
        self, record: DwdTemperatureRecord, retrieved_at: datetime | None = None
    ) -> list[Observation]:
        retrieved = ensure_utc(retrieved_at or self.now())
        provenance = Provenance(
            provider="Deutscher Wetterdienst (DWD)",
            dataset="CDC 10-minute station observations of air temperature - now",
            source_url=HttpUrl(
                "https://opendata.dwd.de/climate_environment/CDC/observations_germany/"
                "climate/10_minutes/air_temperature/now/"
                f"10minutenwerte_TU_{record.station_id}_now.zip"
            ),
            original_identifier=record.station_id,
            observation_time=record.observed_at,
            retrieved_at=retrieved,
            processed_at=self.now(),
            processing_method="DWD semicolon CSV normalisation; -999 preserved as missing",
            agent=self.descriptor.id,
            agent_version=self.descriptor.version,
            source_licence="CC BY 4.0",
            quality_note=(
                "DWD now data have not completed final quality control; "
                "QN is retained in the source record."
            ),
        )
        specs = [
            ("air_temperature_2m", record.temperature_c, "Cel"),
            ("air_temperature_5cm", record.near_ground_temperature_c, "Cel"),
            ("relative_humidity", record.relative_humidity_pct, "%"),
            ("air_pressure_station", record.pressure_hpa, "hPa"),
            ("dew_point_temperature", record.dew_point_c, "Cel"),
        ]
        observations: list[Observation] = []
        for phenomenon, value, unit in specs:
            if value is None:
                continue
            observations.append(
                Observation(
                    id=f"dwd:{record.station_id}:{phenomenon}:{record.observed_at.isoformat()}",
                    entity_id=f"weather-station:dwd:{record.station_id}",
                    phenomenon=phenomenon,
                    value=value,
                    unit=unit,
                    observed_at=record.observed_at,
                    state=DataState.OBSERVED,
                    quality=QualityFlag.SUSPECT
                    if record.quality_level in (None, 1)
                    else QualityFlag.VALID,
                    provenance=provenance,
                )
            )
        self._observations = tuple(observations)
        return observations

    def ingest_official_climate_features(
        self,
        payload: dict[str, Any],
        *,
        feature_type: str,
        retrieved_at: datetime | None = None,
    ) -> list[OfficialModelFeature]:
        """Normalize an official Berlin climate WFS layer without promoting it to observation.

        Properties are preserved as published rather than guessed into project-specific metrics.
        This allows later schema-specific mappings only after the upstream fields are verified.
        """
        if payload.get("type") != "FeatureCollection" or not isinstance(
            payload.get("features"), list
        ):
            raise ValueError("climate source must be a GeoJSON FeatureCollection")
        retrieved = ensure_utc(retrieved_at or self.now())
        output: list[OfficialModelFeature] = []
        for index, raw in enumerate(payload["features"]):
            if not isinstance(raw, dict) or not isinstance(raw.get("geometry"), dict):
                continue
            feature_id = str(raw.get("id") or f"feature-{index}")
            raw_properties = raw.get("properties")
            properties = (
                {str(key): value for key, value in raw_properties.items()}
                if isinstance(raw_properties, dict)
                else {}
            )
            provenance = Provenance(
                provider="Senatsverwaltung für Stadtentwicklung, Bauen und Wohnen Berlin",
                dataset="Klimaanalysekarten 2022 (Umweltatlas)",
                source_url=HttpUrl("https://gdi.berlin.de/services/wfs/ua_klimaanalyse_2022"),
                original_identifier=feature_id,
                retrieved_at=retrieved,
                processed_at=self.now(),
                processing_method=(
                    "official Berlin WFS GeoJSON normalization with source properties preserved"
                ),
                agent=self.descriptor.id,
                agent_version=self.descriptor.version,
                source_licence="Datenlizenz Deutschland - Zero - Version 2.0",
                quality_note="Official model output; not a measured meteorological observation.",
            )
            output.append(
                OfficialModelFeature(
                    id=f"berlin-climate-2022:{feature_type}:{feature_id}",
                    entity_id=f"climate-zone:{feature_type}:{feature_id}",
                    model_name="Klimaanalysekarten 2022",
                    feature_type=feature_type,
                    properties=properties,
                    quality=QualityFlag.VALID,
                    provenance=provenance,
                    spatial=SpatialReference(crs="EPSG:4326", geometry=raw["geometry"]),
                )
            )
        return output

    def observations(self) -> list[Observation]:
        return list(self._observations)

    def health(self) -> AgentHealth:
        now = self.now()
        if not self._observations:
            return self.unavailable_health("No measured Berlin meteorology has been ingested.")
        newest = max(item.observed_at for item in self._observations)
        freshness = classify_freshness(newest, now, timedelta(hours=1))
        status = (
            AvailabilityStatus.AVAILABLE
            if freshness == FreshnessStatus.VALID
            else AvailabilityStatus.DEGRADED
        )
        quality = (
            QualityFlag.SUSPECT
            if any(item.quality == QualityFlag.SUSPECT for item in self._observations)
            else QualityFlag.VALID
        )
        return AgentHealth(
            agent_id=self.descriptor.id,
            status=status,
            checked_at=now,
            freshness=freshness,
            quality=quality,
            detail=f"{len(self._observations)} measured meteorological observations loaded.",
        )
