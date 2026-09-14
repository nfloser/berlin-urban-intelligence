"""Read persisted canonical state and execute explicit, immutable research scenarios."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import networkx as nx
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field

from berlin_urban_intelligence.agents.base import BaseAgent
from berlin_urban_intelligence.agents.energy import EnergyAgent
from berlin_urban_intelligence.agents.exposure import ExposureAgent
from berlin_urban_intelligence.agents.heat import HeatAgent
from berlin_urban_intelligence.agents.live_state import LiveStateAgent
from berlin_urban_intelligence.agents.mobility import MobilityAgent
from berlin_urban_intelligence.agents.resilience import ResilienceAgent
from berlin_urban_intelligence.energy.state import EnergyStateStore
from berlin_urban_intelligence.knowledge.graph import KnowledgeGraph
from berlin_urban_intelligence.orchestrator.assessment import (
    AssessmentRequest,
    IntegratedAssessment,
    IntegratedAssessmentService,
)
from berlin_urban_intelligence.orchestrator.engine import OrchestrationRequest, Orchestrator
from berlin_urban_intelligence.runtime.reference import ReferenceState, ReferenceStateStore
from berlin_urban_intelligence.runtime.state import RuntimeState, RuntimeStateStore
from berlin_urban_intelligence.scenario_engine.models import Scenario
from berlin_urban_intelligence.shared.contracts import AgentDescriptor, Observation
from berlin_urban_intelligence.shared.source_registry import SourceDefinition, SourceRegistry
from berlin_urban_intelligence.shared.source_status import SourceRuntimeStatus, SourceStatusStore


class RouteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    origin: str = Field(min_length=1)
    destination: str = Field(min_length=1)
    scenario: Scenario | None = None


def create_app(*, data_dir: Path | str | None = None) -> FastAPI:
    app = FastAPI(title="Berlin Urban Intelligence", version="0.1.0")
    root = Path(data_dir or os.environ.get("BUI_DATA_DIR", "data/runtime"))
    live_path = (
        Path(os.getenv("BUI_RUNTIME_STATE", str(root / "state.json")))
        if data_dir is None
        else root / "state.json"
    )

    def load() -> tuple[RuntimeState | None, ReferenceState | None, dict[str, BaseAgent]]:
        try:
            state = RuntimeStateStore(live_path).load()
            reference = ReferenceStateStore(root / "reference.json").load()
            energy_state = EnergyStateStore(root / "energy.json").load()
            observations = state.observations if state else ()
            energy = EnergyAgent()
            if energy_state:
                energy.register_berlin_evaluation(energy_state.evaluation)
                for forecast in energy_state.forecasts:
                    energy.register_forecast(forecast)
            agents: dict[str, BaseAgent] = {
                "heat": HeatAgent([o for o in observations if o.provenance.agent == "heat"]),
                "exposure": ExposureAgent(
                    [o for o in observations if o.provenance.agent == "exposure"]
                ),
                "mobility": MobilityAgent(state.mobility if state else None),
                "energy": energy,
                "resilience": ResilienceAgent(list(reference.network_edges) if reference else []),
            }
            agents["live_state"] = LiveStateAgent(list(agents.values()))
            return state, reference, agents
        except (ValueError, OSError) as exc:
            raise HTTPException(
                503,
                detail={
                    "code": "STATE_UNREADABLE",
                    ("message"): (
                        "Persisted state could not be validated; refresh or restore the "
                        "affected file."
                    ),
                },
            ) from exc

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/ready")
    def ready() -> dict[str, str]:
        _, _, agents = load()
        if not any(
            a.health().status == "available" for key, a in agents.items() if key != "live_state"
        ):
            raise HTTPException(
                503,
                detail={
                    "code": "DATA_UNAVAILABLE",
                    "message": "No domain has current operational data.",
                },
            )
        return {"status": "ready"}

    @app.get("/api/v1/system")
    def system() -> dict[str, Any]:
        _, _, agents = load()
        live = agents["live_state"]
        assert isinstance(live, LiveStateAgent)
        return {
            "version": app.version,
            "city": "Berlin",
            "snapshot": live.snapshot(),
            "research_only": True,
        }

    @app.get("/api/v1/agents")
    def descriptors() -> list[AgentDescriptor]:
        return [a.descriptor for a in load()[2].values()]

    @app.get("/api/v1/agents/health")
    def agent_health() -> dict[str, Any]:
        return {key: agent.health() for key, agent in load()[2].items()}

    @app.get("/api/v1/state")
    def state() -> RuntimeState | None:
        return load()[0]

    @app.get("/api/v1/reference")
    def reference() -> ReferenceState | None:
        return load()[1]

    @app.get("/api/v1/observations")
    def observations(phenomenon: str | None = None) -> list[Observation]:
        current = load()[0]
        return (
            [o for o in current.observations if phenomenon is None or o.phenomenon == phenomenon]
            if current
            else []
        )

    @app.get("/api/v1/sources")
    def sources() -> list[SourceDefinition]:
        return SourceRegistry.from_yaml(
            Path(os.getenv("BUI_SOURCE_REGISTRY", "config/sources.yaml"))
        ).all()

    @app.get("/api/v1/source-status")
    def source_status() -> list[SourceRuntimeStatus]:
        current = load()[0]
        store = SourceStatusStore(current.source_statuses if current else {})
        thresholds = {"dwd_open_data": 3600, "vbb_gtfs_rt": 900, "berlin_air_quality": 7200}
        return [
            store.get(
                s.id,
                now=datetime.now(UTC),
                freshness_threshold=timedelta(seconds=thresholds.get(s.id, 86400)),
            )
            for s in sources()
        ]

    @app.get("/api/v1/heat")
    def heat() -> dict[str, Any]:
        _, reference, agents = load()
        agent = agents["heat"]
        assert isinstance(agent, HeatAgent)
        return {
            "health": agent.health(),
            "observations": agent.observations(),
            "official_model_features": reference.official_model_features if reference else [],
        }

    @app.get("/api/v1/environment")
    def environment() -> dict[str, Any]:
        agent = load()[2]["exposure"]
        assert isinstance(agent, ExposureAgent)
        return {"health": agent.health(), "observations": agent.observations()}

    @app.get("/api/v1/mobility")
    def mobility() -> dict[str, Any]:
        current, reference, agents = load()
        return {
            "health": agents["mobility"].health(),
            "snapshot": current.mobility if current else None,
            "transport_stops": reference.transport_stops if reference else [],
        }

    @app.get("/api/v1/energy")
    def energy() -> dict[str, Any]:
        agent = load()[2]["energy"]
        assert isinstance(agent, EnergyAgent)
        return {
            "health": agent.health(),
            "evaluation": agent.evaluation(),
            "forecasts": agent.forecasts(),
        }

    @app.get("/api/v1/resilience")
    def resilience() -> dict[str, Any]:
        _, reference, agents = load()
        return {
            "health": agents["resilience"].health(),
            "nodes": len(reference.network_nodes) if reference else 0,
            "edges": len(reference.network_edges) if reference else 0,
            "critical_facilities": reference.critical_facilities if reference else [],
        }

    @app.get("/api/v1/graph", response_class=Response)
    def graph() -> Response:
        current, reference, agents = load()
        kg = KnowledgeGraph()
        for observation in current.observations if current else ():
            kg.add_observation(observation)
        if reference:
            for entity in (*reference.critical_facilities, *reference.transport_stops):
                kg.add_entity(entity)
            for feature in reference.official_model_features:
                kg.add_official_model_feature(feature)
            for node in reference.network_nodes:
                kg.add_network_node(node)
            for edge in reference.network_edges:
                kg.add_network_edge(edge)
        agent = agents["energy"]
        assert isinstance(agent, EnergyAgent)
        for forecast in agent.forecasts():
            kg.add_forecast(forecast)
        return Response(kg.serialize(), media_type="text/turtle")

    @app.get("/api/v1/map")
    def map_features() -> dict[str, Any]:
        current, reference, _ = load()
        features: list[dict[str, Any]] = []
        items = list(current.observations) if current else []
        for item in items:
            if item.spatial and item.spatial.geometry and item.spatial.crs == "EPSG:4326":
                features.append(
                    {
                        "type": "Feature",
                        "geometry": item.spatial.geometry,
                        "properties": {
                            "id": item.id,
                            "kind": "observation",
                            "label": item.phenomenon,
                            "state": item.state,
                        },
                    }
                )
        if reference:
            for entity in (*reference.critical_facilities, *reference.transport_stops):
                if entity.spatial and entity.spatial.geometry and entity.spatial.crs == "EPSG:4326":
                    features.append(
                        {
                            "type": "Feature",
                            "geometry": entity.spatial.geometry,
                            "properties": {
                                "id": entity.id,
                                "kind": entity.entity_type,
                                "label": entity.name or entity.id,
                            },
                        }
                    )
            for feature in reference.official_model_features:
                if feature.spatial.crs == "EPSG:4326":
                    features.append(
                        {
                            "type": "Feature",
                            "geometry": feature.spatial.geometry,
                            "properties": {
                                "id": feature.id,
                                "kind": "climate",
                                "state": feature.state,
                            },
                        }
                    )
        return {"type": "FeatureCollection", "features": features}

    @app.post("/api/v1/scenarios/validate")
    def validate_scenario(scenario: Scenario) -> Scenario:
        return scenario

    @app.post("/api/v1/orchestrate")
    def orchestrate(request: OrchestrationRequest) -> dict[str, Any]:
        orchestrator = Orchestrator(load()[2])
        return {"plan": orchestrator.plan(request), "execution": orchestrator.execute(request)}

    @app.post("/api/v1/assessments")
    def assess(request: AssessmentRequest) -> IntegratedAssessment:
        _, reference, agents = load()
        heat_agent, energy_agent, resilience_agent = (
            agents["heat"],
            agents["energy"],
            agents["resilience"],
        )
        assert isinstance(heat_agent, HeatAgent)
        assert isinstance(energy_agent, EnergyAgent)
        assert isinstance(resilience_agent, ResilienceAgent)
        return IntegratedAssessmentService(
            heat=heat_agent,
            energy=energy_agent,
            resilience=resilience_agent,
            facilities=reference.critical_facilities if reference else (),
            network_nodes=reference.network_nodes if reference else (),
        ).assess(request)

    @app.post("/api/v1/routes")
    def route(request: RouteRequest) -> Any:
        agent = load()[2]["resilience"]
        assert isinstance(agent, ResilienceAgent)
        try:
            if request.scenario:
                return agent.compare_route(request.origin, request.destination, request.scenario)
            return agent.shortest_path(request.origin, request.destination)
        except (nx.NetworkXException, KeyError, ValueError) as exc:
            raise HTTPException(
                404,
                detail={
                    "code": "ROUTE_UNAVAILABLE",
                    "message": "No route exists for the supplied nodes and network.",
                },
            ) from exc

    return app


app = create_app()
