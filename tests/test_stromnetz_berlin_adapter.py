from datetime import UTC, datetime

import pytest

from berlin_urban_intelligence.adapters.stromnetz_berlin import StromnetzBerlinCsvAdapter

SOURCE_URL = (
    "https://www.stromnetz.berlin/files/globalassets/dokumente/"
    "veroffentlichungspflichten/2025/jahreshoechstlast-2025-hochspannung.csv"
)

OFFICIAL_FIXTURE = """Stromnetz Berlin GmbH;;
Jahreshöchstlast in der Hochspannung;;
2025;;
;;
Max in kW;;1.995.320
Arbeit in kWh;;11.777.668.871
;;
;;
Datum;Zeit;
01.01.2025;00:15;1.158.989
01.01.2025;00:30;1.148.680
01.01.2025;00:45;1.145.428
"""


def test_official_annual_load_curve_contract_is_parsed_explicitly() -> None:
    series = StromnetzBerlinCsvAdapter().parse_published_annual_load_curve(
        OFFICIAL_FIXTURE,
        source_url=SOURCE_URL,
        expected_title="Jahreshöchstlast in der Hochspannung",
        expected_year=2025,
    )

    assert series.unit == "kW"
    assert series.frame["timestamp"].tolist() == [
        datetime(2024, 12, 31, 23, 15, tzinfo=UTC),
        datetime(2024, 12, 31, 23, 30, tzinfo=UTC),
        datetime(2024, 12, 31, 23, 45, tzinfo=UTC),
    ]
    assert series.frame["energy_demand"].tolist() == [1_158_989.0, 1_148_680.0, 1_145_428.0]


def test_official_annual_load_curve_rejects_semantic_drift() -> None:
    changed = OFFICIAL_FIXTURE.replace("Max in kW", "Maximum")

    with pytest.raises(ValueError, match="Max in kW"):
        StromnetzBerlinCsvAdapter().parse_published_annual_load_curve(
            changed,
            source_url=SOURCE_URL,
            expected_title="Jahreshöchstlast in der Hochspannung",
            expected_year=2025,
        )


def test_official_annual_load_curve_rejects_title_or_year_mismatch() -> None:
    adapter = StromnetzBerlinCsvAdapter()

    with pytest.raises(ValueError, match="dataset title"):
        adapter.parse_published_annual_load_curve(
            OFFICIAL_FIXTURE,
            source_url=SOURCE_URL,
            expected_title="Jahreshöchstlast in der Mittelspannung",
            expected_year=2025,
        )
    with pytest.raises(ValueError, match="dataset year"):
        adapter.parse_published_annual_load_curve(
            OFFICIAL_FIXTURE,
            source_url=SOURCE_URL,
            expected_title="Jahreshöchstlast in der Hochspannung",
            expected_year=2024,
        )
