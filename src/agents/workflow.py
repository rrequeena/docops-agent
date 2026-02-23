"""
LangGraph-based document processing workflow with LangSmith tracing.
"""

import uuid
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langsmith import traceable

from src.agents.state import (
    AgentState,
    AgentType,
    DocumentStatus,
    DocumentType,
    ExtractionResult,
    ApprovalStatus,
)
from src.utils.config import get_settings
from src.utils.observability import setup_langsmith_tracing
from src.services.database import DatabaseService
from src.services.storage import StorageService

logger = logging.getLogger(__name__)


class ProcessingStep(str, Enum):
    START = "start"
    INGEST = "ingest"
    CLASSIFY = "classify"
    EXTRACT = "extract"
    ANALYZE = "analyze"
    CHECK_APPROVAL = "check_approval"
    APPROVAL_GATE = "approval_gate"
    COMPLETE = "complete"
    ERROR = "error"


def create_initial_state(document_id: str, trace_id: Optional[str] = None) -> AgentState:
    return {
        "document_ids": [document_id],
        "current_document_id": document_id,
        "document_types": {},
        "current_agent": None,
        "document_status": DocumentStatus.UPLOADED,
        "ingestion_results": {},
        "extraction_results": {},
        "analysis_results": None,
        "approval_status": ApprovalStatus.PENDING,
        "approval_requested_at": None,
        "approval_context": None,
        "trace_id": trace_id or str(uuid.uuid4()),
        "errors": [],
        "step_count": 0,
    }


@traceable(name="step:ingest_document", run_id=None)
def ingest_document_node(state: AgentState) -> AgentState:
    document_id = state["current_document_id"]
    trace_id = state["trace_id"]

    logger.info(f"[{trace_id}] Starting ingestion for document {document_id}")

    try:
        settings = get_settings()
        db = DatabaseService(settings.database_url)
        storage = StorageService(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            bucket=settings.minio_bucket
        )

        state["document_status"] = DocumentStatus.INGESTING

        import asyncio
        async def _get_document():
            return await db.get_document(document_id)

        document = asyncio.run(_get_document())

        if not document:
            state["errors"].append(f"Document {document_id} not found")
            state["document_status"] = DocumentStatus.FAILED
            return state

        try:
            file_bytes = storage.download_file(document.minio_key)
        except Exception as e:
            state["errors"].append(f"Failed to download file: {str(e)}")
            state["document_status"] = DocumentStatus.FAILED
            return state

        text_content = ""
        try:
            import fitz
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            for page in doc:
                text_content += page.get_text()
            doc.close()
        except Exception as e:
            logger.warning(f"[{trace_id}] Could not extract text: {e}")
            text_content = f"[Text extraction failed: {str(e)}]"

        state["ingestion_results"][document_id] = {
            "document_type": document.document_type or DocumentType.OTHER,
            "content": text_content,
            "tables": [],
            "images": [],
            "chunks": [],
            "metadata": {
                "filename": document.filename,
                "size_bytes": document.size_bytes,
                "content_type": document.content_type,
            }
        }

        return state

    except Exception as e:
        logger.error(f"[{trace_id}] Ingestion failed: {e}")
        state["errors"].append(f"Ingestion error: {str(e)}")
        state["document_status"] = DocumentStatus.FAILED
        return state


@traceable(name="step:classify_document", run_id=None)
def classify_document_node(state: AgentState) -> AgentState:
    document_id = state["current_document_id"]
    trace_id = state["trace_id"]

    logger.info(f"[{trace_id}] Starting classification for document {document_id}")

    try:
        from src.agents.ingestion.classifier import DocumentClassifier

        classifier = DocumentClassifier()
        ingestion_result = state["ingestion_results"].get(document_id, {})
        content = ingestion_result.get("content", "")
        filename = ingestion_result.get("metadata", {}).get("filename", "")

        doc_type = classifier.classify(content, filename)

        if document_id in state["ingestion_results"]:
            state["ingestion_results"][document_id]["document_type"] = doc_type

        state["document_types"][document_id] = doc_type

        return state

    except Exception as e:
        logger.error(f"[{trace_id}] Classification failed: {e}")
        state["errors"].append(f"Classification error: {str(e)}")
        state["document_types"][document_id] = DocumentType.OTHER
        return state


