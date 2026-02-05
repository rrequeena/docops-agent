"""
Anomaly detection for document analysis.
"""
from typing import List, Dict, Any, Optional
from datetime import date
from decimal import Decimal
from src.api.models.analysis import AnomalyType, Severity


class Anomaly:
    """Detected anomaly in document analysis."""

    def __init__(
        self,
        anomaly_type: AnomalyType,
        severity: Severity,
        description: str,
        document_ids: List[str],
        details: Dict[str, Any],
        recommendation: Optional[str] = None,
    ):
        self.anomaly_type = anomaly_type
        self.severity = severity
        self.description = description
        self.document_ids = document_ids
        self.details = details
        self.recommendation = recommendation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "anomaly_type": self.anomaly_type.value,
            "severity": self.severity.value,
            "description": self.description,
            "document_ids": self.document_ids,
            "details": self.details,
            "recommendation": self.recommendation,
        }


def detect_price_spikes(
    invoices: List[Dict[str, Any]], threshold_percent: float = 50.0
) -> List[Anomaly]:
    """
    Detect unusual price spikes compared to vendor average.

    Args:
        invoices: List of invoice extractions
        threshold_percent: Percentage above average to flag as spike

    Returns:
        List of detected price spike anomalies
    """
    vendor_totals: Dict[str, List[float]] = {}

    for inv in invoices:
        vendor = inv.get("vendor_name", "Unknown")
        total = inv.get("total")

        if total and vendor:
            if isinstance(total, str):
                total = float(total)
            elif hasattr(total, "float_value"):
                total = float(total)

            if vendor not in vendor_totals:
                vendor_totals[vendor] = []
            vendor_totals[vendor].append(total)

    anomalies = []

    for vendor, totals in vendor_totals.items():
        if len(totals) < 2:
            continue

        avg_total = sum(totals) / len(totals)

        for i, inv in enumerate(invoices):
            if inv.get("vendor_name") == vendor:
                total = inv.get("total")
                if total:
                    if isinstance(total, str):
                        total = float(total)
                    elif hasattr(total, "float_value"):
                        total = float(total)

                    if avg_total > 0:
                        pct_above = ((total - avg_total) / avg_total) * 100

                        if pct_above >= threshold_percent:
                            doc_id = inv.get("document_id", f"doc_{i}")
                            anomalies.append(Anomaly(
                                anomaly_type=AnomalyType.PRICE_SPIKE,
                                severity=Severity.WARNING,
                                description=f"Price {pct_above:.1f}% above vendor average",
                                document_ids=[doc_id],
                                details={
                                    "vendor": vendor,
                                    "invoice_total": total,
                                    "vendor_average": avg_total,
                                    "percent_above": pct_above,
                                },
                                recommendation=f"Review invoice for {vendor} - significantly higher than average",
                            ))

    return anomalies


def detect_duplicate_charges(invoices: List[Dict[str, Any]]) -> List[Anomaly]:
    """
    Detect potential duplicate charges based on vendor, amount, and date.

    Args:
        invoices: List of invoice extractions

    Returns:
        List of detected duplicate charge anomalies
    """
    duplicates = []
    seen: Dict[str, List[int]] = {}

    for i, inv in enumerate(invoices):
        vendor = inv.get("vendor_name", "")
        total = inv.get("total")
        inv_date = inv.get("invoice_date")

        if not (vendor and total and inv_date):
            continue

        if isinstance(total, str):
            total = float(total)
        elif hasattr(total, "float_value"):
            total = float(total)

        key = f"{vendor}|{total}"
        if key not in seen:
            seen[key] = []
        seen[key].append(i)

    for key, indices in seen.items():
        if len(indices) < 2:
            continue

        doc_ids = []
        for idx in indices:
            doc_id = invoices[idx].get("document_id", f"doc_{idx}")
            doc_ids.append(doc_id)

        vendor = key.split("|")[0]
        total = float(key.split("|")[1])

        duplicates.append(Anomaly(
            anomaly_type=AnomalyType.DUPLICATE_CHARGE,
            severity=Severity.CRITICAL,
            description=f"Potential duplicate charges from {vendor}",
            document_ids=doc_ids,
            details={
                "vendor": vendor,
                "amount": total,
                "invoice_count": len(indices),
            },
            recommendation="Verify all invoices are legitimate and not duplicates",
        ))

    return duplicates


