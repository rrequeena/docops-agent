"""
Extraction API endpoints.
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from src.services.database import DatabaseService
from src.utils.config import get_settings


router = APIRouter(prefix="/api/v1", tags=["extraction"])

settings = get_settings()
_db_service = None


def get_db():
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService(database_url=settings.database_url)
    return _db_service


# Response models
class ExtractionResponse(BaseModel):
    id: str
    document_id: str
    schema_type: Optional[str] = None
    confidence: float
    confidence_level: str
    data: dict
    warnings: list
    status: str = "completed"
    extracted_at: Optional[str] = None


class ExtractionStatusResponse(BaseModel):
    document_id: str
    extraction_id: str
    status: str


# Endpoints
@router.post("/extractions/{document_id}", response_model=ExtractionStatusResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_extraction(document_id: str) -> ExtractionStatusResponse:
    """
    Trigger extraction for a document.
    """
    return ExtractionStatusResponse(
        document_id=document_id,
        extraction_id="extraction-triggered",
        status="extracting"
    )


@router.get("/extraction/{document_id}", response_model=ExtractionResponse)
async def get_extraction_by_document(document_id: str) -> ExtractionResponse:
    """
    Get extraction result by document ID.
    """
    db = get_db()

    try:
        extraction = await db.get_document_extraction(document_id)

        if not extraction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Extraction not found"
            )

        return ExtractionResponse(
            id=str(extraction.id),
            document_id=str(extraction.document_id),
            schema_type=extraction.extraction_type,
            confidence=extraction.confidence,
            confidence_level=extraction.confidence_level.value,
            data=extraction.data,
            warnings=extraction.warnings,
            status=extraction.status.value,
            extracted_at=extraction.created_at.isoformat() if extraction.created_at else None
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get extraction: {str(e)}"
        )


@router.get("/extractions/{extraction_id}", response_model=ExtractionResponse)
async def get_extraction(extraction_id: str) -> ExtractionResponse:
    """
    Get extraction result by extraction ID.
    """
    db = get_db()

    try:
        extraction = await db.get_extraction(extraction_id)

        if not extraction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Extraction not found"
            )

        return ExtractionResponse(
            id=str(extraction.id),
            document_id=str(extraction.document_id),
            schema_type=extraction.extraction_type,
            confidence=extraction.confidence,
            confidence_level=extraction.confidence_level.value,
            data=extraction.data,
            warnings=extraction.warnings,
            status=extraction.status.value,
            extracted_at=extraction.created_at.isoformat() if extraction.created_at else None
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get extraction: {str(e)}"
        )
