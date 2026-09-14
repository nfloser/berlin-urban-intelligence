"""Energy forecasting agent boundary with reproducible artefact validation.

The standalone energy prototype validates forecasting methodology on a household in Sceaux,
France. This integrated platform intentionally never reinterprets those values as Berlin demand.
The agent becomes operational only when a Berlin-scoped evaluation and a forecast artefact with
matching model and dataset fingerprints are explicitly registered.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from berlin_urban_intelligence.agents.base import BaseAgent
from berlin_urban_intelligence.shared.contracts import (
    AgentDescriptor,
    AgentHealth,
    AvailabilityStatus,
    Forecast,
    FreshnessStatus,
    Provenance,
    QualityFlag,
)
from berlin_urban_intelligence.shared.temporal import ensure_utc


class ModelMetric(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    model_id: str = Field(min_length=1)
    mae: float = Field(ge=0)
    rmse: float = Field(ge=0)
    evaluation_start: datetime
    evaluation_end: datetime
    dataset_fingerprint: str = Field(min_length=1)
    baseline_model_id: str = Field(min_length=1)
    baseline_mae: float = Field(ge=0)

    @model_validator(mode="after")
    def validate_window(self) -> ModelMetric:
        object.__setattr__(self, "evaluation_start", ensure_utc(self.evaluation_start))
        object.__setattr__(self, "evaluation_end", ensure_utc(self.evaluation_end))
        if self.evaluation_end <= self.evaluation_start:
            raise ValueError("evaluation_end must be later than evaluation_start")
        return self


class ForecastArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    forecast_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    entity_id: str = Field(min_length=1)
    phenomenon: str = "energy_demand"
    value: float
    unit: str = Field(min_length=1)
    issued_at: datetime
    valid_at: datetime
    dataset_fingerprint: str = Field(min_length=1)
    source_dataset: str = Field(min_length=1)
    source_url: HttpUrl
    source_licence: str | None = None
    lower_bound: float | None = None
    upper_bound: float | None = None

    @model_validator(mode="after")
    def validate_times(self) -> ForecastArtifact:
        object.__setattr__(self, "issued_at", ensure_utc(self.issued_at))
        object.__setattr__(self, "valid_at", ensure_utc(self.valid_at))
        if self.valid_at <= self.issued_at:
            raise ValueError("forecast valid_at must be later than issued_at")
        return self


class EnergyAgent(BaseAgent):
    descriptor = AgentDescriptor(
        id="energy",
        version="1.0.0",
        description=(
            "Leakage-safe forecasting boundary; Berlin forecasts require a validated Berlin-scoped "
            "evaluation and matching reproducible forecast artefact."
        ),
        capabilities=("model_evaluation_registry", "energy_forecast_contract", "forecast_registry"),
        input_contracts=("ModelMetric", "ForecastArtifact"),
        output_contracts=("Forecast",),
        source_dependencies=("stromnetz_berlin_grid_load",),
    )

    def __init__(self, *, now_factory: Callable[[], datetime] | None = None) -> None:
        super().__init__(now_factory=now_factory)
        self._berlin_model_metric: ModelMetric | None = None
        self._forecasts: tuple[Forecast, ...] = ()

    def register_berlin_evaluation(self, metric: ModelMetric) -> None:
        """Register metrics calculated by an external reproducible Berlin pipeline."""
        self._berlin_model_metric = metric

    def register_forecast(self, artifact: ForecastArtifact) -> Forecast:
        metric = self._berlin_model_metric
        if metric is None:
            raise ValueError("a Berlin model evaluation must be registered before a forecast")
        if artifact.model_id != metric.model_id:
            raise ValueError("forecast model_id does not match the registered evaluation")
        if artifact.dataset_fingerprint != metric.dataset_fingerprint:
            raise ValueError(
                "forecast dataset fingerprint does not match the registered evaluation"
            )
        provenance = Provenance(
            provider="configured Berlin energy source",
            dataset=artifact.source_dataset,
            source_url=artifact.source_url,
            original_identifier=artifact.forecast_id,
            observation_time=None,
            retrieved_at=artifact.issued_at,
            processed_at=artifact.issued_at,
            processing_method=(
                "forecast artefact registered after fingerprint/model identity validation; "
                "metrics are not recalculated by this boundary"
            ),
            agent=self.descriptor.id,
            agent_version=self.descriptor.version,
            model_version=artifact.model_id,
            source_licence=artifact.source_licence,
            quality_note=(
                f"Evaluation MAE={metric.mae}; RMSE={metric.rmse}; baseline "
                f"{metric.baseline_model_id} MAE={metric.baseline_mae}."
            ),
        )
        forecast = Forecast(
            id=artifact.forecast_id,
            entity_id=artifact.entity_id,
            phenomenon=artifact.phenomenon,
            value=artifact.value,
            unit=artifact.unit,
            issued_at=artifact.issued_at,
            valid_at=artifact.valid_at,
            quality=QualityFlag.VALID,
            provenance=provenance,
            lower_bound=artifact.lower_bound,
            upper_bound=artifact.upper_bound,
        )
        self._forecasts = (*self._forecasts, forecast)
        return forecast

    def forecasts(self) -> list[Forecast]:
        return list(self._forecasts)

    def evaluation(self) -> ModelMetric | None:
        return self._berlin_model_metric

    def health(self) -> AgentHealth:
        now = self.now()
        if self._berlin_model_metric is None:
            return self.unavailable_health(
                "No validated Berlin grid-load dataset/model is configured; "
                "the UCI prototype is research-reference-only."
            )
        if not self._forecasts:
            return AgentHealth(
                agent_id=self.descriptor.id,
                status=AvailabilityStatus.DEGRADED,
                checked_at=now,
                freshness=FreshnessStatus.UNAVAILABLE,
                quality=QualityFlag.VALID,
                detail=(
                    f"Evaluation {self._berlin_model_metric.model_id} is registered, "
                    "but no matching "
                    "Berlin forecast artefact is available."
                ),
            )
        latest = max(self._forecasts, key=lambda item: item.valid_at)
        return AgentHealth(
            agent_id=self.descriptor.id,
            status=AvailabilityStatus.AVAILABLE,
            checked_at=now,
            freshness=FreshnessStatus.VALID if latest.valid_at >= now else FreshnessStatus.STALE,
            quality=latest.quality,
            detail=f"{len(self._forecasts)} validated Berlin forecast artefact(s) registered.",
        )
