"""Write a tiny deterministic reference snapshot for browser acceptance tests.

The fixture is deliberately generated during CI and is never used as a production fallback. It
contains enough Berlin-local reference geometry and network topology to exercise map inspection,
nearest-node selection and baseline-versus-disruption routing through the real API stack.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

from pydantic import HttpUrl

from berlin_urban_intelligence.runtime.reference import ReferenceState, ReferenceStateStore
from berlin_urban_intelligence.shared.contracts import (
    CriticalFacility,
    DataState,
    NetworkEdge,
    NetworkNode,
    OfficialModelFeature,
    Provenance,
    QualityFlag,
    SpatialReference,
    UrbanEntity,
)

FIXTURE_TIME = datetime(2026, 9, 15, 8, 0, tzinfo=UTC)
FIXTURE_URL = HttpUrl("https://example.invalid/berlin-urban-intelligence/acceptance-fixture")


def fixture_provenance(dataset: str, identifier: str) -> Provenance:
    return Provenance(
        provider="Berlin Urban Intelligence acceptance fixture",
        dataset=dataset,
        source_url=FIXTURE_URL,
        original_identifier=identifier,
        retrieved_at=FIXTURE_TIME,
        processed_at=FIXTURE_TIME,
        processing_method="deterministic CI acceptance fixture",
        agent="acceptance-fixture",
        agent_version="1.0.0",
        quality_note="Synthetic test fixture used only by browser acceptance tests.",
    )


def build_reference_fixture() -> ReferenceState:
    facility = CriticalFacility(
        id="critical:acceptance:hospital",
        name="Acceptance Hospital",
        category="hospital",
        confidence="test_fixture",
        quality=QualityFlag.VALID,
        provenance=fixture_provenance("acceptance facilities", "hospital-1"),
        spatial=SpatialReference(
            crs="EPSG:4326",
            geometry={"type": "Point", "coordinates": [13.405, 52.52]},
        ),
        source_identifier="hospital-1",
    )
    stop = UrbanEntity(
        id="transport-stop:acceptance:central",
        entity_type="transport_stop",
        name="Acceptance Central",
        spatial=SpatialReference(
            crs="EPSG:4326",
            geometry={"type": "Point", "coordinates": [13.414, 52.521]},
        ),
        source_identifier="stop-1",
    )
    climate = OfficialModelFeature(
        id="official-model:acceptance:climate-zone",
        entity_id="berlin:acceptance-climate-zone",
        model_name="Acceptance Climate Analysis",
        feature_type="heat_context_zone",
        properties={"class": "fixture-warm", "description": "Acceptance polygon"},
        state=DataState.OFFICIAL_MODELLED,
        quality=QualityFlag.VALID,
        provenance=fixture_provenance("acceptance climate model", "climate-zone-1"),
        spatial=SpatialReference(
            crs="EPSG:4326",
            geometry={
                "type": "Polygon",
                "coordinates": [
                    [
                        [13.397, 52.516],
                        [13.423, 52.516],
                        [13.423, 52.532],
                        [13.397, 52.532],
                        [13.397, 52.516],
                    ]
                ],
            },
        ),
    )

    nodes = (
        NetworkNode(id="acceptance-node-a", longitude=13.4, latitude=52.52),
        NetworkNode(id="acceptance-node-b", longitude=13.42, latitude=52.52),
        NetworkNode(id="acceptance-node-c", longitude=13.41, latitude=52.53),
    )
    edges = (
        NetworkEdge(
            id="acceptance-edge-ab",
            source="acceptance-node-a",
            target="acceptance-node-b",
            travel_time_s=100.0,
            length_m=1400.0,
            bidirectional=True,
        ),
        NetworkEdge(
            id="acceptance-edge-ac",
            source="acceptance-node-a",
            target="acceptance-node-c",
            travel_time_s=80.0,
            length_m=1100.0,
            bidirectional=True,
        ),
        NetworkEdge(
            id="acceptance-edge-cb",
            source="acceptance-node-c",
            target="acceptance-node-b",
            travel_time_s=80.0,
            length_m=1100.0,
            bidirectional=True,
        ),
    )

    return ReferenceState(
        generated_at=FIXTURE_TIME,
        critical_facilities=(facility,),
        official_model_features=(climate,),
        transport_stops=(stop,),
        network_nodes=nodes,
        network_edges=edges,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", default="data/runtime/reference.json")
    args = parser.parse_args()
    state = build_reference_fixture()
    ReferenceStateStore(Path(args.reference)).save(state)
    print(f"reference_fixture={args.reference}")
    print(f"network_nodes={len(state.network_nodes)} network_edges={len(state.network_edges)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
