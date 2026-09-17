"""Pydantic validation schemas for Impact & Savings Measurement (Milestone 4B)."""

from typing import Optional, List
from pydantic import BaseModel, Field


class InterventionCreate(BaseModel):
    """Payload to create a new facility intervention from an insight."""
    insight_id: int = Field(..., description="ID of the source Insight")
    action: Optional[str] = Field(None, description="Custom action description, or defaults to insight recommendation")
    measurement_type: Optional[str] = Field("SIMULATED", description="'SIMULATED' (demo default) or 'MEASURED'")


class InterventionSimulate(BaseModel):
    """Payload to trigger a simulated demo completion."""
    simulated_reduction_factor: Optional[float] = Field(
        0.85,
        ge=0.0,
        le=1.0,
        description="Portion of excess anomaly consumption successfully mitigated (default 85%)",
    )


class InterventionResponse(BaseModel):
    """Detailed response for a facility intervention."""
    id: int
    insight_id: int
    resource_type: str
    building_id: Optional[int] = None
    building_name: Optional[str] = None
    action: str
    status: str = Field(..., description="'PLANNED', 'IN_PROGRESS', or 'COMPLETED'")
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    baseline_value: Optional[float] = None
    before_value: Optional[float] = None
    after_value: Optional[float] = None
    estimated_savings: Optional[float] = None
    savings_percentage: Optional[float] = None
    excess_before: Optional[float] = None
    excess_after: Optional[float] = None
    excess_reduction: Optional[float] = None
    measurement_type: str = Field(..., description="'SIMULATED' or 'MEASURED'")
    created_at: str
    unit: str
    impact_status_message: Optional[str] = None


class ResourceImpactSummary(BaseModel):
    """Aggregate metrics for a specific resource pillar."""
    total_estimated_savings: float
    unit: str
    average_improvement_percent: float
    total_interventions: int
    completed_interventions: int


class ImpactSummaryResponse(BaseModel):
    """Overall campus impact summary payload for GET /api/impact/summary."""
    water: ResourceImpactSummary
    electricity: ResourceImpactSummary
    waste: ResourceImpactSummary
    overall_measurement_type: str = Field(
        ...,
        description="'SIMULATED', 'MEASURED', or 'MIXED'"
    )
    total_completed_interventions: int
    disclaimer: str = Field(
        default="SIMULATED DEMO IMPACT: Results generated from documented simulation models because the prototype environment does not have real-time physical actuators.",
        description="Mandatory clear labeling separating demonstration from physical readings"
    )
