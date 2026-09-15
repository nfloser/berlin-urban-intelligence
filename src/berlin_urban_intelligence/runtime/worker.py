"""Configurable persisted-state refresh worker.

Provider acquisition remains outside HTTP request handling. Each refresh receives the previous
canonical state so source-specific failures can preserve last-known-good observations while updating
availability and freshness metadata.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Protocol

from berlin_urban_intelligence.runtime.state import RuntimeState, RuntimeStateStore


class RuntimeRefreshCoordinator(Protocol):
    def refresh(self, *, previous_state: RuntimeState | None = None) -> RuntimeState: ...


class SnapshotRefreshWorker:
    def __init__(
        self,
        *,
        coordinator: RuntimeRefreshCoordinator,
        store: RuntimeStateStore,
        interval_seconds: float,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be positive")
        self.coordinator = coordinator
        self.store = store
        self.interval_seconds = interval_seconds
        self._sleep = sleep

    def refresh_once(self) -> RuntimeState:
        previous = self.store.load()
        current = self.coordinator.refresh(previous_state=previous)
        self.store.save(current)
        return current

    def run_forever(self, *, after_refresh: Callable[[RuntimeState], None] | None = None) -> None:
        while True:
            state = self.refresh_once()
            if after_refresh is not None:
                after_refresh(state)
            self._sleep(self.interval_seconds)
