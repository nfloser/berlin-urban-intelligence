from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from berlin_urban_intelligence.api.app import create_app
from berlin_urban_intelligence.runtime.state import RuntimeState, RuntimeStateStore


@pytest.fixture
def client(tmp_path):
    return TestClient(create_app(data_dir=tmp_path))


def test_empty_install_is_explicit(client):
    assert client.get("/health").status_code == 200
    assert client.get("/ready").status_code == 503
    assert client.get("/api/v1/observations").json() == []
    assert client.get("/api/v1/energy").json()["forecasts"] == []
    assert len(client.get("/api/v1/agents").json()) == 6


def test_all_documented_reads_and_openapi(client):
    for endpoint in (
        "system",
        "agents",
        "agents/health",
        "sources",
        "source-status",
        "state",
        "observations",
        "environment",
        "heat",
        "mobility",
        "energy",
        "resilience",
        "reference",
        "map",
        "graph",
    ):
        assert client.get("/api/v1/" + endpoint).status_code == 200, endpoint
    schema = client.get("/openapi.json").json()
    assert "/api/v1/assessments" in schema["paths"]


def test_reload_state_without_restart(tmp_path):
    client = TestClient(create_app(data_dir=tmp_path))
    assert client.get("/ready").status_code == 503
    RuntimeStateStore(tmp_path / "state.json").save(RuntimeState(generated_at=datetime.now(UTC)))
    assert client.get("/api/v1/state").json()["generated_at"]
    # An empty persisted snapshot does not mean operational data readiness.
    assert client.get("/ready").status_code == 503


def test_corrupt_state_is_structured_error(tmp_path):
    (tmp_path / "state.json").write_text("{broken")
    client = TestClient(create_app(data_dir=tmp_path))
    response = client.get("/api/v1/state")
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "STATE_UNREADABLE"


def test_scenario_validation_and_no_fabricated_assessment(client):
    scenario = {"name": "Heat +3", "kinds": ["extreme_heat"], "temperature_delta_c": 3}
    assert client.post("/api/v1/scenarios/validate", json=scenario).status_code == 200
    result = client.post("/api/v1/assessments", json={"scenario": scenario})
    assert result.status_code == 200
    assert result.json()["heat"] is None
    assert result.json()["unavailable_dimensions"] == ["heat"]
    assert (
        client.post(
            "/api/v1/scenarios/validate", json={**scenario, "is_hypothetical": False}
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/scenarios/validate", json={"name": "Missing delta", "kinds": ["extreme_heat"]}
        ).status_code
        == 422
    )


def test_unknown_workflow_and_missing_route(client):
    assert client.post("/api/v1/orchestrate", json={"workflow": "invented"}).status_code == 422
    response = client.post("/api/v1/orchestrate", json={"workflow": "urban_snapshot"})
    assert response.json()["execution"]["status"] == "unavailable"
    response = client.post("/api/v1/routes", json={"origin": "a", "destination": "b"})
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "ROUTE_UNAVAILABLE"
