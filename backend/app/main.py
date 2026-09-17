"""Campus Resource Autopilot - FastAPI Application Entry Point.

This module initializes the FastAPI service, configures CORS middleware for the
React/Vite frontend, initializes SQLite tables on startup via lifespan, and mounts
the modular API routers.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import api_router
from app.core.config import settings
from app.core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager to initialize DB tables safely on startup."""
    init_db()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for AI-powered campus sustainability analytics, anomaly detection, and forecasting.",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(api_router)


@app.get("/")
async def root():
    """Root endpoint welcoming developers and pointing to interactive docs."""
    return {
        "project": settings.PROJECT_NAME,
        "description": "AI-powered campus sustainability platform",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/api/health",
        "resources_summary": "/api/resources/summary",
        "resources_history": "/api/resources/history?resource=electricity&range=7d",
        "ml_anomalies": "/api/ml/anomalies?resource=water&range=7d",
        "ml_forecast": "/api/ml/forecast?resource=electricity&horizon=24",
        "ml_evaluation": "/api/ml/evaluation?resource=electricity",
        "insights": "/api/insights?resource=water&range=7d",
        "interventions": "/api/interventions",
        "impact_summary": "/api/impact/summary",
    }




if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
