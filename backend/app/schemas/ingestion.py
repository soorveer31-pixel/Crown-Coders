"""Pydantic schemas for data ingestion and CSV validation."""
from typing import List
from pydantic import BaseModel, Field


class IngestionSummary(BaseModel):
    """Structured response model for CSV telemetry ingestion results."""
    filename: str = Field(..., description="Name of the processed CSV file")
    total_rows: int = Field(..., description="Total rows parsed in CSV (excluding header)")
    valid_rows: int = Field(..., description="Total rows meeting schema and domain validation")
    invalid_rows: int = Field(..., description="Total rows rejected due to validation failures")
    imported_rows: int = Field(..., description="Total new rows successfully committed to database")
    duplicate_rows: int = Field(..., description="Total rows identified as existing duplicates and skipped")
    errors: List[str] = Field(default_factory=list, description="Row-level error explanations for rejected rows")
    warnings: List[str] = Field(default_factory=list, description="Non-fatal warnings (e.g. duplicate skipped details)")
    message: str = Field(default="Import processed successfully", description="High-level human-readable status message")
