"""Resource Predictor and Anomaly Detector Orchestrator.

Integrates feature engineering, Isolation Forest anomaly detection,
and autoregressive demand forecasting across electricity, water, and waste streams.
"""

from typing import Dict, Any, List, Optional
import pandas as pd

from app.ml.anomaly_detector import AnomalyDetector
from app.ml.demand_forecaster import DemandForecaster, RESOURCE_UNITS


class ResourcePredictor:
    """Predictive modeling engine coordinating anomaly detection and forecasting."""

    SUPPORTED_RESOURCES = ["electricity", "water", "waste"]

    def __init__(self):
        self.anomaly_detectors: Dict[str, AnomalyDetector] = {
            res: AnomalyDetector(resource_type=res) for res in self.SUPPORTED_RESOURCES
        }
        self.demand_forecasters: Dict[str, DemandForecaster] = {
            res: DemandForecaster(resource_type=res) for res in self.SUPPORTED_RESOURCES
        }
        self.is_trained: Dict[str, bool] = {res: False for res in self.SUPPORTED_RESOURCES}

    def train_if_needed(self, resource_type: str, df: pd.DataFrame, group_col: Optional[str] = "meter_id"):
        """Ensures both the anomaly detector and forecaster are fitted on historical telemetry."""
        res_key = resource_type.lower().strip()
        if res_key not in self.SUPPORTED_RESOURCES:
            raise ValueError(f"Unsupported resource: {resource_type}")

        if not self.is_trained[res_key] and not df.empty:
            self.anomaly_detectors[res_key].fit(df, group_col=group_col)
            self.demand_forecasters[res_key].fit(df)
            self.is_trained[res_key] = True

    def predict_demand(self, resource_type: str, df: pd.DataFrame, horizon: int = 24) -> List[Dict[str, Any]]:
        """Generates future demand forecasts for the specified horizon periods.

        Args:
            resource_type: 'electricity', 'water', or 'waste'.
            df: Historical telemetry data.
            horizon: Number of periods to predict forward (default 24).

        Returns:
            List of forecast point dictionaries.
        """
        res_key = resource_type.lower().strip()
        if res_key not in self.SUPPORTED_RESOURCES:
            raise ValueError(f"Unsupported resource: {resource_type}")

        self.train_if_needed(res_key, df)
        forecaster = self.demand_forecasters[res_key]
        return forecaster.forecast(df, horizon=horizon)

    def detect_anomalies(
        self,
        resource_type: str,
        df: pd.DataFrame,
        group_col: Optional[str] = "meter_id",
    ) -> pd.DataFrame:
        """Detects anomalous readings in the telemetry DataFrame.

        Args:
            resource_type: 'electricity', 'water', or 'waste'.
            df: DataFrame of readings.
            group_col: Optional grouping column.

        Returns:
            Augmented DataFrame with 'predicted_anomaly' (bool) and 'anomaly_score' (float).
        """
        res_key = resource_type.lower().strip()
        if res_key not in self.SUPPORTED_RESOURCES:
            raise ValueError(f"Unsupported resource: {resource_type}")

        if df.empty:
            df_out = df.copy()
            df_out["predicted_anomaly"] = []
            df_out["anomaly_score"] = []
            return df_out

        self.train_if_needed(res_key, df, group_col=group_col)
        detector = self.anomaly_detectors[res_key]
        preds, scores = detector.predict(df, group_col=group_col)

        df_out = df.copy()
        df_out["predicted_anomaly"] = preds
        df_out["anomaly_score"] = scores
        return df_out

    def evaluate(
        self,
        resource_type: str,
        df: pd.DataFrame,
        ground_truth_col: str = "is_anomaly",
        group_col: Optional[str] = "meter_id",
    ) -> Dict[str, Any]:
        """Calculates evaluation metrics across demand forecasting and anomaly detection.

        Args:
            resource_type: 'electricity', 'water', or 'waste'.
            df: Historical readings with ground-truth anomaly labels.
            ground_truth_col: Ground truth anomaly boolean column.
            group_col: Meter or building grouping column.

        Returns:
            Dictionary containing forecast (MAE, RMSE) and anomaly_detection (Precision, Recall, F1, counts).
        """
        res_key = resource_type.lower().strip()
        if res_key not in self.SUPPORTED_RESOURCES:
            raise ValueError(f"Unsupported resource: {resource_type}")

        self.train_if_needed(res_key, df, group_col=group_col)
        forecast_metrics = self.demand_forecasters[res_key].evaluate(df)
        anomaly_metrics = self.anomaly_detectors[res_key].evaluate(
            df,
            ground_truth_col=ground_truth_col,
            group_col=group_col,
        )

        return {
            "resource": res_key,
            "unit": RESOURCE_UNITS.get(res_key, ""),
            "forecast": forecast_metrics,
            "anomaly_detection": anomaly_metrics,
        }
