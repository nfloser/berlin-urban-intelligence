"""HTTP surfaces for derived information, provenance, dependencies and map reference views."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request

from berlin_urban_intelligence.api.map_reference import (
    MapBounds,
    parse_layer,
    parse_layers,
    reference_feature_collection,
    reference_item,
    reference_search,
)
from berlin_urban_intelligence.runtime.derived import DerivedState
from berlin_urban_intelligence.runtime.reference import ReferenceState

router = APIRouter(prefix="/api/v1")


@router.get("/derived")
def derived_information(request: Request) -> dict[str, object]:
    state: DerivedState | None = request.app.state.derived
    if state is None:
        return {"generated_at": None, "definitions": [], "records": []}
    return state.model_dump(mode="json")


@router.get("/derived/{record_id:path}")
def derived_record(request: Request, record_id: str) -> dict[str, object]:
    state: DerivedState | None = request.app.state.derived
    if state is None:
        raise HTTPException(status_code=404, detail="derived information is not available")
    definition_lookup = {definition.id: definition for definition in state.definitions}
    for record in state.records:
        if record.id == record_id:
            definition = definition_lookup[record.definition_id]
            return {
                "record": record.model_dump(mode="json"),
                "definition": definition.model_dump(mode="json"),
            }
    raise HTTPException(status_code=404, detail=f"derived record not found: {record_id}")


@router.get("/provenance/{record_id:path}")
def provenance(request: Request, record_id: str) -> dict[str, object]:
    state: DerivedState | None = request.app.state.derived
    if state is None:
        raise HTTPException(status_code=404, detail="derived information is not available")
    for record in state.records:
        if record.id == record_id:
            return record.provenance.model_dump(mode="json")
    raise HTTPException(status_code=404, detail=f"provenance record not found: {record_id}")


@router.get("/dependencies/{resource_id:path}")
def dependencies(request: Request, resource_id: str) -> dict[str, object]:
    state: DerivedState | None = request.app.state.derived
    if state is None:
        return {"resource_id": resource_id, "upstream": [], "downstream": [], "status": None}
    graph = state.dependency_graph()
    if resource_id in graph.products():
        upstream = list(graph.upstream(resource_id))
        status: str | None = graph.status(resource_id).value
    else:
        upstream = []
        status = None
    return {
        "resource_id": resource_id,
        "upstream": upstream,
        "downstream": list(graph.downstream(resource_id)),
        "status": status,
    }


@router.get("/map/search")
def search_map(
    request: Request,
    q: str = Query(min_length=2, max_length=120),
    limit: int = Query(default=10, ge=1, le=50),
) -> list[dict[str, object]]:
    reference: ReferenceState | None = request.app.state.reference
    try:
        return reference_search(reference, query=q, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None


@router.get("/map/reference")
def reference_map(
    request: Request,
    west: float = Query(ge=-180, le=180),
    south: float = Query(ge=-90, le=90),
    east: float = Query(ge=-180, le=180),
    north: float = Query(ge=-90, le=90),
    layers: str = Query(default="facilities,stops,climate"),
    limit_per_layer: int = Query(default=2500, ge=1, le=5000),
) -> dict[str, object]:
    try:
        bounds = MapBounds(west=west, south=south, east=east, north=north)
        selected_layers = parse_layers(layers)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
    reference: ReferenceState | None = request.app.state.reference
    return reference_feature_collection(
        reference,
        bounds=bounds,
        layers=selected_layers,
        limit_per_layer=limit_per_layer,
    )


@router.get("/map/reference/{layer}/{resource_id:path}")
def reference_map_detail(request: Request, layer: str, resource_id: str) -> dict[str, object]:
    try:
        selected_layer = parse_layer(layer)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
    reference: ReferenceState | None = request.app.state.reference
    item = reference_item(reference, layer=selected_layer, resource_id=resource_id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"reference object not found: {resource_id}")
    return item.model_dump(mode="json")
