"""Explicit-schema parser for official Stromnetz Berlin load-curve CSV files.

The upstream publication offers multiple CSV files and the parser deliberately does not guess which
column represents time, value, voltage level or unit. Callers must supply the inspected schema.
"""

from __future__ import annotations

import re
from calendar import isleap
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from io import StringIO
from zoneinfo import ZoneInfo

import pandas as pd


@dataclass(frozen=True)
class EnergySeries:
    frame: pd.DataFrame
    unit: str
    source_url: str


class StromnetzBerlinCsvAdapter:
    _PUBLISHED_INTEGER = re.compile(r"(?:0|[1-9]\d*|[1-9]\d{0,2}(?:\.\d{3})+)")

    @staticmethod
    def _validate_source_url(source_url: str) -> None:
        if not source_url.startswith("https://www.stromnetz.berlin/"):
            raise ValueError("source_url must reference the verified Stromnetz Berlin domain")

    @staticmethod
    def _number(value: object) -> float:
        text = str(value).strip().replace("\u00a0", "")
        if not text:
            raise ValueError("energy value is missing")
        if "," in text:
            text = text.replace(".", "").replace(",", ".")
        return float(text)

    @classmethod
    def _published_integer(cls, value: str, *, field: str) -> int:
        text = value.strip().replace("\u00a0", "")
        if not cls._PUBLISHED_INTEGER.fullmatch(text):
            raise ValueError(f"invalid published {field} value: {value!r}")
        return int(text.replace(".", ""))

    @staticmethod
    def _split_published_line(line: str) -> list[str]:
        return [field.strip() for field in line.split(";")]

    @staticmethod
    def _expected_published_wall_time(
        utc_value: datetime,
        previous_utc: datetime | None,
        zone: ZoneInfo,
    ) -> datetime:
        """Return the wall-clock endpoint convention used by Stromnetz Berlin annual curves.

        The publication represents quarter-hour interval endpoints. At the exact DST transition
        boundary, the source labels that endpoint with the offset that applied to the interval that
        just ended; subsequent rows use the new offset. This preserves a continuous physical UTC
        sequence while matching the published 92/100-row DST days.
        """
        local = utc_value.astimezone(zone)
        if previous_utc is not None:
            previous_local = previous_utc.astimezone(zone)
            if local.utcoffset() != previous_local.utcoffset():
                previous_offset = previous_local.utcoffset()
                if previous_offset is None:
                    raise ValueError("source timezone did not provide a UTC offset")
                return (utc_value + previous_offset).replace(tzinfo=None)
        return local.replace(tzinfo=None)

    def parse_published_annual_load_curve(
        self,
        text: str,
        *,
        source_url: str,
        expected_title: str,
        expected_year: int,
        source_timezone: str = "Europe/Berlin",
    ) -> EnergySeries:
        """Parse one complete official annual load curve without inferring broken timestamps.

        Besides the row schema, this validates the publication metadata, exact annual point count,
        quarter-hour physical cadence including DST endpoint conventions, declared maximum and
        integrated annual work. Invalid upstream timestamp labels such as the 2025 ``#BEZUG!``
        block are rejected rather than reconstructed heuristically.
        """
        self._validate_source_url(source_url)
        if not expected_title.strip():
            raise ValueError("expected_title must not be blank")
        if expected_year < 2000 or expected_year > 2100:
            raise ValueError("expected_year is outside the supported publication range")

        lines = [line.lstrip("\ufeff").rstrip("\r") for line in text.splitlines() if line.strip()]
        if len(lines) < 10:
            raise ValueError("published annual load curve is incomplete")

        provider = self._split_published_line(lines[0])
        title = self._split_published_line(lines[1])
        year = self._split_published_line(lines[2])
        maximum = self._split_published_line(lines[4])
        work = self._split_published_line(lines[5])
        header = self._split_published_line(lines[8])

        if not provider or provider[0] != "Stromnetz Berlin GmbH":
            raise ValueError("published dataset provider does not match Stromnetz Berlin GmbH")
        if not title or title[0] != expected_title:
            raise ValueError("published dataset title does not match expected dataset title")
        if not year or year[0] != str(expected_year):
            raise ValueError("published dataset year does not match expected dataset year")
        if len(maximum) < 3 or maximum[0] != "Max in kW":
            raise ValueError("published metadata must contain 'Max in kW'")
        if len(work) < 3 or work[0] != "Arbeit in kWh":
            raise ValueError("published metadata must contain 'Arbeit in kWh'")
        if header[:2] != ["Datum", "Zeit"]:
            raise ValueError("published data header must begin with 'Datum;Zeit'")

        declared_maximum = self._published_integer(maximum[2], field="maximum")
        declared_work = self._published_integer(work[2], field="annual work")
        data_lines = lines[9:]
        expected_points = (366 if isleap(expected_year) else 365) * 96
        if len(data_lines) != expected_points:
            raise ValueError(
                f"published annual load curve requires {expected_points} quarter-hour values; "
                f"received {len(data_lines)}"
            )

        zone = ZoneInfo(source_timezone)
        first_expected = datetime(expected_year, 1, 1, 0, 15)
        first_utc = first_expected.replace(tzinfo=zone).astimezone(UTC)
        timestamps: list[datetime] = []
        values: list[float] = []
        previous_utc: datetime | None = None

        for index, line in enumerate(data_lines):
            fields = self._split_published_line(line)
            if len(fields) < 3:
                raise ValueError(f"published data row {index + 1} does not contain three fields")
            date_label, time_label, value_label = fields[:3]
            try:
                wall_time = datetime.strptime(f"{date_label} {time_label}", "%d.%m.%Y %H:%M")
            except ValueError as exc:
                raise ValueError(
                    f"invalid upstream timestamp in published data row {index + 1}"
                ) from exc

            utc_value = first_utc + timedelta(minutes=15 * index)
            expected_wall = self._expected_published_wall_time(utc_value, previous_utc, zone)
            if wall_time != expected_wall:
                raise ValueError(
                    "published timestamps do not form the expected continuous quarter-hour "
                    f"sequence at data row {index + 1}"
                )
            timestamps.append(utc_value)
            values.append(float(self._published_integer(value_label, field="load")))
            previous_utc = utc_value

        numeric_values = [int(value) for value in values]
        computed_maximum = max(numeric_values)
        if computed_maximum != declared_maximum:
            raise ValueError("published maximum is inconsistent with the quarter-hour load values")
        computed_work = round(sum(numeric_values) * 0.25)
        if computed_work != declared_work:
            raise ValueError(
                "published annual work is inconsistent with the quarter-hour load values"
            )

        frame = pd.DataFrame({"timestamp": timestamps, "energy_demand": values})
        return EnergySeries(frame=frame, unit="kW", source_url=source_url)

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
        self._validate_source_url(source_url)
        raw = pd.read_csv(StringIO(text), sep=delimiter, dtype=str, keep_default_na=False)
        missing = {timestamp_column, value_column}.difference(raw.columns)
        if missing:
            raise ValueError(
                f"CSV schema changed or configured columns are missing: {sorted(missing)}"
            )
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
