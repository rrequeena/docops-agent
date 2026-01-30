"""
Extraction schemas for different document types.
"""

from typing import List, Optional, Any
from pydantic import BaseModel, Field
from datetime import date


class LineItem(BaseModel):
    """Represents a line item in an invoice or receipt."""
    description: str
    quantity: float = 1.0
    unit_price: float
    amount: float
    tax_rate: Optional[float] = 0.0


class InvoiceExtraction(BaseModel):
    """Schema for invoice extraction."""
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    vendor_name: Optional[str] = None
    vendor_address: Optional[str] = None
    vendor_tax_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_address: Optional[str] = None
    line_items: List[LineItem] = Field(default_factory=list)
    subtotal: Optional[float] = None
    tax_amount: Optional[float] = None
    tax_rate: Optional[float] = None
    total: Optional[float] = None
    currency: str = "USD"
    payment_terms: Optional[str] = None
    due_date: Optional[date] = None
    notes: Optional[str] = None


class ContractExtraction(BaseModel):
    """Schema for contract extraction."""
    contract_number: Optional[str] = None
    contract_date: Optional[date] = None
    effective_date: Optional[date] = None
    expiration_date: Optional[date] = None
    parties: List[str] = Field(default_factory=list)
    title: Optional[str] = None
    clauses: List[dict] = Field(default_factory=list)
    obligations: List[str] = Field(default_factory=list)
    terms: Optional[str] = None
    value: Optional[float] = None
    currency: Optional[str] = "USD"


class ReceiptExtraction(BaseModel):
    """Schema for receipt extraction."""
    receipt_number: Optional[str] = None
    transaction_date: Optional[date] = None
    vendor_name: Optional[str] = None
    vendor_address: Optional[str] = None
    items: List[dict] = Field(default_factory=list)
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    tip: Optional[float] = None
    total: Optional[float] = None
    payment_method: Optional[str] = None
    currency: str = "USD"


class FormExtraction(BaseModel):
    """Schema for form extraction."""
    form_type: Optional[str] = None
    fields: dict = Field(default_factory=dict)
    submitted_by: Optional[str] = None
    submission_date: Optional[date] = None


class GenericExtraction(BaseModel):
    """Generic schema for unknown document types."""
    document_type: str
    title: Optional[str] = None
    date: Optional[date] = None
    parties: List[str] = Field(default_factory=list)
    content: str
    key_value_pairs: dict = Field(default_factory=dict)


# Schema mapping
SCHEMA_MAP = {
    "invoice": InvoiceExtraction,
    "contract": ContractExtraction,
    "receipt": ReceiptExtraction,
    "form": FormExtraction,
    "other": GenericExtraction,
}


def get_extraction_schema(document_type: str) -> type[BaseModel]:
    """Get the appropriate schema for a document type."""
    return SCHEMA_MAP.get(document_type.lower(), GenericExtraction)


def get_schema_fields(schema_type: str) -> List[str]:
    """Get list of field names for a schema type."""
    schema = get_extraction_schema(schema_type)
    return list(schema.model_fields.keys())


def validate_extraction_data(
    data: dict,
    document_type: str,
) -> tuple[bool, List[str]]:
    """
    Validate extraction data against the appropriate schema.

    Returns:
        Tuple of (is_valid, error_messages)
    """
    schema = get_extraction_schema(document_type)
    try:
        schema.model_validate(data)
        return True, []
    except Exception as e:
        return False, [str(e)]
