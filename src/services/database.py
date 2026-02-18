"""
Database service for PostgreSQL operations.
"""
from typing import Optional
from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from src.models.document import Base, Document, DocumentStatus, DocumentType
from src.models.extraction import Extraction, ExtractionStatus, ConfidenceLevel
from src.models.approval import Approval, ApprovalStatus, RequestType


class DatabaseService:
    """Database service for PostgreSQL operations."""

    def __init__(self, database_url: str):
        """Initialize database service."""
        # Convert postgresql:// to postgresql+asyncpg://
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")

        self.engine = create_async_engine(database_url, echo=False)
        self.async_session = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    async def create_tables(self):
        """Create all database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self):
        """Drop all database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def get_session(self) -> AsyncSession:
        """Get a database session."""
        async with self.async_session() as session:
            yield session

    # Document operations
    async def create_document(
        self,
        filename: str,
        content_type: str,
        size_bytes: int,
        minio_key: str,
        document_type: Optional[DocumentType] = None,
        metadata: Optional[dict] = None
    ) -> Document:
        """Create a new document record."""
        async with self.async_session() as session:
            document = Document(
                filename=filename,
                content_type=content_type,
                size_bytes=size_bytes,
                minio_key=minio_key,
                document_type=document_type,
                metadata=metadata,
                status=DocumentStatus.UPLOADED
            )
            session.add(document)
            await session.commit()
            await session.refresh(document)
            return document

    async def get_document(self, document_id: str) -> Optional[Document]:
        """Get a document by ID."""
        async with self.async_session() as session:
            return await session.get(Document, document_id)

    async def list_documents(
        self,
        status: Optional[DocumentStatus] = None,
        document_type: Optional[DocumentType] = None,
        limit: int = 20,
        offset: int = 0
    ) -> list[Document]:
        """List documents with optional filters."""
        async with self.async_session() as session:
            query = select(Document)
            if status:
                query = query.where(Document.status == status)
            if document_type:
                query = query.where(Document.document_type == document_type)
            query = query.order_by(Document.uploaded_at.desc()).limit(limit).offset(offset)
            result = await session.execute(query)
            return list(result.scalars().all())

    async def update_document_status(
        self,
        document_id: str,
        status: DocumentStatus
    ) -> Optional[Document]:
        """Update document status."""
        async with self.async_session() as session:
            document = await session.get(Document, document_id)
            if document:
                document.status = status
                await session.commit()
                await session.refresh(document)
            return document

    async def delete_document(self, document_id: str) -> bool:
        """Delete a document and its related records."""
        async with self.async_session() as session:
            document = await session.get(Document, document_id)
            if document:
                # Delete related extractions first
                from src.models.extraction import Extraction
                result = await session.execute(
                    select(Extraction).where(Extraction.document_id == document_id)
                )
                extractions = result.scalars().all()
                for ext in extractions:
                    await session.delete(ext)

                # Delete related approvals
                from src.models.approval import Approval
                result = await session.execute(
                    select(Approval).where(Approval.document_id == document_id)
                )
                approvals = result.scalars().all()
                for app in approvals:
                    await session.delete(app)

                # Delete the document
                await session.delete(document)
                await session.commit()
                return True
            return False

    # Extraction operations
    async def create_extraction(
        self,
        document_id: str,
        extraction_type: str,
        confidence: float,
        confidence_level: ConfidenceLevel,
        data: dict,
        warnings: Optional[list] = None
    ) -> Extraction:
        """Create a new extraction record."""
        async with self.async_session() as session:
            extraction = Extraction(
                document_id=document_id,
                extraction_type=extraction_type,
                confidence=confidence,
                confidence_level=confidence_level,
                data=data,
                warnings=warnings or [],
                status=ExtractionStatus.COMPLETED
            )
            session.add(extraction)
            await session.commit()
            await session.refresh(extraction)
            return extraction

    async def get_extraction(self, extraction_id: str) -> Optional[Extraction]:
        """Get an extraction by ID."""
        async with self.async_session() as session:
            return await session.get(Extraction, extraction_id)

    async def get_document_extraction(self, document_id: str) -> Optional[Extraction]:
        """Get extraction for a document."""
        async with self.async_session() as session:
            query = select(Extraction).where(Extraction.document_id == document_id).order_by(Extraction.created_at.desc()).limit(1)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    # Approval operations
    async def create_approval(
        self,
        document_id: str,
        request_type: RequestType,
        context: Optional[dict] = None
    ) -> Approval:
        """Create a new approval record."""
        async with self.async_session() as session:
            approval = Approval(
                document_id=document_id,
                request_type=request_type,
                context=context,
                status=ApprovalStatus.PENDING
            )
            session.add(approval)
            await session.commit()
            await session.refresh(approval)
            return approval

    async def get_approval(self, approval_id: str) -> Optional[Approval]:
        """Get an approval by ID."""
        async with self.async_session() as session:
            return await session.get(Approval, approval_id)

    async def list_pending_approvals(self) -> list[Approval]:
        """List all pending approvals."""
        async with self.async_session() as session:
            query = select(Approval).where(Approval.status == ApprovalStatus.PENDING).order_by(Approval.requested_at.asc())
            result = await session.execute(query)
            return list(result.scalars().all())

    async def update_approval_status(
        self,
        approval_id: str,
        status: ApprovalStatus,
        notes: Optional[str] = None,
        reviewed_by: Optional[str] = None
    ) -> Optional[Approval]:
        """Update approval status."""
        from datetime import datetime
        async with self.async_session() as session:
            approval = await session.get(Approval, approval_id)
            if approval:
                approval.status = status
                approval.reviewed_at = datetime.utcnow()
                if notes:
                    approval.notes = notes
                if reviewed_by:
                    approval.reviewed_by = reviewed_by
                await session.commit()
                await session.refresh(approval)
            return approval
