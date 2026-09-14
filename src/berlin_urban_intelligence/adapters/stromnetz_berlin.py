"""Explicit-schema parser for official Stromnetz Berlin load-curve CSV files.

The upstream publication offers multiple CSV files and the parser deliberately does not guess which
column represents time, value, voltage level or unit. Callers must supply the inspected schema.
"""

from __future__ import annotations

from dataclasses import dataclass
from io import StringIO

import pandas as pd


@dataclass(frozen=True)
class EnergySeries:
    frame: pd.DataFrame
    unit: str
    source_url: str


class StromnetzBerlinCsvAdapter:
    @staticmethod
    def _number(value: object) -> float:
        text = str(value).strip().replace("\u00a0", "")
        if not text:
            raise ValueError("energy value is missing")
        if "," in text:
            text = text.replace(".", "").replace(",", ".")
        return float(text)

    def parse(
        self,
        text: str,
        *,
        timestamp_column: str,
        value_column: str,
        unit: str,
        source_url: str,
        delimiter: str = ";",
        source_timezone: str = "Europe/Berlin",
    ) -> EnergySeries:
        if not timestamp_column.strip() or not value_column.strip() or not unit.strip():
            raise ValueError("timestamp column, value column and unit are required")
        if not source_url.startswith("https://www.stromnetz.berlin/"):
            raise ValueError("source_url must reference the verified Stromnetz Berlin domain")
        raw = pd.read_csv(StringIO(text), sep=delimiter, dtype=str, keep_default_na=False)
        missing = {timestamp_column, value_column}.difference(raw.columns)
        if missing:
            raise ValueError(f"CSV schema changed or configured columns are missing: {sorted(missing)}")
        timestamps = pd.to_datetime(raw[timestamp_column], dayfirst=True, errors="raise")
        if timestamps.dt.tz is None:
            try:
                timestamps = timestamps.dt.tz_localize(
                    source_timezone, ambiguous="infer", nonexistent="raise"
                )
            except Exception as exc:
                raise ValueError("source timestamps cannot be safely localized") from exc
        timestamps = timestamps.dt.tz_convert("UTC")
        values = raw[value_column].map(self._number).astype(float)
        frame = pd.DataFrame({"timestamp": timestamps, "energy_demand": values})
        if frame["timestamp"].duplicated().any():
            raise ValueError("duplicate timestamps in Stromnetz Berlin source")
        if not frame["timestamp"].is_monotonic_increasing:
            raise ValueError("Stromnetz Berlin source timestamps must be increasing")
        if frame["energy_demand"].isna().any():
            raise ValueError("missing values in Stromnetz Berlin source")
        return EnergySeries(frame=frame, unit=unit, source_url=source_url)
