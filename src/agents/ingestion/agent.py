"""
Ingestion Agent - Handles document ingestion, classification, and parsing.
"""

import uuid
import logging
from typing import Dict, Any, Optional

from src.agents.base import BaseAgent, create_agent_node
from src.agents.state import (
    AgentState,
    AgentType,
    DocumentStatus,
    DocumentType,
    IngestionResult,
    IngestionState,
)
from src.agents.ingestion.classifier import DocumentClassifier
from src.agents.ingestion.parser import DocumentParser
from src.agents.ingestion.chunker import TextChunker

logger = logging.getLogger(__name__)


class IngestionAgent(BaseAgent):
    """Agent responsible for document ingestion and preprocessing."""

    def __init__(self):
        super().__init__("Ingestion", AgentType.INGESTION)
        self.classifier = DocumentClassifier()
        self.parser = DocumentParser()
        self.chunker = TextChunker()

    def get_system_prompt(self) -> str:
        return """You are the Ingestion Agent for DocOps, a multi-agent document intelligence system.

Your responsibilities:
1. Classify incoming documents by type (invoice, contract, form, receipt, etc.)
2. Parse documents to extract text, tables, and images
3. Chunk text for vector storage and RAG
4. Extract metadata from documents

Document types to classify:
- invoice: Bills, receipts requesting payment
- contract: Legal agreements
- form: Application forms, surveys
- receipt: Transaction receipts
- letter: Correspondence
- memo: Internal memoranda
- report: Analytical reports
- other: Unclassified documents

Always provide accurate classification and comprehensive parsing."""

    def process(self, state: AgentState) -> AgentState:
        """Process documents through the ingestion pipeline."""
        current_doc_id = state.get("current_document_id")
        if not current_doc_id:
            logger.warning("No current document ID in state")
            return state

        # Get document file path from storage
        file_path = self._get_file_path(current_doc_id)
        file_bytes = self._get_file_bytes(current_doc_id)

        if not file_bytes:
            state["errors"].append(f"Could not load file for document {current_doc_id}")
            return state

        # Step 1: Parse document
        parse_result = self.parser.parse(file_path, file_bytes)
        if "error" in parse_result:
            state["errors"].append(f"Parse error: {parse_result['error']}")
            return state

        # Step 2: Classify document
        doc_type = self.classifier.classify(parse_result.get("text", ""), file_path)

        # Step 3: Chunk text
        chunks = self.chunker.chunk_text(
            parse_result.get("text", ""),
            metadata={"document_id": current_doc_id, "document_type": doc_type},
        )

        # Build ingestion result
        ingestion_result: IngestionResult = {
            "document_type": doc_type,
            "content": parse_result.get("text", ""),
            "tables": parse_result.get("tables", []),
            "images": parse_result.get("images", []),
            "chunks": [c["text"] for c in chunks],
            "metadata": {
                "file_path": file_path,
                "page_count": parse_result.get("page_count", 0),
                "chunk_count": len(chunks),
                **parse_result.get("metadata", {}),
            },
        }

        # Store result
        if "ingestion_results" not in state:
            state["ingestion_results"] = {}
        state["ingestion_results"][current_doc_id] = ingestion_result

        # Update document type mapping
        if "document_types" not in state:
            state["document_types"] = {}
        state["document_types"][current_doc_id] = doc_type

        # Mark as complete
        state["document_status"] = DocumentStatus.EXTRACTING

        logger.info(f"Ingested document {current_doc_id} as {doc_type}")
        return state

    def _get_file_path(self, document_id: str) -> str:
        """Get file path for document ID."""
        # In production, this would query the database or storage
        return f"documents/{document_id}"

    def _get_file_bytes(self, document_id: str) -> Optional[bytes]:
        """Get file bytes for document ID."""
        # In production, this would load from MinIO or file storage
        # Placeholder implementation
        return None

    def validate_state(self, state: AgentState) -> bool:
        """Validate state has required fields for ingestion."""
        return "current_document_id" in state

    def classify_document(
        self,
        text: str,
        filename: str = "",
    ) -> DocumentType:
        """Classify a document by its text content."""
        return self.classifier.classify(text, filename)

    def parse_document(
        self,
        file_path: str,
        file_bytes: bytes,
    ) -> Dict[str, Any]:
        """Parse a document and extract content."""
        return self.parser.parse(file_path, file_bytes)

    def chunk_for_rag(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> list:
        """Chunk text for RAG."""
        return self.chunker.chunk_text(text, metadata)


# Create LangGraph node
ingestion_node = create_agent_node(IngestionAgent())
