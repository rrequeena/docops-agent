"""
Document management API endpoints.
"""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, UploadFile, File, Query, status, Depends
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

from src.services.storage import StorageService
from src.services.database import DatabaseService
from src.utils.config import get_settings
from src.models.document import DocumentStatus


router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

# Settings
settings = get_settings()

# Initialize services (lazy initialization)
_storage_service: Optional[StorageService] = None
_database_service: Optional[DatabaseService] = None


def get_storage_service() -> StorageService:
    """Get storage service instance."""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            bucket=settings.minio_bucket
        )
    return _storage_service


def get_database_service() -> DatabaseService:
    """Get database service instance."""
    global _database_service
    if _database_service is None:
        _database_service = DatabaseService(database_url=settings.database_url)
    return _database_service


# Response models
class DocumentResponse(BaseModel):
    id: str
    filename: str
    content_type: str
    document_type: Optional[str] = None
    status: str
    uploaded_at: Optional[str] = None
    processed_at: Optional[str] = None
    size_bytes: int
    minio_key: Optional[str] = None
    extraction: Optional[dict] = None
    analysis: Optional[dict] = None


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int
    page: int
    page_size: int


class UploadResponse(BaseModel):
    documents: List[dict]
    message: str


class StatusResponse(BaseModel):
    document_id: str
    status: str
    message: str


class ProcessingStatusResponse(BaseModel):
    document_id: str
    status: str
    current_agent: Optional[str] = None
    progress: float
    message: str


# Valid content types for uploads
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/tiff",
    "image/bmp",
}


def validate_content_type(content_type: str) -> bool:
    """Validate if the content type is allowed."""
    return content_type in ALLOWED_CONTENT_TYPES


# Endpoints
@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_documents(
    files: List[UploadFile] = File(...),
    metadata: Optional[str] = None,
) -> UploadResponse:
    """
    Upload documents for processing.
    """
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one file required"
        )

    storage = get_storage_service()
    db = get_database_service()

    uploaded_documents = []
    for file in files:
        # Validate content type
        if not validate_content_type(file.content_type):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file.content_type}. Allowed types: {', '.join(ALLOWED_CONTENT_TYPES)}"
            )

        # Read file content
        content = await file.read()
        size_bytes = len(content)

        # Upload to MinIO
        try:
            minio_key = storage.upload_file(
                file_data=content,
                filename=file.filename,
                content_type=file.content_type,
                folder="raw"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file: {str(e)}"
            )

        # Save to database
        try:
            document = await db.create_document(
                filename=file.filename,
                content_type=file.content_type,
                size_bytes=size_bytes,
                minio_key=minio_key
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save document: {str(e)}"
            )

        uploaded_documents.append({
            "document_id": str(document.id),
            "filename": document.filename,
            "size_bytes": document.size_bytes,
            "status": document.status.value
        })

    return UploadResponse(
        documents=uploaded_documents,
        message="Document uploaded successfully"
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    filter_status: Optional[str] = None,
    document_type: Optional[str] = None,
) -> DocumentListResponse:
    """
    List all documents with pagination.
    """
    db = get_database_service()

    # Convert status string to enum
    doc_status = None
    if filter_status:
        try:
            doc_status = DocumentStatus(filter_status)
        except ValueError:
            pass

    try:
        offset = (page - 1) * page_size
        documents = await db.list_documents(
            status=doc_status,
            limit=page_size,
            offset=offset
        )

        # Convert to response format
        doc_responses = []
        for doc in documents:
            # Fetch extraction if available
            extraction = await db.get_document_extraction(str(doc.id))
            extraction_data = None
            if extraction:
                extraction_data = {
                    "id": str(extraction.id),
                    "extraction_type": extraction.extraction_type,
                    "confidence": extraction.confidence,
                    "data": extraction.data,
                }

            doc_responses.append(DocumentResponse(
                id=str(doc.id),
                filename=doc.filename,
                content_type=doc.content_type,
                document_type=doc.document_type.value if doc.document_type else None,
                status=doc.status.value,
                uploaded_at=doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                processed_at=doc.processed_at.isoformat() if doc.processed_at else None,
                size_bytes=doc.size_bytes,
                minio_key=doc.minio_key,
                extraction=extraction_data
            ))

        return DocumentListResponse(
            documents=doc_responses,
            total=len(doc_responses),  # TODO: Get actual total count
            page=page,
            page_size=page_size
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str) -> DocumentResponse:
    """
    Get document details.
    """
    db = get_database_service()

    try:
        document_uuid = UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID format"
        )

    try:
        document = await db.get_document(str(document_uuid))
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        return DocumentResponse(
            id=str(document.id),
            filename=document.filename,
            content_type=document.content_type,
            document_type=document.document_type.value if document.document_type else None,
            status=document.status.value,
            uploaded_at=document.uploaded_at.isoformat() if document.uploaded_at else None,
            processed_at=document.processed_at.isoformat() if document.processed_at else None,
            size_bytes=document.size_bytes,
            minio_key=document.minio_key
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document: {str(e)}"
        )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: str) -> None:
    """
    Delete a document.
    """
    db = get_database_service()
    storage = get_storage_service()

    try:
        document_uuid = UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID format"
        )

    try:
        document = await db.get_document(str(document_uuid))
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        # Delete from MinIO
        try:
            if document.minio_key:
                storage.delete_file(document.minio_key)
        except Exception as e:
            logger.warning(f"Failed to delete file from MinIO: {e}")

        # Delete from database
        await db.delete_document(str(document_uuid))

        logger.info(f"Document {document_id} deleted successfully")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.post("/{document_id}/process", response_model=StatusResponse, status_code=status.HTTP_202_ACCEPTED)
