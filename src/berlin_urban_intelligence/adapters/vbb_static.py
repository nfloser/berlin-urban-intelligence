"""VBB GTFS static acquisition and schema-faithful normalization."""

from __future__ import annotations

import csv
from datetime import datetime
from io import BytesIO, TextIOWrapper
from zipfile import BadZipFile, ZipFile

import httpx
from pydantic import BaseModel, ConfigDict, Field

from berlin_urban_intelligence.shared.contracts import SpatialReference, UrbanEntity
from berlin_urban_intelligence.shared.temporal import ensure_utc


class GtfsStaticSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    retrieved_at: datetime
    stop_count: int = Field(ge=0)
    route_count: int = Field(ge=0)
    trip_count: int = Field(ge=0)
    stops: tuple[UrbanEntity, ...]
    source_url: str = "https://unternehmen.vbb.de/gtfs"
    licence: str = "CC BY 4.0"


class VbbGtfsStaticClient:
    URL = "https://unternehmen.vbb.de/gtfs"
    USER_AGENT = "berlin-urban-intelligence/0.1 (+https://github.com/nfloser/berlin-urban-intelligence)"

    def __init__(self, client: httpx.Client | None = None, timeout_s: float = 60.0) -> None:
        self._owned_client = client is None
        self._client = client or httpx.Client(timeout=timeout_s, follow_redirects=True)

    def fetch(self) -> bytes:
        response = self._client.get(self.URL, headers={"User-Agent": self.USER_AGENT})
        response.raise_for_status()
        if not response.content:
            raise ValueError("VBB GTFS static download is empty")
        return response.content

    def close(self) -> None:
        if self._owned_client:
            self._client.close()


class VbbGtfsStaticAdapter:
    REQUIRED_FILES = ("stops.txt", "routes.txt", "trips.txt")
    MAX_UNCOMPRESSED_BYTES = 512 * 1024 * 1024

    @staticmethod
    def _reader(archive: ZipFile, name: str) -> csv.DictReader:
        return csv.DictReader(TextIOWrapper(archive.open(name), encoding="utf-8-sig", newline=""))

    def parse(self, payload: bytes, *, retrieved_at: datetime | str) -> GtfsStaticSnapshot:
        retrieved = ensure_utc(datetime.fromisoformat(retrieved_at.replace("Z", "+00:00")) if isinstance(retrieved_at, str) else retrieved_at)
        try:
            with ZipFile(BytesIO(payload)) as archive:
                names = set(archive.namelist())
                for required in self.REQUIRED_FILES:
                    if required not in names:
                        raise ValueError(f"GTFS archive missing required file: {required}")
                total_size = sum(info.file_size for info in archive.infolist())
                if total_size > self.MAX_UNCOMPRESSED_BYTES:
                    raise ValueError("GTFS archive exceeds configured uncompressed size limit")

                stops: list[UrbanEntity] = []
                stop_reader = self._reader(archive, "stops.txt")
                required_stop_fields = {"stop_id", "stop_name", "stop_lat", "stop_lon"}
                if not stop_reader.fieldnames or not required_stop_fields.issubset(stop_reader.fieldnames):
                    raise ValueError("GTFS stops.txt schema is missing required columns")
                for row in stop_reader:
                    stop_id = (row.get("stop_id") or "").strip()
                    name = (row.get("stop_name") or "").strip()
                    if not stop_id:
                        continue
                    try:
                        lat = float(row["stop_lat"])
                        lon = float(row["stop_lon"])
                    except (TypeError, ValueError) as exc:
                        raise ValueError(f"invalid coordinates for GTFS stop {stop_id}") from exc
                    stops.append(
                        UrbanEntity(
                            id=f"transport-stop:vbb:{stop_id}",
                            entity_type="transport_stop",
                            name=name or None,
                            source_identifier=stop_id,
                            spatial=SpatialReference(
                                crs="EPSG:4326",
                                geometry={"type": "Point", "coordinates": [lon, lat]},
                            ),
                        )
                    )

                route_reader = self._reader(archive, "routes.txt")
                if not route_reader.fieldnames or "route_id" not in route_reader.fieldnames:
                    raise ValueError("GTFS routes.txt schema is missing route_id")
                route_count = sum(1 for row in route_reader if (row.get("route_id") or "").strip())

                trip_reader = self._reader(archive, "trips.txt")
                if not trip_reader.fieldnames or "trip_id" not in trip_reader.fieldnames:
                    raise ValueError("GTFS trips.txt schema is missing trip_id")
                trip_count = sum(1 for row in trip_reader if (row.get("trip_id") or "").strip())
        except BadZipFile as exc:
            raise ValueError("VBB GTFS static payload is not a valid ZIP archive") from exc

        return GtfsStaticSnapshot(
            retrieved_at=retrieved,
            stop_count=len(stops),
            route_count=route_count,
            trip_count=trip_count,
            stops=tuple(stops),
        )
