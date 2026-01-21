"""
Approval API endpoints.
"""
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel


router = APIRouter(prefix="/api/v1/approvals", tags=["approvals"])


# Request models
class ApprovalNotesRequest(BaseModel):
    notes: Optional[str] = None


# Response models
class ApprovalResponse(BaseModel):
    id: str
    document_ids: List[str]
    request_type: str
    status: str
    requested_at: Optional[str] = None
    context: Optional[dict] = None


class ApprovalListResponse(BaseModel):
    approvals: List[ApprovalResponse]


class ApprovalActionResponse(BaseModel):
    approval_id: str
    status: str
    reviewed_at: Optional[str] = None


# Endpoints
@router.get("", response_model=ApprovalListResponse)
async def list_approvals() -> ApprovalListResponse:
    """
    List pending approval requests.
    """
    # TODO: Implement actual database query
    return ApprovalListResponse(approvals=[])


@router.post("/{approval_id}/approve", response_model=ApprovalActionResponse)
async def approve_request(
    approval_id: str,
    request: ApprovalNotesRequest = ApprovalNotesRequest()
) -> ApprovalActionResponse:
    """
    Approve a request.
    """
    # TODO: Implement actual approval
    return ApprovalActionResponse(
        approval_id=approval_id,
        status="approved",
        reviewed_at="2026-02-17T10:10:00Z"
    )


@router.post("/{approval_id}/reject", response_model=ApprovalActionResponse)
async def reject_request(
    approval_id: str,
    request: ApprovalNotesRequest = ApprovalNotesRequest()
) -> ApprovalActionResponse:
    """
    Reject a request.
    """
    # TODO: Implement actual rejection
    return ApprovalActionResponse(
        approval_id=approval_id,
        status="rejected",
        reviewed_at="2026-02-17T10:10:00Z"
    )
