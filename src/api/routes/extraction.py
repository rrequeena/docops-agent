"""
Extraction API endpoints.
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel


router = APIRouter(prefix="/api/v1/extractions", tags=["extraction"])


# Response models
class ExtractionResponse(BaseModel):
    id: str
    document_id: str
    extraction_type: Optional[str] = None
    confidence: float
    confidence_level: str
    data: dict
    warnings: list
    extracted_at: Optional[str] = None


class ExtractionStatusResponse(BaseModel):
    document_id: str
    extraction_id: str
    status: str


# Endpoints
@router.post("/{document_id}", response_model=ExtractionStatusResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_extraction(document_id: str) -> ExtractionStatusResponse:
    """
    Trigger extraction for a document.
    """
    # TODO: Implement actual extraction
    return ExtractionStatusResponse(
        document_id=document_id,
        extraction_id="660e8400-e29b-41d4-a716-446655440001",
        status="extracting"
    )


@router.get("/{extraction_id}", response_model=ExtractionResponse)
async def get_extraction(extraction_id: str) -> ExtractionResponse:
    """
    Get extraction result.
    """
    # TODO: Implement actual database fetch
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Extraction not found"
    )
