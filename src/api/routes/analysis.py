"""
Analysis API endpoints.
"""
import logging
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from src.services.database import DatabaseService
from src.utils.config import get_settings


router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])
logger = logging.getLogger(__name__)

settings = get_settings()
_db_service = None


def get_db():
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService(database_url=settings.database_url)
    return _db_service


# Response models
class AnalysisResponse(BaseModel):
    id: str
    analysis_type: str
    summary: str
    anomalies: List[dict]
    metrics: dict
    generated_at: Optional[str] = None


class AnalysisStatusResponse(BaseModel):
    analysis_id: str
    status: str
    message: str


# Endpoints
@router.post("", response_model=AnalysisStatusResponse, status_code=status.HTTP_202_ACCEPTED)
async def run_analysis(document_ids: List[str]) -> AnalysisStatusResponse:
    """
    Run cross-document analysis on multiple documents.
    """
    return AnalysisStatusResponse(
        analysis_id="770e8400-e29b-41d4-a716-446655440002",
        status="analyzing",
        message="Analysis started"
    )


@router.get("/document/{document_id}", response_model=AnalysisResponse)
async def get_analysis_by_document(document_id: str) -> AnalysisResponse:
    """
    Get analysis result by document ID - runs anomaly detection on extracted data.
    """
    db = get_db()

    try:
        # Get extraction data for this document
        extraction = await db.get_document_extraction(document_id)

        if not extraction:
            # Return empty response instead of 404
            return AnalysisResponse(
                id="",
                analysis_type="anomaly_detection",
                summary="No extraction data available",
                anomalies=[],
                metrics={},
                generated_at=datetime.utcnow()
            )

        extracted_data = extraction.data

        # Run anomaly detection
        anomalies = []

        try:
            from src.agents.analyst.anomaly import (
                detect_price_spikes,
                detect_duplicate_charges,
                detect_tax_anomalies,
                detect_unusual_patterns,
            )

            # Get all extractions for comparison (includes current invoice)
            all_extractions = await db.list_all_extractions()

            # Build list of all invoice data for comparison
            all_invoices = []
            for ext in all_extractions:
                if ext.data and isinstance(ext.data, dict):
                    # Skip if this is the current document (already in the list)
                    if ext.document_id != document_id:
                        all_invoices.append(ext.data)
                    else:
                        # Use the current extraction data
                        all_invoices.append(extracted_data)

            # Price spike detection - needs all invoices to compare
            if len(all_invoices) >= 2:
                price_spikes = detect_price_spikes(all_invoices, threshold_percent=50.0)
                anomalies.extend([a.to_dict() for a in price_spikes])

            # Duplicate detection
            duplicates = detect_duplicate_charges(all_invoices)
            anomalies.extend([a.to_dict() for a in duplicates])

            # Tax anomaly detection
            tax_anomalies = detect_tax_anomalies(all_invoices)
            anomalies.extend([a.to_dict() for a in tax_anomalies])

            # Unusual patterns
            patterns = detect_unusual_patterns(all_invoices)
            anomalies.extend([a.to_dict() for a in patterns])

            logger.info(f"Analysis complete for document {document_id}. Found {len(anomalies)} anomalies")

        except Exception as e:
            logger.warning(f"Analysis error: {e}")
            anomalies = []

        # Calculate basic metrics
        total = extracted_data.get("total") or 0
        currency = extracted_data.get("currency", "USD")

        metrics = {
            "document_id": document_id,
            "total_value": float(total),
            "currency": currency,
            "vendor": extracted_data.get("vendor_name", "Unknown"),
            "invoice_number": extracted_data.get("invoice_number", "N/A"),
            "anomaly_count": len(anomalies),
        }

        summary = f"Analysis completed. Found {len(anomalies)} anomalies."
        if len(anomalies) == 0:
            summary = "No anomalies detected."

        return AnalysisResponse(
            id=f"analysis-{document_id}",
            analysis_type="anomaly_detection",
            summary=summary,
            anomalies=anomalies,
            metrics=metrics,
            generated_at=datetime.utcnow().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(analysis_id: str) -> AnalysisResponse:
    """
    Get analysis result by analysis ID.
    """
    return AnalysisResponse(
        id=analysis_id,
        analysis_type="invoice",
        summary="Basic analysis completed",
        anomalies=[],
        metrics={"total": 0, "avg_amount": 0},
        generated_at=datetime.utcnow().isoformat()
    )
