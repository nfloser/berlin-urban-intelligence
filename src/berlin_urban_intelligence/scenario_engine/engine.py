"""Deterministic scenario transformations that keep hypothetical state explicit."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from berlin_urban_intelligence.scenario_engine.models import Scenario
from berlin_urban_intelligence.shared.contracts import DataState, Forecast, Observation


class ScenarioTemperatureResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str
    baseline_id: str
    scenario_name: str
    phenomenon: str
    value: float
    unit: str
    state: DataState = DataState.SCENARIO


class ScenarioEnergyDemandResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str
    baseline_id: str
    scenario_name: str
    phenomenon: str
    value: float
    unit: str
    state: DataState = DataState.SCENARIO


class ScenarioEngine:
    def apply_temperature_delta(
        self, baseline: Observation, scenario: Scenario
    ) -> ScenarioTemperatureResult:
        if scenario.temperature_delta_c is None:
            raise ValueError("scenario does not define temperature_delta_c")
        if baseline.phenomenon != "air_temperature_2m":
            raise ValueError("temperature scenarios require an air_temperature_2m baseline")
        if baseline.unit not in {"Cel", "°C", "degC"}:
            raise ValueError("temperature scenario currently supports Celsius baselines only")
        if isinstance(baseline.value, bool) or not isinstance(baseline.value, (int, float)):
            raise TypeError("temperature baseline must be numeric")
        return ScenarioTemperatureResult(
            id=f"scenario:{scenario.name}:{baseline.id}",
            baseline_id=baseline.id,
            scenario_name=scenario.name,
            phenomenon=baseline.phenomenon,
            value=float(baseline.value) + scenario.temperature_delta_c,
            unit=baseline.unit,
        )

    def apply_energy_demand_delta(
        self, baseline: Forecast, scenario: Scenario
    ) -> ScenarioEnergyDemandResult:
        if scenario.energy_demand_delta_pct is None:
            raise ValueError("scenario does not define energy_demand_delta_pct")
        if baseline.value < 0:
            raise ValueError("energy-demand forecast baseline must not be negative")
        multiplier = 1.0 + scenario.energy_demand_delta_pct / 100.0
        return ScenarioEnergyDemandResult(
            id=f"scenario:{scenario.name}:{baseline.id}",
            baseline_id=baseline.id,
            scenario_name=scenario.name,
            phenomenon=baseline.phenomenon,
            value=baseline.value * multiplier,
            unit=baseline.unit,
        )
