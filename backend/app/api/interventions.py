"""API Router for Facility Interventions and Impact Measurement (Milestone 4B)."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.impact_service import ImpactService
from app.schemas.impact import (
    InterventionCreate,
    InterventionSimulate,
    InterventionResponse,
    ImpactSummaryResponse,
)

router = APIRouter(tags=["Interventions & Impact Measurement"])


@router.post(
    "/interventions",
    response_model=InterventionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new facility intervention from an insight",
    description="Initiates an intervention with status PLANNED based on an identified anomaly or forecast risk.",
)
def create_intervention(
    payload: InterventionCreate,
    db: Session = Depends(get_db),
):
    service = ImpactService(db)
    try:
        itv = service.create_intervention(
            insight_id=payload.insight_id,
            action=payload.action,
            measurement_type=payload.measurement_type or "SIMULATED",
        )
        return service.get_intervention_by_id(itv.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create facility intervention.")


@router.post(
    "/interventions/{intervention_id}/simulate",
    response_model=InterventionResponse,
    summary="Simulate post-intervention resource reduction (Demo Mode)",
    description="Calculates a transparent demo post-intervention after-value and marks the intervention as COMPLETED.",
)
def simulate_intervention(
    intervention_id: int,
    payload: Optional[InterventionSimulate] = None,
    db: Session = Depends(get_db),
):
    service = ImpactService(db)
    factor = payload.simulated_reduction_factor if payload and payload.simulated_reduction_factor is not None else 0.85
    try:
        service.simulate_intervention(
            intervention_id=intervention_id,
            reduction_factor=factor,
        )
        return service.get_intervention_by_id(intervention_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to simulate facility intervention.")


@router.post(
    "/interventions/{intervention_id}/complete",
    response_model=InterventionResponse,
    summary="Mark an intervention as completed",
    description="Finalizes an intervention with either actual measured post-intervention telemetry or simulated values.",
)
def complete_intervention(
    intervention_id: int,
    after_value: Optional[float] = Query(None, description="Optional measured consumption value after intervention"),
    db: Session = Depends(get_db),
):
    service = ImpactService(db)
    try:
        service.complete_intervention(
            intervention_id=intervention_id,
            after_value=after_value,
        )
        return service.get_intervention_by_id(intervention_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to finalize facility intervention.")


@router.get(
    "/interventions",
    response_model=List[InterventionResponse],
    summary="Get history of facility interventions",
    description="Returns all logged interventions with before, baseline, after, and savings metrics.",
)
def get_interventions(
    resource: Optional[str] = Query(None, description="Filter by resource type: electricity, water, or waste"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: PLANNED, IN_PROGRESS, COMPLETED"),
    db: Session = Depends(get_db),
):
    service = ImpactService(db)
    try:
        return service.get_interventions(resource=resource, status=status_filter)
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch facility interventions.")


@router.get(
    "/interventions/{intervention_id}",
    response_model=InterventionResponse,
    summary="Get single intervention details",
    description="Returns detailed telemetry metrics, status, and savings analysis for an intervention.",
)
def get_intervention(
    intervention_id: int,
    db: Session = Depends(get_db),
):
    service = ImpactService(db)
    try:
        return service.get_intervention_by_id(intervention_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch intervention details.")


@router.get(
    "/impact/summary",
    response_model=ImpactSummaryResponse,
    summary="Get aggregate campus impact and savings summary",
    description="Aggregates resource savings across water (L), electricity (kWh), and waste (kg) with explicit measurement labeling.",
)
def get_impact_summary(
    db: Session = Depends(get_db),
):
    service = ImpactService(db)
    try:
        return service.get_impact_summary()
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to calculate aggregate impact summary.")
