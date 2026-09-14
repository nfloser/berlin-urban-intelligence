import pytest

from berlin_urban_intelligence.adapters.berlin_air_quality import (
    extract_lqi_records,
    parse_lqi_record,
)


def test_official_station_envelope_groups_components_by_timestamp():
    payload = [
        {
            "station": "mc010",
            "data": [
                {"datetime": "2026-09-14T15:00:00+02:00", "component": "lqi", "grade": 3.0},
                {"datetime": "2026-09-14T15:00:00+02:00", "component": "pm25", "grade": 2.0},
                {"datetime": "2026-09-14T15:00:00+02:00", "component": "co", "grade": None},
                {"datetime": "2026-09-14T14:00:00+02:00", "component": "pm25", "grade": 1.0},
            ],
        }
    ]
    rows = extract_lqi_records(payload)
    assert len(rows) == 1
    record = parse_lqi_record(rows[0])
    assert record.grade == 3
    assert record.component_grades == {"PM2.5": 2}
    assert record.observed_at.hour == 13


@pytest.mark.parametrize("grade", [True, 2.5, 0, 7])
def test_invalid_grade_is_not_silently_truncated(grade):
    with pytest.raises(ValueError):
        parse_lqi_record({"station": "mc010", "timestamp": "2026-01-01T00:00:00Z", "grade": grade})


def test_negative_source_grade_does_not_discard_healthy_stations():
    rows = extract_lqi_records(
        [
            {
                "station": "mc010",
                "data": [{"datetime": "2026-01-01T00:00:00Z", "component": "lqi", "grade": 2}],
            },
            {
                "station": "mc124",
                "data": [{"datetime": "2026-01-01T00:00:00Z", "component": "lqi", "grade": -1}],
            },
        ]
    )
    assert [parse_lqi_record(row).station_code for row in rows] == ["MC010"]
