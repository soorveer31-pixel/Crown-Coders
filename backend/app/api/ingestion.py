"""API endpoints for CSV telemetry data ingestion and template downloads."""
from fastapi import APIRouter, Depends, UploadFile, File, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.ingestion import IngestionSummary
from app.services.ingestion_service import IngestionService, generate_csv_template

router = APIRouter(prefix="/ingestion", tags=["Data Ingestion"])


@router.post(
    "/upload",
    response_model=IngestionSummary,
    status_code=status.HTTP_200_OK,
    summary="Upload and ingest campus telemetry CSV",
    description="Validates schema and data rows, prevents duplicate entries, and atomically saves new readings into the existing telemetry database.",
)
async def upload_telemetry_csv(
    file: UploadFile = File(..., description="Canonical CSV file with headers: timestamp,building,resource_type,value"),
    db: Session = Depends(get_db),
) -> IngestionSummary:
    """Processes multipart CSV upload, validating rows and inserting valid non-duplicate readings."""
    return await IngestionService.process_csv_upload(db=db, file=file)


@router.get(
    "/template",
    summary="Download canonical CSV template",
    description="Returns a downloadable CSV template with canonical column headers and real campus examples.",
)
def download_csv_template():
    """Returns downloadable CSV template for college facilities data ingestion."""
    csv_content = generate_csv_template()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=campus_resource_template.csv",
            "Cache-Control": "no-cache",
        },
    )
