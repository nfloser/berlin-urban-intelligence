"""Change-aware loading for persisted application snapshots.

The API serves validated persisted state and never performs provider acquisition in request handlers.
This module only detects atomic snapshot replacement and reloads changed files. Invalid replacements
leave the last-known-good value intact while exposing an explicit diagnostic state.
"""

from __future__ import annotations

from collections.abc import Callable
from enum import StrEnum
from pathlib import Path
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")
FileSignature = tuple[int, int, int]


class SnapshotReloadStatus(StrEnum):
    CURRENT = "current"
    MISSING = "missing"
    INVALID = "invalid"


class SnapshotReloadDiagnostic(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: SnapshotReloadStatus
    last_error: str | None = None


class ReloadingSnapshot(Generic[T]):
    """Cache a validated snapshot and reload only when the backing file identity changes."""

    def __init__(self, path: Path, loader: Callable[[], T | None]) -> None:
        self.path = path
        self._loader = loader
        self._signature: FileSignature | None = None
        self._known_missing = False
        self._value: T | None = None
        self._diagnostic = SnapshotReloadDiagnostic(status=SnapshotReloadStatus.MISSING)

    @property
    def value(self) -> T | None:
        return self._value

    @property
    def diagnostic(self) -> SnapshotReloadDiagnostic:
        return self._diagnostic

    def refresh(self, *, force: bool = False) -> bool:
        """Refresh changed state and return whether a new valid value became active."""

        try:
            stat = self.path.stat()
        except FileNotFoundError:
            if not force and self._known_missing:
                return False
            self._signature = None
            self._known_missing = True
            error = None
            if self._value is not None:
                error = "snapshot file is missing; retaining last-known-good state"
            self._diagnostic = SnapshotReloadDiagnostic(
                status=SnapshotReloadStatus.MISSING,
                last_error=error,
            )
            return False

        signature: FileSignature = (stat.st_mtime_ns, stat.st_size, stat.st_ino)
        if not force and not self._known_missing and signature == self._signature:
            return False

        self._signature = signature
        self._known_missing = False
        try:
            candidate = self._loader()
        except Exception as exc:
            self._diagnostic = SnapshotReloadDiagnostic(
                status=SnapshotReloadStatus.INVALID,
                last_error=f"{type(exc).__name__}: {exc}",
            )
            return False

        if candidate is None:
            self._diagnostic = SnapshotReloadDiagnostic(
                status=SnapshotReloadStatus.MISSING,
                last_error="snapshot disappeared during reload",
            )
            return False

        self._value = candidate
        self._diagnostic = SnapshotReloadDiagnostic(status=SnapshotReloadStatus.CURRENT)
        return True
