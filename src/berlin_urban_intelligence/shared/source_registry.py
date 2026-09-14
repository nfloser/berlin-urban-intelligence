"""Machine-readable external source registry."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, HttpUrl


class SourceDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str
    provider: str
    dataset: str
    domain: str
    reference_url: HttpUrl
    api_url: HttpUrl | None = None
    authoritative: bool = False
    licence: str | None = None
    attribution: str | None = None
    expected_update_frequency: str
    temporal_coverage: str | None = None
    spatial_coverage: str
    status: str = "configured"
    limitations: tuple[str, ...] = ()


class SourceRegistry:
    def __init__(self, sources: list[SourceDefinition]) -> None:
        self._sources = {source.id: source for source in sources}
        if len(self._sources) != len(sources):
            raise ValueError("source ids must be unique")

    @classmethod
    def from_yaml(cls, path: Path) -> "SourceRegistry":
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict) or not isinstance(raw.get("sources"), list):
            raise ValueError("source registry requires a top-level 'sources' list")
        return cls([SourceDefinition.model_validate(item) for item in raw["sources"]])

    def get(self, source_id: str) -> SourceDefinition:
        try:
            return self._sources[source_id]
        except KeyError as exc:
            raise KeyError(f"unknown source: {source_id}") from exc

    def all(self) -> list[SourceDefinition]:
        return list(self._sources.values())
