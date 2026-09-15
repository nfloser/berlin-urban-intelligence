"""Generate point-in-time performance evidence with isolated deterministic persisted state."""

from __future__ import annotations

import argparse
import json
import os
import platform
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient

from berlin_urban_intelligence.api.app import create_app
from berlin_urban_intelligence.performance import BenchmarkResult, benchmark_callable
from berlin_urban_intelligence.runtime.reference import ReferenceState, ReferenceStateStore
from berlin_urban_intelligence.runtime.reload import ReloadingSnapshot
from berlin_urban_intelligence.shared.contracts import (
    CriticalFacility,
    NetworkEdge,
    NetworkNode,
    QualityFlag,
    SpatialReference,
    UrbanEntity,
)

GENERATED_AT = datetime(2026, 9, 15, 12, 0, tzinfo=UTC)


def _point(longitude: float, latitude: float) -> SpatialReference:
    return SpatialReference(
        crs="EPSG:4326",
        geometry={"type": "Point", "coordinates": [longitude, latitude]},
    )


def _reference_fixture(*, stops: int, facilities: int, network_nodes: int) -> ReferenceState:
    transport_stops = tuple(
        UrbanEntity(
            id=f"benchmark-stop-{index:05d}",
            entity_type="transport_stop",
            name=f"Benchmark stop {index}",
            spatial=_point(
                13.25 + ((index % 200) * 0.001),
                52.40 + (((index // 200) % 100) * 0.001),
            ),
        )
        for index in range(stops)
    )
    critical_facilities = tuple(
        CriticalFacility(
            id=f"benchmark-facility-{index:04d}",
            name=f"Benchmark facility {index}",
            category="benchmark",
            quality=QualityFlag.VALID,
            spatial=_point(
                13.30 + ((index % 100) * 0.001),
                52.50 + (((index // 100) % 20) * 0.001),
            ),
        )
        for index in range(facilities)
    )
    nodes = tuple(
        NetworkNode(
            id=f"benchmark-node-{index:04d}",
            longitude=13.30 + (index * 0.00005),
            latitude=52.50,
        )
        for index in range(network_nodes)
    )
    edges = tuple(
        NetworkEdge(
            id=f"benchmark-edge-{index:04d}",
            source=nodes[index].id,
            target=nodes[index + 1].id,
            travel_time_s=5.0,
            length_m=50.0,
        )
        for index in range(max(0, network_nodes - 1))
    )
    return ReferenceState(
        generated_at=GENERATED_AT,
        critical_facilities=critical_facilities,
        transport_stops=transport_stops,
        network_nodes=nodes,
        network_edges=edges,
    )


@contextmanager
def _persisted_state_environment(reference_path: Path) -> Iterator[None]:
    values = {
        "BUI_RUNTIME_STATE": str(reference_path.parent / "missing-runtime.json"),
        "BUI_REFERENCE_STATE": str(reference_path),
        "BUI_ENERGY_STATE": str(reference_path.parent / "missing-energy.json"),
        "BUI_DERIVED_STATE": str(reference_path.parent / "missing-derived.json"),
    }
    previous = {name: os.environ.get(name) for name in values}
    os.environ.update(values)
    try:
        yield
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def _successful_get(client: TestClient, path: str, **kwargs: object) -> bytes:
    response = client.get(path, **kwargs)
    if response.status_code != 200:
        raise RuntimeError(f"GET {path} returned {response.status_code}: {response.text}")
    return response.content


def _successful_post(client: TestClient, path: str, payload: dict[str, object]) -> bytes:
    response = client.post(path, json=payload)
    if response.status_code != 200:
        raise RuntimeError(f"POST {path} returned {response.status_code}: {response.text}")
    return response.content


def run_benchmark(
    *,
    stops: int,
    facilities: int,
    network_nodes: int,
    iterations: int,
    warmups: int,
) -> dict[str, object]:
    if stops < 1 or facilities < 1 or network_nodes < 2:
        raise ValueError("fixture requires stops/facilities >= 1 and network_nodes >= 2")

    with TemporaryDirectory(prefix="bui-performance-") as temporary:
        root = Path(temporary)
        reference_path = root / "reference.json"
        reference = _reference_fixture(
            stops=stops,
            facilities=facilities,
            network_nodes=network_nodes,
        )
        store = ReferenceStateStore(reference_path)
        store.save(reference)

        reload_snapshot = ReloadingSnapshot(reference_path, store.load)
        if not reload_snapshot.refresh(force=True):
            raise RuntimeError("benchmark reference snapshot did not initialize")

        results: list[BenchmarkResult] = [
            benchmark_callable(
                "snapshot_reload_no_change",
                reload_snapshot.refresh,
                iterations=max(iterations * 5, 25),
                warmups=max(warmups, 1),
            )
        ]

        with _persisted_state_environment(reference_path), TestClient(create_app()) as client:
            map_params = {
                "west": 13.20,
                "south": 52.35,
                "east": 13.50,
                "north": 52.60,
                "layers": "facilities,stops",
                "limit_per_layer": 250,
            }
            last_stop = f"benchmark-stop-{stops - 1:05d}"
            last_node = f"benchmark-node-{network_nodes - 1:04d}"

            operations = (
                (
                    "api_system",
                    lambda: _successful_get(client, "/api/v1/system"),
                    iterations,
                ),
                (
                    "api_agent_health",
                    lambda: _successful_get(client, "/api/v1/agents/health"),
                    iterations,
                ),
                (
                    "api_reference_map_bbox",
                    lambda: _successful_get(
                        client,
                        "/api/v1/map/reference",
                        params=map_params,
                    ),
                    iterations,
                ),
                (
                    "api_reference_detail",
                    lambda: _successful_get(
                        client,
                        f"/api/v1/map/reference/stops/{last_stop}",
                    ),
                    iterations,
                ),
                (
                    "api_nearest_network_node",
                    lambda: _successful_get(
                        client,
                        "/api/v1/network/nearest",
                        params={"longitude": 13.31, "latitude": 52.50},
                    ),
                    iterations,
                ),
                (
                    "api_resilience_route",
                    lambda: _successful_post(
                        client,
                        "/api/v1/resilience/routes",
                        {"origin": "benchmark-node-0000", "destination": last_node},
                    ),
                    iterations,
                ),
                (
                    "api_graph_serialization",
                    lambda: _successful_get(client, "/api/v1/graph"),
                    min(iterations, 3),
                ),
            )
            for name, operation, operation_iterations in operations:
                results.append(
                    benchmark_callable(
                        name,
                        operation,
                        iterations=operation_iterations,
                        warmups=warmups,
                    )
                )

            map_response = client.get("/api/v1/map/reference", params=map_params)
            map_response.raise_for_status()
            map_body = map_response.json()
            returned = map_body["metadata"]["returned"]
            if returned["facilities"] > 250 or returned["stops"] > 250:
                raise RuntimeError("map benchmark violated the configured per-layer output bound")

        return {
            "schema_version": "1.0.0",
            "generated_at": datetime.now(UTC).isoformat(),
            "environment": {
                "python": platform.python_version(),
                "platform": platform.platform(),
                "machine": platform.machine(),
                "cpu_count": os.cpu_count(),
                "github_actions": os.environ.get("GITHUB_ACTIONS") == "true",
            },
            "fixture": {
                "transport_stops": stops,
                "critical_facilities": facilities,
                "network_nodes": network_nodes,
                "network_edges": network_nodes - 1,
                "persisted_reference_bytes": reference_path.stat().st_size,
                "synthetic_production_fallback": False,
                "temporary_fixture_only": True,
            },
            "map_contract": {
                "requested_layers": ["facilities", "stops"],
                "limit_per_layer": 250,
                "maximum_returned_features": 500,
            },
            "results": [result.as_dict() for result in results],
            "limitations": [
                (
                    "Timings use in-process FastAPI TestClient and exclude external "
                    "network/proxy latency."
                ),
                "GitHub-hosted runner timings are noisy observations, not production SLOs.",
                "Peak memory is tracemalloc Python allocation peak, not process RSS.",
                (
                    "The deterministic fixture is benchmark-only and is never a production "
                    "data fallback."
                ),
            ],
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--stops", type=int, default=10_000)
    parser.add_argument("--facilities", type=int, default=250)
    parser.add_argument("--network-nodes", type=int, default=750)
    parser.add_argument("--iterations", type=int, default=7)
    parser.add_argument("--warmups", type=int, default=2)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_benchmark(
        stops=args.stops,
        facilities=args.facilities,
        network_nodes=args.network_nodes,
        iterations=args.iterations,
        warmups=args.warmups,
    )
    rendered = json.dumps(report, indent=2, sort_keys=True)
    print(rendered)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
