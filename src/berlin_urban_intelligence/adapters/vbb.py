"""VBB GTFS-Realtime source adapter.

The HTTP layer does not interpret missing entities as normal operation. Protobuf decoding is
isolated so deterministic tests can exercise the analytical logic without a live service.
"""

from __future__ import annotations

from datetime import UTC, datetime

import httpx


class VbbGtfsRealtimeClient:
    URL = "https://production.gtfsrt.vbb.de/data"
    USER_AGENT = (
        "berlin-urban-intelligence/0.1 (+https://github.com/nfloser/berlin-urban-intelligence)"
    )

    def __init__(self, client: httpx.Client | None = None, timeout_s: float = 20.0) -> None:
        self._owned_client = client is None
        self._client = client or httpx.Client(timeout=timeout_s, follow_redirects=True)

    def fetch(self) -> bytes:
        response = self._client.get(self.URL, headers={"User-Agent": self.USER_AGENT})
        response.raise_for_status()
        if not response.content:
            raise ValueError("VBB GTFS-Realtime returned an empty payload")
        return response.content

    def close(self) -> None:
        if self._owned_client:
            self._client.close()

    def __enter__(self) -> VbbGtfsRealtimeClient:
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()


def decode_gtfs_realtime(payload: bytes) -> tuple[datetime | None, list[dict[str, object]]]:
    """Decode GTFS-Realtime if the optional official Python bindings are installed.

    Returns a source timestamp and a compact list of trip-update dictionaries. Import failure is
    explicit rather than silently skipping realtime parsing.
    """
    try:
        from google.transit import gtfs_realtime_pb2
    except ImportError as exc:
        raise RuntimeError(
            "GTFS-Realtime decoding requires the optional 'gtfs-realtime-bindings' dependency"
        ) from exc

    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(payload)
    feed_timestamp = None
    if getattr(feed.header, "timestamp", 0):
        feed_timestamp = datetime.fromtimestamp(int(feed.header.timestamp), tz=UTC)
    records: list[dict[str, object]] = []
    for entity in feed.entity:
        if not entity.HasField("trip_update"):
            continue
        update = entity.trip_update
        trip_id = str(update.trip.trip_id or entity.id)
        delays: list[int] = []
        for stop_time in update.stop_time_update:
            for event_name in ("arrival", "departure"):
                event = getattr(stop_time, event_name)
                if event and event.HasField("delay"):
                    delays.append(int(event.delay))
        records.append({"trip_id": trip_id, "delays_s": delays})
    return feed_timestamp, records
