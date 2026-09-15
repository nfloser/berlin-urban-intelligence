"""Small deterministic helpers for repository performance evidence.

The project does not treat GitHub-hosted runner timings as production SLOs. These helpers only
standardise repeatable latency and Python-allocation observations so point-in-time benchmark runs
can be compared with the same fixture and methodology.
"""

from __future__ import annotations

import tracemalloc
from collections.abc import Callable
from dataclasses import asdict, dataclass
from time import perf_counter


@dataclass(frozen=True)
class BenchmarkResult:
    """Summary of repeated executions of one deterministic operation."""

    name: str
    iterations: int
    p50_ms: float
    p95_ms: float
    max_ms: float
    peak_memory_kib: float

    def as_dict(self) -> dict[str, str | int | float]:
        return asdict(self)


def _percentile(values: list[float], quantile: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("percentile requires at least one value")
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * quantile
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + ((ordered[upper] - ordered[lower]) * fraction)


def benchmark_callable(
    name: str,
    operation: Callable[[], object],
    *,
    iterations: int = 10,
    warmups: int = 2,
) -> BenchmarkResult:
    """Measure repeated wall-clock latency and peak traced Python allocations.

    Warm-up calls are excluded from the reported timings. ``peak_memory_kib`` is the peak Python
    allocation observed by ``tracemalloc`` during the measured loop; it is not process RSS.
    """

    if not name.strip():
        raise ValueError("name must not be empty")
    if iterations <= 0:
        raise ValueError("iterations must be positive")
    if warmups < 0:
        raise ValueError("warmups cannot be negative")

    for _ in range(warmups):
        operation()

    already_tracing = tracemalloc.is_tracing()
    if not already_tracing:
        tracemalloc.start()
    tracemalloc.reset_peak()

    timings_ms: list[float] = []
    try:
        for _ in range(iterations):
            started = perf_counter()
            operation()
            timings_ms.append((perf_counter() - started) * 1000.0)
        _, peak_bytes = tracemalloc.get_traced_memory()
    finally:
        if not already_tracing:
            tracemalloc.stop()

    return BenchmarkResult(
        name=name,
        iterations=iterations,
        p50_ms=round(_percentile(timings_ms, 0.50), 3),
        p95_ms=round(_percentile(timings_ms, 0.95), 3),
        max_ms=round(max(timings_ms), 3),
        peak_memory_kib=round(peak_bytes / 1024.0, 3),
    )
