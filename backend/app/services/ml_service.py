"""Machine Learning Service Layer for Campus Resource Autopilot.

Manages data loading from SQLite, feature orchestration, model caching,
anomaly identification, demand forecasting, and evaluation pipelines.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.campus import Building, ResourceMeter, ConsumptionReading, AnomalyPrediction
from app.ml.predictor import ResourcePredictor, RESOURCE_UNITS

# Module-level cached predictor instance to prevent retraining on every HTTP request
_global_predictor = ResourcePredictor()


class MLService:
    """Service class executing ML intelligence pipelines backed by SQLAlchemy data."""

    SUPPORTED_RESOURCES = ["electricity", "water", "waste"]
    SUPPORTED_RANGES = ["7d", "30d"]

    def __init__(self, db: Session):
        self.db = db
        self.predictor = _global_predictor

    def _load_telemetry_df(self, resource: str) -> pd.DataFrame:
        """Loads all historical telemetry records for a resource including meter and building metadata."""
        query = (
            self.db.query(
                ConsumptionReading.id,
                ConsumptionReading.meter_id,
                ConsumptionReading.timestamp,
                ConsumptionReading.value,
                ConsumptionReading.is_anomaly,
                Building.name.label("building_name"),
            )
            .join(ResourceMeter, ConsumptionReading.meter_id == ResourceMeter.id)
            .join(Building, ResourceMeter.building_id == Building.id)
            .filter(ResourceMeter.resource_type == resource)
            .order_by(ConsumptionReading.timestamp.asc())
        )

        rows = query.all()
        if not rows:
            return pd.DataFrame(
                columns=["id", "meter_id", "timestamp", "value", "is_anomaly", "building_name"]
            )

        data = [
            {
                "id": r.id,
                "meter_id": r.meter_id,
                "timestamp": r.timestamp,
                "value": float(r.value),
                "is_anomaly": bool(r.is_anomaly),
                "building_name": r.building_name,
            }
            for r in rows
        ]
        return pd.DataFrame(data)

    def get_anomalies(self, resource: str, range_str: str = "7d") -> Dict[str, Any]:
        """Detects anomalies and returns those within the requested time window.

        Args:
            resource: 'electricity', 'water', or 'waste'.
            range_str: '7d' or '30d'.

        Returns:
            Dictionary matching AnomalyResponse schema.
        """
        res_key = resource.lower().strip()
        if res_key not in self.SUPPORTED_RESOURCES:
            raise ValueError(f"Invalid resource '{resource}'. Supported: {', '.join(self.SUPPORTED_RESOURCES)}")

        range_key = range_str.lower().strip()
        if range_key not in self.SUPPORTED_RANGES:
            raise ValueError(f"Invalid range '{range_str}'. Supported: {', '.join(self.SUPPORTED_RANGES)}")

        df = self._load_telemetry_df(res_key)
        unit = RESOURCE_UNITS.get(res_key, "")

        if df.empty:
            return {
                "resource": res_key,
                "unit": unit,
                "range": range_key,
                "total_anomalies": 0,
                "anomalies": [],
            }

        # Run Isolation Forest prediction
        pred_df = self.predictor.detect_anomalies(res_key, df, group_col="meter_id")

        # Filter by requested time window
        days = 7 if range_key == "7d" else 30
        max_ts = pred_df["timestamp"].max()
        cutoff = max_ts - timedelta(days=days)
        window_df = pred_df[pred_df["timestamp"] >= cutoff]

        # Extract only predicted anomalies
        anomalies_df = window_df[window_df["predicted_anomaly"] == True].sort_values(
            by=["anomaly_score", "timestamp"], ascending=[False, False]
        )

        anomalies_list = []
        for _, row in anomalies_df.iterrows():
            anomalies_list.append({
                "timestamp": row["timestamp"].isoformat() if hasattr(row["timestamp"], "isoformat") else str(row["timestamp"]),
                "value": round(float(row["value"]), 2),
                "anomaly_score": round(float(row["anomaly_score"]), 4),
                "predicted_anomaly": bool(row["predicted_anomaly"]),
                "building_name": str(row["building_name"]),
                "meter_id": int(row["meter_id"]),
            })

        return {
            "resource": res_key,
            "unit": unit,
            "range": range_key,
            "total_anomalies": len(anomalies_list),
            "anomalies": anomalies_list,
        }

    def get_forecast(self, resource: str, horizon: int = 24) -> Dict[str, Any]:
        """Generates future demand forecasts for the requested horizon periods.

        Args:
            resource: 'electricity', 'water', or 'waste'.
            horizon: Positive integer forecasting steps (1 to 168).

        Returns:
            Dictionary matching ForecastResponse schema.
        """
        res_key = resource.lower().strip()
        if res_key not in self.SUPPORTED_RESOURCES:
            raise ValueError(f"Invalid resource '{resource}'. Supported: {', '.join(self.SUPPORTED_RESOURCES)}")

        if not isinstance(horizon, int) or horizon <= 0 or horizon > 168:
            raise ValueError(f"Horizon must be an integer between 1 and 168. Received: {horizon}")

        df = self._load_telemetry_df(res_key)
        unit = RESOURCE_UNITS.get(res_key, "")
        frequency = "daily" if res_key == "waste" else "hourly"

        if df.empty:
            return {
                "resource": res_key,
                "unit": unit,
                "horizon": horizon,
                "frequency": frequency,
                "predictions": [],
            }

        predictions = self.predictor.predict_demand(res_key, df, horizon=horizon)

        return {
            "resource": res_key,
            "unit": unit,
            "horizon": horizon,
            "frequency": frequency,
            "predictions": predictions,
        }

    def get_evaluation(self, resource: str) -> Dict[str, Any]:
        """Returns rigorous evaluation metrics for both forecasting and anomaly detection.

        Args:
            resource: 'electricity', 'water', or 'waste'.

        Returns:
            Dictionary matching EvaluationResponse schema.
        """
        res_key = resource.lower().strip()
        if res_key not in self.SUPPORTED_RESOURCES:
            raise ValueError(f"Invalid resource '{resource}'. Supported: {', '.join(self.SUPPORTED_RESOURCES)}")

        df = self._load_telemetry_df(res_key)
        unit = RESOURCE_UNITS.get(res_key, "")

        if df.empty:
            return {
                "resource": res_key,
                "unit": unit,
                "forecast": {"mae": 0.0, "rmse": 0.0},
                "anomaly_detection": {
                    "precision": 0.0,
                    "recall": 0.0,
                    "f1": 0.0,
                    "actual_anomalies": 0,
                    "predicted_anomalies": 0,
                    "true_positives": 0,
                    "false_positives": 0,
                    "false_negatives": 0,
                },
            }

        return self.predictor.evaluate(res_key, df, group_col="meter_id")
