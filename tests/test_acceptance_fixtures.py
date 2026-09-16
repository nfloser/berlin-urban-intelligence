from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from berlin_urban_intelligence.runtime.derived import DerivedStateStore
from berlin_urban_intelligence.runtime.reference import ReferenceStateStore
from berlin_urban_intelligence.runtime.state import RuntimeStateStore
from berlin_urban_intelligence.shared.contracts import (
    AvailabilityStatus,
    DerivationStatus,
    FreshnessStatus,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _write_acceptance_state(tmp_path: Path) -> tuple[Path, Path, Path]:
    reference_path = tmp_path / "reference.json"
    runtime_path = tmp_path / "state.json"
    derived_path = tmp_path / "derived.json"
    subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "write_acceptance_fixtures.py"),
            "--reference",
            str(reference_path),
            "--runtime",
            str(runtime_path),
            "--derived",
            str(derived_path),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return reference_path, runtime_path, derived_path


def test_acceptance_fixture_cli_persists_all_expected_state_files(tmp_path: Path) -> None:
    reference_path, runtime_path, derived_path = _write_acceptance_state(tmp_path)

    reference = ReferenceStateStore(reference_path).load()
    runtime = RuntimeStateStore(runtime_path).load()
    derived = DerivedStateStore(derived_path).load()

    assert reference is not None
    assert runtime is not None
    assert derived is not None
    assert len(reference.network_nodes) == 3
    assert len(reference.network_edges) == 3
    assert len(runtime.source_statuses) == 1
    assert len(derived.records) == 3
    assert {record.id for record in derived.records} == {
        "derived:acceptance:mobility-delay-share",
        "derived:context:heat-air-quality:current",
        "derived:context:mobility-air-quality:current",
    }


def test_runtime_acceptance_fixture_exposes_explicit_source_failure_semantics(
    tmp_path: Path,
) -> None:
    _, runtime_path, _ = _write_acceptance_state(tmp_path)
    runtime = RuntimeStateStore(runtime_path).load()
    assert runtime is not None

    status = runtime.source_statuses["berlin_air_quality"]
    assert status.availability is AvailabilityStatus.UNAVAILABLE
    assert status.freshness is FreshnessStatus.STALE
    assert status.error_code == "SOURCE_UNAVAILABLE"
    assert status.last_successful_retrieval is not None
    assert status.latest_observation_time is not None
    assert runtime.errors == {}


def test_derived_acceptance_fixture_exposes_lineage_without_production_fallback(
    tmp_path: Path,
) -> None:
    _, _, derived_path = _write_acceptance_state(tmp_path)
    derived = DerivedStateStore(derived_path).load()
    assert derived is not None

    assert len(derived.definitions) == 3
    definitions = {definition.id: definition for definition in derived.definitions}
    acceptance_definition = definitions["derivation:acceptance:mobility-delay-share"]
    assert acceptance_definition.name == "Acceptance mobility delay share"
    assert acceptance_definition.producer_agent_id == "mobility"
    assert definitions["heat-air-quality-context-v1"].producer_agent_id == "live_state"
    assert definitions["mobility-air-quality-context-v1"].producer_agent_id == "live_state"

    assert len(derived.records) == 3
    records = {record.id: record for record in derived.records}
    record = records["derived:acceptance:mobility-delay-share"]
    assert record.definition_id == acceptance_definition.id
    assert record.freshness is FreshnessStatus.STALE
    assert record.status is DerivationStatus.VALID
    assert [item.id for item in record.inputs] == ["observation:acceptance:mobility-input"]
    assert record.provenance.upstream_ids == ("observation:acceptance:mobility-input",)
    assert record.provenance.provider == "Berlin Urban Intelligence acceptance fixture"
    assert record.provenance.dataset == "acceptance derived lineage"
    assert "Synthetic test fixture" in (record.provenance.quality_note or "")

    heat_air = records["derived:context:heat-air-quality:current"]
    assert heat_air.definition_id == "heat-air-quality-context-v1"
    assert {item.id for item in heat_air.inputs} == {
        "observation:acceptance:temperature",
        "observation:acceptance:lqi",
    }
    assert heat_air.provenance.dataset == "acceptance heat-air cross-domain lineage"

    mobility_air = records["derived:context:mobility-air-quality:current"]
    assert mobility_air.definition_id == "mobility-air-quality-context-v1"
    assert {item.id for item in mobility_air.inputs} == {
        "vbb-gtfs-rt:2026-09-15T08:00:00+00:00",
        "observation:acceptance:lqi",
    }
    assert mobility_air.provenance.dataset == "acceptance mobility-air cross-domain lineage"
