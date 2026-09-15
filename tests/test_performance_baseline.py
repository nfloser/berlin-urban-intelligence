from pathlib import Path

import pytest

from berlin_urban_intelligence.performance import benchmark_callable
from berlin_urban_intelligence.runtime.reload import ReloadingSnapshot


def test_benchmark_callable_records_repeatable_latency_and_memory() -> None:
    calls = 0

    def operation() -> list[int]:
        nonlocal calls
        calls += 1
        return list(range(128))

    result = benchmark_callable("fixture-operation", operation, iterations=5, warmups=2)

    assert calls == 7
    assert result.name == "fixture-operation"
    assert result.iterations == 5
    assert result.p50_ms >= 0
    assert result.p95_ms >= result.p50_ms
    assert result.max_ms >= result.p95_ms
    assert result.peak_memory_kib >= 0


def test_benchmark_callable_rejects_invalid_iteration_counts() -> None:
    with pytest.raises(ValueError, match="iterations must be positive"):
        benchmark_callable("invalid", lambda: None, iterations=0)
    with pytest.raises(ValueError, match="warmups cannot be negative"):
        benchmark_callable("invalid", lambda: None, iterations=1, warmups=-1)


def test_reload_no_change_path_does_not_reparse_snapshot(tmp_path: Path) -> None:
    path = tmp_path / "snapshot.json"
    path.write_text("{}", encoding="utf-8")
    calls = 0

    def loader() -> object:
        nonlocal calls
        calls += 1
        return object()

    snapshot = ReloadingSnapshot(path, loader)
    assert snapshot.refresh(force=True) is True

    for _ in range(100):
        assert snapshot.refresh() is False

    assert calls == 1
