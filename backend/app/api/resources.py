"""Resources API router.

Exposes endpoints for aggregated resource summaries and historical telemetry.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.resource_service import ResourceService

router = APIRouter(prefix="/resources", tags=["Resources"])


class ResourceMetricSummary(BaseModel):
    current: float
    average: float
    total: float
    unit: str


class ResourceSummaryResponse(BaseModel):
    electricity: ResourceMetricSummary
    water: ResourceMetricSummary
    waste: ResourceMetricSummary


class TelemetryDataPoint(BaseModel):
    timestamp: str
    value: float


class ResourceHistoryResponse(BaseModel):
    resource: str
    unit: str
    range: str
    data: List[TelemetryDataPoint]


@router.get("/summary", response_model=ResourceSummaryResponse)
def get_resource_summary(db: Session = Depends(get_db)):
    """Retrieves aggregated consumption metrics across electricity, water, and waste."""
    service = ResourceService(db)
    summary = service.get_resource_summary()
    return summary


@router.get("/history", response_model=ResourceHistoryResponse)
def get_resource_history(
    resource: str = Query(..., description="Resource category ('electricity', 'water', or 'waste')"),
    range: str = Query("7d", description="Historical range ('7d' or '30d')"),
    db: Session = Depends(get_db),
):
    """Retrieves chronological telemetry time-series points suitable for charts."""
    service = ResourceService(db)
    try:
        history = service.get_resource_history(resource=resource, range_str=range)
        return history
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )
