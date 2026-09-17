from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str
    database: str
    environment: str


@router.get("/health", response_model=HealthResponse)
def get_health_status(response: Response, db: Session = Depends(get_db)):
    """Health check endpoint performing an active SELECT 1 database connectivity ping."""
    db_status = "connected"
    overall_status = "healthy"

    try:
        # Perform live ping to verify SQLite / database connectivity
        db.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"disconnected: {str(exc)}"
        overall_status = "degraded"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(
        status=overall_status,
        service="campus-resource-autopilot-backend",
        version=settings.VERSION,
        timestamp=datetime.now(timezone.utc).isoformat(),
        database=db_status,
        environment=settings.ENVIRONMENT,
    )
