"""Write deterministic persisted snapshots for browser acceptance tests.

These fixtures are generated only during CI and are never used as production fallbacks. They use
exactly the same persisted-state contracts/stores as the running application so browser acceptance
covers the real nginx -> FastAPI -> persisted state -> React/MapLibre path.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta
from pathlib import Path

from pydantic import HttpUrl

from berlin_urban_intelligence.knowledge.derivations import (
    DerivationContext,
    DerivationDefinition,
    DerivationInput,
    DerivationRecord,
)
from berlin_urban_intelligence.runtime.derived import DerivedState, DerivedStateStore
from berlin_urban_intelligence.runtime.reference import ReferenceState, ReferenceStateStore
from berlin_urban_intelligence.runtime.state import RuntimeState, RuntimeStateStore
from berlin_urban_intelligence.shared.contracts import (
    AvailabilityStatus,
    CriticalFacility,
    DataState,
    DerivationStatus,
    FreshnessStatus,
    NetworkEdge,
    NetworkNode,
    OfficialModelFeature,
    Provenance,
    QualityFlag,
    SpatialReference,
    UrbanEntity,
)
from berlin_urban_intelligence.shared.source_status import SourceRuntimeStatus

FIXTURE_TIME = datetime(2026, 9, 15, 8, 0, tzinfo=UTC)
FIXTURE_URL = HttpUrl("https://example.invalid/berlin-urban-intelligence/acceptance-fixture")


def fixture_provenance(
    dataset: str,
    identifier: str,
    *,
    agent: str = "acceptance-fixture",
    agent_version: str = "1.0.0",
    upstream_ids: tuple[str, ...] = (),
) -> Provenance:
    return Provenance(
        provider="Berlin Urban Intelligence acceptance fixture",
        dataset=dataset,
        source_url=FIXTURE_URL,
        original_identifier=identifier,
        retrieved_at=FIXTURE_TIME,
        processed_at=FIXTURE_TIME,
        processing_method="deterministic CI acceptance fixture",
        agent=agent,
        agent_version=agent_version,
        quality_note="Synthetic test fixture used only by browser acceptance tests.",
        upstream_ids=upstream_ids,
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


def build_runtime_fixture() -> RuntimeState:
    """Expose explicit source degradation without inventing an observation."""

    return RuntimeState(
        generated_at=FIXTURE_TIME,
        source_statuses={
            "berlin_air_quality": SourceRuntimeStatus(
                source_id="berlin_air_quality",
                availability=AvailabilityStatus.UNAVAILABLE,
                freshness=FreshnessStatus.STALE,
                last_retrieval_attempt=FIXTURE_TIME,
                last_successful_retrieval=FIXTURE_TIME - timedelta(hours=3),
                latest_observation_time=FIXTURE_TIME - timedelta(hours=6),
                error_code="SOURCE_UNAVAILABLE",
            )
        },
    )


def build_derived_fixture() -> DerivedState:
    mobility_input = "observation:acceptance:mobility-input"
    acceptance_definition = DerivationDefinition(
        id="derivation:acceptance:mobility-delay-share",
        name="Acceptance mobility delay share",
        description="Acceptance-only persisted derivation used to verify dashboard lineage UI.",
        producer_agent_id="mobility",
        producer_version="0.1.0",
        algorithm_version="acceptance-v1",
        output_kind="ratio",
    )
    acceptance_record = DerivationRecord(
        id="derived:acceptance:mobility-delay-share",
        definition_id=acceptance_definition.id,
        entity_id="berlin:acceptance",
        phenomenon="acceptance_mobility_delay_share",
        value=0.25,
        unit="1",
        valid_at=FIXTURE_TIME - timedelta(hours=6),
        computed_at=FIXTURE_TIME,
        quality=QualityFlag.PARTIAL,
        freshness=FreshnessStatus.STALE,
        status=DerivationStatus.VALID,
        inputs=(DerivationInput(id=mobility_input, role="mobility_observation"),),
        provenance=fixture_provenance(
            "acceptance derived lineage",
            "mobility-delay-share-1",
            agent="mobility",
            agent_version="0.1.0",
            upstream_ids=(mobility_input,),
        ),
        context=DerivationContext.BASELINE,
    )

    temperature_input = "observation:acceptance:temperature"
    lqi_input = "observation:acceptance:lqi"
    realtime_input = f"vbb-gtfs-rt:{FIXTURE_TIME.isoformat()}"

    heat_air_definition = DerivationDefinition(
        id="heat-air-quality-context-v1",
        name="Latest measured heat and air-quality context",
        description=(
            "Descriptive pairing of the latest measured DWD 2 m air temperature and latest "
            "Berlin LQI grade. Values remain separate; no combined risk score or causal claim "
            "is produced."
        ),
        producer_agent_id="live_state",
        producer_version="0.1.0",
        algorithm_version="1.0.0",
        output_kind="heat_air_quality_context",
    )
    heat_air_record = DerivationRecord(
        id="derived:context:heat-air-quality:current",
        definition_id=heat_air_definition.id,
        entity_id="berlin:measured-context",
        phenomenon="heat_air_quality_context",
        value={
            "temperature_c": 29.5,
            "temperature_entity_id": "weather-station:dwd:acceptance",
            "temperature_observed_at": FIXTURE_TIME.isoformat(),
            "lqi_grade": 3,
            "lqi_entity_id": "air-quality-station:acceptance",
            "lqi_observed_at": FIXTURE_TIME.isoformat(),
        },
        valid_at=FIXTURE_TIME,
        computed_at=FIXTURE_TIME,
        quality=QualityFlag.PARTIAL,
        freshness=FreshnessStatus.STALE,
        status=DerivationStatus.VALID,
        inputs=(
            DerivationInput(id=temperature_input, role="measured_air_temperature_2m"),
            DerivationInput(id=lqi_input, role="measured_berlin_lqi_grade"),
        ),
        provenance=fixture_provenance(
            "acceptance heat-air cross-domain lineage",
            "heat-air-context-1",
            agent="live_state",
            agent_version="0.1.0",
            upstream_ids=(temperature_input, lqi_input),
        ),
        context=DerivationContext.BASELINE,
    )

    mobility_air_definition = DerivationDefinition(
        id="mobility-air-quality-context-v1",
        name="Latest mobility and air-quality context",
        description=(
            "Descriptive co-reporting of the VBB GTFS-Realtime delayed trip-update share and "
            "latest Berlin LQI grade. The values retain separate timestamps and source semantics; "
            "no causal relationship, exposure attribution or combined score is inferred."
        ),
        producer_agent_id="live_state",
        producer_version="0.1.0",
        algorithm_version="1.0.0",
        output_kind="mobility_air_quality_context",
    )
    mobility_air_record = DerivationRecord(
        id="derived:context:mobility-air-quality:current",
        definition_id=mobility_air_definition.id,
        entity_id="berlin:operational-context",
        phenomenon="mobility_air_quality_context",
        value={
            "delayed_trip_update_share": 0.25,
            "mobility_trip_updates": 100,
            "mobility_delayed_trip_updates": 25,
            "mobility_observed_at": FIXTURE_TIME.isoformat(),
            "lqi_grade": 3,
            "lqi_entity_id": "air-quality-station:acceptance",
            "lqi_observed_at": FIXTURE_TIME.isoformat(),
        },
        valid_at=FIXTURE_TIME,
        computed_at=FIXTURE_TIME,
        quality=QualityFlag.PARTIAL,
        freshness=FreshnessStatus.STALE,
        status=DerivationStatus.VALID,
        inputs=(
            DerivationInput(id=realtime_input, role="vbb_gtfs_realtime_snapshot"),
            DerivationInput(id=lqi_input, role="measured_berlin_lqi_grade"),
        ),
        provenance=fixture_provenance(
            "acceptance mobility-air cross-domain lineage",
            "mobility-air-context-1",
            agent="live_state",
            agent_version="0.1.0",
            upstream_ids=(realtime_input, lqi_input),
        ),
        context=DerivationContext.BASELINE,
    )

    return DerivedState(
        generated_at=FIXTURE_TIME,
        definitions=(acceptance_definition, heat_air_definition, mobility_air_definition),
        records=(acceptance_record, heat_air_record, mobility_air_record),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", default="data/runtime/reference.json")
    parser.add_argument("--runtime", default="data/runtime/state.json")
    parser.add_argument("--derived", default="data/runtime/derived.json")
    args = parser.parse_args()

    reference = build_reference_fixture()
    runtime = build_runtime_fixture()
    derived = build_derived_fixture()
    ReferenceStateStore(Path(args.reference)).save(reference)
    RuntimeStateStore(Path(args.runtime)).save(runtime)
    DerivedStateStore(Path(args.derived)).save(derived)

    print(f"reference_fixture={args.reference}")
    print(f"runtime_fixture={args.runtime}")
    print(f"derived_fixture={args.derived}")
    print(
        f"network_nodes={len(reference.network_nodes)} network_edges={len(reference.network_edges)}"
    )
    print(f"derived_records={len(derived.records)} source_statuses={len(runtime.source_statuses)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
