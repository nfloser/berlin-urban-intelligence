"""Adapter for the official Berliner Luftgütemessnetz REST API.

Verified API documentation: https://luftdaten.berlin.de/api/doc
The current LQI endpoint is /api/lqis/data. The current index uses provisional automatic
measurements; consumers must preserve that quality caveat.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field


class LqiRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    station_code: str = Field(min_length=1)
    observed_at: datetime
    grade: int = Field(ge=1, le=6)
    component_grades: dict[str, int] = Field(default_factory=dict)


_COMPONENT_ALIASES = {
    "pm10": "PM10",
    "pm2.5": "PM2.5",
    "pm25": "PM2.5",
    "pm2_5": "PM2.5",
    "no2": "NO2",
    "o3": "O3",
    "co": "CO",
    "so2": "SO2",
}


def _first(payload: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in payload and payload[key] is not None:
            return payload[key]
    return None


def _grade(value: Any) -> int:
    grade = int(value)
    if not 1 <= grade <= 6:
        raise ValueError("LQI grade must be between 1 and 6")
    return grade


def extract_lqi_records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("data", "items", "results", "lqis"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    raise ValueError("Unsupported Berlin LQI response envelope")


def parse_lqi_record(payload: dict[str, Any]) -> LqiRecord:
    station = _first(payload, "station", "station_code", "stationCode", "code")
    if isinstance(station, dict):
        station = _first(station, "code", "station_code", "stationCode")
    station_code = str(station or "").strip().upper()
    if not station_code:
        raise ValueError("LQI observation requires a station code")

    timestamp = _first(payload, "timestamp", "date", "datetime", "observed_at", "observedAt")
    if not timestamp:
        raise ValueError("LQI observation requires a timestamp")
    observed_at = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
    if observed_at.tzinfo is None or observed_at.utcoffset() is None:
        raise ValueError("LQI timestamp must include a timezone")
    observed_at = observed_at.astimezone(UTC)

    grade_value = _first(payload, "lqi", "index", "grade", "value")
    if grade_value is None:
        raise ValueError("LQI observation requires an overall grade")

    values: dict[str, Any] = {}
    nested = payload.get("components")
    if isinstance(nested, dict):
        values.update(nested)
    for alias in _COMPONENT_ALIASES:
        if alias in payload:
            values[alias] = payload[alias]
    component_grades: dict[str, int] = {}
    for key, value in values.items():
        if value in (None, "", "-", "×", "U"):
            continue
        canonical = _COMPONENT_ALIASES.get(str(key).lower())
        if canonical:
            component_grades[canonical] = _grade(value)

    return LqiRecord(
        station_code=station_code,
        observed_at=observed_at,
        grade=_grade(grade_value),
        component_grades=component_grades,
    )


class BerlinAirQualityClient:
    BASE_URL = "https://luftdaten.berlin.de/api"

    def __init__(self, client: httpx.Client | None = None, timeout_s: float = 15.0) -> None:
        self._owned_client = client is None
        self._client = client or httpx.Client(timeout=timeout_s, follow_redirects=True)

    def get_lqi_data(self) -> Any:
        response = self._client.get(f"{self.BASE_URL}/lqis/data")
        response.raise_for_status()
        return response.json()

    def get_stations(self) -> Any:
        response = self._client.get(f"{self.BASE_URL}/stations")
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        if self._owned_client:
            self._client.close()

    def __enter__(self) -> BerlinAirQualityClient:
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()
