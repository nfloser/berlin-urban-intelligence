"""Acquire and persist Berlin reference layers from verified public sources.

WFS layers and VBB static GTFS are enabled by default. OSM road acquisition is opt-in because a
full Berlin road graph is comparatively expensive and requires the optional ``osm`` dependency.
No source failure is replaced with fabricated data; last-known-good state is retained per source.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from berlin_urban_intelligence.adapters.osm_network import OsmnxRoadNetworkClient
from berlin_urban_intelligence.knowledge.graph import KnowledgeGraph
from berlin_urban_intelligence.runtime.reference import ReferenceStateStore
from berlin_urban_intelligence.runtime.reference_acquisition import ReferenceAcquisitionCoordinator


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", default="data/runtime/reference.json")
    parser.add_argument("--rdf", default="data/generated/reference.ttl")
    parser.add_argument("--skip-gtfs", action="store_true", help="Skip VBB static GTFS acquisition")
    parser.add_argument("--with-osm", action="store_true", help="Acquire an OSM road graph")
    parser.add_argument("--place", default="Berlin, Germany", help="OSMnx place query")
    parser.add_argument("--network-type", default="drive")
    parser.add_argument(
        "--overpass-url",
        default=None,
        help=(
            "Optional explicit OSMnx Overpass base API URL. If omitted, OSMnx keeps its own "
            "configured default endpoint."
        ),
    )
    parser.add_argument(
        "--allow-osmnx-speed-imputation",
        action="store_true",
        help=(
            "Explicitly allow OSMnx to derive/impute missing edge speeds before calculating "
            "travel time. This is recorded in provenance."
        ),
    )
    args = parser.parse_args()

    store = ReferenceStateStore(Path(args.state))
    previous = store.load()
    coordinator = ReferenceAcquisitionCoordinator(
        road_client=OsmnxRoadNetworkClient(overpass_url=args.overpass_url)
    )
    state = coordinator.refresh(
        previous=previous,
        include_gtfs=not args.skip_gtfs,
        include_osm=args.with_osm,
        place=args.place,
        network_type=args.network_type,
        allow_speed_imputation=args.allow_osmnx_speed_imputation,
    )
    store.save(state)

    graph = KnowledgeGraph()
    for facility in state.critical_facilities:
        graph.add_entity(facility)
    for stop in state.transport_stops:
        graph.add_entity(stop)
    for feature in state.official_model_features:
        graph.add_official_model_feature(feature)
    for node in state.network_nodes:
        graph.add_network_node(node)
    for edge in state.network_edges:
        graph.add_network_edge(edge)
    rdf_path = Path(args.rdf)
    rdf_path.parent.mkdir(parents=True, exist_ok=True)
    rdf_path.write_text(graph.serialize(), encoding="utf-8")

    print(f"reference_state={args.state}")
    print(f"critical_facilities={len(state.critical_facilities)}")
    print(f"official_model_features={len(state.official_model_features)}")
    print(f"transport_stops={len(state.transport_stops)}")
    print(f"network_nodes={len(state.network_nodes)}")
    print(f"network_edges={len(state.network_edges)}")
    for source_id, error in sorted(state.errors.items()):
        print(f"source={source_id} error={error}")
    return 2 if state.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