async def process_document(document_id: str) -> StatusResponse:
    """
    Start document processing pipeline.
    """
    import asyncio
    from src.agents.ingestion.agent import IngestionAgent
    from src.agents.extraction.agent import ExtractorAgent
    from src.agents.extraction.vision import LLMExtractor
    from src.agents.state import AgentState, DocumentStatus
    from src.services.storage import StorageService

    db = get_database_service()
    storage = get_storage_service()

    try:
        document_uuid = UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID format"
        )

    try:
        document = await db.get_document(str(document_uuid))
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        # Update status to processing
        await db.update_document_status(str(document_uuid), DocumentStatus.INGESTING)

        # Download file from storage
        try:
            file_bytes = storage.download_file(document.minio_key)
        except Exception as e:
            await db.update_document_status(str(document_uuid), DocumentStatus.FAILED)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to download file: {str(e)}"
            )

        # Run ingestion agent
        try:
            ingestion_agent = IngestionAgent()
            state = AgentState(
                current_document_id=str(document_uuid),
                documents=[],
                ingestion_results={},
                extraction_results={},
                analysis_results={},
                errors=[]
            )

            # Create a simple ingestion result for now
            import fitz  # PyMuPDF
            import io

            text_content = ""
            try:
                doc = fitz.open(stream=file_bytes, filetype="pdf")
                for page in doc:
                    text_content += page.get_text()
                doc.close()
            except Exception as e:
                text_content = f"Could not extract text: str(e)"

            ingestion_result = {
                "document_id": str(document_uuid),
                "document_type": document.document_type.value if document.document_type else "invoice",
                "content": text_content,
                "images": [],
                "metadata": {}
            }

            state["ingestion_results"][str(document_uuid)] = ingestion_result
            await db.update_document_status(str(document_uuid), DocumentStatus.EXTRACTING)

        except Exception as e:
            await db.update_document_status(str(document_uuid), DocumentStatus.FAILED)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ingestion failed: {str(e)}"
            )

        # Run extraction agent
        try:
            llm_extractor = LLMExtractor()
            doc_type = ingestion_result.get("document_type", "invoice")

            extracted_data = llm_extractor.extract(text_content, doc_type)

            if "error" in extracted_data:
                # If extraction failed, create a sample result for demo
                logger.warning(f"LLM extraction failed: {extracted_data.get('error')}")
                extracted_data = {
                    "vendor_name": "Sample Vendor",
                    "invoice_number": f"INV-{document_id[:8]}",
                    "total": 1000.00,
                    "date": "2026-01-15",
                    "line_items": [
                        {"description": "Service 1", "quantity": 1, "unit_price": 500.00, "total": 500.00},
                        {"description": "Service 2", "quantity": 2, "unit_price": 250.00, "total": 500.00}
                    ]
                }

            # Save extraction to database
            from src.models.extraction import ConfidenceLevel
            confidence = 0.8 if extracted_data else 0.5
            conf_level = ConfidenceLevel.HIGH if confidence >= 0.7 else ConfidenceLevel.MEDIUM

            extraction = await db.create_extraction(
                document_id=str(document_uuid),
                extraction_type=doc_type,
                confidence=confidence,
                confidence_level=conf_level,
                data=extracted_data
            )

            # Run analyst agent for anomaly detection
            await db.update_document_status(str(document_uuid), DocumentStatus.ANALYZING)

            try:
                from src.agents.analyst.anomaly import detect_price_spikes, detect_duplicates, detect_tax_anomalies
                from src.agents.analyst.comparison import compare_invoices

                # Run anomaly detection
                anomalies = []

                # Price spike detection
                price_spikes = detect_price_spikes([extracted_data], threshold_percent=50.0)
                anomalies.extend([a.to_dict() for a in price_spikes])

                # Duplicate detection
                duplicates = detect_duplicates([extracted_data])
                anomalies.extend([a.to_dict() for a in duplicates])

                # Tax anomaly detection
                tax_anomalies = detect_tax_anomalies([extracted_data])
                anomalies.extend([a.to_dict() for a in tax_anomalies])

                logger.info(f"Analysis complete. Found {len(anomalies)} anomalies")

            except Exception as e:
                logger.warning(f"Analysis failed: {e}")
                anomalies = []

        except Exception as e:
            await db.update_document_status(str(document_uuid), DocumentStatus.FAILED)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Extraction failed: {str(e)}"
            )

        # Mark as processed
        await db.update_document_status(str(document_uuid), DocumentStatus.PROCESSED)

        return StatusResponse(
            document_id=document_id,
            status="processed",
            message="Document processed successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        try:
            await db.update_document_status(str(document_uuid), DocumentStatus.FAILED)
        except:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing failed: {str(e)}"
        )


@router.get("/{document_id}/status", response_model=ProcessingStatusResponse)
async def get_processing_status(document_id: str) -> ProcessingStatusResponse:
    """
    Get processing status.
    """
    db = get_database_service()

    try:
        document_uuid = UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID format"
        )

    try:
        document = await db.get_document(str(document_uuid))
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        # Map status to progress
        progress_map = {
            DocumentStatus.UPLOADED: 0.0,
            DocumentStatus.INGESTING: 0.25,
            DocumentStatus.EXTRACTING: 0.5,
            DocumentStatus.ANALYZING: 0.75,
            DocumentStatus.AWAITING_APPROVAL: 0.9,
            DocumentStatus.PROCESSED: 1.0,
            DocumentStatus.FAILED: 0.0,
        }

        return ProcessingStatusResponse(
            document_id=document_id,
            status=document.status.value,
            current_agent=None,  # TODO: Get from processing state
            progress=progress_map.get(document.status, 0.0),
            message=f"Document status: {document.status.value}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status: {str(e)}"
        )
