from datetime import UTC, datetime, timedelta
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from pyshacl import validate
from rdflib import Graph

from berlin_urban_intelligence.adapters.dwd import DwdTenMinuteAirTemperatureClient
from berlin_urban_intelligence.agents.heat import HeatAgent
from berlin_urban_intelligence.api.app import create_app
from berlin_urban_intelligence.energy.pipeline import EnergyForecastPipeline
from berlin_urban_intelligence.runtime.refresh import RefreshCoordinator
from berlin_urban_intelligence.runtime.state import RuntimeState, RuntimeStateStore
from berlin_urban_intelligence.shared.dependencies import DependencyGraph


def test_dwd_to_api_rdf_shacl_and_scenario(tmp_path):
    now = datetime.now(UTC).replace(second=0, microsecond=0)
    archive = BytesIO()
    with ZipFile(archive, "w") as z:
        z.writestr(
            "produkt_tu.txt",
            "STATIONS_ID;MESS_DATUM;QN;PP_10;TT_10;TM5_10;RF_10;TD_10\n"
            f"433;{now:%Y%m%d%H%M};3;1012;24;-999;50;13\n",
        )
    record = DwdTenMinuteAirTemperatureClient.parse_latest(archive.getvalue(), "00433")
    agent = HeatAgent(now_factory=lambda: now)
    observations = agent.ingest_dwd_record(record, now)
    assert len(observations) == 4
    assert all(o.value != -999 for o in observations)
    RuntimeStateStore(tmp_path / "state.json").save(
        RuntimeState(generated_at=now, observations=tuple(observations))
    )
    client = TestClient(create_app(data_dir=tmp_path))
    assert client.get("/ready").status_code == 200
    rdf = Graph().parse(data=client.get("/api/v1/graph").text, format="turtle")
    shapes = Graph().parse("knowledge/ontology/shapes.ttl")
    assert validate(rdf, shacl_graph=shapes)[0]
    query = Path("knowledge/queries/latest_observations.sparql").read_text()
    assert list(rdf.query(query))
    result = client.post(
        "/api/v1/assessments",
        json={"scenario": {"name": "heat", "kinds": ["extreme_heat"], "temperature_delta_c": 3}},
    )
    assert result.json()["heat"]["value"] == 27
    assert result.json()["heat"]["state"] == "scenario"
    assert (
        client.get("/api/v1/observations", params={"phenomenon": "air_temperature_2m"}).json()[0][
            "value"
        ]
        == 24
    )


def test_failure_keeps_last_known_good_without_fabrication():
    class Offline:
        def fetch(self):
            raise OSError("offline")

        def get_lqi_data(self):
            raise OSError("offline")

    now = datetime.now(UTC)
    previous = RuntimeState(generated_at=now - timedelta(hours=1))
    offline = Offline()
    result = RefreshCoordinator(air_client=offline, dwd_client=offline, vbb_client=offline).refresh(
        previous_state=previous
    )
    assert result.observations == ()
    assert len(result.errors) == 3
    assert all(s.availability == "unavailable" for s in result.source_statuses.values())


def test_feature_lags_do_not_see_future_targets():
    frame = pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-01-01", periods=100, freq="15min", tz="UTC"),
            "load": range(100),
        }
    )
    pipeline = EnergyForecastPipeline(target_column="load", seasonal_lag=4)
    original = pipeline.build_features(frame)
    frame.loc[50:, "load"] = 10000
    changed = pipeline.build_features(frame)
    pd.testing.assert_frame_equal(original.loc[:50], changed.loc[:50])
    forecast = pipeline.forecast_next(frame, model_id="persistence")
    assert forecast.value == 10000
    assert forecast.valid_at > forecast.issued_at


def test_dependency_cycle_rejection_preserves_existing_graph():
    dependencies = DependencyGraph()
    dependencies.add_derivation("b", ["a"])
    dependencies.add_derivation("c", ["b"])
    with pytest.raises(ValueError):
        dependencies.add_derivation("b", ["c"])
    assert dependencies.mark_upstream_changed("a") == {"b", "c"}
