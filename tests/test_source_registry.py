from pathlib import Path

from berlin_urban_intelligence.shared.source_registry import SourceRegistry


def test_registry_has_unique_verified_domain_sources() -> None:
    registry = SourceRegistry.from_yaml(Path("config/sources.yaml"))
    sources = registry.all()
    ids = [source.id for source in sources]
    assert len(ids) == len(set(ids))
    assert "berlin_air_quality" in ids
    assert "vbb_gtfs_rt" in ids
    assert "dwd_open_data" in ids
    assert "stromnetz_berlin_grid_load" in ids


def test_non_berlin_energy_reference_is_explicitly_not_operational() -> None:
    registry = SourceRegistry.from_yaml(Path("config/sources.yaml"))
    reference = registry.get("energy_reference_uci")
    assert reference.authoritative is False
    assert reference.status == "research-reference-only"
    assert "France" in reference.spatial_coverage
