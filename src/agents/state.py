from typing import TypedDict, List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    INGESTING = "ingesting"
    EXTRACTING = "extracting"
    ANALYZING = "analyzing"
    AWAITING_APPROVAL = "awaiting_approval"
    PROCESSED = "processed"
    FAILED = "failed"


class AgentType(str, Enum):
    SUPERVISOR = "supervisor"
    INGESTION = "ingestion"
    EXTRACTION = "extraction"
    ANALYST = "analyst"
    ACTION = "action"


class DocumentType(str, Enum):
    INVOICE = "invoice"
    CONTRACT = "contract"
    FORM = "form"
    RECEIPT = "receipt"
    LETTER = "letter"
    MEMO = "memo"
    REPORT = "report"
    OTHER = "other"


class IngestionResult(TypedDict):
    document_type: DocumentType
    content: str
    tables: List[Dict[str, Any]]
    images: List[str]
    chunks: List[str]
    metadata: Dict[str, Any]


class ExtractionResult(TypedDict):
    document_id: str
    schema_type: str
    data: Dict[str, Any]
    confidence: float
    validation_errors: List[str]
    raw_response: Optional[str]


class Anomaly(TypedDict):
    type: str
    severity: str
    description: str
    document_ids: List[str]
    details: Dict[str, Any]


class AnalysisResult(TypedDict):
    summary: str
    anomalies: List[Anomaly]
    metrics: Dict[str, Any]
    trends: Dict[str, Any]


class AgentState(TypedDict):
    """Main state container for the LangGraph agent workflow."""

    # Document tracking
    document_ids: List[str]
    current_document_id: str
    document_types: Dict[str, DocumentType]

    # Processing state
    current_agent: Optional[AgentType]
    document_status: DocumentStatus

    # Results
    ingestion_results: Dict[str, IngestionResult]
    extraction_results: Dict[str, ExtractionResult]
    analysis_results: Optional[AnalysisResult]

    # Approval flow
    approval_status: ApprovalStatus
    approval_requested_at: Optional[datetime]
    approval_context: Optional[Dict[str, Any]]

    # Observability
    trace_id: str
    errors: List[str]
    step_count: int


class SupervisorState(TypedDict):
    """State specific to the supervisor agent."""

    task_type: str
    documents_to_process: List[str]
    current_step: str
    routing_decision: Optional[str]
    requires_approval: bool
    approval_result: Optional[Dict[str, Any]]


class IngestionState(TypedDict):
    """State specific to the ingestion agent."""

    document_id: str
    file_path: str
    file_bytes: Optional[bytes]
    classified_type: Optional[DocumentType]
    parsed_content: Optional[str]
    parsed_tables: List[Dict[str, Any]]
    parsed_images: List[str]
    text_chunks: List[str]
    embeddings: Optional[List[List[float]]]


class ExtractionState(TypedDict):
    """State specific to the extraction agent."""

    document_id: str
    document_type: DocumentType
    content: str
    schema_name: str
    extracted_data: Optional[Dict[str, Any]]
    confidence: float
    validation_passed: bool
    validation_errors: List[str]
    needs_retry: bool


class AnalystState(TypedDict):
    """State specific to the analyst agent."""

    document_ids: List[str]
    extraction_results: Dict[str, ExtractionResult]
    analysis_type: str
    anomalies_found: List[Anomaly]
    metrics_computed: Dict[str, Any]
    report_generated: bool