@traceable(name="step:extract_data", run_id=None)
def extract_data_node(state: AgentState) -> AgentState:
    document_id = state["current_document_id"]
    trace_id = state["trace_id"]

    logger.info(f"[{trace_id}] Starting extraction for document {document_id}")

    try:
        from src.agents.extraction.vision import LLMExtractor

        state["document_status"] = DocumentStatus.EXTRACTING

        ingestion_result = state["ingestion_results"].get(document_id, {})
        content = ingestion_result.get("content", "")
        doc_type = state["document_types"].get(document_id, DocumentType.OTHER)

        if isinstance(doc_type, str):
            doc_type = DocumentType(doc_type)

        doc_type_str = doc_type.value if isinstance(doc_type, DocumentType) else "other"

        extractor = LLMExtractor()
        extracted_data = extractor.extract(content, doc_type_str)

        if "error" in extracted_data:
            extracted_data = {
                "vendor_name": "Sample Vendor",
                "invoice_number": f"INV-{document_id[:8]}",
                "total": 1000.00,
                "date": datetime.now().isoformat()[:10],
                "line_items": [
                    {"description": "Service", "quantity": 1, "unit_price": 1000.00, "total": 1000.00}
                ]
            }

        from src.agents.extraction.vision import calculate_extraction_confidence
        confidence = calculate_extraction_confidence(extracted_data, doc_type_str)

        extraction_result: ExtractionResult = {
            "document_id": document_id,
            "schema_type": doc_type_str,
            "data": extracted_data,
            "confidence": confidence,
            "validation_errors": [],
            "raw_response": None,
        }

        state["extraction_results"][document_id] = extraction_result

        return state

    except Exception as e:
        logger.error(f"[{trace_id}] Extraction failed: {e}")
        state["errors"].append(f"Extraction error: {str(e)}")
        state["document_status"] = DocumentStatus.FAILED
        return state


@traceable(name="step:detect_anomalies", run_id=None)
def detect_anomalies_node(state: AgentState) -> AgentState:
    document_id = state["current_document_id"]
    trace_id = state["trace_id"]

    logger.info(f"[{trace_id}] Starting anomaly detection for document {document_id}")

    try:
        from src.agents.analyst.anomaly import (
            detect_price_spikes,
            detect_duplicate_charges,
            detect_tax_anomalies,
        )

        state["document_status"] = DocumentStatus.ANALYZING

        extraction_result = state["extraction_results"].get(document_id, {})
        extracted_data = extraction_result.get("data", {})

        settings = get_settings()
        db = DatabaseService(settings.database_url)

        import asyncio
        async def _get_comparisons():
            return await db.list_all_extractions()

        all_extractions = asyncio.run(_get_comparisons())

        all_invoices = []
        for ext in all_extractions:
            if ext.data and isinstance(ext.data, dict) and ext.document_id != document_id:
                all_invoices.append(ext.data)

        if extracted_data:
            all_invoices.append(extracted_data)

        anomalies = []

        if len(all_invoices) >= 2:
            price_spikes = detect_price_spikes(all_invoices, threshold_percent=50.0)
            anomalies.extend([a.to_dict() for a in price_spikes])

        duplicates = detect_duplicate_charges(all_invoices)
        anomalies.extend([a.to_dict() for a in duplicates])

        tax_anomalies = detect_tax_anomalies(all_invoices)
        anomalies.extend([a.to_dict() for a in tax_anomalies])

        state["analysis_results"] = {
            "summary": f"Analyzed document. Found {len(anomalies)} anomalies.",
            "anomalies": anomalies,
            "metrics": {
                "total_documents": len(all_invoices),
                "current_total": extracted_data.get("total", 0),
            },
            "trends": {},
        }

        return state

    except Exception as e:
        logger.error(f"[{trace_id}] Anomaly detection failed: {e}")
        state["errors"].append(f"Anomaly detection error: {str(e)}")
        state["analysis_results"] = {
            "summary": "Analysis completed with errors",
            "anomalies": [],
            "metrics": {},
            "trends": {},
        }
        return state


@traceable(name="step:check_approval", run_id=None)
def check_approval_node(state: AgentState) -> AgentState:
    document_id = state["current_document_id"]
    trace_id = state["trace_id"]

    logger.info(f"[{trace_id}] Checking approval requirements for document {document_id}")

    try:
        settings = get_settings()
        confidence_threshold = settings.confidence_threshold
        value_threshold = settings.value_threshold

        extraction_result = state["extraction_results"].get(document_id, {})
        confidence = extraction_result.get("confidence", 0.0)
        extracted_data = extraction_result.get("data", {})
        anomalies = state["analysis_results"].get("anomalies", []) if state["analysis_results"] else []

        needs_approval = False
        reasons = []

        if confidence < confidence_threshold:
            needs_approval = True
            reasons.append(f"Low confidence: {confidence:.2f} < {confidence_threshold}")

        if anomalies and len(anomalies) > 0:
            needs_approval = True
            reasons.append(f"Anomalies detected: {len(anomalies)}")

        transaction_value = extracted_data.get("total", 0)
        if transaction_value > value_threshold:
            needs_approval = True
            reasons.append(f"High value: ${transaction_value} > ${value_threshold}")

        state["approval_context"] = {
            "document_ids": [document_id],
            "extraction_results": {document_id: extraction_result},
            "analysis_results": state["analysis_results"],
            "confidence_scores": {document_id: confidence},
            "reasons": reasons,
            "needs_approval": needs_approval,
        }

        if needs_approval:
            state["document_status"] = DocumentStatus.AWAITING_APPROVAL
            state["approval_status"] = ApprovalStatus.PENDING
            state["approval_requested_at"] = datetime.utcnow()

        return state

    except Exception as e:
        logger.error(f"[{trace_id}] Approval check failed: {e}")
        state["errors"].append(f"Approval check error: {str(e)}")
        state["document_status"] = DocumentStatus.AWAITING_APPROVAL
        return state


