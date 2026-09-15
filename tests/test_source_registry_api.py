from fastapi.testclient import TestClient

from berlin_urban_intelligence.api.app import create_app


def test_sources_endpoint_uses_configured_registry_path(monkeypatch, tmp_path) -> None:
    registry = tmp_path / "sources.yaml"
    registry.write_text(
        """sources:
  - id: acceptance_source
    provider: Acceptance Provider
    dataset: Acceptance Dataset
    domain: acceptance
    reference_url: https://example.invalid/source
    authoritative: false
    expected_update_frequency: test-only
    spatial_coverage: acceptance fixture
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("BUI_SOURCE_REGISTRY", str(registry))
    monkeypatch.setenv("BUI_RUNTIME_STATE", str(tmp_path / "missing-runtime.json"))
    monkeypatch.setenv("BUI_REFERENCE_STATE", str(tmp_path / "missing-reference.json"))
    monkeypatch.setenv("BUI_ENERGY_STATE", str(tmp_path / "missing-energy.json"))
    monkeypatch.setenv("BUI_DERIVED_STATE", str(tmp_path / "missing-derived.json"))

    with TestClient(create_app()) as client:
        response = client.get("/api/v1/sources")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": "acceptance_source",
            "provider": "Acceptance Provider",
            "dataset": "Acceptance Dataset",
            "domain": "acceptance",
            "reference_url": "https://example.invalid/source",
            "api_url": None,
            "authoritative": False,
            "licence": None,
            "attribution": None,
            "expected_update_frequency": "test-only",
            "temporal_coverage": None,
            "spatial_coverage": "acceptance fixture",
            "status": "configured",
            "limitations": [],
        }
    ]
