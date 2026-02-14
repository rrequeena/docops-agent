"""
Supervisor Agent - Central orchestrator for the DocOps system.

Handles:
- Routing tasks to appropriate agents
- Managing global state
- Enforcing human approval gates
- Handling error recovery
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from src.agents.base import BaseAgent, create_agent_node
from src.agents.state import (
    AgentState,
    AgentType,
    DocumentStatus,
    ApprovalStatus,
    DocumentType,
    SupervisorState,
)


class SupervisorAgent(BaseAgent):
    """Central orchestrator agent that manages the document processing workflow."""

    def __init__(
        self,
        confidence_threshold: float = 0.7,
        value_threshold: float = 1000.0,
    ):
        super().__init__("Supervisor", AgentType.SUPERVISOR)
        self.confidence_threshold = confidence_threshold
        self.value_threshold = value_threshold

    def get_system_prompt(self) -> str:
        return """You are the Supervisor Agent for DocOps, a multi-agent document intelligence system.

Your responsibilities:
1. Route incoming tasks to the appropriate specialized agent based on document type
2. Manage global state across the workflow
3. Enforce human approval gates for high-stakes actions
4. Handle error recovery and retries
5. Log all decisions for observability

Available routes:
- ingestion: For document classification and parsing
- extraction: For structured data extraction
- analyst: For cross-document analysis
- action: For executing actions based on analysis

Approval triggers:
- High-value transactions (configurable threshold)
- Anomalies detected by analyst
- Low confidence extractions
- Manual escalation requests

Always respond with a clear routing decision and reasoning."""

    def process(self, state: AgentState) -> AgentState:
        """Process the current state and determine next action."""
        current_step = state.get("current_agent")

        # Initialize trace_id if not present
        if "trace_id" not in state:
            state["trace_id"] = str(uuid.uuid4())

        # Initialize step count
        if "step_count" not in state:
            state["step_count"] = 0

        # Initialize result dictionaries if not present
        if "ingestion_results" not in state:
            state["ingestion_results"] = {}
        if "extraction_results" not in state:
            state["extraction_results"] = {}
        if "errors" not in state:
            state["errors"] = []

        # Route based on current state
        if current_step is None:
            # Starting point - route to ingestion
            state = self._route_to_ingestion(state)
        elif current_step == AgentType.INGESTION:
            # Ingestion complete - route to extraction
            state = self._route_to_extraction(state)
        elif current_step == AgentType.EXTRACTION:
            # Extraction complete - check if we need analyst
            state = self._route_to_analyst_or_approval(state)
        elif current_step == AgentType.ANALYST:
            # Analysis complete - route to approval
            state = self._route_to_approval(state)
        elif current_step == AgentType.ACTION:
            # Action complete - finalize
            state = self._finalize(state)

        return state

    def _route_to_ingestion(self, state: AgentState) -> AgentState:
        """Route to ingestion agent."""
        state["current_agent"] = AgentType.INGESTION
        state["document_status"] = DocumentStatus.INGESTING
        return state

    def _route_to_extraction(self, state: AgentState) -> AgentState:
        """Route to extraction agent."""
        state["current_agent"] = AgentType.EXTRACTION
        state["document_status"] = DocumentStatus.EXTRACTING
        return state

    def _route_to_analyst_or_approval(self, state: AgentState) -> AgentState:
        """Determine if analyst is needed or go straight to approval."""
        # Check if we have multiple documents for cross-document analysis
        if len(state.get("document_ids", [])) > 1:
            state["current_agent"] = AgentType.ANALYST
            state["document_status"] = DocumentStatus.ANALYZING
        else:
            # Single document - go to approval
            state = self._request_approval(state)
        return state

    def _route_to_approval(self, state: AgentState) -> AgentState:
        """Route to approval gate."""
        return self._request_approval(state)

    def _request_approval(self, state: AgentState) -> AgentState:
        """Request human approval for the current task."""
        state["document_status"] = DocumentStatus.AWAITING_APPROVAL
        state["approval_status"] = ApprovalStatus.PENDING
        state["approval_requested_at"] = datetime.utcnow()

        # Build approval context
        approval_context = {
            "document_ids": state.get("document_ids", []),
            "extraction_results": state.get("extraction_results", {}),
            "analysis_results": state.get("analysis_results"),
            "confidence_scores": self._get_confidence_summary(state),
        }
        state["approval_context"] = approval_context

        return state

    def _get_confidence_summary(self, state: AgentState) -> Dict[str, float]:
        """Get summary of confidence scores from extraction results."""
        scores = {}
        for doc_id, result in state.get("extraction_results", {}).items():
            scores[doc_id] = result.get("confidence", 0.0)
        return scores

    def _finalize(self, state: AgentState) -> AgentState:
        """Finalize the workflow."""
        state["document_status"] = DocumentStatus.PROCESSED
        return state

    def route_task(self, document_type: DocumentType) -> str:
        """Determine which agent should handle the document type."""
        routing_map = {
            DocumentType.INVOICE: "extraction",
            DocumentType.CONTRACT: "extraction",
            DocumentType.FORM: "extraction",
            DocumentType.RECEIPT: "extraction",
            DocumentType.LETTER: "extraction",
            DocumentType.MEMO: "extraction",
            DocumentType.REPORT: "analyst",
            DocumentType.OTHER: "extraction",
        }
        return routing_map.get(document_type, "extraction")

    def should_request_approval(
        self,
        confidence: float,
        anomaly_detected: bool = False,
        transaction_value: Optional[float] = None,
        threshold: Optional[float] = None,
    ) -> bool:
        """Determine if approval should be requested."""
        # Use instance thresholds if not provided
        if threshold is None:
            threshold = self.value_threshold

        # Low confidence
        if confidence < self.confidence_threshold:
            return True
        # Anomaly detected
        if anomaly_detected:
            return True
        # High value transaction
        if transaction_value and transaction_value > threshold:
            return True
        return False

    def validate_state(self, state: AgentState) -> bool:
        """Validate state has required fields."""
        return "document_ids" in state


# Create LangGraph node
supervisor_node = create_agent_node(SupervisorAgent())
