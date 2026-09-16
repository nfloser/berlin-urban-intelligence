import logging
from datetime import UTC, datetime
from pathlib import Path

import pytest

import berlin_urban_intelligence.shared.observability as observability
from berlin_urban_intelligence.runtime.derived_refresh import DerivedRefreshCoordinator
from berlin_urban_intelligence.runtime.refresh import RefreshCoordinator
from berlin_urban_intelligence.runtime.reload import ReloadingSnapshot
from berlin_urban_intelligence.runtime.state import RuntimeState
from berlin_urban_intelligence.scenario_engine.engine import ScenarioEngine
from berlin_urban_intelligence.scenario_engine.models import Scenario, ScenarioKind
from berlin_urban_intelligence.shared.contracts import (
    DataState,
    Observation,
    Provenance,
    QualityFlag,
)
from berlin_urban_intelligence.shared.observability import observe_operation

NOW = datetime(2026, 9, 16, 9, 0, tzinfo=UTC)


def _capture_events(monkeypatch) -> list[tuple[str, dict[str, object]]]:
    events: list[tuple[str, dict[str, object]]] = []

    def capture(_logger: logging.Logger, message: str, **context: object) -> None:
        events.append((message, context))

    monkeypatch.setattr(observability, "structured_log", capture)
    return events


def test_observe_operation_emits_success_and_failure_without_raw_error(monkeypatch) -> None:
    events = _capture_events(monkeypatch)
    logger = logging.getLogger("berlin_urban_intelligence.test")

    with observe_operation(
        logger,
        "test_operation",
        operation_id="op-success",
        agent="test-agent",
        source="fixture",
    ):
        pass

    with pytest.raises(ValueError, match="sensitive-value"):
        with observe_operation(
            logger,
            "test_operation",
            operation_id="op-failure",
            agent="test-agent",
            source="fixture",
        ):
            raise ValueError("sensitive-value")

    assert events[0][0] == "test_operation"
    assert events[0][1]["operation_id"] == "op-success"
    assert events[0][1]["error_state"] is None
    assert isinstance(events[0][1]["duration_ms"], float)
    assert events[1][1]["operation_id"] == "op-failure"
    assert events[1][1]["error_state"] == "ValueError"
    assert "sensitive-value" not in repr(events)


def test_snapshot_reload_logs_changed_operation_but_not_no_change(
    monkeypatch, tmp_path: Path
) -> None:
    events = _capture_events(monkeypatch)
    path = tmp_path / "runtime.json"
    path.write_text("{}", encoding="utf-8")
    snapshot = ReloadingSnapshot(path, lambda: {"ok": True}, name="runtime")

    assert snapshot.refresh(force=True, operation_id="request-1") is True
    assert snapshot.refresh(operation_id="request-2") is False

    reload_events = [item for item in events if item[0] == "snapshot_reload"]
    assert len(reload_events) == 1
    assert reload_events[0][1]["operation_id"] == "request-1"
    assert reload_events[0][1]["source"] == "snapshot:runtime"
    assert reload_events[0][1]["error_state"] is None


def test_snapshot_reload_failure_logs_error_type_without_exception_message(
    monkeypatch, tmp_path: Path
) -> None:
    events = _capture_events(monkeypatch)
    path = tmp_path / "reference.json"
    path.write_text("{}", encoding="utf-8")

    def broken_loader() -> object:
        raise ValueError("provider-token=must-not-leak")

    snapshot = ReloadingSnapshot(path, broken_loader, name="reference")
    assert snapshot.refresh(force=True, operation_id="request-3") is False

    event = next(item for item in events if item[0] == "snapshot_reload")
    assert event[1]["operation_id"] == "request-3"
    assert event[1]["error_state"] == "ValueError"
    assert "must-not-leak" not in repr(events)


def test_live_refresh_correlates_independent_source_failures(monkeypatch) -> None:
    events = _capture_events(monkeypatch)

    class BrokenAirClient:
        def get_lqi_data(self) -> object:
            raise RuntimeError("air-secret-must-not-leak")

    class BrokenFetchClient:
        def fetch(self) -> bytes:
            raise RuntimeError("provider-secret-must-not-leak")

    state = RefreshCoordinator(
        air_client=BrokenAirClient(),
        dwd_client=BrokenFetchClient(),
        vbb_client=BrokenFetchClient(),
        now_factory=lambda: NOW,
    ).refresh()

    source_events = [item for item in events if item[0] == "source_refresh"]
    assert len(source_events) == 3
    assert len({item[1]["operation_id"] for item in source_events}) == 1
    assert {item[1]["source"] for item in source_events} == {
        "berlin_air_quality",
        "dwd_open_data",
        "vbb_gtfs_rt",
    }
    assert all(item[1]["error_state"] == "RuntimeError" for item in source_events)
    assert set(state.errors) == {"berlin_air_quality", "dwd_open_data", "vbb_gtfs_rt"}
    assert "must-not-leak" not in repr(events)


def test_derivation_refresh_emits_one_operation_event(monkeypatch) -> None:
    events = _capture_events(monkeypatch)

    outcome = DerivedRefreshCoordinator().refresh(RuntimeState(generated_at=NOW), None)

    derivation_events = [item for item in events if item[0] == "derivation_refresh"]
    assert outcome.changed is True
    assert len(derivation_events) == 1
    assert derivation_events[0][1]["agent"] == "derived"
    assert derivation_events[0][1]["source"] == "runtime_state"
    assert derivation_events[0][1]["error_state"] is None


def test_scenario_calculation_inherits_explicit_operation_id(monkeypatch) -> None:
    events = _capture_events(monkeypatch)
    provenance = Provenance(
        provider="fixture-provider",
        dataset="fixture-dataset",
        source_url="https://example.invalid/fixture",
        retrieved_at=NOW,
        processed_at=NOW,
        processing_method="deterministic fixture",
        agent="heat",
        agent_version="test",
    )
    baseline = Observation(
        id="fixture:temperature",
        entity_id="fixture:station",
        phenomenon="air_temperature_2m",
        value=20.0,
        unit="Cel",
        observed_at=NOW,
        state=DataState.OBSERVED,
        quality=QualityFlag.VALID,
        provenance=provenance,
    )
    scenario = Scenario(
        name="fixture-heat",
        kinds={ScenarioKind.EXTREME_HEAT},
        temperature_delta_c=3.0,
    )

    result = ScenarioEngine().apply_temperature_delta(
        baseline, scenario, operation_id="request-scenario"
    )

    scenario_events = [item for item in events if item[0] == "scenario_calculation"]
    assert result.value == 23.0
    assert len(scenario_events) == 1
    assert scenario_events[0][1]["operation_id"] == "request-scenario"
    assert scenario_events[0][1]["agent"] == "heat"
    assert scenario_events[0][1]["source"] == "temperature_delta"
    assert scenario_events[0][1]["error_state"] is None