def detect_tax_anomalies(invoices: List[Dict[str, Any]]) -> List[Anomaly]:
    """
    Detect tax calculation anomalies.

    Args:
        invoices: List of invoice extractions

    Returns:
        List of detected tax anomalies
    """
    anomalies = []

    for i, inv in enumerate(invoices):
        subtotal = inv.get("subtotal")
        tax = inv.get("tax")
        tax_rate = inv.get("tax_rate")
        total = inv.get("total")

        if not (subtotal and tax and total):
            continue

        if isinstance(subtotal, str):
            subtotal = float(subtotal)
        elif hasattr(subtotal, "float_value"):
            subtotal = float(subtotal)

        if isinstance(tax, str):
            tax = float(tax)
        elif hasattr(tax, "float_value"):
            tax = float(tax)

        if isinstance(total, str):
            total = float(total)
        elif hasattr(total, "float_value"):
            total = float(total)

        calculated_total = subtotal + tax
        total_diff = abs(total - calculated_total)

        if total_diff > 0.01:
            doc_id = inv.get("document_id", f"doc_{i}")
            anomalies.append(Anomaly(
                anomaly_type=AnomalyType.TAX_ANOMALY,
                severity=Severity.WARNING,
                description="Tax calculation does not match total",
                document_ids=[doc_id],
                details={
                    "subtotal": subtotal,
                    "tax": tax,
                    "stated_total": total,
                    "calculated_total": calculated_total,
                    "difference": total_diff,
                },
                recommendation="Verify tax calculation and total",
            ))

        if tax_rate:
            if isinstance(tax_rate, str):
                tax_rate = float(tax_rate)
            elif hasattr(tax_rate, "float_value"):
                tax_rate = float(tax_rate)

            expected_tax = subtotal * tax_rate
            tax_diff = abs(tax - expected_tax)

            if tax_diff > 0.01:
                doc_id = inv.get("document_id", f"doc_{i}")
                anomalies.append(Anomaly(
                    anomaly_type=AnomalyType.TAX_ANOMALY,
                    severity=Severity.WARNING,
                    description="Tax amount does not match tax rate",
                    document_ids=[doc_id],
                    details={
                        "subtotal": subtotal,
                        "tax_rate": tax_rate,
                        "expected_tax": expected_tax,
                        "actual_tax": tax,
                        "difference": tax_diff,
                    },
                    recommendation="Verify tax rate application",
                ))

    return anomalies


def detect_unusual_patterns(invoices: List[Dict[str, Any]]) -> List[Anomaly]:
    """
    Detect unusual patterns in invoices.

    Args:
        invoices: List of invoice extractions

    Returns:
        List of detected pattern anomalies
    """
    anomalies = []

    for i, inv in enumerate(invoices):
        issues = []

        total = inv.get("total")
        if total and total > 100000:
            issues.append("Very high invoice total")

        line_items = inv.get("line_items", [])
        if len(line_items) == 0:
            issues.append("No line items")

        if inv.get("vendor_name") and len(inv.get("vendor_name", "")) < 3:
            issues.append("Vendor name suspiciously short")

        if issues:
            doc_id = inv.get("document_id", f"doc_{i}")
            anomalies.append(Anomaly(
                anomaly_type=AnomalyType.UNUSUAL_PATTERN,
                severity=Severity.INFO,
                description=f"Unusual pattern detected: {'; '.join(issues)}",
                document_ids=[doc_id],
                details={"issues": issues},
                recommendation="Review for potential issues",
            ))

    return anomalies


def detect_all_anomalies(invoices: List[Dict[str, Any]]) -> List[Anomaly]:
    """
    Run all anomaly detection methods.

    Args:
        invoices: List of invoice extractions

    Returns:
        Combined list of all detected anomalies
    """
    all_anomalies = []

    all_anomalies.extend(detect_price_spikes(invoices))
    all_anomalies.extend(detect_duplicate_charges(invoices))
    all_anomalies.extend(detect_tax_anomalies(invoices))
    all_anomalies.extend(detect_unusual_patterns(invoices))

    return all_anomalies


__all__ = [
    "Anomaly",
    "detect_price_spikes",
    "detect_duplicate_charges",
    "detect_tax_anomalies",
    "detect_unusual_patterns",
    "detect_all_anomalies",
]
