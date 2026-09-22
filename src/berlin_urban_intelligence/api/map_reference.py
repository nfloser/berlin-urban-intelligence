"""Map-oriented projection of persisted reference state.

The canonical reference snapshot remains authoritative. This module creates a bounded GeoJSON view
for interactive maps so clients do not need to download tens of thousands of complete canonical
objects merely to render the current viewport.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from numbers import Real
from typing import Any, Literal, cast

from berlin_urban_intelligence.runtime.reference import ReferenceState
from berlin_urban_intelligence.shared.contracts import (
    CriticalFacility,
    OfficialModelFeature,
    UrbanEntity,
)

MapLayer = Literal["facilities", "stops", "climate"]
MAP_LAYERS: tuple[MapLayer, ...] = ("facilities", "stops", "climate")
MapItem = CriticalFacility | UrbanEntity | OfficialModelFeature


@dataclass(frozen=True)
class MapBounds:
    west: float
    south: float
    east: float
    north: float

    def __post_init__(self) -> None:
        if self.west >= self.east:
            raise ValueError("west must be smaller than east")
        if self.south >= self.north:
            raise ValueError("south must be smaller than north")

    def intersects(self, geometry_bounds: tuple[float, float, float, float]) -> bool:
        west, south, east, north = geometry_bounds
        return not (
            east < self.west or west > self.east or north < self.south or south > self.north
        )


def parse_layers(value: str) -> tuple[MapLayer, ...]:
    requested = tuple(part.strip() for part in value.split(",") if part.strip())
    if not requested:
        raise ValueError("at least one map layer is required")
    unknown = [layer for layer in requested if layer not in MAP_LAYERS]
    if unknown:
        raise ValueError(f"unknown map layer: {', '.join(unknown)}")
    deduplicated = tuple(dict.fromkeys(requested))
    return cast(tuple[MapLayer, ...], deduplicated)


def parse_layer(value: str) -> MapLayer:
    if value not in MAP_LAYERS:
        raise ValueError(f"unknown map layer: {value}")
    return value


def _coordinate_pairs(value: Any) -> Iterable[tuple[float, float]]:
    if isinstance(value, (list, tuple)):
        if (
            len(value) >= 2
            and isinstance(value[0], Real)
            and not isinstance(value[0], bool)
            and isinstance(value[1], Real)
            and not isinstance(value[1], bool)
        ):
            yield float(value[0]), float(value[1])
            return
        for child in value:
            yield from _coordinate_pairs(child)


def geometry_bounds(geometry: dict[str, Any] | None) -> tuple[float, float, float, float] | None:
    if not geometry:
        return None
    if geometry.get("type") == "GeometryCollection":
        child_bounds = [
            bounds
            for child in geometry.get("geometries", [])
            if isinstance(child, dict)
            for bounds in [geometry_bounds(child)]
            if bounds is not None
        ]
        if not child_bounds:
            return None
        return (
            min(item[0] for item in child_bounds),
            min(item[1] for item in child_bounds),
            max(item[2] for item in child_bounds),
            max(item[3] for item in child_bounds),
        )
    pairs = list(_coordinate_pairs(geometry.get("coordinates")))
    if not pairs:
        return None
    xs = [pair[0] for pair in pairs]
    ys = [pair[1] for pair in pairs]
    return min(xs), min(ys), max(xs), max(ys)


def _mappable(item: object, bounds: MapBounds) -> bool:
    spatial = getattr(item, "spatial", None)
    if spatial is None or spatial.crs != "EPSG:4326" or spatial.geometry is None:
        return False
    item_bounds = geometry_bounds(spatial.geometry)
    return item_bounds is not None and bounds.intersects(item_bounds)


def _feature(item: MapItem, layer: MapLayer) -> dict[str, Any]:
    spatial = item.spatial
    assert spatial is not None and spatial.geometry is not None
    properties: dict[str, Any] = {"id": item.id, "layer": layer}
    if layer == "facilities":
        assert isinstance(item, CriticalFacility)
        properties.update(
            name=item.name,
            category=item.category,
            quality=item.quality.value,
            source_identifier=item.source_identifier,
        )
    elif layer == "stops":
        assert isinstance(item, UrbanEntity)
        properties.update(
            name=item.name,
            entity_type=item.entity_type,
            source_identifier=item.source_identifier,
        )
    else:
        assert isinstance(item, OfficialModelFeature)
        properties.update(
            entity_id=item.entity_id,
            model_name=item.model_name,
            feature_type=item.feature_type,
            quality=item.quality.value,
            state=item.state.value,
        )
    return {
        "type": "Feature",
        "id": item.id,
        "geometry": spatial.geometry,
        "properties": properties,
    }


def _layer_items(state: ReferenceState | None, layer: MapLayer) -> Sequence[MapItem]:
    if state is None:
        return ()
    if layer == "facilities":
        return state.critical_facilities
    if layer == "stops":
        return state.transport_stops
    return state.official_model_features


def _point_coordinates(item: MapItem) -> tuple[float, float] | None:
    spatial = item.spatial
    if (
        spatial is None
        or spatial.crs != "EPSG:4326"
        or spatial.geometry is None
        or spatial.geometry.get("type") != "Point"
    ):
        return None
    coordinates = spatial.geometry.get("coordinates")
    if (
        not isinstance(coordinates, (list, tuple))
        or len(coordinates) < 2
        or not isinstance(coordinates[0], Real)
        or isinstance(coordinates[0], bool)
        or not isinstance(coordinates[1], Real)
        or isinstance(coordinates[1], bool)
    ):
        return None
    return float(coordinates[0]), float(coordinates[1])


def reference_search(
    state: ReferenceState | None,
    *,
    query: str,
    limit: int = 10,
) -> list[dict[str, Any]]:
    normalized = " ".join(query.casefold().split())
    if len(normalized) < 2:
        raise ValueError("search query must contain at least two characters")
    if limit <= 0 or limit > 50:
        raise ValueError("search limit must be between 1 and 50")
    if state is None:
        return []

    ranked: list[tuple[int, int, str, str, dict[str, Any]]] = []

    def add(
        item: CriticalFacility | UrbanEntity,
        *,
        layer: Literal["facilities", "stops"],
        subtitle: str,
        layer_rank: int,
    ) -> None:
        coordinates = _point_coordinates(item)
        if coordinates is None:
            return
        name = item.name or item.id
        name_key = name.casefold()
        subtitle_key = subtitle.casefold()
        if normalized not in name_key and normalized not in subtitle_key:
            return
        score = 0 if name_key.startswith(normalized) else 1 if normalized in name_key else 2
        longitude, latitude = coordinates
        result = {
            "id": item.id,
            "layer": layer,
            "name": name,
            "subtitle": subtitle,
            "longitude": longitude,
            "latitude": latitude,
        }
        ranked.append((score, layer_rank, name_key, item.id, result))

    for facility in state.critical_facilities:
        add(
            facility,
            layer="facilities",
            subtitle=facility.category.replace("_", " "),
            layer_rank=0,
        )
    for stop in state.transport_stops:
        add(
            stop,
            layer="stops",
            subtitle="transport stop",
            layer_rank=1,
        )

    ranked.sort(key=lambda item: item[:4])
    return [item[4] for item in ranked[:limit]]


def _point_coordinates(item: MapItem) -> tuple[float, float] | None:
    spatial = item.spatial
    if spatial is None or spatial.crs != "EPSG:4326" or spatial.geometry is None:
        return None
    if spatial.geometry.get("type") != "Point":
        return None
    coordinates = spatial.geometry.get("coordinates")
    if (
        not isinstance(coordinates, (list, tuple))
        or len(coordinates) < 2
        or not isinstance(coordinates[0], Real)
        or isinstance(coordinates[0], bool)
        or not isinstance(coordinates[1], Real)
        or isinstance(coordinates[1], bool)
    ):
        return None
    return float(coordinates[0]), float(coordinates[1])


def reference_search(
    state: ReferenceState | None,
    *,
    query: str,
    limit: int = 12,
) -> list[dict[str, object]]:
    normalized = query.strip().casefold()
    if len(normalized) < 2:
        raise ValueError("search query must contain at least two characters")
    if limit <= 0 or limit > 50:
        raise ValueError("search limit must be between 1 and 50")
    if state is None:
        return []

    matches: list[tuple[int, str, str, dict[str, object]]] = []
    layer_rank = {"facilities": 0, "stops": 1}
    for layer in ("facilities", "stops"):
        for item in _layer_items(state, cast(MapLayer, layer)):
            coordinates = _point_coordinates(item)
            if coordinates is None:
                continue
            if isinstance(item, CriticalFacility):
                name = item.name or item.id
                subtitle = item.category.replace("_", " ")
                searchable = " ".join(
                    part
                    for part in (
                        item.id,
                        item.name,
                        item.category,
                        item.source_identifier,
                    )
                    if part
                ).casefold()
            elif isinstance(item, UrbanEntity):
                name = item.name or item.id
                subtitle = item.entity_type.replace("_", " ")
                searchable = " ".join(
                    part
                    for part in (
                        item.id,
                        item.name,
                        item.entity_type,
                        item.source_identifier,
                    )
                    if part
                ).casefold()
            else:
                continue
            if normalized not in searchable:
                continue
            longitude, latitude = coordinates
            matches.append(
                (
                    layer_rank[layer],
                    name.casefold(),
                    item.id,
                    {
                        "id": item.id,
                        "layer": layer,
                        "name": name,
                        "subtitle": subtitle,
                        "longitude": longitude,
                        "latitude": latitude,
                    },
                )
            )
    matches.sort(key=lambda item: (item[0], item[1], item[2]))
    return [item[3] for item in matches[:limit]]


def reference_item(
    state: ReferenceState | None, *, layer: MapLayer, resource_id: str
) -> MapItem | None:
    for item in _layer_items(state, layer):
        if item.id == resource_id:
            return item
    return None


def reference_feature_collection(
    state: ReferenceState | None,
    *,
    bounds: MapBounds,
    layers: tuple[MapLayer, ...] = MAP_LAYERS,
    limit_per_layer: int = 2500,
) -> dict[str, Any]:
    if limit_per_layer <= 0:
        raise ValueError("limit_per_layer must be positive")

    features: list[dict[str, Any]] = []
    totals: dict[str, int] = {}
    matched: dict[str, int] = {}
    returned: dict[str, int] = {}
    truncated: dict[str, bool] = {}

    for layer in layers:
        items = _layer_items(state, layer)
        selected: list[MapItem] = []
        matched_count = 0
        for item in items:
            if not _mappable(item, bounds):
                continue
            matched_count += 1
            if len(selected) < limit_per_layer:
                selected.append(item)
        features.extend(_feature(item, layer) for item in selected)
        totals[layer] = len(items)
        matched[layer] = matched_count
        returned[layer] = len(selected)
        truncated[layer] = matched_count > len(selected)

    return {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "bounds": {
                "west": bounds.west,
                "south": bounds.south,
                "east": bounds.east,
                "north": bounds.north,
            },
            "totals": totals,
            "matched": matched,
            "returned": returned,
            "truncated": truncated,
        },
    }
