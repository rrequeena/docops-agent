"""
Vision extraction wrapper using Gemini for document extraction.
"""

import logging
import json
from typing import Dict, Any, Optional

import google.generativeai as genai

from src.agents.extraction.schemas import (
    get_extraction_schema,
    SCHEMA_MAP,
)

logger = logging.getLogger(__name__)


class VisionExtractor:
    """Extracts structured data from documents using Gemini vision."""

    def __init__(self, model_name: str = "gemini-1.5-flash"):
        self.model_name = model_name
        self.model = None
        self._initialize_model()

    def _initialize_model(self):
        """Initialize the Gemini model."""
        from src.utils.config import get_settings
        settings = get_settings()

        if not settings.google_api_key:
            logger.warning("GOOGLE_API_KEY not configured")
            self.model = None
            return

        genai.configure(api_key=settings.google_api_key)
        try:
            self.model = genai.GenerativeModel(self.model_name)
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini model: {e}")
            self.model = None

    def extract(
        self,
        image_bytes: bytes,
        document_type: str,
        prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Extract structured data from an image using vision.

        Args:
            image_bytes: Image data as bytes
            document_type: Type of document
            prompt: Optional custom prompt

        Returns:
            Extracted data dictionary
        """
        if not self.model:
            logger.error("Gemini model not initialized")
            return {"error": "Model not available"}

        try:
            # Get the schema for the document type
            schema = get_extraction_schema(document_type)
            schema_json = schema.model_json_schema()

            # Build prompt
            if prompt is None:
                prompt = f"""Analyze this document and extract the information into a structured format.

Document type: {document_type}

Extract all relevant fields according to this schema:
{json.dumps(schema_json, indent=2)}

Return ONLY valid JSON matching the schema. If a field is not present in the document, use null for optional fields."""

            # Generate content
            response = self.model.generate_content([
                prompt,
                {"mime_type": "image/jpeg", "data": image_bytes}
            ])

            # Parse response
            return self._parse_response(response.text, document_type)

        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return {"error": str(e)}

    def extract_from_pdf_page(
        self,
        pdf_bytes: bytes,
        page_number: int,
        document_type: str,
    ) -> Dict[str, Any]:
        """
        Extract from a PDF page by converting to image.

        Args:
            pdf_bytes: PDF file bytes
            page_number: Page number to extract
            document_type: Type of document

        Returns:
            Extracted data
        """
        # Convert PDF page to image (simplified - would need PDF rendering)
        # For now, return error indicating PDF needs conversion
        return {"error": "PDF page extraction requires image conversion"}

    def extract_text_based(
        self,
        text: str,
        document_type: str,
    ) -> Dict[str, Any]:
        """
        Extract structured data from text (for text-based PDFs).

        Args:
            text: Extracted text from document
            document_type: Type of document

        Returns:
            Extracted data
        """
        if not self.model:
            logger.error("Gemini model not initialized")
            return {"error": "Model not available"}

        try:
            schema = get_extraction_schema(document_type)
            schema_json = schema.model_json_schema()

            prompt = f"""Analyze this document text and extract the information into a structured format.

Document type: {document_type}

Text content:
{text}

Extract all relevant fields according to this schema:
{json.dumps(schema_json, indent=2)}

Return ONLY valid JSON matching the schema. If a field is not present in the document, use null for optional fields."""

            response = self.model.generate_content(prompt)
            return self._parse_response(response.text, document_type)

        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            return {"error": str(e)}

    def _parse_response(
        self,
        response_text: str,
        document_type: str,
    ) -> Dict[str, Any]:
        """
        Parse the LLM response into structured data.

        Args:
            response_text: Raw response from LLM
            document_type: Document type

        Returns:
            Parsed data dictionary
        """
        try:
            # Try to extract JSON from response
            # Handle markdown code blocks
            response_text = response_text.strip()
            if response_text.startswith("```"):
                # Remove code block markers
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])

            # Parse JSON
            data = json.loads(response_text)
            return data

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            return {
                "error": "Failed to parse extraction response",
                "raw_response": response_text,
            }


class LLMExtractor:
    """Extracts structured data using LLM text generation."""

    def __init__(self, model_name: str = "gemini-1.5-flash"):
        self.model_name = model_name
        self.model = None
        self._initialize_model()

    def _initialize_model(self):
        """Initialize the Gemini model."""
        from src.utils.config import get_settings
        settings = get_settings()

        if not settings.google_api_key:
            logger.warning("GOOGLE_API_KEY not configured")
            self.model = None
            return

        genai.configure(api_key=settings.google_api_key)
        try:
            self.model = genai.GenerativeModel(self.model_name)
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini model: {e}")
            self.model = None

    def extract(
        self,
        text: str,
        document_type: str,
    ) -> Dict[str, Any]:
        """
        Extract structured data from text using LLM.

        Args:
            text: Document text
            document_type: Type of document

        Returns:
            Extracted data
        """
        if not self.model:
            return {"error": "Model not available"}

        try:
            schema = get_extraction_schema(document_type)
            schema_json = schema.model_json_schema()

            prompt = f"""Extract structured data from this {document_type} text.

Text:
{text}

Schema:
{json.dumps(schema_json, indent=2)}

Return ONLY valid JSON."""

            response = self.model.generate_content(prompt)

            # Parse response
            response_text = response.text.strip()
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])

            return json.loads(response_text)

        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return {"error": str(e)}


def calculate_extraction_confidence(
    extracted_data: Dict[str, Any],
    document_type: str,
) -> float:
    """
    Calculate confidence score for extraction.

    Args:
        extracted_data: Extracted data
        document_type: Document type

    Returns:
        Confidence score 0-1
    """
    schema = get_extraction_schema(document_type)
    fields = schema.model_fields

    if not fields:
        return 0.5

    filled = 0
    for field_name in fields:
        if field_name in extracted_data and extracted_data[field_name] is not None:
            value = extracted_data[field_name]
            if isinstance(value, str) and value.strip():
                filled += 1
            elif isinstance(value, (list, dict)) and len(value) > 0:
                filled += 1
            elif value is not None:
                filled += 1

    base_confidence = filled / len(fields)

    # Penalize for errors
    if "error" in extracted_data:
        base_confidence *= 0.5

    # Penalize for empty raw response
    if not extracted_data or len(extracted_data) == 0:
        base_confidence = 0.0

    return min(max(base_confidence, 0.0), 1.0)
