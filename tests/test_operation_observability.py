import logging
from pathlib import Path

import pytest

import berlin_urban_intelligence.shared.observability as observability
from berlin_urban_intelligence.runtime.reload import ReloadingSnapshot
from berlin_urban_intelligence.shared.observability import observe_operation


def test_observe_operation_emits_success_and_failure_without_raw_error(monkeypatch) -> None:
    events: list[tuple[str, dict[str, object]]] = []

    def capture(_logger: logging.Logger, message: str, **context: object) -> None:
        events.append((message, context))

    monkeypatch.setattr(observability, "structured_log", capture)
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


def test_snapshot_reload_logs_changed_operation_but_not_no_change(monkeypatch, tmp_path: Path) -> None:
    events: list[tuple[str, dict[str, object]]] = []

    def capture(_logger: logging.Logger, message: str, **context: object) -> None:
        events.append((message, context))

    monkeypatch.setattr(observability, "structured_log", capture)
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
    events: list[tuple[str, dict[str, object]]] = []

    def capture(_logger: logging.Logger, message: str, **context: object) -> None:
        events.append((message, context))

    monkeypatch.setattr(observability, "structured_log", capture)
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
