"""Typed multi-domain scenario assessment without composite scoring."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from berlin_urban_intelligence.agents.energy import EnergyAgent
from berlin_urban_intelligence.agents.heat import HeatAgent
from berlin_urban_intelligence.agents.resilience import ResilienceAgent, SnappedAccessibilityResult
from berlin_urban_intelligence.scenario_engine.engine import ScenarioEnergyDemandResult, ScenarioEngine, ScenarioTemperatureResult
from berlin_urban_intelligence.scenario_engine.models import Scenario, ScenarioKind
from berlin_urban_intelligence.shared.contracts import CriticalFacility, NetworkNode


class AssessmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    scenario: Scenario
    origin_node: str | None = None
    travel_time_budget_s: float = Field(default=900.0, gt=0, le=86_400)
    max_snap_distance_m: float = Field(default=1_000.0, gt=0, le=50_000)

    @model_validator(mode="after")
    def validate_network_inputs(self) -> "AssessmentRequest":
        network_kinds = {ScenarioKind.NETWORK_DISRUPTION, ScenarioKind.INFRASTRUCTURE_DEGRADATION}
        if self.scenario.kinds & network_kinds and not self.origin_node:
            raise ValueError("network/infrastructure assessment requires origin_node")
        return self


class IntegratedAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    generated_at: datetime
    scenario_name: str
    heat: ScenarioTemperatureResult | None = None
    energy: ScenarioEnergyDemandResult | None = None
    resilience: SnappedAccessibilityResult | None = None
    unavailable_dimensions: list[str] = Field(default_factory=list)
    dimension_errors: dict[str, str] = Field(default_factory=dict)
    composite_score: None = None
    note: str = (
        "Dimensions are intentionally reported independently. No cross-domain composite score "
        "or causal claim is produced."
    )


class IntegratedAssessmentService:
    """Coordinate transparent domain calculations for one explicit hypothetical scenario."""

    def __init__(self, *, heat: HeatAgent, energy: EnergyAgent, resilience: ResilienceAgent, facilities: tuple[CriticalFacility, ...] | list[CriticalFacility] = (), network_nodes: tuple[NetworkNode, ...] | list[NetworkNode] = (), now_factory: Callable[[], datetime] | None = None) -> None:
        self.heat = heat
        self.energy = energy
        self.resilience = resilience
        self.facilities = tuple(facilities)
        self.network_nodes = tuple(network_nodes)
        self.now_factory = now_factory or (lambda: datetime.now(UTC))
        self.scenarios = ScenarioEngine()

    def assess(self, request: AssessmentRequest) -> IntegratedAssessment:
        now = self.now_factory()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("now_factory must return a timezone-aware datetime")
        now = now.astimezone(UTC)
        unavailable: list[str] = []
        errors: dict[str, str] = {}
        heat_result: ScenarioTemperatureResult | None = None
        energy_result: ScenarioEnergyDemandResult | None = None
        resilience_result: SnappedAccessibilityResult | None = None

        if ScenarioKind.EXTREME_HEAT in request.scenario.kinds:
            candidates = [item for item in self.heat.observations() if item.phenomenon == "air_temperature_2m"]
            if not candidates:
                unavailable.append("heat")
                errors["heat"] = "INSUFFICIENT_DATA: no measured air_temperature_2m baseline"
            else:
                baseline = max(candidates, key=lambda item: item.observed_at)
                heat_result = self.scenarios.apply_temperature_delta(baseline, request.scenario)

        if ScenarioKind.ENERGY_DEMAND in request.scenario.kinds:
            forecasts = self.energy.forecasts()
            if not forecasts:
                unavailable.append("energy")
                errors["energy"] = "MODEL_UNAVAILABLE: no validated Berlin forecast baseline"
            else:
                baseline_forecast = max(forecasts, key=lambda item: (item.valid_at, item.issued_at))
                energy_result = self.scenarios.apply_energy_demand_delta(baseline_forecast, request.scenario)

        if request.scenario.kinds & {ScenarioKind.NETWORK_DISRUPTION, ScenarioKind.INFRASTRUCTURE_DEGRADATION}:
            if not self.facilities or not self.network_nodes:
                unavailable.append("resilience")
                errors["resilience"] = "INSUFFICIENT_DATA: persisted network nodes and critical facilities are required"
            else:
                try:
                    resilience_result = self.resilience.accessibility_links(
                        request.origin_node or "", self.facilities, self.network_nodes,
                        request.travel_time_budget_s, scenario=request.scenario,
                        max_snap_distance_m=request.max_snap_distance_m,
                    )
                except (ValueError, KeyError) as exc:
                    unavailable.append("resilience")
                    errors["resilience"] = f"DERIVATION_FAILED: {exc}"

        return IntegratedAssessment(
            generated_at=now,
            scenario_name=request.scenario.name,
            heat=heat_result,
            energy=energy_result,
            resilience=resilience_result,
            unavailable_dimensions=sorted(set(unavailable)),
            dimension_errors=dict(sorted(errors.items())),
        )