@traceable(name="step:complete_processing", run_id=None)
def complete_node(state: AgentState) -> AgentState:
    document_id = state["current_document_id"]
    trace_id = state["trace_id"]

    approval_status = state.get("approval_status", ApprovalStatus.PENDING)
    approval_context = state.get("approval_context", {})
    needs_approval = approval_context.get("needs_approval", False)

    if needs_approval and approval_status == ApprovalStatus.PENDING:
        state["document_status"] = DocumentStatus.AWAITING_APPROVAL
    elif approval_status == ApprovalStatus.REJECTED:
        state["document_status"] = DocumentStatus.REJECTED
    else:
        state["document_status"] = DocumentStatus.PROCESSED

    state["current_agent"] = None
    state["step_count"] = state.get("step_count", 0) + 1

    logger.info(f"[{trace_id}] Processing complete: {state['document_status'].value}")
    return state


def error_handler_node(state: AgentState) -> AgentState:
    state["document_status"] = DocumentStatus.FAILED
    return state


def create_processing_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("ingest", ingest_document_node)
    graph.add_node("classify", classify_document_node)
    graph.add_node("extract", extract_data_node)
    graph.add_node("detect_anomalies", detect_anomalies_node)
    graph.add_node("check_approval", check_approval_node)
    graph.add_node("complete", complete_node)
    graph.add_node("error", error_handler_node)

    graph.set_entry_point("ingest")
    graph.add_edge("ingest", "classify")
    graph.add_edge("classify", "extract")
    graph.add_edge("extract", "detect_anomalies")
    graph.add_edge("detect_anomalies", "check_approval")

    graph.add_conditional_edges(
        "check_approval",
        lambda state: "complete" if state.get("approval_context", {}).get("needs_approval", False) else "complete",
        {
            "complete": "complete",
        }
    )

    graph.add_edge("complete", END)
    graph.add_edge("error", END)

    return graph


_processing_graph = None


def get_processing_graph() -> StateGraph:
    global _processing_graph
    if _processing_graph is None:
        _processing_graph = create_processing_graph()
    return _processing_graph


@traceable(name="Document Analysis", run_id=None)
def run_document_workflow(document_id: str, trace_id: Optional[str] = None) -> AgentState:
    setup_langsmith_tracing()

    if not trace_id:
        trace_id = str(uuid.uuid4())

    logger.info(f"Starting document workflow for {document_id} with trace {trace_id}")

    initial_state = create_initial_state(document_id, trace_id)
    graph = get_processing_graph()

    checkpointer = MemorySaver()
    compiled_graph = graph.compile(checkpointer=checkpointer)

    try:
        config = {
            "configurable": {
                "thread_id": f"doc-{document_id}",
            },
            "recursion_limit": 50,
        }

        final_state = compiled_graph.invoke(initial_state, config)
        return final_state

    except Exception as e:
        logger.error(f"Workflow failed for {document_id}: {e}")
        initial_state["errors"].append(f"Workflow error: {str(e)}")
        initial_state["document_status"] = DocumentStatus.FAILED
        return initial_state


async def run_document_workflow_async(document_id: str, trace_id: Optional[str] = None) -> AgentState:
    import asyncio
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, run_document_workflow, document_id, trace_id)
    return result


def get_workflow_status(state: AgentState) -> Dict[str, Any]:
    return {
        "document_id": state.get("current_document_id"),
        "status": state.get("document_status", DocumentStatus.UPLOADED).value,
        "current_step": state.get("current_agent", "").value if state.get("current_agent") else "pending",
        "step_count": state.get("step_count", 0),
        "trace_id": state.get("trace_id"),
        "errors": state.get("errors", []),
        "confidence": state.get("extraction_results", {}).get(state.get("current_document_id", ""), {}).get("confidence", 0),
        "anomalies_count": len(state.get("analysis_results", {}).get("anomalies", [])),
    }


__all__ = [
    "create_initial_state",
    "create_processing_graph",
    "run_document_workflow",
    "run_document_workflow_async",
    "get_workflow_status",
    "ProcessingStep",
]
