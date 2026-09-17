"""Machine Learning API Router for Campus Resource Autopilot.

Exposes REST endpoints for anomaly detection, demand forecasting,
and model performance evaluation.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.ml_service import MLService
from app.schemas.ml import AnomalyResponse, ForecastResponse, EvaluationResponse

router = APIRouter(prefix="/ml", tags=["Machine Learning"])


@router.get(
    "/anomalies",
    response_model=AnomalyResponse,
    summary="Detect resource consumption anomalies",
    description="Runs Isolation Forest anomaly detection to identify statistical outliers and continuous leaks.",
)
def get_anomalies(
    resource: str = Query("electricity", description="Resource type: electricity, water, or waste"),
    range: str = Query("7d", description="Time window: 7d or 30d"),
    db: Session = Depends(get_db),
):
    service = MLService(db)
    try:
        return service.get_anomalies(resource=resource, range_str=range)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal error during anomaly detection.")


@router.get(
    "/forecast",
    response_model=ForecastResponse,
    summary="Predict short-term resource demand",
    description="Generates future consumption predictions for the next N periods (hourly for electricity/water, daily for waste).",
)
def get_forecast(
    resource: str = Query("electricity", description="Resource type: electricity, water, or waste"),
    horizon: int = Query(24, ge=1, le=168, description="Prediction horizon periods (1 to 168)"),
    db: Session = Depends(get_db),
):
    service = MLService(db)
    try:
        return service.get_forecast(resource=resource, horizon=horizon)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal error during demand forecasting.")


@router.get(
    "/evaluation",
    response_model=EvaluationResponse,
    summary="Get ML model evaluation metrics",
    description="Returns out-of-sample chronological evaluation metrics (MAE, RMSE, Precision, Recall, F1).",
)
def get_evaluation(
    resource: str = Query("electricity", description="Resource type: electricity, water, or waste"),
    db: Session = Depends(get_db),
):
    service = MLService(db)
    try:
        return service.get_evaluation(resource=resource)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal error during model evaluation.")
