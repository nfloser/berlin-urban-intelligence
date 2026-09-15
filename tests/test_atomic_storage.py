from pathlib import Path

from berlin_urban_intelligence.runtime.atomic import atomic_write_text


def test_atomic_write_replaces_target_and_cleans_temporary_file(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    target.write_text("old", encoding="utf-8")

    atomic_write_text(target, "new")

    assert target.read_text(encoding="utf-8") == "new"
    assert not target.with_suffix(".json.tmp").exists()


def test_atomic_write_creates_parent_directory(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "state.json"
    atomic_write_text(target, "value")
    assert target.read_text(encoding="utf-8") == "value"
