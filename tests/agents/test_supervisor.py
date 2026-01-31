"""
Tests for the supervisor agent.
"""

import pytest
from src.agents.supervisor.agent import SupervisorAgent
from src.agents.state import AgentState, DocumentStatus, ApprovalStatus, AgentType


class TestSupervisorAgent:
    """Test cases for SupervisorAgent."""

    def test_initialization(self):
        """Test supervisor agent initialization."""
        agent = SupervisorAgent()
        assert agent.name == "Supervisor"
        assert agent.agent_type == AgentType.SUPERVISOR

    def test_system_prompt(self):
        """Test supervisor system prompt."""
        agent = SupervisorAgent()
        prompt = agent.get_system_prompt()
        assert "Supervisor Agent" in prompt
        assert "routing" in prompt.lower()

    def test_validate_state(self):
        """Test state validation."""
        agent = SupervisorAgent()
        valid_state = {"document_ids": ["doc-001"]}
        invalid_state = {}

        assert agent.validate_state(valid_state) is True
        assert agent.validate_state(invalid_state) is False

    def test_route_task(self):
        """Test task routing."""
        agent = SupervisorAgent()

        assert agent.route_task("invoice") == "extraction"
        assert agent.route_task("contract") == "extraction"
        assert agent.route_task("report") == "analyst"
        assert agent.route_task("unknown") == "extraction"

    def test_should_request_approval_low_confidence(self):
        """Test approval request for low confidence."""
        agent = SupervisorAgent()

        assert agent.should_request_approval(confidence=0.5) is True
        assert agent.should_request_approval(confidence=0.8) is False

    def test_should_request_approval_anomaly(self):
        """Test approval request for anomalies."""
        agent = SupervisorAgent()

        assert agent.should_request_approval(confidence=0.9, anomaly_detected=True) is True

    def test_should_request_approval_high_value(self):
        """Test approval request for high value transactions."""
        agent = SupervisorAgent()

        assert agent.should_request_approval(
            confidence=0.9,
            transaction_value=2000.0,
            threshold=1000.0,
        ) is True


class TestSupervisorState:
    """Test cases for supervisor state management."""

    def test_update_supervisor_state(self):
        """Test updating supervisor state."""
        from src.agents.supervisor.state import update_supervisor_state

        state: AgentState = {
            "document_ids": ["doc-001"],
            "current_document_id": "doc-001",
            "document_types": {},
            "current_agent": None,
            "document_status": "uploaded",
            "ingestion_results": {},
            "extraction_results": {},
            "analysis_results": None,
            "approval_status": ApprovalStatus.PENDING,
            "approval_requested_at": None,
            "approval_context": None,
            "trace_id": "test-001",
            "errors": [],
            "step_count": 0,
        }

        updated = update_supervisor_state(state, "ingestion", routing="extraction")

        assert "supervisor_state" in updated
        assert updated["supervisor_state"]["current_step"] == "ingestion"
        assert updated["supervisor_state"]["routing_decision"] == "extraction"

    def test_check_approval_required_low_confidence(self):
        """Test approval check for low confidence."""
        from src.agents.supervisor.state import check_approval_required

        state: AgentState = {
            "document_ids": ["doc-001"],
            "current_document_id": "doc-001",
            "document_types": {},
            "current_agent": AgentType.EXTRACTION,
            "document_status": DocumentStatus.EXTRACTING,
            "ingestion_results": {},
            "extraction_results": {
                "doc-001": {
                    "confidence": 0.5,
                    "data": {},
                }
            },
            "analysis_results": None,
            "approval_status": ApprovalStatus.PENDING,
            "approval_requested_at": None,
            "approval_context": None,
            "trace_id": "test-001",
            "errors": [],
            "step_count": 0,
        }

        assert check_approval_required(state, confidence_threshold=0.7) is True

    def test_check_approval_required_anomaly(self):
        """Test approval check for anomalies."""
        from src.agents.supervisor.state import check_approval_required

        state: AgentState = {
            "document_ids": ["doc-001"],
            "current_document_id": "doc-001",
            "document_types": {},
            "current_agent": AgentType.ANALYST,
            "document_status": DocumentStatus.ANALYZING,
            "ingestion_results": {},
            "extraction_results": {
                "doc-001": {
                    "confidence": 0.9,
                    "data": {},
                }
            },
            "analysis_results": {
                "anomalies": [
                    {"type": "price_spike", "severity": "high"}
                ]
            },
            "approval_status": ApprovalStatus.PENDING,
            "approval_requested_at": None,
            "approval_context": None,
            "trace_id": "test-001",
            "errors": [],
            "step_count": 0,
        }

        assert check_approval_required(state) is True
