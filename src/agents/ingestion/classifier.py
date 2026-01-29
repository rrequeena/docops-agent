"""
Document classifier for the ingestion agent.
"""

import logging
from typing import Optional, Dict, Any
import google.generativeai as genai
from io import BytesIO

from src.agents.state import DocumentType

logger = logging.getLogger(__name__)

# Document type keywords for rule-based classification
DOCUMENT_KEYWORDS = {
    DocumentType.INVOICE: [
        "invoice", "bill to", "billing", "total due", "payment terms",
        "invoice number", "inv#", "subtotal", "tax", "vendor",
    ],
    DocumentType.CONTRACT: [
        "contract", "agreement", "parties", "hereby", "whereas",
        "terms and conditions", "signatures", "effective date",
    ],
    DocumentType.FORM: [
        "form", "application", "please complete", "fields",
        "section", "check the box", "select one",
    ],
    DocumentType.RECEIPT: [
        "receipt", "thank you for", "transaction", "paid",
        "payment method", "cash", "card", "change",
    ],
    DocumentType.LETTER: [
        "dear", "sincerely", "regards", "to whom it may concern",
        "re:", "subject",
    ],
    DocumentType.MEMO: [
        "memo", "internal", "from:", "to:", "date:",
        "re:", "action required", "FYI",
    ],
    DocumentType.REPORT: [
        "report", "executive summary", "introduction", "conclusion",
        "methodology", "findings", "recommendations",
    ],
}


class DocumentClassifier:
    """Classifies documents into types using keyword matching and LLM."""

    def __init__(self, gemini_model=None):
        self.gemini_model = gemini_model

    def classify(self, text: str, filename: str = "") -> DocumentType:
        """
        Classify a document by its content.

        Args:
            text: Extracted text from the document
            filename: Original filename for additional context

        Returns:
            DocumentType classification
        """
        # First try rule-based classification
        doc_type = self._classify_by_keywords(text)
        if doc_type != DocumentType.OTHER:
            return doc_type

        # Try LLM classification if available
        if self.gemini_model:
            return self._classify_with_llm(text, filename)

        # Default to OTHER
        return DocumentType.OTHER

    def _classify_by_keywords(self, text: str) -> DocumentType:
        """
        Classify based on keyword matching.

        Args:
            text: Document text

        Returns:
            DocumentType or OTHER if no match
        """
        text_lower = text.lower()
        scores = {}

        for doc_type, keywords in DOCUMENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[doc_type] = score

        if not scores:
            return DocumentType.OTHER

        # Return the type with highest score
        return max(scores, key=scores.get)

    def _classify_with_llm(
        self,
        text: str,
        filename: str,
    ) -> DocumentType:
        """
        Classify using LLM for ambiguous cases.

        Args:
            text: Document text
            filename: Original filename

        Returns:
            DocumentType classification
        """
        try:
            # Take first 1000 chars for classification
            sample_text = text[:1000]

            prompt = f"""Classify this document into one of these types:
- invoice
- contract
- form
- receipt
- letter
- memo
- report
- other

Filename: {filename}
First 1000 characters of text:
{sample_text}

Respond with only the document type in lowercase."""

            response = self.gemini_model.generate_content(prompt)
            result = response.text.strip().lower()

            # Map response to DocumentType
            type_map = {
                "invoice": DocumentType.INVOICE,
                "contract": DocumentType.CONTRACT,
                "form": DocumentType.FORM,
                "receipt": DocumentType.RECEIPT,
                "letter": DocumentType.LETTER,
                "memo": DocumentType.MEMO,
                "report": DocumentType.REPORT,
                "other": DocumentType.OTHER,
            }

            return type_map.get(result, DocumentType.OTHER)

        except Exception as e:
            logger.warning(f"LLM classification failed: {e}")
            return DocumentType.OTHER

    def get_confidence(self, text: str, doc_type: DocumentType) -> float:
        """
        Get classification confidence score.

        Args:
            text: Document text
            doc_type: Predicted document type

        Returns:
            Confidence score between 0 and 1
        """
        text_lower = text.lower()
        keywords = DOCUMENT_KEYWORDS.get(doc_type, [])
        matches = sum(1 for kw in keywords if kw in text_lower)

        if not keywords:
            return 0.5

        # Normalize to 0-1 range
        confidence = min(matches / len(keywords), 1.0)
        return confidence
