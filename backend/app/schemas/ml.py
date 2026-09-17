"""Pydantic schemas for Machine Learning endpoints."""

from typing import List, Optional
from pydantic import BaseModel, Field


class AnomalyItem(BaseModel):
    """Represents an identified anomaly telemetry point."""
    timestamp: str
    value: float
    anomaly_score: float = Field(..., ge=0.0, le=1.0, description="Outlier score normalized between 0.0 and 1.0")
    predicted_anomaly: bool
    building_name: Optional[str] = None
    meter_id: Optional[int] = None


class AnomalyResponse(BaseModel):
    """Response payload for GET /api/ml/anomalies."""
    resource: str
    unit: str
    range: str
    total_anomalies: int
    anomalies: List[AnomalyItem]


class ForecastPoint(BaseModel):
    """Represents a discrete forecasted timestep."""
    timestamp: str
    predicted_value: float
    resource: str
    unit: str


class ForecastResponse(BaseModel):
    """Response payload for GET /api/ml/forecast."""
    resource: str
    unit: str
    horizon: int
    frequency: str
    predictions: List[ForecastPoint]


class ForecastMetrics(BaseModel):
    """Out-of-sample forecasting evaluation metrics."""
    mae: float
    rmse: float


class AnomalyMetrics(BaseModel):
    """Anomaly detection evaluation metrics against ground-truth labels."""
    precision: float
    recall: float
    f1: float
    actual_anomalies: int
    predicted_anomalies: int
    true_positives: int
    false_positives: int
    false_negatives: int


class EvaluationResponse(BaseModel):
    """Response payload for GET /api/ml/evaluation."""
    resource: str
    unit: str
    forecast: ForecastMetrics
    anomaly_detection: AnomalyMetrics
