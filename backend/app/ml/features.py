"""Feature Engineering Module for Campus Resource Autopilot.

Constructs temporal, lag, and backward-looking rolling statistical features
for anomaly detection and demand prediction. Strictly guarantees ZERO data leakage
by ensuring rolling windows and lag terms only observe prior historical timestamps.
"""

from typing import List, Optional
import pandas as pd
import numpy as np


def add_temporal_features(df: pd.DataFrame, timestamp_col: str = "timestamp") -> pd.DataFrame:
    """Extracts calendar and diurnal temporal features from the timestamp column.

    Args:
        df: Input DataFrame containing the timestamp column.
        timestamp_col: Name of the column with timestamp values.

    Returns:
        DataFrame augmented with hour, day_of_week, and is_weekend columns.
    """
    res = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(res[timestamp_col]):
        res[timestamp_col] = pd.to_datetime(res[timestamp_col])

    res["hour"] = res[timestamp_col].dt.hour
    res["day_of_week"] = res[timestamp_col].dt.dayofweek
    res["is_weekend"] = res["day_of_week"].isin([5, 6]).astype(int)
    res["month"] = res[timestamp_col].dt.month
    return res


def add_lag_and_rolling_features(
    df: pd.DataFrame,
    resource_type: str,
    value_col: str = "value",
    timestamp_col: str = "timestamp",
    group_col: Optional[str] = None,
) -> pd.DataFrame:
    """Computes autoregressive lag and rolling window metrics strictly avoiding future leakage.

    All rolling aggregations use `shift(1)` so that the current timestep's observation
    is never included in its own historical baseline.

    Args:
        df: Input DataFrame with timestamp and consumption values.
        resource_type: 'electricity', 'water', or 'waste'.
        value_col: Name of consumption reading column.
        timestamp_col: Name of datetime column.
        group_col: Optional grouping column (e.g., 'meter_id' or 'building_id').

    Returns:
        DataFrame augmented with lag, rolling mean, rolling std, z_score, and deviation features.
    """
    res = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(res[timestamp_col]):
        res[timestamp_col] = pd.to_datetime(res[timestamp_col])

    # Assign an internal ordering index to restore original input order afterwards
    res["_orig_idx"] = np.arange(len(res))

    is_daily = resource_type.lower() == "waste"
    window_size = 7 if is_daily else 24
    long_lag = 7 if is_daily else 24

    def _compute_for_series(sub_df: pd.DataFrame) -> pd.DataFrame:
        sub_df = sub_df.sort_values(by=timestamp_col).copy()
        val = sub_df[value_col]
        # Past-only series (shifted by 1) to prevent current or future observation leakage
        past_val = val.shift(1)

        # 1. Lag Features
        lag_1 = past_val.bfill().fillna(val)
        lag_2 = val.shift(2).bfill().fillna(lag_1)
        lag_long = val.shift(long_lag).bfill().fillna(lag_1)

        # 2. Backward-looking Rolling Metrics (past only)
        rolling_mean = past_val.rolling(window=window_size, min_periods=1).mean()
        rolling_mean = rolling_mean.bfill().fillna(val)

        rolling_std = past_val.rolling(window=window_size, min_periods=1).std()
        rolling_std = rolling_std.fillna(0.0)

        # 3. Deviation & Normalized metrics
        deviation = val - rolling_mean
        z_score = np.where(rolling_std > 1e-4, deviation / (rolling_std + 1e-4), 0.0)

        sub_df["lag_1"] = lag_1
        sub_df["lag_2"] = lag_2
        sub_df[f"lag_{long_lag}"] = lag_long
        sub_df["rolling_mean"] = rolling_mean
        sub_df["rolling_std"] = rolling_std
        sub_df["deviation_from_rolling_mean"] = deviation
        sub_df["z_score"] = z_score
        return sub_df

    if group_col and group_col in res.columns:
        sub_dfs = []
        for _, group in res.groupby(group_col, sort=False):
            sub_dfs.append(_compute_for_series(group))
        res = pd.concat(sub_dfs, ignore_index=True)
    else:
        res = _compute_for_series(res)

    # Restore the exact row alignment of the input dataframe
    res = res.sort_values(by="_orig_idx").drop(columns=["_orig_idx"]).reset_index(drop=True)
    return res


def extract_features(
    df: pd.DataFrame,
    resource_type: str,
    for_forecasting: bool = False,
    value_col: str = "value",
    timestamp_col: str = "timestamp",
    group_col: Optional[str] = None,
) -> pd.DataFrame:
    """End-to-end feature extraction pipeline for time-series telemetry.

    Args:
        df: Input DataFrame with readings.
        resource_type: 'electricity', 'water', or 'waste'.
        for_forecasting: If True, returns features suitable for autoregressive forecasting.
        value_col: Column with numeric consumption.
        timestamp_col: Column with datetimes.
        group_col: Optional entity ID column.

    Returns:
        Augmented DataFrame with all engineered feature columns preserving input row order.
    """
    if df.empty:
        return df.copy()

    df_temporal = add_temporal_features(df, timestamp_col=timestamp_col)
    df_features = add_lag_and_rolling_features(
        df_temporal,
        resource_type=resource_type,
        value_col=value_col,
        timestamp_col=timestamp_col,
        group_col=group_col,
    )
    return df_features


def get_anomaly_feature_columns(resource_type: str) -> List[str]:
    """Returns the standardized feature column names used for anomaly detection."""
    return [
        "value",
        "hour",
        "day_of_week",
        "is_weekend",
        "lag_1",
        "rolling_mean",
        "rolling_std",
        "deviation_from_rolling_mean",
        "z_score",
    ]


def get_forecast_feature_columns(resource_type: str) -> List[str]:
    """Returns the standardized feature column names used for forecasting (no current value)."""
    long_lag = 7 if resource_type.lower() == "waste" else 24
    return [
        "hour",
        "day_of_week",
        "is_weekend",
        "lag_1",
        "lag_2",
        f"lag_{long_lag}",
        "rolling_mean",
    ]
