"""
Tests for the ingestion agent.
"""

import pytest
from src.agents.ingestion.agent import IngestionAgent
from src.agents.ingestion.classifier import DocumentClassifier
from src.agents.ingestion.parser import DocumentParser
from src.agents.ingestion.chunker import TextChunker
from src.agents.state import AgentType, DocumentType


class TestDocumentClassifier:
    """Test cases for DocumentClassifier."""

    def test_classify_invoice_by_keywords(self):
        """Test invoice classification by keywords."""
        classifier = DocumentClassifier()

        invoice_text = """
        INVOICE #12345
        Bill To: Customer Name
        Total Due: $500.00
        Payment Terms: Net 30
        """

        doc_type = classifier.classify(invoice_text, "document.pdf")
        assert doc_type == DocumentType.INVOICE

    def test_classify_contract_by_keywords(self):
        """Test contract classification by keywords."""
        classifier = DocumentClassifier()

        contract_text = """
        CONTRACT AGREEMENT
        This Agreement is entered into between Party A and Party B
        WHEREAS the parties agree to the following terms
        """

        doc_type = classifier.classify(contract_text, "agreement.pdf")
        assert doc_type == DocumentType.CONTRACT

    def test_classify_receipt_by_keywords(self):
        """Test receipt classification by keywords."""
        classifier = DocumentClassifier()

        receipt_text = """
        RECEIPT
        Thank you for your purchase
        Paid: $25.00
        Payment Method: Credit Card
        """

        doc_type = classifier.classify(receipt_text, "receipt.pdf")
        assert doc_type == DocumentType.RECEIPT

    def test_classify_memo_by_keywords(self):
        """Test memo classification by keywords."""
        classifier = DocumentClassifier()

        memo_text = """
        MEMO
        From: John Doe
        To: Jane Smith
        Date: January 15, 2024
        Re: Project Update
        Action Required: Review attached
        """

        doc_type = classifier.classify(memo_text, "memo.pdf")
        assert doc_type == DocumentType.MEMO

    def test_classify_returns_other_for_unknown(self):
        """Test that unknown documents return OTHER type."""
        classifier = DocumentClassifier()

        unknown_text = "This is just some random text without specific structure"

        doc_type = classifier.classify(unknown_text, "file.txt")
        assert doc_type == DocumentType.OTHER

    def test_get_confidence(self):
        """Test confidence scoring."""
        classifier = DocumentClassifier()

        invoice_text = "Invoice #12345 Total Due: $500.00"

        confidence = classifier.get_confidence(invoice_text, DocumentType.INVOICE)
        assert confidence > 0


class TestDocumentParser:
    """Test cases for DocumentParser."""

    def test_parse_text_file(self):
        """Test parsing text files."""
        parser = DocumentParser()

        text_content = b"This is a test document"
        result = parser.parse("test.txt", text_content)

        assert "text" in result
        assert "This is a test document" in result["text"]

    def test_get_extension(self):
        """Test file extension extraction."""
        parser = DocumentParser()

        assert parser._get_extension("document.pdf") == ".pdf"
        assert parser._get_extension("image.jpg") == ".jpg"
        assert parser._get_extension("doc.PNG") == ".png"


class TestTextChunker:
    """Test cases for TextChunker."""

    def test_chunk_text_basic(self):
        """Test basic text chunking."""
        chunker = TextChunker(chunk_size=100, chunk_overlap=20)

        text = "A" * 200  # 200 character text
        chunks = chunker.chunk_text(text)

        assert len(chunks) > 1

    def test_chunk_text_returns_metadata(self):
        """Test that chunks include metadata."""
        chunker = TextChunker(chunk_size=100, chunk_overlap=20)

        text = "Sample text for chunking"
        chunks = chunker.chunk_text(text, metadata={"doc_id": "test"})

        assert len(chunks) > 0
        assert "metadata" in chunks[0]
        assert chunks[0]["metadata"]["doc_id"] == "test"

    def test_chunk_by_paragraphs(self):
        """Test paragraph-based chunking."""
        chunker = TextChunker(chunk_size=50, chunk_overlap=10)

        text = "Paragraph one here.\n\nParagraph two here.\n\nParagraph three here."
        chunks = chunker.chunk_by_paragraphs(text)

        assert len(chunks) >= 1  # At least one chunk

    def test_clean_text(self):
        """Test text cleaning."""
        chunker = TextChunker()

        dirty_text = "Multiple   spaces\n\nand\ttabs"
        cleaned = chunker._clean_text(dirty_text)

        assert "  " not in cleaned


class TestIngestionAgent:
    """Test cases for IngestionAgent."""

    def test_initialization(self):
        """Test ingestion agent initialization."""
        agent = IngestionAgent()
        assert agent.name == "Ingestion"
        assert agent.agent_type == AgentType.INGESTION

    def test_system_prompt(self):
        """Test ingestion agent system prompt."""
        agent = IngestionAgent()
        prompt = agent.get_system_prompt()
        assert "Ingestion Agent" in prompt
        assert "classify" in prompt.lower()

    def test_validate_state(self):
        """Test state validation."""
        agent = IngestionAgent()

        valid_state = {"current_document_id": "doc-001"}
        invalid_state = {}

        assert agent.validate_state(valid_state) is True
        assert agent.validate_state(invalid_state) is False
