"""
Document Pydantic models.
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    INGESTING = "ingesting"
    EXTRACTING = "extracting"
    ANALYZING = "analyzing"
    AWAITING_APPROVAL = "awaiting_approval"
    PROCESSED = "processed"
    FAILED = "failed"


class DocumentType(str, Enum):
    INVOICE = "invoice"
    CONTRACT = "contract"
    FORM = "form"
    RECEIPT = "receipt"
    LETTER = "letter"
    MEMO = "memo"
    REPORT = "report"
    OTHER = "other"


class Document(BaseModel):
    id: str
    filename: str
    content_type: str
    document_type: Optional[DocumentType] = None
    status: DocumentStatus = DocumentStatus.UPLOADED
    uploaded_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    size_bytes: int
    minio_key: Optional[str] = None


class DocumentWithExtraction(Document):
    extraction: Optional[dict] = None
    analysis: Optional[dict] = None


class DocumentMetadata(BaseModel):
    metadata: Optional[dict] = None


class DocumentUploadResponse(BaseModel):
    documents: List[Document]
    message: str


class DocumentListParams(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    status: Optional[DocumentStatus] = None
    document_type: Optional[DocumentType] = None
