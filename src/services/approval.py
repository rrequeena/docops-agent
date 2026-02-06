"""
Approval service for managing approval workflows.
"""
from typing import List, Optional
from datetime import datetime
import uuid

from src.models.approval import Approval, ApprovalStatus, RequestType
from src.services.database import DatabaseService
from src.utils.config import get_settings


class ApprovalService:
    """Service for managing approval workflows."""

    def __init__(self):
        self.settings = get_settings()
        self.db = DatabaseService(self.settings.database_url)

    async def request_approval(
        self,
        document_id: str,
        request_type: RequestType,
        context: Optional[dict] = None,
    ) -> Approval:
        """
        Create a new approval request.

        Args:
            document_id: ID of the document to approve
            request_type: Type of approval request
            context: Additional context for the approval

        Returns:
            Created approval object
        """
        approval = await self.db.create_approval(
            document_id=document_id,
            request_type=request_type,
            context=context,
        )
        return approval

    async def get_pending_approvals(self) -> List[Approval]:
        """
        Get all pending approvals.

        Returns:
            List of pending approvals
        """
        return await self.db.list_pending_approvals()

    async def approve(
        self,
        approval_id: str,
        notes: Optional[str] = None,
        reviewed_by: Optional[str] = None,
    ) -> Approval:
        """
        Approve an approval request.

        Args:
            approval_id: ID of the approval to approve
            notes: Optional notes for the approval
            reviewed_by: Optional reviewer name

        Returns:
            Updated approval object

        Raises:
            ValueError: If approval is not found or not pending
        """
        approval = await self.db.get_approval(approval_id)
        if not approval:
            raise ValueError(f"Approval {approval_id} not found")

        if approval.status != ApprovalStatus.PENDING:
            raise ValueError(f"Approval is not pending, current status: {approval.status.value}")

        return await self.db.update_approval_status(
            approval_id=approval_id,
            status=ApprovalStatus.APPROVED,
            notes=notes,
            reviewed_by=reviewed_by,
        )

    async def reject(
        self,
        approval_id: str,
        notes: Optional[str] = None,
        reviewed_by: Optional[str] = None,
    ) -> Approval:
        """
        Reject an approval request.

        Args:
            approval_id: ID of the approval to reject
            notes: Required reason for rejection
            reviewed_by: Optional reviewer name

        Returns:
            Updated approval object

        Raises:
            ValueError: If approval is not found or not pending
        """
        approval = await self.db.get_approval(approval_id)
        if not approval:
            raise ValueError(f"Approval {approval_id} not found")

        if approval.status != ApprovalStatus.PENDING:
            raise ValueError(f"Approval is not pending, current status: {approval.status.value}")

        return await self.db.update_approval_status(
            approval_id=approval_id,
            status=ApprovalStatus.REJECTED,
            notes=notes,
            reviewed_by=reviewed_by,
        )

    async def get_approval(self, approval_id: str) -> Optional[Approval]:
        """
        Get an approval by ID.

        Args:
            approval_id: ID of the approval

        Returns:
            Approval object or None if not found
        """
        return await self.db.get_approval(approval_id)

    async def list_by_document(self, document_id: str) -> List[Approval]:
        """
        List all approvals for a document.

        Args:
            document_id: ID of the document

        Returns:
            List of approvals for the document
        """
        from sqlalchemy import select
        async with self.db.async_session() as session:
            result = await session.execute(
                select(Approval)
                .filter(Approval.document_id == document_id)
                .order_by(Approval.requested_at.desc())
            )
            return result.scalars().all()


__all__ = ["ApprovalService"]
