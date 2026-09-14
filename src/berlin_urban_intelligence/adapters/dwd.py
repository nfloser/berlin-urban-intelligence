"""DWD CDC 10-minute air-temperature adapter.

The `now` product uses UTC timestamps, semicolon-separated CSV and -999 as the missing-value
sentinel. Quality control is explicitly incomplete for the `now` directory. This module never
replaces -999 with a plausible value.
"""

from __future__ import annotations

import csv
from datetime import UTC, datetime
from io import BytesIO, TextIOWrapper
from zipfile import ZipFile

import httpx
from pydantic import BaseModel, ConfigDict


class DwdTemperatureRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    station_id: str
    observed_at: datetime
    quality_level: int | None
    pressure_hpa: float | None
    temperature_c: float | None
    near_ground_temperature_c: float | None
    relative_humidity_pct: float | None
    dew_point_c: float | None


def _number(value: str | None) -> float | None:
    if value is None:
        return None
    stripped = value.strip()
    if stripped in {"", "-999", "-999.0"}:
        return None
    return float(stripped)


def _quality(value: str | None) -> int | None:
    number = _number(value)
    return None if number is None else int(number)


class DwdTenMinuteAirTemperatureClient:
    """Fetch and parse the current Berlin-Tempelhof (station 00433) DWD product by default."""

    BASE_URL = (
        "https://opendata.dwd.de/climate_environment/CDC/observations_germany/"
        "climate/10_minutes/air_temperature/now"
    )
    DEFAULT_STATION_ID = "00433"

    def __init__(self, client: httpx.Client | None = None, timeout_s: float = 20.0) -> None:
        self._owned_client = client is None
        self._client = client or httpx.Client(timeout=timeout_s, follow_redirects=True)

    def fetch(self, station_id: str = DEFAULT_STATION_ID) -> DwdTemperatureRecord:
        station = station_id.strip().zfill(5)
        url = f"{self.BASE_URL}/10minutenwerte_TU_{station}_now.zip"
        response = self._client.get(url)
        response.raise_for_status()
        return self.parse_latest(response.content, station_id=station)

    @staticmethod
    def parse_latest(payload: bytes, station_id: str) -> DwdTemperatureRecord:
        with ZipFile(BytesIO(payload)) as archive:
            candidates = [
                name
                for name in archive.namelist()
                if name.lower().endswith(".txt") and "produkt" in name.lower()
            ]
            if not candidates:
                raise ValueError("DWD archive contains no product text file")
            with archive.open(candidates[0]) as raw:
                reader = csv.DictReader(TextIOWrapper(raw, encoding="latin-1"), delimiter=";")
                rows = list(reader)
        if not rows:
            raise ValueError("DWD product contains no observations")

        def parse_time(row: dict[str, str]) -> datetime:
            value = (row.get("MESS_DATUM") or "").strip()
            if not value:
                raise ValueError("DWD row is missing MESS_DATUM")
            return datetime.strptime(value, "%Y%m%d%H%M").replace(tzinfo=UTC)

        latest = max(rows, key=parse_time)
        parsed_station = (latest.get("STATIONS_ID") or station_id).strip().zfill(5)
        if parsed_station != station_id.strip().zfill(5):
            raise ValueError("DWD product station id does not match requested station")
        return DwdTemperatureRecord(
            station_id=parsed_station,
            observed_at=parse_time(latest),
            quality_level=_quality(latest.get("QN")),
            pressure_hpa=_number(latest.get("PP_10")),
            temperature_c=_number(latest.get("TT_10")),
            near_ground_temperature_c=_number(latest.get("TM5_10")),
            relative_humidity_pct=_number(latest.get("RF_10")),
            dew_point_c=_number(latest.get("TD_10")),
        )

    def close(self) -> None:
        if self._owned_client:
            self._client.close()

    def __enter__(self) -> DwdTenMinuteAirTemperatureClient:
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()
