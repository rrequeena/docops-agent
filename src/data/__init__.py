"""
Data module for synthetic data generation.
"""
from src.data.generator import (
    generate_invoices,
    save_invoices_to_json,
    load_invoices_from_json,
    VENDORS,
    LINE_ITEM_DESCRIPTIONS,
    TAX_RATES,
)

__all__ = [
    "generate_invoices",
    "save_invoices_to_json",
    "load_invoices_from_json",
    "VENDORS",
    "LINE_ITEM_DESCRIPTIONS",
    "TAX_RATES",
]
