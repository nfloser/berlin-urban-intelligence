from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from berlin_urban_intelligence.adapters.stromnetz_berlin import StromnetzBerlinCsvAdapter

SOURCE_URL = (
    "https://www.stromnetz.berlin/files/globalassets/dokumente/"
    "veroffentlichungspflichten/2024/Jahreshoechstlast-2024-Hochspannung.csv"
)
TITLE = "Jahreshöchstlast in der Hochspannung"


def _german_integer(value: int) -> str:
    return f"{value:,}".replace(",", ".")


def _published_wall_label(utc_value: datetime, previous_utc: datetime | None) -> str:
    zone = ZoneInfo("Europe/Berlin")
    local = utc_value.astimezone(zone)
    if previous_utc is not None:
        previous_local = previous_utc.astimezone(zone)
        if local.utcoffset() != previous_local.utcoffset():
            offset = previous_local.utcoffset()
            assert offset is not None
            naive = (utc_value + offset).replace(tzinfo=None)
            return naive.strftime("%d.%m.%Y;%H:%M")
    return local.strftime("%d.%m.%Y;%H:%M")


def _official_2024_fixture() -> str:
    value = 1_000_000
    periods = 366 * 96
    first_utc = datetime(2023, 12, 31, 23, 15, tzinfo=UTC)
    rows: list[str] = []
    previous_utc: datetime | None = None
    for index in range(periods):
        utc_value = first_utc + timedelta(minutes=15 * index)
        label = _published_wall_label(utc_value, previous_utc)
        rows.append(f"{label};{_german_integer(value)}")
        previous_utc = utc_value
    annual_work = periods * value // 4
    metadata = [
        "Stromnetz Berlin GmbH;;",
        f"{TITLE};;",
        "2024;;",
        ";;",
        f"Max in kW;;{_german_integer(value)}",
        f"Arbeit in kWh;;{_german_integer(annual_work)}",
        ";;",
        ";;",
        "Datum;Zeit;",
    ]
    return "\n".join([*metadata, *rows, ""])


def test_official_annual_load_curve_contract_is_parsed_explicitly() -> None:
    series = StromnetzBerlinCsvAdapter().parse_published_annual_load_curve(
        _official_2024_fixture(),
        source_url=SOURCE_URL,
        expected_title=TITLE,
        expected_year=2024,
    )

    assert series.unit == "kW"
    assert len(series.frame) == 35_136
    assert series.frame["timestamp"].iloc[0] == datetime(2023, 12, 31, 23, 15, tzinfo=UTC)
    assert series.frame["timestamp"].iloc[-1] == datetime(2024, 12, 31, 23, 0, tzinfo=UTC)
    assert series.frame["timestamp"].diff().dropna().nunique() == 1
    assert series.frame["timestamp"].diff().dropna().iloc[0] == timedelta(minutes=15)
    assert set(series.frame["energy_demand"]) == {1_000_000.0}


def test_official_annual_load_curve_rejects_upstream_reference_error() -> None:
    changed = _official_2024_fixture().replace(
        "01.05.2024;00:15;1.000.000", "#BEZUG!;#BEZUG!;1.000.000", 1
    )

    with pytest.raises(ValueError, match="invalid upstream timestamp"):
        StromnetzBerlinCsvAdapter().parse_published_annual_load_curve(
            changed,
            source_url=SOURCE_URL,
            expected_title=TITLE,
            expected_year=2024,
        )


def test_official_annual_load_curve_rejects_semantic_drift() -> None:
    changed = _official_2024_fixture().replace("Max in kW", "Maximum")

    with pytest.raises(ValueError, match="Max in kW"):
        StromnetzBerlinCsvAdapter().parse_published_annual_load_curve(
            changed,
            source_url=SOURCE_URL,
            expected_title=TITLE,
            expected_year=2024,
        )


def test_official_annual_load_curve_rejects_title_or_year_mismatch() -> None:
    adapter = StromnetzBerlinCsvAdapter()
    fixture = _official_2024_fixture()

    with pytest.raises(ValueError, match="dataset title"):
        adapter.parse_published_annual_load_curve(
            fixture,
            source_url=SOURCE_URL,
            expected_title="Jahreshöchstlast in der Mittelspannung",
            expected_year=2024,
        )
    with pytest.raises(ValueError, match="dataset year"):
        adapter.parse_published_annual_load_curve(
            fixture,
            source_url=SOURCE_URL,
            expected_title=TITLE,
            expected_year=2023,
        )


def test_official_annual_load_curve_rejects_inconsistent_summary_values() -> None:
    fixture = _official_2024_fixture()
    wrong_maximum = fixture.replace("Max in kW;;1.000.000", "Max in kW;;1.000.001")
    wrong_work = fixture.replace("Arbeit in kWh;;8.784.000.000", "Arbeit in kWh;;8.784.000.001")
    adapter = StromnetzBerlinCsvAdapter()

    with pytest.raises(ValueError, match="maximum"):
        adapter.parse_published_annual_load_curve(
            wrong_maximum,
            source_url=SOURCE_URL,
            expected_title=TITLE,
            expected_year=2024,
        )
    with pytest.raises(ValueError, match="annual work"):
        adapter.parse_published_annual_load_curve(
            wrong_work,
            source_url=SOURCE_URL,
            expected_title=TITLE,
            expected_year=2024,
        )
