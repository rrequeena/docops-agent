"""
Database models for documents.
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, String, Integer, DateTime, Enum, JSON, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class DocumentStatus(PyEnum):
    UPLOADED = "uploaded"
    INGESTING = "ingesting"
    EXTRACTING = "extracting"
    ANALYZING = "analyzing"
    AWAITING_APPROVAL = "awaiting_approval"
    PROCESSED = "processed"
    FAILED = "failed"


class DocumentType(PyEnum):
    INVOICE = "invoice"
    CONTRACT = "contract"
    FORM = "form"
    RECEIPT = "receipt"
    LETTER = "letter"
    MEMO = "memo"
    REPORT = "report"
    OTHER = "other"


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(512), nullable=False)
    content_type = Column(String(128), nullable=False)
    document_type = Column(Enum(DocumentType), nullable=True)
    status = Column(
        Enum(DocumentStatus),
        default=DocumentStatus.UPLOADED,
        nullable=False
    )
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    size_bytes = Column(BigInteger, nullable=False)
    minio_key = Column(String(512), nullable=True)
    doc_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Document(id={self.id}, filename={self.filename}, status={self.status})>"
