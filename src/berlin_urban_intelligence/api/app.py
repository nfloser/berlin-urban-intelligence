"""Versioned HTTP API for Berlin Urban Intelligence.

The API only serves persisted canonical state. Missing files or unavailable domains remain explicit;
there is no synthetic runtime fallback.
"""

from __future__ import annotations

import logging
import os
from collections.abc import AsyncIterator, Awaitable, Callable, Sequence
from contextlib import asynccontextmanager
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, ConfigDict, Field

from berlin_urban_intelligence import __version__
from berlin_urban_intelligence.agents.base import BaseAgent
from berlin_urban_intelligence.agents.energy import EnergyAgent
from berlin_urban_intelligence.agents.exposure import ExposureAgent
from berlin_urban_intelligence.agents.heat import HeatAgent
from berlin_urban_intelligence.agents.live_state import LiveStateAgent
from berlin_urban_intelligence.agents.mobility import MobilityAgent
from berlin_urban_intelligence.agents.resilience import ResilienceAgent, nearest_network_node
from berlin_urban_intelligence.energy.state import EnergyStateStore
from berlin_urban_intelligence.knowledge.graph import KnowledgeGraph
from berlin_urban_intelligence.orchestrator.assessment import (
    AssessmentRequest,
    IntegratedAssessmentService,
)
from berlin_urban_intelligence.orchestrator.engine import (
    OrchestrationRequest,
    Orchestrator,
)
from berlin_urban_intelligence.runtime.reference import ReferenceState, ReferenceStateStore
from berlin_urban_intelligence.runtime.state import RuntimeState, RuntimeStateStore
from berlin_urban_intelligence.scenario_engine.models import Scenario
from berlin_urban_intelligence.shared.contracts import NetworkNode
from berlin_urban_intelligence.shared.observability import structured_log
from berlin_urban_intelligence.shared.source_registry import SourceRegistry

LOGGER = logging.getLogger("berlin_urban_intelligence.api")
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RUNTIME_STATE = PROJECT_ROOT / "data" / "runtime" / "state.json"
DEFAULT_REFERENCE_STATE = PROJECT_ROOT / "data" / "runtime" / "reference.json"
DEFAULT_ENERGY_STATE = PROJECT_ROOT / "data" / "runtime" / "energy.json"
DEFAULT_SOURCE_REGISTRY = PROJECT_ROOT / "config" / "sources.yaml"
MAX_PAGE_SIZE = 1000


class RouteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    origin: str = Field(min_length=1)
    destination: str = Field(min_length=1)
    scenario: Scenario | None = None


class AccessibilityRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    origin: str = Field(min_length=1)
    travel_time_budget_s: float = Field(gt=0, le=86_400)
    max_snap_distance_m: float = Field(default=1000.0, gt=0, le=50_000)
    scenario: Scenario | None = None


def _path_from_env(name: str, default: Path) -> Path:
    return Path(os.environ.get(name, str(default)))


def _load_runtime() -> RuntimeState | None:
    return RuntimeStateStore(_path_from_env("BUI_RUNTIME_STATE", DEFAULT_RUNTIME_STATE)).load()


def _load_reference() -> ReferenceState | None:
    return ReferenceStateStore(
        _path_from_env("BUI_REFERENCE_STATE", DEFAULT_REFERENCE_STATE)
    ).load()


def _build_energy_agent() -> EnergyAgent:
    agent = EnergyAgent()
    state = EnergyStateStore(_path_from_env("BUI_ENERGY_STATE", DEFAULT_ENERGY_STATE)).load()
    if state is None:
        return agent
    agent.register_berlin_evaluation(state.evaluation)
    for forecast in state.forecasts:
        agent.register_forecast(forecast)
    return agent


def _build_agents(
    runtime: RuntimeState | None, reference: ReferenceState | None
) -> dict[str, BaseAgent]:
    observations = tuple(runtime.observations if runtime else ())
    exposure = ExposureAgent([item for item in observations if item.provenance.agent == "exposure"])
    heat = HeatAgent([item for item in observations if item.provenance.agent == "heat"])
    mobility = MobilityAgent(runtime.mobility if runtime else None)
    energy = _build_energy_agent()
    resilience = ResilienceAgent(list(reference.network_edges if reference else ()))
    live_state = LiveStateAgent([mobility, exposure, heat, energy, resilience])
    return {
        "live_state": live_state,
        "mobility": mobility,
        "exposure": exposure,
        "heat": heat,
        "energy": energy,
        "resilience": resilience,
    }


