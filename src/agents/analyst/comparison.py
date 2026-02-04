"""
Comparison engine for analyzing multiple documents.
"""
from typing import List, Dict, Any, Optional
from datetime import date, datetime
from decimal import Decimal


class ComparisonResult:
    """Result of document comparison."""

    def __init__(
        self,
        compared_documents: List[str],
        similarities: Dict[str, float],
        differences: Dict[str, Any],
        shared_vendors: List[str],
        price_variance: Optional[float] = None,
    ):
        self.compared_documents = compared_documents
        self.similarities = similarities
        self.differences = differences
        self.shared_vendors = shared_vendors
        self.price_variance = price_variance


def compare_invoices(invoices: List[Dict[str, Any]]) -> ComparisonResult:
    """
    Compare multiple invoice extractions.

    Args:
        invoices: List of invoice extraction dictionaries

    Returns:
        ComparisonResult with analysis
    """
    if not invoices:
        return ComparisonResult(
            compared_documents=[],
            similarities={},
            differences={},
            shared_vendors=[],
        )

    doc_ids = [inv.get("document_id", f"doc_{i}") for i, inv in enumerate(invoices)]

    vendors = [inv.get("vendor_name") for inv in invoices if inv.get("vendor_name")]
    shared_vendors = list(set([v for v in vendors if vendors.count(v) > 1]))

    totals = []
    for inv in invoices:
        total = inv.get("total")
        if total is not None:
            if isinstance(total, str):
                total = float(total)
            elif hasattr(total, "float_value"):
                total = float(total)
            totals.append(total)

    price_variance = None
    if len(totals) > 1:
        avg_total = sum(totals) / len(totals)
        max_diff = max(abs(t - avg_total) for t in totals)
        price_variance = (max_diff / avg_total * 100) if avg_total > 0 else 0

    dates = []
    for inv in invoices:
        inv_date = inv.get("invoice_date")
        if inv_date:
            if isinstance(inv_date, str):
                dates.append(inv_date)
            else:
                dates.append(str(inv_date))

    similarities = {
        "vendor_count": len(set(vendors)),
        "date_range": f"{min(dates)} to {max(dates)}" if dates else "N/A",
    }

    differences = {
        "total_count": len(invoices),
        "total_value": sum(totals) if totals else 0,
        "average_value": sum(totals) / len(totals) if totals else 0,
    }

    return ComparisonResult(
        compared_documents=doc_ids,
        similarities=similarities,
        differences=differences,
        shared_vendors=shared_vendors,
        price_variance=price_variance,
    )


def compare_vendor_pricing(
    invoices: List[Dict[str, Any]], vendor_name: str
) -> Dict[str, Any]:
    """
    Compare pricing for a specific vendor across multiple invoices.

    Args:
        invoices: List of invoice extractions
        vendor_name: Vendor to compare

    Returns:
        Pricing comparison data
    """
    vendor_invoices = [
        inv for inv in invoices if inv.get("vendor_name", "").lower() == vendor_name.lower()
    ]

    if not vendor_invoices:
        return {"error": f"No invoices found for vendor: {vendor_name}"}

    prices = []
    for inv in vendor_invoices:
        total = inv.get("total")
        if total:
            if isinstance(total, str):
                total = float(total)
            elif hasattr(total, "float_value"):
                total = float(total)
            prices.append(total)

    line_item_prices = {}
    for inv in vendor_invoices:
        for item in inv.get("line_items", []):
            desc = item.get("description", "unknown")
            if desc not in line_item_prices:
                line_item_prices[desc] = []
            price = item.get("unit_price")
            if price:
                if isinstance(price, str):
                    price = float(price)
                elif hasattr(price, "float_value"):
                    price = float(price)
                line_item_prices[desc].append(price)

    return {
        "vendor_name": vendor_name,
        "invoice_count": len(vendor_invoices),
        "total_spent": sum(prices),
        "average_invoice": sum(prices) / len(prices) if prices else 0,
        "price_range": {"min": min(prices), "max": max(prices)} if prices else None,
        "line_item_prices": {
            desc: {
                "min": min(prices),
                "max": max(prices),
                "avg": sum(prices) / len(prices),
            }
            for desc, prices in line_item_prices.items()
            if prices
        },
    }


def detect_pricing_trends(invoices: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Detect pricing trends over time for vendors.

    Args:
        invoices: List of invoice extractions

    Returns:
        Trend analysis data
    """
    dated_invoices = []
    for inv in invoices:
        inv_date = inv.get("invoice_date")
        total = inv.get("total")
        if inv_date and total:
            if isinstance(total, str):
                total = float(total)
            elif hasattr(total, "float_value"):
                total = float(total)
            dated_invoices.append({"date": inv_date, "total": total, "vendor": inv.get("vendor_name")})

    if not dated_invoices:
        return {"error": "No dated invoices found"}

    dated_invoices.sort(key=lambda x: x["date"])

    vendors = {}
    for inv in dated_invoices:
        vendor = inv.get("vendor", "unknown")
        if vendor not in vendors:
            vendors[vendor] = []
        vendors[vendor].append({"date": inv["date"], "total": inv["total"]})

    trends = {}
    for vendor, items in vendors.items():
        if len(items) < 2:
            continue
        first_total = items[0]["total"]
        last_total = items[-1]["total"]
        change_pct = ((last_total - first_total) / first_total * 100) if first_total > 0 else 0
        trends[vendor] = {
            "first_invoice": items[0]["total"],
            "last_invoice": items[-1]["total"],
            "change_percent": change_pct,
            "trend": "increasing" if change_pct > 5 else "decreasing" if change_pct < -5 else "stable",
        }

    return {"trends": trends, "dated_invoices": len(dated_invoices)}
