"""
Approval API endpoints.
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.database import DatabaseService
from src.models.approval import ApprovalStatus, RequestType
from src.models.document import DocumentStatus
from src.utils.config import get_settings


router = APIRouter(prefix="/api/v1/approvals", tags=["approvals"])


def get_settings_lazy():
    """Lazy import of settings to avoid Pydantic validation at import time."""
    return get_settings()


async def get_db():
    """Dependency to get database session."""
    settings = get_settings_lazy()
    db = DatabaseService(settings.database_url)
    async with db.async_session() as session:
        yield session


# Request models
class ApprovalCreateRequest(BaseModel):
    document_id: str
    request_type: str
    context: Optional[dict] = None


class ApprovalNotesRequest(BaseModel):
    notes: Optional[str] = None


# Response models
class ApprovalResponse(BaseModel):
    id: str
    document_id: str
    request_type: str
    status: str
    context: Optional[dict] = None
    notes: Optional[str] = None
    requested_at: Optional[str] = None
    reviewed_at: Optional[str] = None
    reviewed_by: Optional[str] = None


class ApprovalListResponse(BaseModel):
    approvals: List[ApprovalResponse]
    total: int


class ApprovalActionResponse(BaseModel):
    approval_id: str
    status: str
    reviewed_at: Optional[str] = None
    notes: Optional[str] = None


def approval_to_response(approval) -> ApprovalResponse:
    """Convert approval model to response."""
    return ApprovalResponse(
        id=str(approval.id),
        document_id=str(approval.document_id),
        request_type=approval.request_type.value,
        status=approval.status.value,
        context=approval.context,
        notes=approval.notes,
        requested_at=approval.requested_at.isoformat() if approval.requested_at else None,
        reviewed_at=approval.reviewed_at.isoformat() if approval.reviewed_at else None,
        reviewed_by=approval.reviewed_by,
    )


# Endpoints
@router.get("", response_model=ApprovalListResponse)
async def list_approvals(
    status_filter: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> ApprovalListResponse:
    """
    List approval requests with optional status filter.
    """
    settings = get_settings_lazy()
    db = DatabaseService(settings.database_url)

    if status_filter:
        status_enum = ApprovalStatus(status_filter.lower())
        approvals = await db.list_pending_approvals()
        if status_filter.lower() == "pending":
            approvals = [a for a in approvals if a.status == ApprovalStatus.PENDING]
        else:
            approvals = []
    else:
        approvals = await db.list_pending_approvals()

    return ApprovalListResponse(
        approvals=[approval_to_response(a) for a in approvals],
        total=len(approvals),
    )


@router.get("/{approval_id}", response_model=ApprovalResponse)
async def get_approval(approval_id: str) -> ApprovalResponse:
    """
    Get a specific approval by ID.
    """
    settings = get_settings_lazy()
    db = DatabaseService(settings.database_url)
    approval = await db.get_approval(approval_id)

    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval {approval_id} not found"
        )

    return approval_to_response(approval)


@router.post("", response_model=ApprovalResponse, status_code=status.HTTP_201_CREATED)
async def create_approval(request: ApprovalCreateRequest) -> ApprovalResponse:
    """
    Create a new approval request.
    """
    settings = get_settings_lazy()
    db = DatabaseService(settings.database_url)

    try:
        request_type = RequestType(request.request_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request type: {request.request_type}"
        )

    approval = await db.create_approval(
        document_id=request.document_id,
        request_type=request_type,
        context=request.context,
    )

    return approval_to_response(approval)


@router.post("/{approval_id}/approve", response_model=ApprovalActionResponse)
async def approve_request(
    approval_id: str,
    request: ApprovalNotesRequest = ApprovalNotesRequest()
) -> ApprovalActionResponse:
    """
    Approve a request.
    """
    settings = get_settings_lazy()
    db = DatabaseService(settings.database_url)

    approval = await db.get_approval(approval_id)
    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval {approval_id} not found"
        )

    if approval.status != ApprovalStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Approval is not pending, current status: {approval.status.value}"
        )

    updated = await db.update_approval_status(
        approval_id=approval_id,
        status=ApprovalStatus.APPROVED,
        notes=request.notes,
    )

    # If this was an anomaly review, update the document status to processed
    if approval.document_id:
        await db.update_document_status(approval.document_id, DocumentStatus.PROCESSED)

    return ApprovalActionResponse(
        approval_id=approval_id,
        status="approved",
        reviewed_at=updated.reviewed_at.isoformat() if updated.reviewed_at else None,
        notes=request.notes,
    )


@router.post("/{approval_id}/reject", response_model=ApprovalActionResponse)
async def reject_request(
    approval_id: str,
    request: ApprovalNotesRequest = ApprovalNotesRequest()
) -> ApprovalActionResponse:
    """
    Reject a request.
    """
    settings = get_settings_lazy()
    db = DatabaseService(settings.database_url)

    approval = await db.get_approval(approval_id)
    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval {approval_id} not found"
        )

    if approval.status != ApprovalStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Approval is not pending, current status: {approval.status.value}"
        )

    updated = await db.update_approval_status(
        approval_id=approval_id,
        status=ApprovalStatus.REJECTED,
        notes=request.notes,
    )

    # If this was an anomaly review, mark the document as rejected
    if approval.document_id:
        await db.update_document_status(approval.document_id, DocumentStatus.REJECTED)

    return ApprovalActionResponse(
        approval_id=approval_id,
        status="rejected",
        reviewed_at=updated.reviewed_at.isoformat() if updated.reviewed_at else None,
        notes=request.notes,
    )


@router.get("/{approval_id}/status", response_model=ApprovalResponse)
async def get_approval_status(approval_id: str) -> ApprovalResponse:
    """
    Get approval status.
    """
    settings = get_settings_lazy()
    db = DatabaseService(settings.database_url)
    approval = await db.get_approval(approval_id)

    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval {approval_id} not found"
        )

    return approval_to_response(approval)
