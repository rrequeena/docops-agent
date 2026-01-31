"""
Tests for the extraction agent.
"""

import pytest
from src.agents.extraction.agent import ExtractorAgent
from src.agents.extraction.schemas import (
    get_extraction_schema,
    InvoiceExtraction,
    ContractExtraction,
    validate_extraction_data,
)
from src.agents.extraction.validator import ExtractionValidator, validate_extraction
from src.agents.extraction.vision import calculate_extraction_confidence
from src.agents.state import AgentType, DocumentType


class TestExtractionSchemas:
    """Test cases for extraction schemas."""

    def test_get_invoice_schema(self):
        """Test getting invoice schema."""
        schema = get_extraction_schema("invoice")
        assert schema == InvoiceExtraction

    def test_get_contract_schema(self):
        """Test getting contract schema."""
        schema = get_extraction_schema("contract")
        assert schema == ContractExtraction

    def test_get_unknown_schema(self):
        """Test getting unknown schema returns generic."""
        from src.agents.extraction.schemas import GenericExtraction
        schema = get_extraction_schema("unknown")
        assert schema == GenericExtraction

    def test_invoice_validation_valid(self):
        """Test invoice validation with valid data."""
        data = {
            "invoice_number": "12345",
            "vendor_name": "ABC Corp",
            "total": 500.00,
            "currency": "USD",
        }

        is_valid, errors = validate_extraction_data(data, "invoice")
        assert is_valid is True
        assert len(errors) == 0

    def test_invoice_validation_invalid(self):
        """Test invoice validation with invalid data."""
        data = {
            "invoice_number": "12345",
            "line_items": "not a list",  # Should be a list
        }

        is_valid, errors = validate_extraction_data(data, "invoice")
        assert is_valid is False


class TestExtractionValidator:
    """Test cases for ExtractionValidator."""

    def test_validate_valid_data(self):
        """Test validation with valid data."""
        validator = ExtractionValidator()

        data = {
            "invoice_number": "12345",
            "vendor_name": "ABC Corp",
            "total": 500.00,
        }

        is_valid, errors = validator.validate(data, "invoice")
        assert is_valid is True

    def test_validate_invalid_data(self):
        """Test validation with invalid data."""
        validator = ExtractionValidator()

        data = {
            "line_items": "invalid",  # Should be list
        }

        is_valid, errors = validator.validate(data, "invoice")
        assert is_valid is False
        assert len(errors) > 0

    def test_get_field_completeness(self):
        """Test field completeness calculation."""
        validator = ExtractionValidator()

        data = {
            "invoice_number": "12345",
            "vendor_name": "ABC Corp",
            # Missing many fields
        }

        completeness = validator.get_field_completeness(data, "invoice")
        assert 0 < completeness < 1

    def test_validate_invoice_business_rules(self):
        """Test business rule validation for invoices."""
        validator = ExtractionValidator()

        # Total doesn't match line items + tax
        data = {
            "invoice_number": "12345",
            "line_items": [
                {"description": "Item", "quantity": 1, "unit_price": 100, "amount": 100}
            ],
            "subtotal": 100,
            "tax_amount": 10,
            "total": 200,  # Should be 110
        }

        errors = validator.validate_business_rules(data, "invoice")
        assert len(errors) > 0

    def test_validate_invoice_rules_passes(self):
        """Test business rule validation passes."""
        validator = ExtractionValidator()

        data = {
            "invoice_number": "12345",
            "line_items": [
                {"description": "Item", "quantity": 1, "unit_price": 100, "amount": 100}
            ],
            "subtotal": 100,
            "tax_amount": 10,
            "total": 110,
        }

        errors = validator.validate_business_rules(data, "invoice")
        assert len(errors) == 0


class TestValidateExtraction:
    """Test cases for comprehensive extraction validation."""

    def test_validate_extraction_complete(self):
        """Test comprehensive validation with complete data."""
        data = {
            "invoice_number": "12345",
            "vendor_name": "ABC Corp",
            "total": 500.00,
            "currency": "USD",
            "line_items": [],
        }

        is_valid, errors, completeness = validate_extraction(data, "invoice")
        assert is_valid is True
        assert completeness > 0.8

    def test_validate_extraction_incomplete(self):
        """Test comprehensive validation with incomplete data."""
        data = {
            "invoice_number": "12345",
            # Missing other fields
        }

        is_valid, errors, completeness = validate_extraction(data, "invoice")
        # Should still be valid schema-wise but low completeness
        assert completeness < 0.5


class TestConfidenceScoring:
    """Test cases for confidence scoring."""

    def test_calculate_confidence_complete(self):
        """Test confidence with complete data."""
        data = {
            "invoice_number": "12345",
            "vendor_name": "ABC Corp",
            "total": 500.00,
            "currency": "USD",
            "line_items": [{"description": "Item", "amount": 100}],
        }

        confidence = calculate_extraction_confidence(data, "invoice")
        assert confidence > 0.8

    def test_calculate_confidence_empty(self):
        """Test confidence with empty data."""
        data = {}

        confidence = calculate_extraction_confidence(data, "invoice")
        assert confidence == 0.0

    def test_calculate_confidence_with_error(self):
        """Test confidence with error in data."""
        data = {
            "invoice_number": "12345",
            "error": "Some extraction error",
        }

        confidence = calculate_extraction_confidence(data, "invoice")
        assert confidence < 0.5


class TestExtractorAgent:
    """Test cases for ExtractorAgent."""

    def test_initialization(self):
        """Test extractor agent initialization."""
        agent = ExtractorAgent()
        assert agent.name == "Extractor"
        assert agent.agent_type == AgentType.EXTRACTION

    def test_system_prompt(self):
        """Test extractor agent system prompt."""
        agent = ExtractorAgent()
        prompt = agent.get_system_prompt()
        assert "Extractor Agent" in prompt
        assert "confidence" in prompt.lower()

    def test_validate_state(self):
        """Test state validation."""
        agent = ExtractorAgent()

        valid_state = {
            "current_document_id": "doc-001",
            "ingestion_results": {"doc-001": {}},
        }
        invalid_state = {"current_document_id": "doc-001"}

        assert agent.validate_state(valid_state) is True
        assert agent.validate_state(invalid_state) is False
