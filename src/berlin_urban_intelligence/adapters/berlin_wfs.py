"""Generic read-only adapter for Berlin Geoportal WFS services.

The adapter deliberately discovers feature type names from GetCapabilities rather than
hard-coding undocumented source schemas. GeoJSON is requested in EPSG:4326 for API interchange.
Metric calculations must still reproject to a suitable projected CRS elsewhere in the system.
"""

from __future__ import annotations

import json
from typing import Any
from xml.etree import ElementTree

import httpx


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_feature_type_names(payload: bytes) -> list[str]:
    """Return WFS feature type names in document order.

    Namespace prefixes vary between WFS servers, so parsing is based on local XML element names.
    """

    try:
        root = ElementTree.fromstring(payload)
    except ElementTree.ParseError as exc:
        raise ValueError("WFS capabilities response is not valid XML") from exc

    names: list[str] = []
    for feature_type in root.iter():
        if _local_name(feature_type.tag) != "FeatureType":
            continue
        for child in feature_type:
            if _local_name(child.tag) == "Name" and child.text and child.text.strip():
                names.append(child.text.strip())
                break
    if not names:
        raise ValueError("WFS capabilities response contains no feature types")
    return names


class BerlinWfsClient:
    """Minimal standards-based WFS client for public Berlin Geoportal services."""

    def __init__(
        self,
        base_url: str,
        *,
        client: Any | None = None,
        timeout_s: float = 30.0,
    ) -> None:
        if not base_url.startswith("https://gdi.berlin.de/services/wfs/"):
            raise ValueError("BerlinWfsClient only accepts official gdi.berlin.de WFS endpoints")
        self.base_url = base_url.rstrip("?")
        self._owned_client = client is None
        self._client = client or httpx.Client(timeout=timeout_s, follow_redirects=True)

    def capabilities(self) -> bytes:
        response = self._client.get(
            self.base_url,
            params={"service": "WFS", "request": "GetCapabilities", "version": "2.0.0"},
        )
        response.raise_for_status()
        if not response.content:
            raise ValueError("WFS capabilities response is empty")
        return bytes(response.content)

    def feature_types(self) -> list[str]:
        return parse_feature_type_names(self.capabilities())

    def discover_feature_type(self, *keywords: str) -> str:
        """Resolve one feature type by case-insensitive keyword matching.

        Ambiguous matches are rejected instead of choosing an arbitrary layer.
        """

        cleaned = tuple(keyword.strip().lower() for keyword in keywords if keyword.strip())
        if not cleaned:
            raise ValueError("at least one discovery keyword is required")
        matches = [
            name
            for name in self.feature_types()
            if all(keyword in name.lower() for keyword in cleaned)
        ]
        if len(matches) != 1:
            raise ValueError(
                f"feature type discovery expected exactly one match for {cleaned!r}, found {matches!r}"
            )
        return matches[0]

    def fetch_geojson(
        self,
        feature_type: str,
        *,
        count: int | None = None,
        start_index: int | None = None,
    ) -> dict[str, Any]:
        if not feature_type.strip():
            raise ValueError("feature_type must not be empty")
        if count is not None and not 1 <= count <= 100_000:
            raise ValueError("count must be between 1 and 100000")
        if start_index is not None and start_index < 0:
            raise ValueError("start_index must not be negative")
        params: dict[str, object] = {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeNames": feature_type,
            "outputFormat": "application/json",
            "srsName": "EPSG:4326",
        }
        if count is not None:
            params["count"] = count
        if start_index is not None:
            params["startIndex"] = start_index
        response = self._client.get(self.base_url, params=params)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict) or payload.get("type") != "FeatureCollection":
            raise ValueError("WFS did not return a GeoJSON FeatureCollection")
        features = payload.get("features")
        if not isinstance(features, list):
            raise ValueError("GeoJSON FeatureCollection has no features list")
        return payload

    def fetch_all_geojson(
        self,
        feature_type: str,
        *,
        page_size: int = 5_000,
        max_features: int = 100_000,
    ) -> dict[str, Any]:
        """Retrieve a complete WFS layer with bounded, verified pagination.

        A service that ignores ``startIndex`` is rejected rather than returning a silently
        truncated or duplicated layer. The hard maximum protects research runs from an
        unexpectedly huge source schema while making the limitation explicit.
        """
        if not 1 <= page_size <= 20_000:
            raise ValueError("page_size must be between 1 and 20000")
        if not page_size <= max_features <= 1_000_000:
            raise ValueError("max_features must be >= page_size and <= 1000000")

        features: list[Any] = []
        previous_signature: str | None = None
        start_index = 0
        while True:
            page = self.fetch_geojson(
                feature_type, count=page_size, start_index=start_index
            )
            page_features = page["features"]
            if not page_features:
                break
            signature = json.dumps(page_features, sort_keys=True, separators=(",", ":"), default=str)
            if previous_signature == signature:
                raise ValueError("WFS pagination did not advance; refusing duplicated/truncated data")
            previous_signature = signature
            features.extend(page_features)
            if len(features) > max_features:
                raise ValueError(
                    f"WFS layer exceeds configured max_features={max_features}; acquisition aborted"
                )
            if len(page_features) < page_size:
                break
            start_index += len(page_features)

        return {"type": "FeatureCollection", "features": features}

    def close(self) -> None:
        if self._owned_client:
            self._client.close()

    def __enter__(self) -> "BerlinWfsClient":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()
