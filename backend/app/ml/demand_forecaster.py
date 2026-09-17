"""Demand Forecasting Engine for Campus Resource Streams.

Implements short-term predictive modeling for electricity (hourly), water (hourly),
and waste (daily) using autoregressive feature engineering and Scikit-learn regressors.
Evaluates forecasting performance using strict chronological train/test splitting.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error

from app.ml.features import (
    extract_features,
    get_forecast_feature_columns,
)


RESOURCE_UNITS: Dict[str, str] = {
    "electricity": "kWh",
    "water": "L",
    "waste": "kg",
}


class DemandForecaster:
    """Predicts future resource demand using autoregressive features and chronological evaluation."""

    def __init__(self, resource_type: str, random_state: int = 42):
        self.resource_type = resource_type.lower().strip()
        self.unit = RESOURCE_UNITS.get(self.resource_type, "")
        self.random_state = random_state
        self.feature_columns = get_forecast_feature_columns(self.resource_type)
        self.model: Optional[RandomForestRegressor] = None
        self.is_fitted = False
        self.evaluation_metrics: Dict[str, float] = {"mae": 0.0, "rmse": 0.0}

    @property
    def frequency(self) -> str:
        """Returns the native sampling frequency of the resource."""
        return "daily" if self.resource_type == "waste" else "hourly"

    def _aggregate_series(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggregates campus-wide telemetry by timestamp to produce a single demand curve."""
        if df.empty:
            return pd.DataFrame(columns=["timestamp", "value"])

        res = df.copy()
        if not pd.api.types.is_datetime64_any_dtype(res["timestamp"]):
            res["timestamp"] = pd.to_datetime(res["timestamp"])

        agg = res.groupby("timestamp", as_index=False)["value"].sum()
        agg = agg.sort_values(by="timestamp").reset_index(drop=True)
        return agg

    def fit(self, df: pd.DataFrame) -> "DemandForecaster":
        """Fits the forecasting regressor and evaluates on a chronological 80/20 test split.

        Args:
            df: Raw DataFrame containing at least 'timestamp' and 'value'.

        Returns:
            self
        """
        agg_df = self._aggregate_series(df)
        if agg_df.empty or len(agg_df) < 10:
            return self

        features_df = extract_features(
            agg_df,
            resource_type=self.resource_type,
            for_forecasting=True,
        )

        cols = self.feature_columns
        X = features_df[cols].fillna(0.0).values
        y = features_df["value"].values

        # Chronological train/test split: first 80% train, last 20% test
        split_idx = max(int(len(features_df) * 0.8), 2)
        X_train, y_train = X[:split_idx], y[:split_idx]
        X_test, y_test = X[split_idx:], y[split_idx:]

        # Train regressor on historical training partition
        eval_model = RandomForestRegressor(
            n_estimators=60,
            max_depth=10,
            random_state=self.random_state,
        )
        eval_model.fit(X_train, y_train)

        # Compute test set error
        if len(y_test) > 0:
            y_pred = eval_model.predict(X_test)
            mae = float(mean_absolute_error(y_test, y_pred))
            rmse = float(root_mean_squared_error(y_test, y_pred))
            self.evaluation_metrics = {
                "mae": round(mae, 2),
                "rmse": round(rmse, 2),
            }

        # Train full production model on 100% of historical data for future forecasting
        self.model = RandomForestRegressor(
            n_estimators=60,
            max_depth=10,
            random_state=self.random_state,
        )
        self.model.fit(X, y)
        self.is_fitted = True
        return self

    def evaluate(self, df: Optional[pd.DataFrame] = None) -> Dict[str, float]:
        """Returns the out-of-sample chronological evaluation metrics."""
        if not self.is_fitted and df is not None and not df.empty:
            self.fit(df)
        return self.evaluation_metrics

    def forecast(self, df: pd.DataFrame, horizon: int = 24) -> List[Dict[str, Any]]:
        """Generates future demand forecasts for the specified number of periods.

        Args:
            df: Historical readings DataFrame to anchor future predictions.
            horizon: Number of time steps to project forward (default 24).

        Returns:
            List of forecast dicts with timestamp, predicted_value, resource, and unit.
        """
        if not self.is_fitted:
            self.fit(df)

        if not self.is_fitted:
            return []

        agg_df = self._aggregate_series(df)
        if agg_df.empty:
            return []

        is_daily = self.resource_type == "waste"
        step_delta = timedelta(days=1) if is_daily else timedelta(hours=1)
        long_lag = 7 if is_daily else 24
        window_size = 7 if is_daily else 24

        last_ts = agg_df["timestamp"].max()
        if pd.isna(last_ts):
            return []

        # Maintain buffer of recent known historical values for autoregressive stepping
        buffer_vals = list(agg_df["value"].values[-max(long_lag * 2, 48):])
        predictions = []

        for step in range(1, horizon + 1):
            next_ts = last_ts + (step * step_delta)
            hour = next_ts.hour
            day_of_week = next_ts.weekday()
            is_weekend = int(day_of_week >= 5)

            lag_1 = buffer_vals[-1] if len(buffer_vals) >= 1 else 0.0
            lag_2 = buffer_vals[-2] if len(buffer_vals) >= 2 else lag_1
            lag_long = buffer_vals[-long_lag] if len(buffer_vals) >= long_lag else buffer_vals[0]

            window_slice = buffer_vals[-window_size:] if len(buffer_vals) >= window_size else buffer_vals
            rolling_mean = float(np.mean(window_slice)) if window_slice else lag_1

            feature_vec = np.array([[hour, day_of_week, is_weekend, lag_1, lag_2, lag_long, rolling_mean]])
            pred_val = float(self.model.predict(feature_vec)[0])
            pred_val = max(0.0, pred_val)

            # Append to buffer for subsequent autoregressive predictions
            buffer_vals.append(pred_val)

            predictions.append({
                "timestamp": next_ts.isoformat(),
                "predicted_value": round(pred_val, 2),
                "resource": self.resource_type,
                "unit": self.unit,
            })

        return predictions
