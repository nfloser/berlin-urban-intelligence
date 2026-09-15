"""HTTP surfaces for derived information, provenance and dependency lineage."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from berlin_urban_intelligence.runtime.derived import DerivedState

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
