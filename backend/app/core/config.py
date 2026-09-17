"""Application configuration module."""
import os
from typing import List


class Settings:
    PROJECT_NAME: str = "Campus Resource Autopilot"
    VERSION: str = "0.2.0"
    API_V1_STR: str = "/api"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # Database configuration defaulting to SQLite
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/campus.db")

    # Allowed origins for CORS in development
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


settings = Settings()
