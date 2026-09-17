"""API routing module."""
from fastapi import APIRouter
from app.api.health import router as health_router
from app.api.resources import router as resources_router
from app.api.ml import router as ml_router
from app.api.insights import router as insights_router
from app.api.interventions import router as interventions_router
from app.api.ingestion import router as ingestion_router

api_router = APIRouter(prefix="/api")
api_router.include_router(health_router, tags=["Health"])
api_router.include_router(resources_router)
api_router.include_router(ml_router)
api_router.include_router(insights_router)
api_router.include_router(interventions_router)
api_router.include_router(ingestion_router)

__all__ = ["api_router"]


