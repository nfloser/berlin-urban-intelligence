from fastapi.testclient import TestClient

from berlin_urban_intelligence.api.app import create_app


def test_agent_api_exposes_complete_metadata_and_composed_health(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("BUI_RUNTIME_STATE", str(tmp_path / "missing-runtime.json"))
    monkeypatch.setenv("BUI_REFERENCE_STATE", str(tmp_path / "missing-reference.json"))
    monkeypatch.setenv("BUI_ENERGY_STATE", str(tmp_path / "missing-energy.json"))
    monkeypatch.setenv("BUI_DERIVED_STATE", str(tmp_path / "missing-derived.json"))

    with TestClient(create_app()) as client:
        descriptors_response = client.get("/api/v1/agents")
        health_response = client.get("/api/v1/agents/health")

    assert descriptors_response.status_code == 200
    descriptors = {item["id"]: item for item in descriptors_response.json()}
    assert set(descriptors) == {
        "live_state",
        "mobility",
        "exposure",
        "heat",
        "energy",
        "resilience",
    }
    for descriptor in descriptors.values():
        assert descriptor["name"]
        assert descriptor["domain"]
        assert descriptor["capabilities"]
        assert descriptor["input_contracts"]
        assert descriptor["output_contracts"]

    assert set(descriptors["live_state"]["agent_dependencies"]) == {
        "mobility",
        "exposure",
        "heat",
        "energy",
        "resilience",
    }

    assert health_response.status_code == 200
    health = health_response.json()
    assert set(health) == set(descriptors)
    for agent_id in ("mobility", "exposure", "heat", "energy", "resilience"):
        assert health[agent_id]["agent_id"] == agent_id
        assert health[agent_id]["status"] == "unavailable"
    assert health["live_state"]["agent_id"] == "live_state"
    assert health["live_state"]["status"] == "unavailable"
    assert "synthetic" in health["live_state"]["detail"].lower()
