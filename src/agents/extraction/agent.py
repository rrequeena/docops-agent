"""
Extractor Agent - Extracts structured data from documents.
"""

import logging
from typing import Dict, Any, Optional

from src.agents.base import BaseAgent, create_agent_node
from src.agents.state import (
    AgentState,
    AgentType,
    DocumentStatus,
    DocumentType,
    ExtractionResult,
)
from src.agents.extraction.schemas import get_extraction_schema
from src.agents.extraction.validator import ExtractionValidator, validate_extraction
from src.agents.extraction.vision import VisionExtractor, LLMExtractor, calculate_extraction_confidence

logger = logging.getLogger(__name__)


class ExtractorAgent(BaseAgent):
    """Agent responsible for extracting structured data from documents."""

    def __init__(self):
        super().__init__("Extractor", AgentType.EXTRACTION)
        self.vision_extractor = VisionExtractor()
        self.llm_extractor = LLMExtractor()
        self.validator = ExtractionValidator()

    def get_system_prompt(self) -> str:
        return """You are the Extractor Agent for DocOps, a multi-agent document intelligence system.

Your responsibilities:
1. Extract structured data from document content
2. Map extracted data to appropriate schemas (Invoice, Contract, Receipt, etc.)
3. Validate extracted data against schemas
4. Calculate confidence scores for extractions
5. Flag low-confidence extractions for review

You have access to:
- Vision extraction for image-based documents
- LLM extraction for text-based documents
- Schema validation
- Confidence scoring

Always validate extractions and provide confidence scores."""

    def process(self, state: AgentState) -> AgentState:
        """Process documents through the extraction pipeline."""
        current_doc_id = state.get("current_document_id")
        if not current_doc_id:
            logger.warning("No current document ID in state")
            return state

        # Get ingestion results
        ingestion_results = state.get("ingestion_results", {})
        ingestion_result = ingestion_results.get(current_doc_id)

        if not ingestion_result:
            state["errors"].append(f"No ingestion result for document {current_doc_id}")
            return state

        # Get document type
        document_type = ingestion_result.get("document_type", DocumentType.OTHER)
        if isinstance(document_type, str):
            document_type = DocumentType(document_type)

        # Get content
        content = ingestion_result.get("content", "")
        if not content:
            # Try to use images if no text
            images = ingestion_result.get("images", [])
            if images:
                content = "[Image-based document - use vision extraction]"
            else:
                state["errors"].append(f"No content for document {current_doc_id}")
                return state

        # Extract data
        extracted_data = self._extract_data(content, document_type, ingestion_result)

        # Validate
        doc_type_str = document_type.value if isinstance(document_type, DocumentType) else str(document_type)
        is_valid, validation_errors, completeness = validate_extraction(
            extracted_data, doc_type_str
        )

        # Calculate confidence
        confidence = calculate_extraction_confidence(extracted_data, doc_type_str)

        # Determine if retry is needed
        needs_retry = confidence < 0.7 or not is_valid

        # Build extraction result
        extraction_result: ExtractionResult = {
            "document_id": current_doc_id,
            "schema_type": doc_type_str,
            "data": extracted_data,
            "confidence": confidence,
            "validation_errors": validation_errors,
            "raw_response": None,
        }

        # Store result
        if "extraction_results" not in state:
            state["extraction_results"] = {}
        state["extraction_results"][current_doc_id] = extraction_result

        # Update status
        state["document_status"] = DocumentStatus.ANALYZING

        logger.info(
            f"Extracted from document {current_doc_id}: "
            f"confidence={confidence:.2f}, valid={is_valid}"
        )
        return state

    def _extract_data(
        self,
        content: str,
        document_type: DocumentType,
        ingestion_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Extract structured data from content."""
        doc_type_str = document_type.value if isinstance(document_type, DocumentType) else str(document_type)

        # Check if we have images and should use vision
        images = ingestion_result.get("images", [])
        has_images = len(images) > 0

        if has_images and not content.strip():
            # Use vision extraction for image-only documents
            logger.info(f"Using vision extraction for document type {doc_type_str}")
            return self.vision_extractor.extract_from_pdf_page(
                b"",  # Would need actual image bytes
                0,
                doc_type_str,
            )

        # Use LLM extraction for text-based documents
        logger.info(f"Using LLM extraction for document type {doc_type_str}")
        return self.llm_extractor.extract(content, doc_type_str)

    def extract_with_vision(
        self,
        image_bytes: bytes,
        document_type: str,
    ) -> Dict[str, Any]:
        """Extract using vision model."""
        return self.vision_extractor.extract(image_bytes, document_type)

    def extract_with_llm(
        self,
        text: str,
        document_type: str,
    ) -> Dict[str, Any]:
        """Extract using LLM."""
        return self.llm_extractor.extract(text, document_type)

    def validate_schema(
        self,
        data: Dict[str, Any],
        document_type: str,
    ) -> tuple[bool, list]:
        """Validate extraction against schema."""
        return self.validator.validate(data, document_type)

    def calculate_confidence(
        self,
        extracted_data: Dict[str, Any],
        document_type: str,
    ) -> float:
        """Calculate confidence score."""
        return calculate_extraction_confidence(extracted_data, document_type)

    def validate_state(self, state: AgentState) -> bool:
        """Validate state has required fields."""
        return (
            "current_document_id" in state and
            "ingestion_results" in state
        )


# Create LangGraph node
extraction_node = create_agent_node(ExtractorAgent())
