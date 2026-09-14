"""Reproducible Berlin energy evaluation and one-step forecasting workflow."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from pydantic import HttpUrl

from berlin_urban_intelligence.adapters.stromnetz_berlin import EnergySeries
from berlin_urban_intelligence.agents.energy import ForecastArtifact
from berlin_urban_intelligence.energy.pipeline import EnergyForecastPipeline
from berlin_urban_intelligence.energy.state import EnergyState


class EnergyForecastWorkflow:
    def __init__(self, *, now_factory: Callable[[], datetime] | None = None) -> None:
        self.now_factory = now_factory or (lambda: datetime.now(UTC))

    def run(
        self,
        series: EnergySeries,
        *,
        source_dataset: str,
        seasonal_lag: int = 96,
        test_fraction: float = 0.2,
        entity_id: str = "energy:grid:berlin",
    ) -> EnergyState:
        if not source_dataset.strip():
            raise ValueError("source_dataset must not be blank")
        frame = series.frame.rename(columns={"energy_demand": "demand"})
        pipeline = EnergyForecastPipeline(target_column="demand", seasonal_lag=seasonal_lag)
        evaluation = pipeline.evaluate(frame, test_fraction=test_fraction)
        candidate = pipeline.select_candidate(evaluation)
        point = pipeline.forecast_next(frame, model_id=candidate.model_id)
        artifact = ForecastArtifact(
            forecast_id=f"forecast:berlin-grid:{point.valid_at.isoformat()}",
            model_id=point.model_id,
            entity_id=entity_id,
            value=point.value,
            unit=series.unit,
            issued_at=point.issued_at,
            valid_at=point.valid_at,
            dataset_fingerprint=point.dataset_fingerprint,
            source_dataset=source_dataset,
            source_url=HttpUrl(series.source_url),
            source_licence=None,
        )
        generated = self.now_factory()
        if generated.tzinfo is None or generated.utcoffset() is None:
            raise ValueError("now_factory must produce timezone-aware datetimes")
        return EnergyState(
            generated_at=generated.astimezone(UTC),
            evaluation=candidate,
            forecasts=(artifact,),
            notes=(
                "Candidate selected by lowest chronological holdout MAE, then RMSE; simpler "
                "baselines win exact ties. Forecast is one source interval ahead.",
                "No prediction interval is emitted because no calibrated "
                "uncertainty method is implemented.",
            ),
        )
