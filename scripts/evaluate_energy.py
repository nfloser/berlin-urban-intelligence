"""Evaluate Berlin grid-load data chronologically and persist a one-step forecast.

The command deliberately requires explicit timestamp/value column names because upstream CSV
schemas must be inspected rather than guessed. Input may be a local copy or an HTTPS Stromnetz
Berlin URL. Generated metrics are calculated from holdout predictions; no metric is embedded.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import httpx

from berlin_urban_intelligence.adapters.stromnetz_berlin import StromnetzBerlinCsvAdapter
from berlin_urban_intelligence.energy.state import EnergyStateStore
from berlin_urban_intelligence.energy.workflow import EnergyForecastWorkflow


def _load_text(value: str) -> tuple[str, str | None]:
    if value.startswith("https://"):
        if not value.startswith("https://www.stromnetz.berlin/"):
            raise ValueError(
                "remote energy input must use the verified www.stromnetz.berlin domain"
            )
        response = httpx.get(value, timeout=60.0, follow_redirects=True)
        response.raise_for_status()
        return response.text, value
    path = Path(value)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(path)
    return path.read_text(encoding="utf-8-sig"), None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input", required=True, help="Local CSV path or verified Stromnetz Berlin HTTPS URL"
    )
    parser.add_argument("--source-url", help="Required provenance URL when --input is a local file")
    parser.add_argument("--dataset", required=True, help="Inspected upstream dataset title")
    parser.add_argument("--timestamp-column", required=True)
    parser.add_argument("--value-column", required=True)
    parser.add_argument("--unit", default="MW")
    parser.add_argument("--delimiter", default=";")
    parser.add_argument("--source-timezone", default="Europe/Berlin")
    parser.add_argument("--seasonal-lag", type=int, default=96)
    parser.add_argument("--test-fraction", type=float, default=0.2)
    parser.add_argument("--state", default="data/runtime/energy.json")
    args = parser.parse_args()

    text, remote_url = _load_text(args.input)
    source_url = remote_url or args.source_url
    if not source_url:
        raise ValueError("--source-url is required when evaluating a local source copy")
    series = StromnetzBerlinCsvAdapter().parse(
        text,
        timestamp_column=args.timestamp_column,
        value_column=args.value_column,
        unit=args.unit,
        source_url=source_url,
        delimiter=args.delimiter,
        source_timezone=args.source_timezone,
    )
    state = EnergyForecastWorkflow().run(
        series,
        source_dataset=args.dataset,
        seasonal_lag=args.seasonal_lag,
        test_fraction=args.test_fraction,
    )
    EnergyStateStore(args.state).save(state)
    metric = state.evaluation
    forecast = state.forecasts[0]
    print(f"energy_state={args.state}")
    print(f"selected_model={metric.model_id}")
    print(f"mae={metric.mae:.6f}")
    print(f"rmse={metric.rmse:.6f}")
    print(f"baseline_model={metric.baseline_model_id}")
    print(f"baseline_mae={metric.baseline_mae:.6f}")
    print(f"forecast_valid_at={forecast.valid_at.isoformat()}")
    print(f"forecast_value={forecast.value:.6f} {forecast.unit}")
    print(f"dataset_fingerprint={metric.dataset_fingerprint}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
