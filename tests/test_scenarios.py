import pytest
from pydantic import ValidationError

from berlin_urban_intelligence.scenario_engine.models import Scenario, ScenarioKind


def test_temperature_delta_requires_heat_kind() -> None:
    with pytest.raises(ValidationError, match="extreme_heat"):
        Scenario(
            name="fixture-scenario",
            kinds={ScenarioKind.NETWORK_DISRUPTION},
            temperature_delta_c=3.0,
        )


def test_heat_kind_requires_temperature_delta() -> None:
    with pytest.raises(ValidationError, match="temperature_delta_c"):
        Scenario(
            name="fixture-scenario",
            kinds={ScenarioKind.EXTREME_HEAT},
        )


def test_energy_kind_requires_demand_delta() -> None:
    with pytest.raises(ValidationError, match="energy_demand_delta_pct"):
        Scenario(
            name="fixture-scenario",
            kinds={ScenarioKind.ENERGY_DEMAND},
        )


def test_network_changes_require_disruption_kind() -> None:
    with pytest.raises(ValidationError, match="network_disruption"):
        Scenario(
            name="fixture-scenario",
            kinds={ScenarioKind.EXTREME_HEAT},
            temperature_delta_c=3.0,
            closed_network_edges=["fixture-edge"],
        )


def test_scenario_resource_limits_are_enforced() -> None:
    with pytest.raises(ValidationError):
        Scenario(
            name="fixture-scenario",
            kinds={ScenarioKind.NETWORK_DISRUPTION},
            closed_network_edges=[f"fixture-edge-{index}" for index in range(501)],
        )


def test_valid_compound_scenario_remains_hypothetical() -> None:
    scenario = Scenario(
        name="fixture-compound",
        kinds={ScenarioKind.EXTREME_HEAT, ScenarioKind.ENERGY_DEMAND},
        temperature_delta_c=3.0,
        energy_demand_delta_pct=10.0,
    )
    assert scenario.temperature_delta_c == 3.0
    assert ScenarioKind.ENERGY_DEMAND in scenario.kinds
