"""Isolation Forest Anomaly Detection Engine for Campus Telemetry.

Identifies multivariate consumption anomalies (sudden spikes, persistent off-hour leaks,
and unusual surges) without using or overwriting ground-truth simulation labels.
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from app.ml.features import (
    extract_features,
    get_anomaly_feature_columns,
)


class AnomalyDetector:
    """Isolation Forest anomaly detection wrapper tailored for campus resource time series."""

    def __init__(
        self,
        resource_type: str,
        contamination: float = 0.02,
        random_state: int = 42,
    ):
        self.resource_type = resource_type
        self.contamination = contamination
        self.random_state = random_state
        self.model: Optional[IsolationForest] = None
        self.feature_columns = get_anomaly_feature_columns(resource_type)
        self.is_fitted = False
        self._score_min: float = -0.5
        self._score_max: float = 0.5

    def fit(self, df: pd.DataFrame, group_col: Optional[str] = None) -> "AnomalyDetector":
        """Fits the Isolation Forest on engineered features extracted from historical readings.

        Args:
            df: Raw DataFrame containing at minimum 'timestamp' and 'value'.
            group_col: Optional column name for entity grouping (e.g. 'meter_id').

        Returns:
            self
        """
        if df.empty or len(df) < 5:
            return self

        effective_group = group_col if (group_col and group_col in df.columns) else None
        features_df = extract_features(
            df,
            resource_type=self.resource_type,
            for_forecasting=False,
            group_col=effective_group,
        )
        X = features_df[self.feature_columns].fillna(0.0).values

        # Set contamination safely bounded
        contam = min(max(self.contamination, 0.005), 0.15)

        self.model = IsolationForest(
            contamination=contam,
            random_state=self.random_state,
            n_estimators=100,
        )
        self.model.fit(X)
        self.is_fitted = True

        raw_scores = self.model.decision_function(X)
        self._score_min = float(raw_scores.min())
        self._score_max = float(raw_scores.max())
        return self

    def predict(self, df: pd.DataFrame, group_col: Optional[str] = None) -> Tuple[np.ndarray, np.ndarray]:
        """Predicts anomaly status and normalized scores for the given records.

        Args:
            df: Input DataFrame with readings.
            group_col: Optional column name for entity grouping.

        Returns:
            Tuple of (predicted_anomaly_bool_array, normalized_anomaly_score_float_array).
        """
        if not self.is_fitted or df.empty:
            zeros = np.zeros(len(df), dtype=float)
            bools = np.zeros(len(df), dtype=bool)
            return bools, zeros

        effective_group = group_col if (group_col and group_col in df.columns) else None
        features_df = extract_features(
            df,
            resource_type=self.resource_type,
            for_forecasting=False,
            group_col=effective_group,
        )
        X = features_df[self.feature_columns].fillna(0.0).values

        raw_preds = self.model.predict(X)  # -1 for anomaly, 1 for inlier
        predicted_anomaly = (raw_preds == -1)

        raw_scores = self.model.decision_function(X)
        denom = (self._score_max - self._score_min) if (self._score_max > self._score_min) else 1.0
        normalized_scores = (self._score_max - raw_scores) / denom
        normalized_scores = np.clip(normalized_scores, 0.0, 1.0)

        return predicted_anomaly, np.round(normalized_scores, 4)

    def evaluate(
        self,
        df: pd.DataFrame,
        ground_truth_col: str = "is_anomaly",
        group_col: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Evaluates detection performance against ground-truth labels.

        Args:
            df: DataFrame containing readings and the boolean ground_truth_col.
            ground_truth_col: Name of the ground-truth anomaly label column.
            group_col: Optional grouping column.

        Returns:
            Dictionary containing Precision, Recall, F1, and confusion counts.
        """
        if df.empty or ground_truth_col not in df.columns:
            return {
                "precision": 0.0,
                "recall": 0.0,
                "f1": 0.0,
                "actual_anomalies": 0,
                "predicted_anomalies": 0,
                "true_positives": 0,
                "false_positives": 0,
                "false_negatives": 0,
            }

        preds, _ = self.predict(df, group_col=group_col)
        actuals = df[ground_truth_col].astype(bool).values

        tp = int(np.sum(preds & actuals))
        fp = int(np.sum(preds & ~actuals))
        fn = int(np.sum(~preds & actuals))
        tn = int(np.sum(~preds & ~actuals))

        actual_count = int(np.sum(actuals))
        pred_count = int(np.sum(preds))

        precision = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 0.0
        recall = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0.0
        f1 = round(2 * (precision * recall) / (precision + recall), 4) if (precision + recall) > 0 else 0.0

        return {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "actual_anomalies": actual_count,
            "predicted_anomalies": pred_count,
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
        }
