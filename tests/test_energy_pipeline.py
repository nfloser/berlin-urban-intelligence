import numpy as np
import pandas as pd

from berlin_urban_intelligence.energy.pipeline import EnergyForecastPipeline


def fixture_frame(periods: int = 320) -> pd.DataFrame:
    timestamps = pd.date_range("2026-01-01", periods=periods, freq="15min", tz="UTC")
    phase = np.arange(periods) * (2 * np.pi / 96)
    demand = 500.0 + 80.0 * np.sin(phase) + np.arange(periods) * 0.05
    return pd.DataFrame({"timestamp": timestamps, "grid_load_mw": demand})


def test_future_target_cannot_change_past_features() -> None:
    pipeline = EnergyForecastPipeline(target_column="grid_load_mw", seasonal_lag=96)
    original = fixture_frame()
    mutated = original.copy()
    mutated.loc[250:, "grid_load_mw"] = mutated.loc[250:, "grid_load_mw"] + 10_000
    before = pipeline.build_features(original).iloc[:250]
    after = pipeline.build_features(mutated).iloc[:250]
    pd.testing.assert_frame_equal(before, after)


def test_evaluation_is_chronological_and_metrics_are_calculated() -> None:
    pipeline = EnergyForecastPipeline(target_column="grid_load_mw", seasonal_lag=96)
    evaluation = pipeline.evaluate(fixture_frame())
    assert evaluation.train_end < evaluation.test_start <= evaluation.test_end
    assert {metric.model_id for metric in evaluation.metrics} == {
        "persistence",
        "seasonal_naive",
        "ridge",
        "hist_gradient_boosting",
    }
    assert all(metric.mae >= 0 and metric.rmse >= 0 for metric in evaluation.metrics)
    assert len({metric.dataset_fingerprint for metric in evaluation.metrics}) == 1


def test_selected_candidate_can_produce_one_step_forecast() -> None:
    frame = fixture_frame()
    pipeline = EnergyForecastPipeline(target_column="grid_load_mw", seasonal_lag=96)
    evaluation = pipeline.evaluate(frame)
    selected = pipeline.select_candidate(evaluation)
    forecast = pipeline.forecast_next(frame, model_id=selected.model_id)
    assert forecast.valid_at > forecast.issued_at
    assert forecast.dataset_fingerprint == selected.dataset_fingerprint
    assert np.isfinite(forecast.value)
