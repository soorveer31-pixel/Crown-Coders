"""API Router for Autopilot Insights and Actionable Recommendations."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.insights_service import InsightsService
from app.schemas.insights import InsightsResponse

router = APIRouter(prefix="/insights", tags=["Insights & Recommendations"])


@router.get(
    "",
    response_model=InsightsResponse,
    summary="Get explainable insights and actionable facility recommendations",
    description="Analyzes ML anomaly detections and forecasted demand spikes to generate deterministic explanations, priority scores, and facility directives.",
)
def get_insights(
    resource: Optional[str] = Query(None, description="Filter by resource: electricity, water, or waste"),
    range: str = Query("7d", description="Time window filter: 7d or 30d"),
    db: Session = Depends(get_db),
):
    service = InsightsService(db)
    try:
        return service.get_insights(resource=resource, range_str=range)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal error generating insights.")
