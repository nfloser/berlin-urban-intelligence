from __future__ import annotations

from datetime import UTC, datetime, timedelta

from berlin_urban_intelligence.runtime.traffic_disruption_refresh import (
    TrafficDisruptionRefreshCoordinator,
)
from berlin_urban_intelligence.runtime.traffic_disruptions import TrafficDisruptionState
from berlin_urban_intelligence.shared.contracts import FreshnessStatus

NOW = datetime(2026, 9, 19, 16, 30, tzinfo=UTC)


class SuccessfulClient:
    source_url = "https://api.viz.berlin.de/daten/baustellen_sperrungen_viz.json"

    def fetch(self) -> dict[str, object]:
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [13.4, 52.52]},
                    "properties": {
                        "id": "viz:1",
                        "subtype": "Sperrung",
                        "severity": "Vollsperrung",
                        "validity": {
                            "from": "2026-09-19T17:00",
                            "to": "2026-09-19T20:00",
                        },
                        "tstore": "2026-09-19T15:01:00Z",
                        "street": "Teststraße",
                        "section": "Testabschnitt",
                        "content": "Vollsperrung",
                        "direction": "beide Richtungen",
                        "netrefs": None,
                        "objectState": "modified",
                    },
                }
            ],
        }


class FailingClient:
    source_url = SuccessfulClient.source_url

    def __init__(self, exc: Exception) -> None:
        self.exc = exc

    def fetch(self) -> dict[str, object]:
        raise self.exc


def test_refresh_success_persists_current_source_state() -> None:
    state = TrafficDisruptionRefreshCoordinator(
        client=SuccessfulClient(),
        now_factory=lambda: NOW,
    ).refresh()

    assert state.generated_at == NOW
    assert state.last_success_at == NOW
    assert state.latest_source_update_at == datetime(2026, 9, 19, 15, 1, tzinfo=UTC)
    assert state.source_error is None
    assert state.freshness is FreshnessStatus.VALID
    assert [item.id for item in state.disruptions] == ["viz:1"]


def test_refresh_source_failure_preserves_last_known_good_and_marks_stale() -> None:
    previous = TrafficDisruptionRefreshCoordinator(
        client=SuccessfulClient(),
        now_factory=lambda: NOW,
    ).refresh()
    later = NOW + timedelta(minutes=10)

    state = TrafficDisruptionRefreshCoordinator(
        client=FailingClient(RuntimeError("network down")),
        now_factory=lambda: later,
    ).refresh(previous_state=previous)

    assert state.generated_at == later
    assert state.last_success_at == NOW
    assert state.disruptions == previous.disruptions
    assert state.source_error == "SOURCE_UNAVAILABLE"
    assert state.freshness is FreshnessStatus.STALE


def test_refresh_schema_failure_preserves_last_known_good_with_explicit_code() -> None:
    previous = TrafficDisruptionRefreshCoordinator(
        client=SuccessfulClient(),
        now_factory=lambda: NOW,
    ).refresh()

    state = TrafficDisruptionRefreshCoordinator(
        client=FailingClient(ValueError("schema changed")),
        now_factory=lambda: NOW + timedelta(minutes=5),
    ).refresh(previous_state=previous)

    assert state.disruptions == previous.disruptions
    assert state.source_error == "SCHEMA_CHANGED"
    assert state.freshness is FreshnessStatus.STALE


def test_first_failure_is_unavailable_without_fabricated_events() -> None:
    state = TrafficDisruptionRefreshCoordinator(
        client=FailingClient(RuntimeError("offline")),
        now_factory=lambda: NOW,
    ).refresh()

    assert state.disruptions == ()
    assert state.source_error == "SOURCE_UNAVAILABLE"
    assert state.last_success_at is None
    assert state.freshness is FreshnessStatus.UNAVAILABLE


def test_previous_state_source_id_must_match() -> None:
    previous = TrafficDisruptionState(
        generated_at=NOW,
        source_id="wrong_source",
    )

    try:
        TrafficDisruptionRefreshCoordinator(
            client=SuccessfulClient(),
            now_factory=lambda: NOW,
        ).refresh(previous_state=previous)
    except ValueError as exc:
        assert "source_id" in str(exc)
    else:
        raise AssertionError("mismatched source state must be rejected")


class StaleSuccessfulClient(SuccessfulClient):
    def fetch(self) -> dict[str, object]:
        payload = super().fetch()
        payload["features"][0]["properties"]["tstore"] = "2026-09-15T10:00:00Z"
        return payload


def test_successful_but_old_provider_content_is_marked_stale() -> None:
    state = TrafficDisruptionRefreshCoordinator(
        client=StaleSuccessfulClient(),
        now_factory=lambda: NOW,
    ).refresh()

    assert state.last_success_at == NOW
    assert state.latest_source_update_at == datetime(2026, 9, 15, 10, 0, tzinfo=UTC)
    assert state.source_error is None
    assert state.disruptions
    assert state.freshness is FreshnessStatus.STALE
