"""
Supervisor state management functions.
"""

from typing import Dict, Any, Optional
from datetime import datetime

from src.agents.state import AgentState, SupervisorState, ApprovalStatus, AgentType


def initialize_supervisor_state(
    document_ids: list,
    task_type: str = "document_processing",
) -> SupervisorState:
    """Initialize supervisor-specific state."""
    return {
        "task_type": task_type,
        "documents_to_process": document_ids,
        "current_step": "init",
        "routing_decision": None,
        "requires_approval": False,
        "approval_result": None,
    }


def update_supervisor_state(
    state: AgentState,
    step: str,
    routing: Optional[str] = None,
    requires_approval: bool = False,
) -> AgentState:
    """Update supervisor state with new step information."""
    state["current_agent"] = AgentType.SUPERVISOR
    # Store in a separate key for supervisor-specific state
    if "supervisor_state" not in state:
        state["supervisor_state"] = {}
    state["supervisor_state"]["current_step"] = step
    if routing:
        state["supervisor_state"]["routing_decision"] = routing
    state["supervisor_state"]["requires_approval"] = requires_approval
    return state


def handle_approval_result(
    state: AgentState,
    approved: bool,
    feedback: Optional[str] = None,
) -> AgentState:
    """Handle the result of a human approval decision."""
    if approved:
        state["approval_status"] = ApprovalStatus.APPROVED
        # Continue workflow based on current step
        if state.get("document_status") == "awaiting_approval":
            # Resume processing
            pass
    else:
        state["approval_status"] = ApprovalStatus.REJECTED
        state["document_status"] = "rejected"
        if feedback:
            state["errors"].append(f"Rejected with feedback: {feedback}")
    return state


def check_approval_required(
    state: AgentState,
    confidence_threshold: float = 0.7,
    value_threshold: float = 1000.0,
) -> bool:
    """Check if approval is required based on current state."""
    # Check extraction confidence
    extraction_results = state.get("extraction_results", {})
    for doc_id, result in extraction_results.items():
        confidence = result.get("confidence", 1.0)
        if confidence < confidence_threshold:
            return True

    # Check for anomalies
    analysis_results = state.get("analysis_results")
    if analysis_results and analysis_results.get("anomalies"):
        return True

    # Check transaction values
    for result in extraction_results.values():
        data = result.get("data", {})
        total = data.get("total") or data.get("amount") or 0
        if isinstance(total, (int, float)) and total > value_threshold:
            return True

    return False


def get_next_agent(state: AgentState) -> Optional[AgentType]:
    """Determine the next agent based on current state and workflow."""
    current = state.get("current_agent")

    workflow_map = {
        None: AgentType.INGESTION,
        AgentType.INGESTION: AgentType.EXTRACTION,
        AgentType.EXTRACTION: AgentType.ANALYST,
        AgentType.ANALYST: None,  # Requires approval
    }

    return workflow_map.get(current)


def get_workflow_status(state: AgentState) -> Dict[str, Any]:
    """Get a summary of the current workflow status."""
    return {
        "trace_id": state.get("trace_id"),
        "current_agent": state.get("current_agent"),
        "document_status": state.get("document_status"),
        "approval_status": state.get("approval_status"),
        "step_count": state.get("step_count", 0),
        "documents_processed": len(state.get("extraction_results", {})),
        "errors": state.get("errors", []),
    }
