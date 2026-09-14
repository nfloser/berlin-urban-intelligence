from pathlib import Path

from fastapi.testclient import TestClient

from berlin_urban_intelligence.api import app as api_module
from berlin_urban_intelligence.api.app import create_app


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
