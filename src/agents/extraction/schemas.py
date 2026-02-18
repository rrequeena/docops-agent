"""
Extraction schemas for different document types.
"""

from typing import List, Optional, Any
from pydantic import BaseModel, Field, field_validator
from datetime import date
from decimal import Decimal


class LineItem(BaseModel):
    """Represents a line item in an invoice or receipt."""
    item_number: Optional[int] = None
    description: str
    quantity: Decimal = Field(..., decimal_places=2)
    unit_price: Decimal = Field(..., decimal_places=2)
    total: Decimal = Field(..., decimal_places=2)
    unit: str = Field(default="ea")
    sku: Optional[str] = None
    tax_rate: Optional[float] = 0.0


class InvoiceExtraction(BaseModel):
    """Schema for invoice extraction."""
    vendor_name: str
    vendor_address: Optional[str] = None
    vendor_email: Optional[str] = None
    vendor_phone: Optional[str] = None
    vendor_tax_id: Optional[str] = None
    invoice_number: str
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    customer_name: Optional[str] = None
    customer_address: Optional[str] = None
    line_items: List[LineItem] = Field(default_factory=list)
    subtotal: Optional[Decimal] = None
    tax: Decimal = Field(default=Decimal("0.00"))
    tax_rate: Optional[Decimal] = Field(None, decimal_places=4)
    total: Optional[Decimal] = None
    currency: str = "USD"
    payment_terms: Optional[str] = None
    notes: Optional[str] = None
    # Additional invoice fields
    previous_balance: Optional[Decimal] = Field(None, decimal_places=2, description="Previous balance or amount due from previous period")
    payments_credits: Optional[Decimal] = Field(None, decimal_places=2, description="Payments and credits applied")
    total_due: Optional[Decimal] = Field(None, decimal_places=2, description="Final total amount due including previous balance")

    @field_validator('line_items', mode='before')
    @classmethod
    def validate_line_items(cls, v):
        if not v:
            return []
        return v


class Party(BaseModel):
    """Contract party information."""
    name: str
    role: str
    address: Optional[str] = None
    contact: Optional[str] = None


class Clause(BaseModel):
    """Contract clause."""
    number: str
    title: str
    content: str
    page_reference: Optional[int] = None


class Obligation(BaseModel):
    """Contractual obligation."""
    party: str
    description: str
    due_date: Optional[date] = None


class ContractExtraction(BaseModel):
    """Schema for contract extraction."""
    title: str
    contract_type: Optional[str] = None
    contract_number: Optional[str] = None
    contract_date: Optional[date] = None
    effective_date: Optional[date] = None
    expiration_date: Optional[date] = None
    parties: List[Party] = Field(default_factory=list)
    clauses: List[Clause] = Field(default_factory=list)
    obligations: List[Obligation] = Field(default_factory=list)
    terms: Optional[str] = None
    total_value: Optional[Decimal] = None
    currency: Optional[str] = "USD"


class FormField(BaseModel):
    """Form field with label and value."""
    label: str
    value: str
    field_type: str
    page_number: int


class FormExtraction(BaseModel):
    """Schema for form extraction."""
    form_title: str
    form_type: Optional[str] = None
    fields: List[FormField] = Field(default_factory=list)
    signature_required: bool = False
    signed_date: Optional[date] = None
    submitted_by: Optional[str] = None
    submission_date: Optional[date] = None


class ReceiptItem(BaseModel):
    """Item on a receipt."""
    name: str
    quantity: Optional[Decimal] = None
    price: Decimal
    total: Decimal


class ReceiptExtraction(BaseModel):
    """Schema for receipt extraction."""
    vendor_name: str
    vendor_address: Optional[str] = None
    receipt_date: Optional[date] = None
    receipt_time: Optional[str] = None
    receipt_number: Optional[str] = None
    items: List[ReceiptItem] = Field(default_factory=list)
    subtotal: Optional[Decimal] = None
    tax: Optional[Decimal] = None
    tip: Decimal = Field(default=Decimal("0.00"))
    total: Optional[Decimal] = None
    payment_method: Optional[str] = None
    transaction_id: Optional[str] = None
    currency: str = "USD"


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