def _graph(
    runtime: RuntimeState | None, reference: ReferenceState | None, energy: EnergyAgent
) -> KnowledgeGraph:
    graph = KnowledgeGraph()
    if runtime:
        for observation in runtime.observations:
            graph.add_observation(observation)
    if reference:
        for facility in reference.critical_facilities:
            graph.add_entity(facility)
        for stop in reference.transport_stops:
            graph.add_entity(stop)
        for feature in reference.official_model_features:
            graph.add_official_model_feature(feature)
        for node in reference.network_nodes:
            graph.add_network_node(node)
        for edge in reference.network_edges:
            graph.add_network_edge(edge)
    for forecast in energy.forecasts():
        graph.add_forecast(forecast)
    return graph


def _slice[T](items: Sequence[T], offset: int, limit: int) -> list[T]:
    return list(items[offset : offset + limit])


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.runtime = _load_runtime()
        app.state.reference = _load_reference()
        app.state.agents = _build_agents(app.state.runtime, app.state.reference)
        app.state.orchestrator = Orchestrator(app.state.agents)
        yield

    app = FastAPI(
        title="Berlin Urban Intelligence API",
        version=__version__,
        description=(
            "Research API exposing provenance-bearing Berlin urban state, reference layers, "
            "deterministic orchestration and explicit hypothetical scenarios."
        ),
        lifespan=lifespan,
    )

    @app.middleware("http")
    async def operation_context(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        operation_id = str(uuid4())
        started = perf_counter()
        response: Response | None = None
        try:
            response = await call_next(request)
            error_state = None if response.status_code < 400 else f"HTTP_{response.status_code}"
            return response
        except Exception:
            error_state = "UNHANDLED_EXCEPTION"
            raise
        finally:
            duration_ms = round((perf_counter() - started) * 1000.0, 3)
            structured_log(
                LOGGER,
                "api_request",
                operation_id=operation_id,
                agent="api",
                source=None,
                error_state=error_state,
                duration_ms=duration_ms,
            )
            if response is not None:
                response.headers["X-Operation-Id"] = operation_id

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    @app.get("/ready")
    def ready(request: Request, response: Response) -> dict[str, object]:
        runtime: RuntimeState | None = request.app.state.runtime
        reference: ReferenceState | None = request.app.state.reference
        ready_now = runtime is not None or reference is not None
        if not ready_now:
            response.status_code = 503
        return {
            "ready": ready_now,
            "runtime_state": runtime is not None,
            "reference_state": reference is not None,
        }

    @app.get("/api/v1/system")
    def system(request: Request) -> dict[str, object]:
        runtime: RuntimeState | None = request.app.state.runtime
        reference: ReferenceState | None = request.app.state.reference
        return {
            "name": "Berlin Urban Intelligence",
            "version": __version__,
            "contract_version": "1.0.0",
            "runtime_generated_at": runtime.generated_at if runtime else None,
            "reference_generated_at": reference.generated_at if reference else None,
            "synthetic_production_fallback": False,
        }

    @app.get("/api/v1/agents")
    def agents(request: Request) -> list[dict[str, object]]:
        return [
            agent.descriptor.model_dump(mode="json") for agent in request.app.state.agents.values()
        ]

    @app.get("/api/v1/agents/health")
    def agent_health(request: Request) -> dict[str, object]:
        return {
            name: agent.health().model_dump(mode="json")
            for name, agent in request.app.state.agents.items()
        }

    @app.get("/api/v1/sources")
    def sources() -> list[dict[str, object]]:
        registry = SourceRegistry.from_yaml(DEFAULT_SOURCE_REGISTRY)
        return [source.model_dump(mode="json") for source in registry.all()]

    @app.get("/api/v1/source-status")
    def source_status(request: Request) -> dict[str, object]:
        runtime: RuntimeState | None = request.app.state.runtime
        if runtime is None:
            return {}
        return {
            key: value.model_dump(mode="json") for key, value in runtime.source_statuses.items()
        }

    @app.get("/api/v1/state")
    def state(request: Request) -> dict[str, object]:
        runtime: RuntimeState | None = request.app.state.runtime
        reference: ReferenceState | None = request.app.state.reference
        return {
            "runtime": runtime.model_dump(mode="json") if runtime else None,
            "reference_summary": {
                "critical_facilities": len(reference.critical_facilities),
                "official_model_features": len(reference.official_model_features),
                "transport_stops": len(reference.transport_stops),
                "network_nodes": len(reference.network_nodes),
                "network_edges": len(reference.network_edges),
                "errors": reference.errors,
            }
            if reference
            else None,
        }

    @app.get("/api/v1/observations")
    def observations(
        request: Request,
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=250, ge=1, le=MAX_PAGE_SIZE),
    ) -> list[dict[str, object]]:
        runtime: RuntimeState | None = request.app.state.runtime
        items = runtime.observations if runtime else ()
        return [item.model_dump(mode="json") for item in _slice(items, offset, limit)]

    @app.get("/api/v1/environment")
    def environment(request: Request) -> dict[str, object]:
        agent: ExposureAgent = request.app.state.agents["exposure"]
        return {
            "health": agent.health().model_dump(mode="json"),
            "observations": [item.model_dump(mode="json") for item in agent.observations()],
        }

    @app.get("/api/v1/heat")
    def heat(request: Request) -> dict[str, object]:
        agent: HeatAgent = request.app.state.agents["heat"]
        return {
            "health": agent.health().model_dump(mode="json"),
            "observations": [item.model_dump(mode="json") for item in agent.observations()],
        }

    @app.get("/api/v1/mobility")
    def mobility(request: Request) -> dict[str, object]:
        agent: MobilityAgent = request.app.state.agents["mobility"]
        snapshot = agent.snapshot()
        return {
            "health": agent.health().model_dump(mode="json"),
            "snapshot": snapshot.model_dump(mode="json") if snapshot else None,
        }

    @app.get("/api/v1/energy")
    def energy(request: Request) -> dict[str, object]:
        agent: EnergyAgent = request.app.state.agents["energy"]
        evaluation = agent.evaluation()
        return {
            "health": agent.health().model_dump(mode="json"),
            "evaluation": evaluation.model_dump(mode="json") if evaluation else None,
            "forecasts": [item.model_dump(mode="json") for item in agent.forecasts()],
        }

    @app.get("/api/v1/facilities")
    def facilities(
        request: Request,
        response: Response,
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=250, ge=1, le=MAX_PAGE_SIZE),
    ) -> list[dict[str, object]]:
        reference: ReferenceState | None = request.app.state.reference
        items = reference.critical_facilities if reference else ()
        response.headers["X-Total-Count"] = str(len(items))
        return [item.model_dump(mode="json") for item in _slice(items, offset, limit)]

    @app.get("/api/v1/climate-features")
    def climate_features(
        request: Request,
        response: Response,
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=250, ge=1, le=MAX_PAGE_SIZE),
    ) -> list[dict[str, object]]:
        reference: ReferenceState | None = request.app.state.reference
        items = reference.official_model_features if reference else ()
        response.headers["X-Total-Count"] = str(len(items))
        return [item.model_dump(mode="json") for item in _slice(items, offset, limit)]

    @app.get("/api/v1/transport-stops")
    def transport_stops(
        request: Request,
        response: Response,
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=250, ge=1, le=MAX_PAGE_SIZE),
    ) -> list[dict[str, object]]:
        reference: ReferenceState | None = request.app.state.reference
        items = reference.transport_stops if reference else ()
        response.headers["X-Total-Count"] = str(len(items))
        return [item.model_dump(mode="json") for item in _slice(items, offset, limit)]

    @app.get("/api/v1/network/nodes")
    def network_nodes(
        request: Request,
        response: Response,
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=500, ge=1, le=MAX_PAGE_SIZE),
    ) -> list[dict[str, object]]:
        reference: ReferenceState | None = request.app.state.reference
        items = reference.network_nodes if reference else ()
        response.headers["X-Total-Count"] = str(len(items))
        return [item.model_dump(mode="json") for item in _slice(items, offset, limit)]

    @app.post("/api/v1/scenarios/validate")
    def validate_scenario(scenario: Scenario) -> dict[str, object]:
        return {"valid": True, "scenario": scenario.model_dump(mode="json")}

    @app.post("/api/v1/orchestrate")
    def orchestrate(request: Request, payload: OrchestrationRequest) -> dict[str, object]:
        orchestrator: Orchestrator = request.app.state.orchestrator
        return {
            "plan": orchestrator.plan(payload).model_dump(mode="json"),
            "execution": orchestrator.execute(payload).model_dump(mode="json"),
        }

    @app.get("/api/v1/network/nearest")
    def nearest_network(
        request: Request,
        longitude: float = Query(ge=-180, le=180),
        latitude: float = Query(ge=-90, le=90),
    ) -> dict[str, object]:
        reference: ReferenceState | None = request.app.state.reference
        if reference is None or not reference.network_nodes:
            raise HTTPException(status_code=409, detail="INSUFFICIENT_DATA: routing network required")
        try:
            return nearest_network_node(
                longitude, latitude, reference.network_nodes
            ).model_dump(mode="json")
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=f"DERIVATION_FAILED: {exc}") from None

    @app.post("/api/v1/resilience/routes")
    def route(request: Request, payload: RouteRequest) -> dict[str, object]:
        if payload.scenario is not None:
            raise HTTPException(status_code=422, detail="baseline route does not accept a scenario")
        agent: ResilienceAgent = request.app.state.agents["resilience"]
        try:
            result = agent.shortest_path(payload.origin, payload.destination)
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"DERIVATION_FAILED: {exc}") from None
        reference: ReferenceState | None = request.app.state.reference
        nodes = {node.id: node for node in (reference.network_nodes if reference else ())}
        coordinates = [
            [nodes[node_id].longitude, nodes[node_id].latitude]
            for node_id in result.node_path
            if node_id in nodes
            and nodes[node_id].longitude is not None
            and nodes[node_id].latitude is not None
        ]
        body = result.model_dump(mode="json")
        body["geometry"] = (
            {"type": "LineString", "coordinates": coordinates} if len(coordinates) >= 2 else None
        )
        return body

    @app.post("/api/v1/resilience/routes/compare")
    def route_compare(request: Request, payload: RouteRequest) -> dict[str, object]:
        if payload.scenario is None:
            raise HTTPException(status_code=422, detail="scenario is required for route comparison")
        agent: ResilienceAgent = request.app.state.agents["resilience"]
        try:
            result = agent.compare_route(payload.origin, payload.destination, payload.scenario)
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"DERIVATION_FAILED: {exc}") from None
        reference: ReferenceState | None = request.app.state.reference
        node_lookup: dict[str, NetworkNode] = {
            node.id: node for node in (reference.network_nodes if reference else ())
        }

        def line(path: list[str]) -> dict[str, object] | None:
            coordinates = [
                [node_lookup[node_id].longitude, node_lookup[node_id].latitude]
                for node_id in path
                if node_id in node_lookup
                and node_lookup[node_id].longitude is not None
                and node_lookup[node_id].latitude is not None
            ]
            if len(coordinates) < 2:
                return None
            return {"type": "LineString", "coordinates": coordinates}

        body = result.model_dump(mode="json")
        body["baseline_geometry"] = line(result.baseline_node_path)
        body["scenario_geometry"] = line(result.scenario_node_path)
        return body

    @app.post("/api/v1/resilience/accessibility")
    def accessibility(request: Request, payload: AccessibilityRequest) -> dict[str, object]:
        reference: ReferenceState | None = request.app.state.reference
        if reference is None or not reference.network_nodes or not reference.critical_facilities:
            raise HTTPException(
                status_code=409, detail="INSUFFICIENT_DATA: network and facilities required"
            )
        agent: ResilienceAgent = request.app.state.agents["resilience"]
        try:
            result = agent.accessibility_links(
                payload.origin,
                reference.critical_facilities,
                reference.network_nodes,
                payload.travel_time_budget_s,
                scenario=payload.scenario,
                max_snap_distance_m=payload.max_snap_distance_m,
            )
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"DERIVATION_FAILED: {exc}") from None
        return result.model_dump(mode="json")

    @app.post("/api/v1/assess")
    def assess(request: Request, payload: AssessmentRequest) -> dict[str, object]:
        reference: ReferenceState | None = request.app.state.reference
        heat_agent: HeatAgent = request.app.state.agents["heat"]
        energy_agent: EnergyAgent = request.app.state.agents["energy"]
        resilience_agent: ResilienceAgent = request.app.state.agents["resilience"]
        service = IntegratedAssessmentService(
            heat=heat_agent,
            energy=energy_agent,
            resilience=resilience_agent,
            facilities=reference.critical_facilities if reference else (),
            network_nodes=reference.network_nodes if reference else (),
        )
        return service.assess(payload).model_dump(mode="json")

    @app.get("/api/v1/graph", response_class=PlainTextResponse)
    def graph(request: Request) -> str:
        agents = request.app.state.agents
        return _graph(
            request.app.state.runtime,
            request.app.state.reference,
            agents["energy"],
        ).serialize()

    return app


app = create_app()
