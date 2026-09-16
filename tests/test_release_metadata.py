from __future__ import annotations

from pathlib import Path
import re
import tomllib


ROOT = Path(__file__).resolve().parents[1]


def _repository_version() -> str:
    return (ROOT / "VERSION").read_text(encoding="utf-8").strip()


def test_stable_release_metadata_is_consistent() -> None:
    version = _repository_version()
    parts = version.split(".")

    assert len(parts) == 3 and all(part.isdigit() for part in parts)
    assert int(parts[0]) >= 1, "stable release metadata must use a major version >= 1"

    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["version"] == version

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert f"**Version {version}**" in readme

    licence = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert licence.startswith("MIT License")
    assert "MIT License" in readme

    changelog_path = ROOT / "CHANGELOG.md"
    assert changelog_path.is_file(), "stable releases require a project changelog"
    changelog = changelog_path.read_text(encoding="utf-8")
    assert re.search(
        rf"^## \[{re.escape(version)}\] - \d{{4}}-\d{{2}}-\d{{2}}$",
        changelog,
        flags=re.MULTILINE,
    )

    release_notes_path = ROOT / "docs" / "releases" / f"v{version}.md"
    assert release_notes_path.is_file(), "stable releases require versioned release notes"
    release_notes = release_notes_path.read_text(encoding="utf-8")
    assert f"v{version}" in release_notes
    assert "Limitations" in release_notes
