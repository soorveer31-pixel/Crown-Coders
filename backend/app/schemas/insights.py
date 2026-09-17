"""Pydantic validation schemas for Autopilot Insights and Recommendations."""

from typing import List, Optional
from pydantic import BaseModel, Field


class InsightItem(BaseModel):
    """Represents a single actionable insight (detected anomaly or forecast risk)."""
    id: Optional[str] = None
    resource: str
    building: str
    timestamp: str
    type: str = Field(..., description="'anomaly' for detected issues, 'forecast_risk' for upcoming projected risks")
    severity: str = Field(..., description="'LOW', 'MEDIUM', 'HIGH', or 'CRITICAL'")
    priority_score: float = Field(..., ge=0.0, le=1.0, description="Deterministic priority score between 0.0 and 1.0")
    title: str
    explanation: str
    observed_value: float
    expected_value: float
    deviation_percent: float
    recommendation: str
    recommended_action: str
    unit: Optional[str] = ""


class InsightsResponse(BaseModel):
    """Response payload for GET /api/insights."""
    resource: Optional[str] = "all"
    range: str
    total_insights: int
    detected_issues_count: int
    upcoming_risks_count: int
    insights: List[InsightItem]
