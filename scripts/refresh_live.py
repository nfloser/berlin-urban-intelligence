"""Acquire currently available real data and persist canonical state plus RDF.

This command performs network I/O. It has no synthetic fallback. With ``--interval-seconds`` it runs
as a persistent acquisition worker; otherwise it performs one refresh and exits. Derived products
are updated through the dependency-aware refresh coordinator after the source-backed runtime state
has been persisted.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from berlin_urban_intelligence.knowledge.derived_graph import project_derived_state
from berlin_urban_intelligence.knowledge.graph import KnowledgeGraph
from berlin_urban_intelligence.runtime.derived import DerivedState, DerivedStateStore
from berlin_urban_intelligence.runtime.derived_refresh import DerivedRefreshCoordinator
from berlin_urban_intelligence.runtime.refresh import RefreshCoordinator
from berlin_urban_intelligence.runtime.state import RuntimeState, RuntimeStateStore
from berlin_urban_intelligence.runtime.worker import SnapshotRefreshWorker


def _write_rdf(state: RuntimeState, derived: DerivedState, path: Path) -> None:
    graph = KnowledgeGraph()
    for observation in state.observations:
        graph.add_observation(observation)
    project_derived_state(graph, derived)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(graph.serialize(), encoding="utf-8")


def _print_summary(state: RuntimeState, state_path: str, derived_records: int) -> None:
    print(f"runtime_state={state_path}", flush=True)
    print(f"observations={len(state.observations)}", flush=True)
    print(f"mobility_snapshot={'yes' if state.mobility is not None else 'no'}", flush=True)
    print(f"derived_records={derived_records}", flush=True)
    for source_id, source_state in sorted(state.source_statuses.items()):
        print(
            f"source={source_id} availability={source_state.availability.value} "
            f"freshness={source_state.freshness.value} error={source_state.error_code or '-'}",
            flush=True,
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", default="data/runtime/state.json")
    parser.add_argument("--derived", default="data/runtime/derived.json")
    parser.add_argument("--rdf", default="data/generated/latest.ttl")
    parser.add_argument(
        "--interval-seconds",
        type=float,
        default=0.0,
        help="Run continuously at this interval; 0 performs a single refresh.",
    )
    args = parser.parse_args()
    if args.interval_seconds < 0:
        parser.error("--interval-seconds must be non-negative")

    store = RuntimeStateStore(Path(args.state))
    derived_store = DerivedStateStore(Path(args.derived))
    derived_refresh = DerivedRefreshCoordinator()
    worker = SnapshotRefreshWorker(
        coordinator=RefreshCoordinator(),
        store=store,
        interval_seconds=args.interval_seconds or 1.0,
    )
    rdf_path = Path(args.rdf)

    def after_refresh(state: RuntimeState) -> None:
        previous_derived = derived_store.load()
        outcome = derived_refresh.refresh(state, previous_derived)
        if outcome.changed:
            derived_store.save(outcome.state)
        _write_rdf(state, outcome.state, rdf_path)
        _print_summary(state, args.state, len(outcome.state.records))

    if args.interval_seconds > 0:
        worker.run_forever(after_refresh=after_refresh)
        return 0

    state = worker.refresh_once()
    after_refresh(state)
    return (
        0
        if any(item.availability.value == "available" for item in state.source_statuses.values())
        else 2
    )


if __name__ == "__main__":
    raise SystemExit(main())
