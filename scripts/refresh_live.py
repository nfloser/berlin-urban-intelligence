"""Acquire currently available real data and persist canonical state plus RDF.

This command performs network I/O. It has no synthetic fallback.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from berlin_urban_intelligence.knowledge.graph import KnowledgeGraph
from berlin_urban_intelligence.runtime.refresh import RefreshCoordinator
from berlin_urban_intelligence.runtime.state import RuntimeStateStore


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", default="data/runtime/state.json")
    parser.add_argument("--rdf", default="data/generated/latest.ttl")
    args = parser.parse_args()

    state = RefreshCoordinator().refresh()
    RuntimeStateStore(Path(args.state)).save(state)

    graph = KnowledgeGraph()
    for observation in state.observations:
        graph.add_observation(observation)
    rdf_path = Path(args.rdf)
    rdf_path.parent.mkdir(parents=True, exist_ok=True)
    rdf_path.write_text(graph.serialize(), encoding="utf-8")

    print(f"runtime_state={args.state}")
    print(f"observations={len(state.observations)}")
    print(f"mobility_snapshot={'yes' if state.mobility is not None else 'no'}")
    for source_id, source_state in sorted(state.source_statuses.items()):
        print(
            f"source={source_id} availability={source_state.availability.value} "
            f"freshness={source_state.freshness.value} error={source_state.error_code or '-'}"
        )
    return (
        0
        if any(item.availability.value == "available" for item in state.source_statuses.values())
        else 2
    )


if __name__ == "__main__":
    raise SystemExit(main())
