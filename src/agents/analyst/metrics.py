"""
Metrics calculator for document analysis.
"""
from typing import List, Dict, Any, Optional
from datetime import date, datetime
from decimal import Decimal
import statistics


class AnalysisMetrics:
    """Container for analysis metrics."""

    def __init__(
        self,
        total_documents: int,
        total_value: float,
        average_value: float,
        median_value: Optional[float] = None,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        standard_deviation: Optional[float] = None,
    ):
        self.total_documents = total_documents
        self.total_value = total_value
        self.average_value = average_value
        self.median_value = median_value
        self.min_value = min_value
        self.max_value = max_value
        self.standard_deviation = standard_deviation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_documents": self.total_documents,
            "total_value": self.total_value,
            "average_value": self.average_value,
            "median_value": self.median_value,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "standard_deviation": self.standard_deviation,
        }


def calculate_invoice_metrics(invoices: List[Dict[str, Any]]) -> AnalysisMetrics:
    """
    Calculate metrics from invoice extractions.

    Args:
        invoices: List of invoice extraction dictionaries

    Returns:
        AnalysisMetrics with calculated values
    """
    if not invoices:
        return AnalysisMetrics(
            total_documents=0,
            total_value=0.0,
            average_value=0.0,
        )

    totals = []
    for inv in invoices:
        total = inv.get("total")
        if total is not None:
            if isinstance(total, str):
                total = float(total)
            elif hasattr(total, "float_value"):
                total = float(total)
            totals.append(total)

    if not totals:
        return AnalysisMetrics(
            total_documents=len(invoices),
            total_value=0.0,
            average_value=0.0,
        )

    total_value = sum(totals)
    average_value = total_value / len(totals)

    median_value = statistics.median(totals) if len(totals) > 1 else totals[0]
    min_value = min(totals)
    max_value = max(totals)

    std_dev = None
    if len(totals) > 1:
        std_dev = statistics.stdev(totals)

    return AnalysisMetrics(
        total_documents=len(invoices),
        total_value=total_value,
        average_value=average_value,
        median_value=median_value,
        min_value=min_value,
        max_value=max_value,
        standard_deviation=std_dev,
    )


def calculate_vendor_metrics(invoices: List[Dict[str, Any]]) -> Dict[str, AnalysisMetrics]:
    """
    Calculate metrics grouped by vendor.

    Args:
        invoices: List of invoice extraction dictionaries

    Returns:
        Dictionary mapping vendor names to their metrics
    """
    vendor_invoices = {}

    for inv in invoices:
        vendor = inv.get("vendor_name", "Unknown")
        if vendor not in vendor_invoices:
            vendor_invoices[vendor] = []
        vendor_invoices[vendor].append(inv)

    vendor_metrics = {}
    for vendor, vendor_invs in vendor_invoices.items():
        vendor_metrics[vendor] = calculate_invoice_metrics(vendor_invs)

    return vendor_metrics


def calculate_monthly_metrics(invoices: List[Dict[str, Any]]) -> Dict[str, AnalysisMetrics]:
    """
    Calculate metrics grouped by month.

    Args:
        invoices: List of invoice extraction dictionaries

    Returns:
        Dictionary mapping month keys to their metrics
    """
    monthly_invoices = {}

    for inv in invoices:
        inv_date = inv.get("invoice_date")
        if inv_date:
            month_key = f"{inv_date.year}-{inv_date.month:02d}"
            if month_key not in monthly_invoices:
                monthly_invoices[month_key] = []
            monthly_invoices[month_key].append(inv)

    monthly_metrics = {}
    for month, month_invs in monthly_invoices.items():
        monthly_metrics[month] = calculate_invoice_metrics(month_invs)

    return monthly_metrics


def calculate_percentage_distribution(values: List[float]) -> Dict[str, float]:
    """
    Calculate percentage distribution of values.

    Args:
        values: List of numeric values

    Returns:
        Dictionary with distribution percentages
    """
    if not values:
        return {}

    total = sum(values)
    if total == 0:
        return {}

    return {f"pct_{i}": (v / total * 100) for i, v in enumerate(sorted(values, reverse=True))}


def calculate_category_breakdown(
    invoices: List[Dict[str, Any]], category_field: str = "vendor_name"
) -> Dict[str, float]:
    """
    Calculate spending breakdown by category.

    Args:
        invoices: List of invoice extractions
        category_field: Field to group by

    Returns:
        Dictionary mapping categories to total values
    """
    category_totals = {}

    for inv in invoices:
        category = inv.get(category_field, "Unknown")
        total = inv.get("total")

        if total:
            if isinstance(total, str):
                total = float(total)
            elif hasattr(total, "float_value"):
                total = float(total)

            if category not in category_totals:
                category_totals[category] = 0.0
            category_totals[category] += total

    return dict(sorted(category_totals.items(), key=lambda x: x[1], reverse=True))


def calculate_summary_statistics(invoices: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate comprehensive summary statistics.

    Args:
        invoices: List of invoice extractions

    Returns:
        Dictionary with various statistics
    """
    metrics = calculate_invoice_metrics(invoices)

    vendor_metrics = calculate_vendor_metrics(invoices)
    top_vendor = max(vendor_metrics.items(), key=lambda x: x[1].total_value) if vendor_metrics else (None, None)

    category_breakdown = calculate_category_breakdown(invoices)

    return {
        "overall": metrics.to_dict(),
        "by_vendor": {k: v.to_dict() for k, v in vendor_metrics.items()},
        "top_vendor": top_vendor[0] if top_vendor[0] else None,
        "top_vendor_total": top_vendor[1].total_value if top_vendor[1] else 0,
        "category_breakdown": category_breakdown,
    }
