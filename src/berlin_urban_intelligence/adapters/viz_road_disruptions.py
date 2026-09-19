"""Strict adapter for official Berlin VIZ road-disruption GeoJSON."""

from __future__ import annotations

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import httpx
from pydantic import HttpUrl

from berlin_urban_intelligence.runtime.traffic_disruptions import TrafficDisruption
from berlin_urban_intelligence.shared.contracts import Provenance, SpatialReference

BERLIN_TZ = ZoneInfo("Europe/Berlin")
PROVIDER = "Verkehrsinformationszentrale Berlin (VIZ)"
DATASET = (
    "Baustellen, Sperrungen und sonstige Störungen von besonderem verkehrlichem Interesse "
    "(VIZ-Redaktion)"
)
LICENCE = "Datenlizenz Deutschland - Namensnennung - Version 2.0"


def _local_berlin_time(value: object, field_name: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty Berlin local-time string")
    text = value.strip()
    try:
        naive = (
            datetime.fromisoformat(text)
            if "T" in text
            else datetime.strptime(text, "%d.%m.%Y %H:%M")
        )
    except ValueError as exc:
        raise ValueError(f"{field_name} must use YYYY-MM-DDTHH:MM or DD.MM.YYYY HH:MM") from exc
    if naive.tzinfo is not None:
        raise ValueError(f"{field_name} must be a timezone-naive Berlin civil time")

    first = naive.replace(tzinfo=BERLIN_TZ, fold=0)
    second = naive.replace(tzinfo=BERLIN_TZ, fold=1)
    if first.utcoffset() != second.utcoffset():
        raise ValueError(f"{field_name} is ambiguous across the Europe/Berlin DST fold")
    return first.astimezone(UTC)


def _source_timestamp(value: object) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("tstore must be a non-empty ISO timestamp")
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError("tstore must be an ISO timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("tstore must be timezone-aware")
    return parsed.astimezone(UTC)


def _optional_text(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string or null")
    cleaned = value.strip()
    return cleaned or None


def _required_text(value: object, field_name: str) -> str:
    cleaned = _optional_text(value, field_name)
    if cleaned is None:
        raise ValueError(f"{field_name} must be a non-empty string")
    return cleaned


def _network_reference_ids(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError("netrefs must be a list or null")
    identifiers: set[str] = set()
    for item in value:
        if not isinstance(item, dict):
            raise ValueError("netrefs entries must be objects")
        identifier = item.get("id")
        if isinstance(identifier, str) and identifier.strip():
            identifiers.add(identifier.strip())
    return tuple(sorted(identifiers))


class VizRoadDisruptionClient:
    """Small network client restricted to the official public VIZ disruption endpoint."""

    source_url = "https://api.viz.berlin.de/daten/baustellen_sperrungen_viz.json"

    def __init__(self, *, client: httpx.Client | None = None, timeout_s: float = 30.0) -> None:
        self._owned_client = client is None
        self._client = client or httpx.Client(timeout=timeout_s, follow_redirects=True)

    def fetch(self) -> dict[str, object]:
        response = self._client.get(
            self.source_url,
            headers={"Accept": "application/geo+json, application/json"},
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("VIZ response root must be an object")
        return payload

    def close(self) -> None:
        if self._owned_client:
            self._client.close()


class VizRoadDisruptionAdapter:
    """Convert the current official VIZ GeoJSON schema into canonical disruptions."""

    def parse(
        self,
        payload: object,
        *,
        retrieved_at: datetime,
        source_url: str,
    ) -> tuple[TrafficDisruption, ...]:
        if retrieved_at.tzinfo is None or retrieved_at.utcoffset() is None:
            raise ValueError("retrieved_at must be timezone-aware")
        retrieved_at = retrieved_at.astimezone(UTC)
        if not source_url.startswith("https://api.viz.berlin.de/"):
            raise ValueError("source_url must use the official api.viz.berlin.de HTTPS host")
        if not isinstance(payload, dict) or payload.get("type") != "FeatureCollection":
            raise ValueError("VIZ response must be a GeoJSON FeatureCollection")
        features = payload.get("features")
        if not isinstance(features, list):
            raise ValueError("VIZ FeatureCollection must contain a features list")

        disruptions: list[TrafficDisruption] = []
        for index, feature in enumerate(features):
            disruptions.append(
                self._parse_feature(
                    feature,
                    index=index,
                    retrieved_at=retrieved_at,
                    source_url=source_url,
                )
            )
        disruptions.sort(key=lambda item: item.id)
        if len({item.id for item in disruptions}) != len(disruptions):
            raise ValueError("VIZ response contains duplicate disruption IDs")
        return tuple(disruptions)

    def _parse_feature(
        self,
        feature: object,
        *,
        index: int,
        retrieved_at: datetime,
        source_url: str,
    ) -> TrafficDisruption:
        if not isinstance(feature, dict) or feature.get("type") != "Feature":
            raise ValueError(f"feature[{index}] must be a GeoJSON Feature")
        properties = feature.get("properties")
        geometry = feature.get("geometry")
        if not isinstance(properties, dict):
            raise ValueError(f"feature[{index}].properties must be an object")
        if not isinstance(geometry, dict):
            raise ValueError(f"feature[{index}].geometry must be an object")

        required_keys = {"id", "subtype", "severity", "validity", "content", "tstore"}
        missing = sorted(required_keys - set(properties))
        if missing:
            raise ValueError(f"feature[{index}] missing required fields: {', '.join(missing)}")

        identifier = _required_text(properties.get("id"), "id")
        subtype = _required_text(properties.get("subtype"), "subtype")
        severity = _optional_text(properties.get("severity"), "severity")
        validity = properties.get("validity")
        if not isinstance(validity, dict):
            raise ValueError("validity must be an object")
        valid_from = _local_berlin_time(validity.get("from"), "validity.from")
        valid_to = _local_berlin_time(validity.get("to"), "validity.to")
        source_updated_at = _source_timestamp(properties.get("tstore"))
        spatial = SpatialReference(crs="EPSG:4326", geometry=geometry)

        direction = _optional_text(properties.get("direction"), "direction")
        street = _optional_text(properties.get("street"), "street")
        section = _optional_text(properties.get("section"), "section")
        description = _required_text(properties.get("content"), "content")
        is_future_value = properties.get("is_future")
        if is_future_value is not None and not isinstance(is_future_value, bool):
            raise ValueError("is_future must be boolean or null")

        network_reference_ids = _network_reference_ids(properties.get("netrefs"))
        provenance = Provenance(
            provider=PROVIDER,
            dataset=DATASET,
            source_url=HttpUrl(source_url),
            original_identifier=identifier,
            observation_time=source_updated_at,
            retrieved_at=retrieved_at,
            processed_at=retrieved_at,
            processing_method=(
                "strict GeoJSON schema validation; validity interpreted as Europe/Berlin "
                "civil time; no inferred traffic-speed penalty"
            ),
            agent="resilience",
            agent_version="1.0.0",
            source_licence=LICENCE,
            upstream_ids=network_reference_ids,
        )
        return TrafficDisruption(
            id=identifier,
            subtype=subtype,
            severity=severity,
            street=street,
            section=section,
            description=description,
            direction=direction,
            valid_from=valid_from,
            valid_to=valid_to,
            source_updated_at=source_updated_at,
            is_future=is_future_value,
            network_reference_ids=network_reference_ids,
            is_full_closure=severity == "Vollsperrung",
            spatial=spatial,
            provenance=provenance,
        )
