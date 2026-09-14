"""Explicit hypothetical scenario contracts."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ScenarioKind(StrEnum):
    NETWORK_DISRUPTION = "network_disruption"
    EXTREME_HEAT = "extreme_heat"
    ENERGY_DEMAND = "energy_demand"
    INFRASTRUCTURE_DEGRADATION = "infrastructure_degradation"


class Scenario(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str | None = None
    name: str = Field(min_length=1)
    kinds: set[ScenarioKind] = Field(min_length=1)
    temperature_delta_c: float | None = Field(default=None, ge=-20.0, le=20.0)
    energy_demand_delta_pct: float | None = Field(default=None, ge=-100.0, le=500.0)
    closed_network_edges: list[str] = Field(default_factory=list, max_length=500)
    unavailable_facilities: list[str] = Field(default_factory=list, max_length=500)
    edge_penalties: dict[str, float] = Field(default_factory=dict, max_length=500)
    is_hypothetical: bool = True

    @model_validator(mode="after")
    def validate_scenario(self) -> "Scenario":
        if self.temperature_delta_c is not None and ScenarioKind.EXTREME_HEAT not in self.kinds:
            raise ValueError("temperature_delta_c requires extreme_heat scenario kind")
        if self.energy_demand_delta_pct is not None and ScenarioKind.ENERGY_DEMAND not in self.kinds:
            raise ValueError("energy_demand_delta_pct requires energy_demand scenario kind")
        if (self.closed_network_edges or self.edge_penalties) and ScenarioKind.NETWORK_DISRUPTION not in self.kinds:
            raise ValueError("network edge changes require network_disruption scenario kind")
        if self.unavailable_facilities and ScenarioKind.INFRASTRUCTURE_DEGRADATION not in self.kinds:
            raise ValueError("facility changes require infrastructure_degradation scenario kind")
        if any(penalty < 1.0 or penalty > 100.0 for penalty in self.edge_penalties.values()):
            raise ValueError("edge penalties must be between 1.0 and 100.0")
        identifiers = [*self.closed_network_edges, *self.unavailable_facilities, *self.edge_penalties.keys()]
        if any(not identifier.strip() for identifier in identifiers):
            raise ValueError("scenario identifiers must not be blank")
        if not self.is_hypothetical:
            raise ValueError("Scenario objects are always hypothetical")
        return self
