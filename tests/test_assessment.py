from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from berlin_urban_intelligence.agents.energy import EnergyAgent
from berlin_urban_intelligence.agents.heat import HeatAgent
from berlin_urban_intelligence.agents.resilience import ResilienceAgent
from berlin_urban_intelligence.api import app as api_module
from berlin_urban_intelligence.api.app import create_app
from berlin_urban_intelligence.orchestrator.assessment import (
    AssessmentRequest,
    IntegratedAssessmentService,
)
from berlin_urban_intelligence.scenario_engine.models import Scenario, ScenarioKind
from berlin_urban_intelligence.shared.contracts import (
    DataState,
    Forecast,
    Observation,
    Provenance,
    QualityFlag,
)

NOW = datetime(2026, 9, 15, 10, 0, tzinfo=UTC)


def provenance() -> Provenance:
    return Provenance(
        provider="fixture-provider",
        dataset="fixture-dataset",
        source_url="https://example.invalid/fixture",
        retrieved_at=NOW,
        processed_at=NOW,
        processing_method="deterministic test fixture",
        agent="fixture-agent",
        agent_version="0.0-test",
    )


def heat_observation(
    observed_at: datetime,
    *,
    quality: QualityFlag = QualityFlag.VALID,
) -> Observation:
    return Observation(
        id=f"fixture:heat:{observed_at.isoformat()}",
        entity_id="fixture:station",
        phenomenon="air_temperature_2m",
        value=20.0,
        unit="Cel",
        observed_at=observed_at,
        state=DataState.OBSERVED,
        quality=quality,
        provenance=provenance(),
    )


def energy_forecast(issued_at: datetime, valid_at: datetime) -> Forecast:
    return Forecast(
        id=f"fixture:forecast:{issued_at.isoformat()}",
        entity_id="fixture:grid",
        phenomenon="energy_demand",
        value=100.0,
        unit="MW",
        issued_at=issued_at,
        valid_at=valid_at,
        quality=QualityFlag.VALID,
        provenance=provenance(),
    )


class FixtureEnergyAgent(EnergyAgent):
    def __init__(self, forecasts: tuple[Forecast, ...]) -> None:
        super().__init__(now_factory=lambda: NOW)
        self._fixture_forecasts = forecasts

    def forecasts(self) -> tuple[Forecast, ...]:
        return self._fixture_forecasts


def service(
    *,
    heat: tuple[Observation, ...] = (),
    energy: tuple[Forecast, ...] = (),
) -> IntegratedAssessmentService:
    return IntegratedAssessmentService(
        heat=HeatAgent(heat, now_factory=lambda: NOW),
        energy=FixtureEnergyAgent(energy),
        resilience=ResilienceAgent(now_factory=lambda: NOW),
        now_factory=lambda: NOW,
    )


def test_assessment_reports_missing_heat_baseline_without_fabrication(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(api_module, "DEFAULT_RUNTIME_STATE", tmp_path / "missing-runtime.json")
    monkeypatch.setattr(api_module, "DEFAULT_REFERENCE_STATE", tmp_path / "missing-reference.json")
    monkeypatch.setattr(api_module, "DEFAULT_ENERGY_STATE", tmp_path / "missing-energy.json")
    app = create_app()
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/assess",
            json={
                "scenario": {
                    "name": "fixture heat stress",
                    "kinds": ["extreme_heat"],
                    "temperature_delta_c": 3.0,
                }
            },
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload["heat"] is None
    assert payload["unavailable_dimensions"] == ["heat"]
    assert payload["dimension_errors"]["heat"].startswith("INSUFFICIENT_DATA")
    assert payload["composite_score"] is None


@pytest.mark.parametrize(
    ("observed_at", "quality"),
    [
        (NOW - timedelta(hours=2), QualityFlag.VALID),
        (NOW + timedelta(minutes=5), QualityFlag.VALID),
        (NOW - timedelta(minutes=5), QualityFlag.STALE),
        (NOW - timedelta(minutes=5), QualityFlag.INVALID),
    ],
)
def test_heat_assessment_rejects_noncurrent_baselines(
    observed_at: datetime, quality: QualityFlag
) -> None:
    assessment = service(heat=(heat_observation(observed_at, quality=quality),)).assess(
        AssessmentRequest(
            scenario=Scenario(
                name="fixture heat stress",
                kinds={ScenarioKind.EXTREME_HEAT},
                temperature_delta_c=3.0,
            )
        )
    )

    assert assessment.heat is None
    assert assessment.unavailable_dimensions == ["heat"]
    assert "current measured" in assessment.dimension_errors["heat"]


@pytest.mark.parametrize(
    ("issued_at", "valid_at"),
    [
        (NOW - timedelta(hours=2), NOW - timedelta(minutes=1)),
        (NOW + timedelta(minutes=1), NOW + timedelta(hours=1)),
    ],
)
def test_energy_assessment_rejects_forecasts_outside_validity_window(
    issued_at: datetime, valid_at: datetime
) -> None:
    assessment = service(energy=(energy_forecast(issued_at, valid_at),)).assess(
        AssessmentRequest(
            scenario=Scenario(
                name="fixture demand stress",
                kinds={ScenarioKind.ENERGY_DEMAND},
                energy_demand_delta_pct=10.0,
            )
        )
    )

    assert assessment.energy is None
    assert assessment.unavailable_dimensions == ["energy"]
    assert assessment.dimension_errors["energy"].startswith("MODEL_UNAVAILABLE")


def test_assessment_accepts_current_heat_and_energy_baselines() -> None:
    assessment = service(
        heat=(heat_observation(NOW - timedelta(minutes=30)),),
        energy=(energy_forecast(NOW - timedelta(minutes=15), NOW + timedelta(minutes=15)),),
    ).assess(
        AssessmentRequest(
            scenario=Scenario(
                name="fixture compound stress",
                kinds={ScenarioKind.EXTREME_HEAT, ScenarioKind.ENERGY_DEMAND},
                temperature_delta_c=3.0,
                energy_demand_delta_pct=10.0,
            )
        )
    )

    assert assessment.heat is not None
    assert assessment.heat.value == 23.0
    assert assessment.energy is not None
    assert assessment.energy.value == 110.0
    assert assessment.unavailable_dimensions == []


def test_network_assessment_requires_origin_node() -> None:
    app = create_app()
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/assess",
            json={
                "scenario": {
                    "name": "fixture closure",
                    "kinds": ["network_disruption"],
                    "closed_network_edges": ["edge-1"],
                }
            },
        )
    assert response.status_code == 422
