"""Map-oriented projection of persisted reference state.

The canonical reference snapshot remains authoritative. This module creates a bounded GeoJSON view
for interactive maps so clients do not need to download tens of thousands of complete canonical
objects merely to render the current viewport.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from numbers import Real
from typing import Any, Literal

from berlin_urban_intelligence.runtime.reference import ReferenceState
from berlin_urban_intelligence.shared.contracts import (
    CriticalFacility,
    OfficialModelFeature,
    UrbanEntity,
)

MapLayer = Literal["facilities", "stops", "climate"]
MAP_LAYERS: tuple[MapLayer, ...] = ("facilities", "stops", "climate")


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
            east < self.west
            or west > self.east
            or north < self.south
            or south > self.north
        )


def parse_layers(value: str) -> tuple[MapLayer, ...]:
    requested = tuple(part.strip() for part in value.split(",") if part.strip())
    if not requested:
        raise ValueError("at least one map layer is required")
    unknown = [layer for layer in requested if layer not in MAP_LAYERS]
    if unknown:
        raise ValueError(f"unknown map layer: {', '.join(unknown)}")
    return tuple(dict.fromkeys(requested))  # type: ignore[return-value]


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


def _feature(item: CriticalFacility | UrbanEntity | OfficialModelFeature, layer: MapLayer) -> dict[str, Any]:
    spatial = item.spatial
    assert spatial is not None and spatial.geometry is not None
    properties: dict[str, Any] = {"id": item.id, "layer": layer}
    if layer == "facilities":
        facility = item
        assert isinstance(facility, CriticalFacility)
        properties.update(
            name=facility.name,
            category=facility.category,
            quality=facility.quality.value,
            source_identifier=facility.source_identifier,
        )
    elif layer == "stops":
        stop = item
        assert isinstance(stop, UrbanEntity)
        properties.update(
            name=stop.name,
            entity_type=stop.entity_type,
            source_identifier=stop.source_identifier,
        )
    else:
        climate = item
        assert isinstance(climate, OfficialModelFeature)
        properties.update(
            entity_id=climate.entity_id,
            model_name=climate.model_name,
            feature_type=climate.feature_type,
            quality=climate.quality.value,
            state=climate.state.value,
        )
    return {
        "type": "Feature",
        "id": item.id,
        "geometry": spatial.geometry,
        "properties": properties,
    }


def _layer_items(
    state: ReferenceState, layer: MapLayer
) -> Sequence[CriticalFacility | UrbanEntity | OfficialModelFeature]:
    if layer == "facilities":
        return state.critical_facilities
    if layer == "stops":
        return state.transport_stops
    return state.official_model_features


def reference_feature_collection(
    state: ReferenceState,
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
        matches = [item for item in items if _mappable(item, bounds)]
        selected = matches[:limit_per_layer]
        features.extend(_feature(item, layer) for item in selected)
        totals[layer] = len(items)
        matched[layer] = len(matches)
        returned[layer] = len(selected)
        truncated[layer] = len(matches) > len(selected)

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
