"""
Database models for approvals.
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, String, DateTime, Enum, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.models.document import Base


class ApprovalStatus(PyEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class RequestType(PyEnum):
    PROCESSING_APPROVAL = "processing_approval"
    EXTRACTION_APPROVAL = "extraction_approval"
    ACTION_APPROVAL = "action_approval"


class Approval(Base):
    __tablename__ = "approvals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=False
    )
    request_type = Column(
        Enum(RequestType, values_callable=lambda x: [e.value for e in x], native_enum=False),
        nullable=False
    )
    status = Column(
        Enum(ApprovalStatus, values_callable=lambda x: [e.value for e in x], native_enum=False),
        default=ApprovalStatus.PENDING,
        nullable=False
    )
    context = Column(JSON, nullable=True)
    notes = Column(String(2048), nullable=True)
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(String(256), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    document = relationship("Document", backref="approvals")

    def __repr__(self):
        return f"<Approval(id={self.id}, document_id={self.document_id}, status={self.status})>"
