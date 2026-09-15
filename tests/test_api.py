from datetime import UTC, datetime
from uuid import UUID

from fastapi.testclient import TestClient

from berlin_urban_intelligence.api.app import create_app
from berlin_urban_intelligence.runtime.state import RuntimeState, RuntimeStateStore


def client_without_state(monkeypatch, tmp_path) -> TestClient:
    monkeypatch.setenv("BUI_RUNTIME_STATE", str(tmp_path / "missing-runtime.json"))
    monkeypatch.setenv("BUI_REFERENCE_STATE", str(tmp_path / "missing-reference.json"))
    monkeypatch.setenv("BUI_ENERGY_STATE", str(tmp_path / "missing-energy.json"))
    return TestClient(create_app())


def test_liveness_is_independent_of_data_availability(monkeypatch, tmp_path) -> None:
    with client_without_state(monkeypatch, tmp_path) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    UUID(response.headers["X-Operation-Id"])


def test_readiness_reports_missing_persisted_state(monkeypatch, tmp_path) -> None:
    with client_without_state(monkeypatch, tmp_path) as client:
        response = client.get("/ready")
    assert response.status_code == 503
    assert response.json() == {
        "ready": False,
        "runtime_state": False,
        "reference_state": False,
    }


def test_unavailable_domains_are_not_replaced_with_demo_values(monkeypatch, tmp_path) -> None:
    with client_without_state(monkeypatch, tmp_path) as client:
        mobility = client.get("/api/v1/mobility").json()
        energy = client.get("/api/v1/energy").json()
    assert mobility["snapshot"] is None
    assert mobility["health"]["status"] == "unavailable"
    assert energy["evaluation"] is None
    assert energy["forecasts"] == []
    assert energy["health"]["status"] == "unavailable"


def test_scenario_endpoint_preserves_hypothetical_parameters(monkeypatch, tmp_path) -> None:
    payload = {
        "name": "fixture-heat",
        "kinds": ["extreme_heat"],
        "temperature_delta_c": 3.0,
    }
    with client_without_state(monkeypatch, tmp_path) as client:
        response = client.post("/api/v1/scenarios/validate", json=payload)
    assert response.status_code == 200
    assert response.json()["scenario"]["temperature_delta_c"] == 3.0


def test_map_payloads_have_hard_page_limit(monkeypatch, tmp_path) -> None:
    with client_without_state(monkeypatch, tmp_path) as client:
        response = client.get("/api/v1/facilities?limit=1001")
    assert response.status_code == 422


def test_running_api_reloads_changed_runtime_snapshot(monkeypatch, tmp_path) -> None:
    runtime_path = tmp_path / "runtime.json"
    reference_path = tmp_path / "missing-reference.json"
    energy_path = tmp_path / "missing-energy.json"
    monkeypatch.setenv("BUI_RUNTIME_STATE", str(runtime_path))
    monkeypatch.setenv("BUI_REFERENCE_STATE", str(reference_path))
    monkeypatch.setenv("BUI_ENERGY_STATE", str(energy_path))

    first_time = datetime(2026, 9, 15, 7, 0, tzinfo=UTC)
    second_time = datetime(2026, 9, 15, 7, 5, tzinfo=UTC)
    store = RuntimeStateStore(runtime_path)
    store.save(RuntimeState(generated_at=first_time))

    with TestClient(create_app()) as client:
        first = client.get("/api/v1/system").json()
        assert first["runtime_generated_at"] == first_time.isoformat().replace("+00:00", "Z")

        store.save(RuntimeState(generated_at=second_time))
        second = client.get("/api/v1/system").json()

    assert second["runtime_generated_at"] == second_time.isoformat().replace("+00:00", "Z")
    assert second["snapshot_reload"]["runtime"]["status"] == "current"
    assert second["snapshot_reload"]["runtime"]["last_error"] is None


def test_invalid_runtime_replacement_preserves_last_known_good_state(monkeypatch, tmp_path) -> None:
    runtime_path = tmp_path / "runtime.json"
    reference_path = tmp_path / "missing-reference.json"
    energy_path = tmp_path / "missing-energy.json"
    monkeypatch.setenv("BUI_RUNTIME_STATE", str(runtime_path))
    monkeypatch.setenv("BUI_REFERENCE_STATE", str(reference_path))
    monkeypatch.setenv("BUI_ENERGY_STATE", str(energy_path))

    generated_at = datetime(2026, 9, 15, 7, 0, tzinfo=UTC)
    RuntimeStateStore(runtime_path).save(RuntimeState(generated_at=generated_at))

    with TestClient(create_app()) as client:
        assert client.get("/api/v1/system").json()[
            "runtime_generated_at"
        ] == generated_at.isoformat().replace("+00:00", "Z")
        runtime_path.write_text("{not-valid-json", encoding="utf-8")
        response = client.get("/api/v1/system")

    assert response.status_code == 200
    body = response.json()
    assert body["runtime_generated_at"] == generated_at.isoformat().replace("+00:00", "Z")
    assert body["snapshot_reload"]["runtime"]["status"] == "invalid"
    assert body["snapshot_reload"]["runtime"]["last_error"]
