"""Refresh provenance-bearing, non-live Berlin reference layers from official WFS services."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, Protocol

from berlin_urban_intelligence.adapters.berlin_wfs import BerlinWfsClient
from berlin_urban_intelligence.agents.heat import HeatAgent
from berlin_urban_intelligence.agents.resilience import CriticalInfrastructureRegistry
from berlin_urban_intelligence.runtime.reference import ReferenceState


class WfsReader(Protocol):
    def feature_types(self) -> list[str]: ...
    def discover_feature_type(self, *keywords: str) -> str: ...
    def fetch_geojson(self, feature_type: str, *, count: int | None = None) -> dict[str, Any]: ...


class ReferenceRefreshCoordinator:
    HOSPITAL_URL = "https://gdi.berlin.de/services/wfs/krankenhaeuser"
    FIRE_URL = "https://gdi.berlin.de/services/wfs/feuerwehr"
    CLIMATE_URL = "https://gdi.berlin.de/services/wfs/ua_klimaanalyse_2022"

    def __init__(
        self,
        *,
        hospital_client: WfsReader | None = None,
        fire_client: WfsReader | None = None,
        climate_client: WfsReader | None = None,
        now_factory: Callable[[], datetime] | None = None,
    ) -> None:
        self.hospital_client = hospital_client or BerlinWfsClient(self.HOSPITAL_URL)
        self.fire_client = fire_client or BerlinWfsClient(self.FIRE_URL)
        self.climate_client = climate_client or BerlinWfsClient(self.CLIMATE_URL)
        self.now_factory = now_factory or (lambda: datetime.now(UTC))

    @staticmethod
    def _source_failure(exc: Exception) -> str:
        return (
            "SCHEMA_CHANGED"
            if isinstance(exc, (ValueError, KeyError, TypeError))
            else "SOURCE_UNAVAILABLE"
        )

    @staticmethod
    def _fetch_complete_layer(client: WfsReader, feature_type: str) -> dict[str, Any]:
        fetch_all = getattr(client, "fetch_all_geojson", None)
        if callable(fetch_all):
            return fetch_all(feature_type)
        return client.fetch_geojson(feature_type)

    def refresh(self, *, previous: ReferenceState | None = None) -> ReferenceState:
        now = self.now_factory()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("now_factory must produce timezone-aware datetimes")
        now = now.astimezone(UTC)
        facilities: list = []
        climate_features: list = []
        errors: dict[str, str] = {}
        registry = CriticalInfrastructureRegistry()
        heat = HeatAgent(now_factory=self.now_factory)

        facility_specs = (
            (
                "berlin_hospitals",
                self.hospital_client,
                ("kranken",),
                "hospital",
                "Senatsverwaltung für Wissenschaft, Gesundheit und Pflege Berlin",
                "Krankenhäuser in Berlin",
                self.HOSPITAL_URL,
            ),
            (
                "berlin_fire_stations",
                self.fire_client,
                ("feuer",),
                "fire_station",
                "Berliner Feuerwehr",
                "Standorte der Berliner Feuerwehr",
                self.FIRE_URL,
            ),
        )
        for source_id, client, keywords, category, provider, dataset, url in facility_specs:
            try:
                feature_type = client.discover_feature_type(*keywords)
                payload = self._fetch_complete_layer(client, feature_type)
                facilities.extend(
                    registry.ingest_official_geojson(
                        payload,
                        category=category,
                        provider=provider,
                        dataset=dataset,
                        source_url=url,
                        licence="Datenlizenz Deutschland - Zero - Version 2.0",
                        retrieved_at=now,
                    )
                )
            except Exception as exc:
                errors[source_id] = self._source_failure(exc)
                if previous is not None:
                    facilities.extend(
                        item for item in previous.critical_facilities if item.category == category
                    )

        try:
            feature_types_method = getattr(self.climate_client, "feature_types", None)
            feature_types = (
                feature_types_method()
                if callable(feature_types_method)
                else [self.climate_client.discover_feature_type("klima")]
            )
            if not feature_types:
                raise ValueError("climate WFS advertises no feature types")
            candidate_features: list = []
            for feature_type in feature_types:
                payload = self._fetch_complete_layer(self.climate_client, feature_type)
                candidate_features.extend(
                    heat.ingest_official_climate_features(
                        payload, feature_type=feature_type, retrieved_at=now
                    )
                )
            climate_features = candidate_features
        except Exception as exc:
            errors["berlin_climate_analysis_2022"] = self._source_failure(exc)
            if previous is not None:
                climate_features = list(previous.official_model_features)

        return ReferenceState(
            generated_at=now,
            critical_facilities=tuple(sorted(facilities, key=lambda item: item.id)),
            official_model_features=tuple(sorted(climate_features, key=lambda item: item.id)),
            transport_stops=previous.transport_stops if previous is not None else (),
            network_nodes=previous.network_nodes if previous is not None else (),
            network_edges=previous.network_edges if previous is not None else (),
            errors=dict(sorted(errors.items())),
        )
