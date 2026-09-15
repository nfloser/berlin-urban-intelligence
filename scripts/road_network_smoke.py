"""Run a point-in-time real OSM road-network readiness check.

This is intentionally separate from deterministic PR CI. It performs live external acquisition and
returns non-zero when the provider, schema or resulting network is not routing-ready. Failures are
recorded as evidence and are never replaced with synthetic data.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from berlin_urban_intelligence.adapters.osm_network import OsmnxRoadNetworkClient
from berlin_urban_intelligence.runtime.road_readiness import verify_road_network_snapshot


def _write_evidence(path: Path | None, payload: dict[str, Any]) -> None:
    rendered = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)
    print(rendered)
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--place",
        default="Mitte, Berlin, Germany",
        help="Real OSMnx place query used for the smoke scope.",
    )
    parser.add_argument("--network-type", default="drive")
    parser.add_argument(
        "--allow-osmnx-speed-imputation",
        action="store_true",
        help=(
            "Explicitly allow OSMnx add_edge_speeds/add_edge_travel_times. "
            "The resulting derivation must be visible in provenance."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional JSON evidence file. Failure evidence is written before returning non-zero.",
    )
    args = parser.parse_args()

    try:
        snapshot = OsmnxRoadNetworkClient().fetch(
            args.place,
            network_type=args.network_type,
            allow_speed_imputation=args.allow_osmnx_speed_imputation,
        )
        report = verify_road_network_snapshot(
            snapshot,
            require_speed_imputation_visible=args.allow_osmnx_speed_imputation,
        )
    except Exception as exc:
        _write_evidence(
            args.output,
            {
                "status": "failed",
                "place": args.place,
                "network_type": args.network_type,
                "speed_imputation_enabled": args.allow_osmnx_speed_imputation,
                "error_type": type(exc).__name__,
                "error": str(exc),
                "synthetic_fallback": False,
            },
        )
        return 2

    _write_evidence(
        args.output,
        {
            "status": "passed",
            "place": args.place,
            "network_type": args.network_type,
            "speed_imputation_enabled": args.allow_osmnx_speed_imputation,
            "synthetic_fallback": False,
            "readiness": report.model_dump(mode="json"),
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
