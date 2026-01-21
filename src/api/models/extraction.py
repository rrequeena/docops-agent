"""
Extraction Pydantic models.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ExtractionStatus(str, Enum):
    PENDING = "pending"
    EXTRACTING = "extracting"
    COMPLETED = "completed"
    FAILED = "failed"


class LineItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    total: float


class InvoiceExtraction(BaseModel):
    vendor_name: str
    invoice_number: str
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    line_items: List[LineItem] = Field(default_factory=list)
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    total: Optional[float] = None
    currency: str = "USD"
    payment_terms: Optional[str] = None
    notes: Optional[str] = None


class Extraction(BaseModel):
    id: str
    document_id: str
    extraction_type: str
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel
    data: Dict[str, Any]
    warnings: List[str] = Field(default_factory=list)
    status: ExtractionStatus = ExtractionStatus.PENDING
    extracted_at: Optional[datetime] = None


class ExtractionRequest(BaseModel):
    document_id: str
    extraction_type: Optional[str] = None
