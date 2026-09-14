"""Leakage-safe short-horizon energy forecasting evaluation.

This module contains no embedded production data. It operates on an explicitly supplied,
time-ordered data frame and computes every reported metric from out-of-sample predictions.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from berlin_urban_intelligence.agents.energy import ModelMetric


@dataclass(frozen=True)
class EnergyEvaluation:
    metrics: tuple[ModelMetric, ...]
    train_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp


@dataclass(frozen=True)
class EnergyPointForecast:
    model_id: str
    value: float
    issued_at: datetime
    valid_at: datetime
    dataset_fingerprint: str


def fingerprint_frame(frame: pd.DataFrame) -> str:
    """Stable SHA-256 over timestamp/value content and column names."""
    canonical = frame.copy()
    if "timestamp" not in canonical.columns:
        raise ValueError("energy frame requires timestamp column")
    canonical["timestamp"] = pd.to_datetime(canonical["timestamp"], utc=True).map(
        lambda value: value.isoformat()
    )
    payload = canonical.to_csv(index=False, lineterminator="\n", float_format="%.12g")
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class EnergyForecastPipeline:
    """One-step-ahead evaluator using only information available before each target time."""

    def __init__(self, *, target_column: str, seasonal_lag: int = 96, ridge_alpha: float = 1.0) -> None:
        if not target_column.strip():
            raise ValueError("target_column must not be blank")
        if seasonal_lag < 2:
            raise ValueError("seasonal_lag must be at least 2")
        if ridge_alpha <= 0:
            raise ValueError("ridge_alpha must be positive")
        self.target_column = target_column
        self.seasonal_lag = seasonal_lag
        self.ridge_alpha = ridge_alpha

    def _validated(self, frame: pd.DataFrame) -> pd.DataFrame:
        required = {"timestamp", self.target_column}
        missing = required.difference(frame.columns)
        if missing:
            raise ValueError(f"energy frame missing required columns: {sorted(missing)}")
        result = frame.copy()
        result["timestamp"] = pd.to_datetime(result["timestamp"], utc=True, errors="raise")
        if result["timestamp"].duplicated().any():
            raise ValueError("timestamp column contains duplicates")
        if not result["timestamp"].is_monotonic_increasing:
            raise ValueError("timestamp column must be strictly increasing")
        result[self.target_column] = pd.to_numeric(result[self.target_column], errors="raise")
        if result[self.target_column].isna().any() or not np.isfinite(result[self.target_column]).all():
            raise ValueError("target contains missing or non-finite values")
        return result

    def build_features(self, frame: pd.DataFrame) -> pd.DataFrame:
        data = self._validated(frame)
        target = data[self.target_column]
        timestamp = data["timestamp"]
        shifted = target.shift(1)
        features = pd.DataFrame(index=data.index)
        features["lag_1"] = shifted
        features["lag_seasonal"] = target.shift(self.seasonal_lag)
        features["rolling_mean_4"] = shifted.rolling(4, min_periods=4).mean()
        features["rolling_mean_16"] = shifted.rolling(16, min_periods=16).mean()
        minute_of_day = timestamp.dt.hour * 60 + timestamp.dt.minute
        phase = 2.0 * np.pi * minute_of_day / (24.0 * 60.0)
        features["time_sin"] = np.sin(phase)
        features["time_cos"] = np.cos(phase)
        features["weekday"] = timestamp.dt.dayofweek.astype(float)
        return features

    @staticmethod
    def _scores(actual: pd.Series, predicted: pd.Series | np.ndarray) -> tuple[float, float]:
        mae = float(mean_absolute_error(actual, predicted))
        rmse = float(mean_squared_error(actual, predicted) ** 0.5)
        return mae, rmse

    def evaluate(self, frame: pd.DataFrame, *, test_fraction: float = 0.2) -> EnergyEvaluation:
        if not 0.1 <= test_fraction <= 0.5:
            raise ValueError("test_fraction must be between 0.1 and 0.5")
        data = self._validated(frame)
        features = self.build_features(data)
        usable = features.notna().all(axis=1)
        data = data.loc[usable].copy()
        features = features.loc[usable].copy()
        if len(data) < 50:
            raise ValueError("insufficient usable observations for chronological evaluation")
        split = int(len(data) * (1.0 - test_fraction))
        if split < 20 or len(data) - split < 10:
            raise ValueError("insufficient train/test observations")
        x_train, x_test = features.iloc[:split], features.iloc[split:]
        y_train = data[self.target_column].iloc[:split]
        y_test = data[self.target_column].iloc[split:]
        persistence = x_test["lag_1"]
        seasonal = x_test["lag_seasonal"]
        persistence_mae, persistence_rmse = self._scores(y_test, persistence)
        seasonal_mae, seasonal_rmse = self._scores(y_test, seasonal)

        ridge = Pipeline(
            [
                ("scale", StandardScaler()),
                ("model", Ridge(alpha=self.ridge_alpha)),
            ]
        )
        ridge.fit(x_train, y_train)
        ridge_prediction = ridge.predict(x_test)
        ridge_mae, ridge_rmse = self._scores(y_test, ridge_prediction)

        boosting = HistGradientBoostingRegressor(
            learning_rate=0.05,
            max_depth=4,
            max_iter=200,
            random_state=0,
        )
        boosting.fit(x_train, y_train)
        boosting_prediction = boosting.predict(x_test)
        boosting_mae, boosting_rmse = self._scores(y_test, boosting_prediction)

        fingerprint = fingerprint_frame(frame)
        evaluation_start = data["timestamp"].iloc[split].to_pydatetime()
        evaluation_end = data["timestamp"].iloc[-1].to_pydatetime()

        def metric(model_id: str, mae: float, rmse: float) -> ModelMetric:
            return ModelMetric(
                model_id=model_id,
                mae=mae,
                rmse=rmse,
                evaluation_start=evaluation_start,
                evaluation_end=evaluation_end,
                dataset_fingerprint=fingerprint,
                baseline_model_id="persistence",
                baseline_mae=persistence_mae,
            )

        return EnergyEvaluation(
            metrics=(
                metric("persistence", persistence_mae, persistence_rmse),
                metric("seasonal_naive", seasonal_mae, seasonal_rmse),
                metric("ridge", ridge_mae, ridge_rmse),
                metric("hist_gradient_boosting", boosting_mae, boosting_rmse),
            ),
            train_end=data["timestamp"].iloc[split - 1],
            test_start=data["timestamp"].iloc[split],
            test_end=data["timestamp"].iloc[-1],
        )

    @staticmethod
    def select_candidate(evaluation: EnergyEvaluation) -> ModelMetric:
        """Select the genuinely best holdout model, preferring simpler models on exact ties."""
        priority = {
            "persistence": 0,
            "seasonal_naive": 1,
            "ridge": 2,
            "hist_gradient_boosting": 3,
        }
        if not evaluation.metrics:
            raise ValueError("evaluation contains no model metrics")
        return min(
            evaluation.metrics,
            key=lambda metric: (metric.mae, metric.rmse, priority.get(metric.model_id, 99), metric.model_id),
        )

    def forecast_next(self, frame: pd.DataFrame, *, model_id: str) -> EnergyPointForecast:
        """Train the requested evaluated model on all available history and forecast one interval.

        This method does not create uncertainty bounds because no calibrated interval method is
        implemented. The next timestamp is derived only when the source cadence is regular.
        """
        data = self._validated(frame)
        if len(data) <= self.seasonal_lag + 16:
            raise ValueError("insufficient observations for next-step forecast")
        deltas = data["timestamp"].diff().dropna()
        if deltas.empty or deltas.nunique() != 1:
            raise ValueError("next-step forecast requires a regular timestamp cadence")
        interval = deltas.iloc[0]
        if interval <= pd.Timedelta(0):
            raise ValueError("timestamp cadence must be positive")
        next_timestamp = data["timestamp"].iloc[-1] + interval
        target = data[self.target_column]
        seasonal_position = len(data) - self.seasonal_lag
        if seasonal_position < 0:
            raise ValueError("insufficient seasonal history")
        minute_of_day = next_timestamp.hour * 60 + next_timestamp.minute
        phase = 2.0 * np.pi * minute_of_day / (24.0 * 60.0)
        next_features = pd.DataFrame(
            [{
                "lag_1": float(target.iloc[-1]),
                "lag_seasonal": float(target.iloc[seasonal_position]),
                "rolling_mean_4": float(target.iloc[-4:].mean()),
                "rolling_mean_16": float(target.iloc[-16:].mean()),
                "time_sin": float(np.sin(phase)),
                "time_cos": float(np.cos(phase)),
                "weekday": float(next_timestamp.dayofweek),
            }]
        )

        if model_id == "persistence":
            value = float(next_features["lag_1"].iloc[0])
        elif model_id == "seasonal_naive":
            value = float(next_features["lag_seasonal"].iloc[0])
        else:
            features = self.build_features(data)
            usable = features.notna().all(axis=1)
            x_train = features.loc[usable]
            y_train = data.loc[usable, self.target_column]
            if len(x_train) < 20:
                raise ValueError("insufficient usable observations to train forecast model")
            if model_id == "ridge":
                model = Pipeline(
                    [("scale", StandardScaler()), ("model", Ridge(alpha=self.ridge_alpha))]
                )
            elif model_id == "hist_gradient_boosting":
                model = HistGradientBoostingRegressor(
                    learning_rate=0.05, max_depth=4, max_iter=200, random_state=0
                )
            else:
                raise ValueError(f"unsupported model_id: {model_id}")
            model.fit(x_train, y_train)
            value = float(model.predict(next_features)[0])

        return EnergyPointForecast(
            model_id=model_id,
            value=value,
            issued_at=data["timestamp"].iloc[-1].to_pydatetime(),
            valid_at=next_timestamp.to_pydatetime(),
            dataset_fingerprint=fingerprint_frame(frame),
        )
