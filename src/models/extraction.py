"""
Database models for extractions.
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, String, Float, DateTime, Enum, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.models.document import Base


class ExtractionStatus(PyEnum):
    PENDING = "pending"
    EXTRACTING = "extracting"
    COMPLETED = "completed"
    FAILED = "failed"


class ConfidenceLevel(PyEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Extraction(Base):
    __tablename__ = "extractions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=False
    )
    extraction_type = Column(String(64), nullable=False)
    confidence = Column(Float, nullable=False)
    confidence_level = Column(
        Enum(ConfidenceLevel),
        nullable=False
    )
    data = Column(JSON, nullable=False)
    warnings = Column(JSON, default=list, nullable=False)
    status = Column(
        Enum(ExtractionStatus),
        default=ExtractionStatus.PENDING,
        nullable=False
    )
    extracted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    document = relationship("Document", backref="extractions")

    def __repr__(self):
        return f"<Extraction(id={self.id}, document_id={self.document_id}, confidence={self.confidence})>"
