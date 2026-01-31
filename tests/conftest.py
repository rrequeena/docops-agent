"""
Test fixtures for agent tests.
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime


@pytest.fixture
def sample_agent_state():
    """Sample agent state for testing."""
    return {
        "document_ids": ["doc-001", "doc-002"],
        "current_document_id": "doc-001",
        "document_types": {},
        "current_agent": None,
        "document_status": "uploaded",
        "ingestion_results": {},
        "extraction_results": {},
        "analysis_results": None,
        "approval_status": "pending",
        "approval_requested_at": None,
        "approval_context": None,
        "trace_id": "test-trace-001",
        "errors": [],
        "step_count": 0,
    }


@pytest.fixture
def sample_ingestion_result():
    """Sample ingestion result for testing."""
    return {
        "document_type": "invoice",
        "content": "Invoice #12345\nVendor: ABC Corp\nTotal: $500.00",
        "tables": [],
        "images": [],
        "chunks": ["Invoice #12345", "Vendor: ABC Corp", "Total: $500.00"],
        "metadata": {"page_count": 1, "chunk_count": 3},
    }


@pytest.fixture
def sample_extraction_result():
    """Sample extraction result for testing."""
    return {
        "document_id": "doc-001",
        "schema_type": "invoice",
        "data": {
            "invoice_number": "12345",
            "vendor_name": "ABC Corp",
            "total": 500.00,
            "currency": "USD",
        },
        "confidence": 0.85,
        "validation_errors": [],
        "raw_response": None,
    }


@pytest.fixture
def mock_gemini_model():
    """Mock Gemini model for testing."""
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '{"invoice_number": "12345", "vendor_name": "ABC Corp"}'
    mock_model.generate_content.return_value = mock_response
    return mock_model


@pytest.fixture
def sample_invoice_text():
    """Sample invoice text for testing."""
    return """
    INVOICE

    Invoice Number: INV-2024-001
    Invoice Date: January 15, 2024
    Due Date: February 15, 2024

    Vendor:
    ABC Corporation
    123 Business Street
    New York, NY 10001

    Bill To:
    XYZ Company
    456 Client Ave
    Los Angeles, CA 90001

    Items:
    Description         Quantity    Unit Price    Amount
    Product A           10          $25.00        $250.00
    Product B           5           $50.00        $250.00

    Subtotal: $500.00
    Tax (10%): $50.00
    Total: $550.00

    Payment Terms: Net 30
    """


@pytest.fixture
def sample_contract_text():
    """Sample contract text for testing."""
    return """
    CONTRACT AGREEMENT

    This Agreement is entered into as of January 1, 2024

    BETWEEN:
    Party A: ABC Corporation
    Party B: XYZ Company

    TERMS AND CONDITIONS:
    1. The term of this agreement is 12 months
    2. The total contract value is $100,000
    3. Payment shall be made monthly

    SIGNATURES:
    _________________          _________________
    Party A                   Party B
    """


@pytest.fixture
def sample_receipt_text():
    """Sample receipt text for testing."""
    return """
    RECEIPT

    Transaction Date: January 20, 2024
    Receipt #: RCP-98765

    Vendor: Coffee Shop
    123 Main Street

    Items:
    Coffee           $4.50
    Muffin           $3.00
    Water            $1.50

    Subtotal: $9.00
    Tax: $0.72
    Total: $9.72

    Payment Method: Credit Card
    """
