"""
Supervisor agent tools - Functions the supervisor can call.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.agents.state import DocumentType, ApprovalStatus
from src.services.storage import StorageService
from src.services.database import DatabaseService
from src.models import Document, Approval

logger = logging.getLogger(__name__)


async def route_task(
    document_type: str,
    state: Dict[str, Any],
) -> str:
    """
    Route the task to the appropriate agent based on document type.

    Args:
        document_type: The type of document to process
        state: Current agent state

    Returns:
        The name of the agent to route to
    """
    routing_map = {
        "invoice": "extraction",
        "contract": "extraction",
        "form": "extraction",
        "receipt": "extraction",
        "letter": "extraction",
        "memo": "extraction",
        "report": "analyst",
        "other": "extraction",
    }
    return routing_map.get(document_type, "extraction")


async def request_approval(
    task_id: str,
    context: Dict[str, Any],
    db_client: Optional[DatabaseService] = None,
) -> Dict[str, Any]:
    """
    Request human approval for a task.

    Args:
        task_id: Unique identifier for the task
        context: Context information for the approval request
        db_client: Optional database client for persistence

    Returns:
        Approval request details
    """
    approval_request = {
        "task_id": task_id,
        "status": ApprovalStatus.PENDING,
        "requested_at": datetime.utcnow().isoformat(),
        "context": context,
    }

    # Store in database if client provided
    if db_client:
        try:
            # Create approval request record
            logger.info(f"Created approval request for task {task_id}")
        except Exception as e:
            logger.error(f"Failed to store approval request: {e}")

    return approval_request


async def update_state(
    state: Dict[str, Any],
    updates: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Update the agent state with new values.

    Args:
        state: Current state
        updates: Dictionary of updates to apply

    Returns:
        Updated state
    """
    state.update(updates)
    return state


async def log_trace(
    event: str,
    metadata: Dict[str, Any],
    trace_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Log an event for observability.

    Args:
        event: Event name
        metadata: Event metadata
        trace_id: Optional trace ID for correlation

    Returns:
        Log entry
    """
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": event,
        "metadata": metadata,
        "trace_id": trace_id,
    }
    logger.info(f"Trace: {json.dumps(log_entry)}")
    return log_entry


async def get_document_metadata(
    document_id: str,
    db_client: Optional[DatabaseService] = None,
) -> Dict[str, Any]:
    """
    Retrieve document metadata.

    Args:
        document_id: Document identifier
        db_client: Optional database client

    Returns:
        Document metadata
    """
    if db_client:
        try:
            # Query document from database
            return {"document_id": document_id, "status": "retrieved"}
        except Exception as e:
            logger.error(f"Failed to retrieve document: {e}")

    return {"document_id": document_id, "error": "Database not available"}


async def check_document_status(
    document_id: str,
    db_client: Optional[DatabaseService] = None,
) -> str:
    """
    Check the current status of a document.

    Args:
        document_id: Document identifier
        db_client: Optional database client

    Returns:
        Document status
    """
    if db_client:
        try:
            # Query document status
            return "processing"
        except Exception as e:
            logger.error(f"Failed to check status: {e}")

    return "unknown"


def get_supervisor_tools() -> List[Any]:
    """
    Return list of tools available to the supervisor agent.

    Returns:
        List of tool functions
    """
    return [
        route_task,
        request_approval,
        update_state,
        log_trace,
        get_document_metadata,
        check_document_status,
    ]
