"""Refresh provenance-bearing, non-live Berlin reference layers from official WFS services."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, Protocol, cast

from berlin_urban_intelligence.adapters.berlin_wfs import BerlinWfsClient
from berlin_urban_intelligence.agents.heat import HeatAgent
from berlin_urban_intelligence.agents.resilience import CriticalInfrastructureRegistry
from berlin_urban_intelligence.runtime.reference import ReferenceState
from berlin_urban_intelligence.shared.contracts import CriticalFacility, OfficialModelFeature


class WfsReader(Protocol):
    def feature_types(self) -> list[str]: ...
    def fetch_geojson(self, feature_type: str, *, count: int | None = None) -> dict[str, Any]: ...


class ReferenceRefreshCoordinator:
    HOSPITAL_URL = "https://gdi.berlin.de/services/wfs/krankenhaeuser"
    FIRE_URL = "https://gdi.berlin.de/services/wfs/feuerwehr"
    CLIMATE_URL = "https://gdi.berlin.de/services/wfs/ua_klimaanalyse_2022"

    # The upstream climate service currently advertises dozens of layers, including source
    # geometries with hundreds of thousands of features. The reference state intentionally loads
    # a verified, semantically relevant map subset instead of silently downloading the entire WFS.
    CLIMATE_LAYER_LOCAL_NAMES = (
        "ta_kak_luftaustausch_2022",
        "te_kak_klimarelevante_bebauung_2022",
        "tf_kak_windfeldveraenderung_2022",
        "ti_kak_kaltluftabfluss_2022",
        "tk_kak_leitbahnkorridor_2022",
    )

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
            return cast(dict[str, Any], fetch_all(feature_type))
        return client.fetch_geojson(feature_type)

    @staticmethod
    def _matching_feature_types(
        client: WfsReader,
        *,
        include: tuple[str, ...],
        exclude: tuple[str, ...] = (),
    ) -> list[str]:
        include_lower = tuple(value.lower() for value in include)
        exclude_lower = tuple(value.lower() for value in exclude)
        matches = [
            name
            for name in client.feature_types()
            if all(value in name.lower() for value in include_lower)
            and not any(value in name.lower() for value in exclude_lower)
        ]
        if not matches:
            raise ValueError(
                f"WFS advertises no feature type matching include={include!r}, exclude={exclude!r}"
            )
        return sorted(matches)

    @classmethod
    def _selected_climate_feature_types(cls, client: WfsReader) -> list[str]:
        advertised = client.feature_types()
        by_local_name = {name.split(":", 1)[-1]: name for name in advertised}
        missing = [
            local_name
            for local_name in cls.CLIMATE_LAYER_LOCAL_NAMES
            if local_name not in by_local_name
        ]
        if missing:
            raise ValueError(f"climate WFS is missing verified reference layers: {missing!r}")
        return [by_local_name[name] for name in cls.CLIMATE_LAYER_LOCAL_NAMES]

    def refresh(self, *, previous: ReferenceState | None = None) -> ReferenceState:
        now = self.now_factory()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("now_factory must produce timezone-aware datetimes")
        now = now.astimezone(UTC)
        facilities: list[CriticalFacility] = []
        climate_features: list[OfficialModelFeature] = []
        errors: dict[str, str] = {}
        registry = CriticalInfrastructureRegistry()
        heat = HeatAgent(now_factory=self.now_factory)

        facility_specs = (
            (
                "berlin_hospitals",
                self.hospital_client,
                ("krankenhaeuser",),
                (),
                "hospital",
                "Senatsverwaltung für Wissenschaft, Gesundheit und Pflege Berlin",
                "Krankenhäuser in Berlin",
                self.HOSPITAL_URL,
            ),
            (
                "berlin_fire_stations",
                self.fire_client,
                ("feuerwehr", "standorte"),
                ("einsatzbereiche",),
                "fire_station",
                "Berliner Feuerwehr",
                "Standorte der Berliner Feuerwehr",
                self.FIRE_URL,
            ),
        )
        for source_id, client, include, exclude, category, provider, dataset, url in facility_specs:
            try:
                feature_types = self._matching_feature_types(
                    client, include=include, exclude=exclude
                )
                source_facilities: list[CriticalFacility] = []
                for feature_type in feature_types:
                    payload = self._fetch_complete_layer(client, feature_type)
                    source_facilities.extend(
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
                facilities.extend(source_facilities)
            except Exception as exc:
                errors[source_id] = self._source_failure(exc)
                if previous is not None:
                    facilities.extend(
                        item for item in previous.critical_facilities if item.category == category
                    )

        try:
            feature_types = self._selected_climate_feature_types(self.climate_client)
            candidate_features: list[OfficialModelFeature] = []
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
