from datetime import UTC, datetime

import pytest

from berlin_urban_intelligence.runtime.state import RuntimeState, RuntimeStateStore
from berlin_urban_intelligence.runtime.worker import SnapshotRefreshWorker


class FakeCoordinator:
    def __init__(self, result: RuntimeState) -> None:
        self.result = result
        self.previous_states: list[RuntimeState | None] = []

    def refresh(self, *, previous_state: RuntimeState | None = None) -> RuntimeState:
        self.previous_states.append(previous_state)
        return self.result


def test_refresh_worker_supplies_previous_state_and_persists_replacement(tmp_path) -> None:
    path = tmp_path / "runtime.json"
    store = RuntimeStateStore(path)
    previous = RuntimeState(generated_at=datetime(2026, 9, 15, 7, 0, tzinfo=UTC))
    replacement = RuntimeState(generated_at=datetime(2026, 9, 15, 7, 5, tzinfo=UTC))
    store.save(previous)
    coordinator = FakeCoordinator(replacement)

    worker = SnapshotRefreshWorker(coordinator=coordinator, store=store, interval_seconds=60)
    result = worker.refresh_once()

    assert coordinator.previous_states == [previous]
    assert result == replacement
    assert store.load() == replacement


def test_refresh_worker_rejects_non_positive_interval(tmp_path) -> None:
    store = RuntimeStateStore(tmp_path / "runtime.json")
    coordinator = FakeCoordinator(RuntimeState(generated_at=datetime.now(UTC)))
    with pytest.raises(ValueError, match="interval_seconds"):
        SnapshotRefreshWorker(coordinator=coordinator, store=store, interval_seconds=0)
