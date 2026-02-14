"""
Schema validation for extraction results.
"""

import logging
from typing import Dict, Any, List, Tuple, Optional

from src.agents.extraction.schemas import get_extraction_schema

logger = logging.getLogger(__name__)


class ExtractionValidator:
    """Validates extraction results against Pydantic schemas."""

    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode
        self.validation_errors = []

    def validate(
        self,
        data: Dict[str, Any],
        document_type: str,
    ) -> Tuple[bool, List[str]]:
        """
        Validate extraction data against schema.

        Args:
            data: Extracted data dictionary
            document_type: Type of document

        Returns:
            Tuple of (is_valid, error_messages)
        """
        schema = get_extraction_schema(document_type)
        errors = []

        try:
            # Try to validate against schema
            schema.model_validate(data)
            return True, []
        except Exception as e:
            errors.append(str(e))
            return False, errors

    def validate_field(
        self,
        field_name: str,
        value: Any,
        field_schema: Any,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate a single field.

        Args:
            field_name: Name of the field
            value: Value to validate
            field_schema: Field schema definition

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required fields using Pydantic v2 approach
        if field_schema.is_required() if hasattr(field_schema, 'is_required') else not field_schema.has_default() and value is None:
            return False, f"Required field '{field_name}' is missing"

        # Type validation
        if value is not None:
            # Get the annotation from Pydantic v2 FieldInfo
            if hasattr(field_schema, 'annotation'):
                expected_type = field_schema.annotation
            elif hasattr(field_schema, 'type_'):
                expected_type = field_schema.type_
            else:
                return True, None  # Skip type check if we can't determine type

            if not isinstance(value, expected_type):
                return False, f"Field '{field_name}' has incorrect type"

        return True, None

    def get_field_completeness(
        self,
        data: Dict[str, Any],
        document_type: str,
    ) -> float:
        """
        Calculate field completeness score.

        Args:
            data: Extraction data
            document_type: Document type

        Returns:
            Completeness score from 0 to 1
        """
        schema = get_extraction_schema(document_type)
        fields = schema.model_fields

        if not fields:
            return 0.0

        filled_fields = 0
        for field_name, field_info in fields.items():
            if field_name in data and data[field_name] is not None:
                # Check if the value is not empty
                value = data[field_name]
                if isinstance(value, str) and value.strip():
                    filled_fields += 1
                elif isinstance(value, (list, dict)) and len(value) > 0:
                    filled_fields += 1
                elif not isinstance(value, (str, list, dict)):
                    filled_fields += 1

        return filled_fields / len(fields)

    def validate_business_rules(
        self,
        data: Dict[str, Any],
        document_type: str,
    ) -> List[str]:
        """
        Validate business rules specific to document type.

        Args:
            data: Extraction data
            document_type: Document type

        Returns:
            List of validation warnings/errors
        """
        errors = []

        if document_type == "invoice":
            errors.extend(self._validate_invoice_rules(data))
        elif document_type == "receipt":
            errors.extend(self._validate_receipt_rules(data))
        elif document_type == "contract":
            errors.extend(self._validate_contract_rules(data))

        return errors

    def _validate_invoice_rules(self, data: Dict[str, Any]) -> List[str]:
        """Validate invoice-specific business rules."""
        errors = []

        # Check total consistency
        line_items = data.get("line_items", [])
        if line_items:
            calculated_total = sum(
                item.get("total", 0) for item in line_items
            )
            tax = data.get("tax", 0)
            stated_total = data.get("total", 0)

            # Allow small rounding differences
            if abs(calculated_total + tax - stated_total) > 0.01:
                errors.append(
                    "Total does not match sum of line items plus tax"
                )

        # Check date ordering
        invoice_date = data.get("invoice_date")
        due_date = data.get("due_date")
        if invoice_date and due_date:
            # Handle both string dates and date objects
            if isinstance(invoice_date, str):
                from datetime import datetime
                invoice_date = datetime.fromisoformat(invoice_date.replace("Z", "+00:00")).date() if "T" in invoice_date else datetime.strptime(invoice_date, "%Y-%m-%d").date()
            if isinstance(due_date, str):
                from datetime import datetime
                due_date = datetime.fromisoformat(due_date.replace("Z", "+00:00")).date() if "T" in due_date else datetime.strptime(due_date, "%Y-%m-%d").date()
            if due_date < invoice_date:
                errors.append("Due date is before invoice date")

        return errors

    def _validate_receipt_rules(self, data: Dict[str, Any]) -> List[str]:
        """Validate receipt-specific business rules."""
        errors = []

        # Check total consistency
        subtotal = data.get("subtotal", 0)
        tax = data.get("tax", 0)
        tip = data.get("tip", 0)
        total = data.get("total", 0)

        if abs(subtotal + tax + tip - total) > 0.01:
            errors.append(
                "Total does not match subtotal plus tax plus tip"
            )

        return errors

    def _validate_contract_rules(self, data: Dict[str, Any]) -> List[str]:
        """Validate contract-specific business rules."""
        errors = []

        # Check required parties
        parties = data.get("parties", [])
        if len(parties) < 2:
            errors.append("Contract should have at least two parties")

        # Check date ordering
        effective = data.get("effective_date")
        expiration = data.get("expiration_date")
        if effective and expiration and expiration < effective:
            errors.append("Expiration date is before effective date")

        return errors


def validate_extraction(
    data: Dict[str, Any],
    document_type: str,
    strict: bool = False,
) -> Tuple[bool, List[str], float]:
    """
    Comprehensive extraction validation.

    Args:
        data: Extraction data
        document_type: Document type
        strict: Whether to use strict validation

    Returns:
        Tuple of (is_valid, errors, completeness_score)
    """
    validator = ExtractionValidator(strict_mode=strict)

    # Schema validation
    is_valid, errors = validator.validate(data, document_type)

    # Business rules validation
    business_errors = validator.validate_business_rules(data, document_type)
    errors.extend(business_errors)

    # Calculate completeness
    completeness = validator.get_field_completeness(data, document_type)

    return is_valid and len(errors) == 0, errors, completeness
