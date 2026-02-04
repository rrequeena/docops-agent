"""
Trend analyzer for time-series document analysis.
"""
from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
from collections import defaultdict
from decimal import Decimal


class TrendReport:
    """Report of trend analysis."""

    def __init__(
        self,
        period_start: date,
        period_end: date,
        data_points: int,
        trends: Dict[str, Any],
        summary: str,
    ):
        self.period_start = period_start
        self.period_end = period_end
        self.data_points = data_points
        self.trends = trends
        self.summary = summary


def analyze_spending_trends(invoices: List[Dict[str, Any]]) -> TrendReport:
    """
    Analyze spending trends over time.

    Args:
        invoices: List of invoice extractions

    Returns:
        TrendReport with analysis
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
            dated_invoices.append({"date": inv_date, "total": total})

    if not dated_invoices:
        return TrendReport(
            period_start=date.today(),
            period_end=date.today(),
            data_points=0,
            trends={},
            summary="No data available for trend analysis",
        )

    dated_invoices.sort(key=lambda x: x["date"])

    period_start = dated_invoices[0]["date"]
    period_end = dated_invoices[-1]["date"]

    monthly_totals = defaultdict(float)
    for inv in dated_invoices:
        month_key = f"{inv['date'].year}-{inv['date'].month:02d}"
        monthly_totals[month_key] += inv["total"]

    monthly_data = sorted(monthly_totals.items())
    if len(monthly_data) >= 2:
        first_month = monthly_data[0][1]
        last_month = monthly_data[-1][1]
        change_pct = ((last_month - first_month) / first_month * 100) if first_month > 0 else 0
    else:
        change_pct = 0

    total_spent = sum(inv["total"] for inv in dated_invoices)
    avg_monthly = total_spent / len(monthly_data) if monthly_data else 0

    return TrendReport(
        period_start=period_start,
        period_end=period_end,
        data_points=len(dated_invoices),
        trends={
            "monthly_totals": dict(monthly_data),
            "total_spent": total_spent,
            "average_monthly": avg_monthly,
            "overall_change_percent": change_pct,
        },
        summary=f"Analyzed {len(dated_invoices)} invoices from {period_start} to {period_end}. "
        f"Total spent: ${total_spent:,.2f}, Monthly average: ${avg_monthly:,.2f}",
    )


def analyze_vendor_trends(invoices: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze vendor-specific trends.

    Args:
        invoices: List of invoice extractions

    Returns:
        Vendor trend analysis
    """
    vendor_data = defaultdict(lambda: {"invoices": [], "total": 0, "count": 0})

    for inv in invoices:
        vendor = inv.get("vendor_name", "Unknown")
        total = inv.get("total")
        inv_date = inv.get("invoice_date")

        if total and inv_date:
            if isinstance(total, str):
                total = float(total)
            elif hasattr(total, "float_value"):
                total = float(total)
            vendor_data[vendor]["invoices"].append({"date": inv_date, "total": total})
            vendor_data[vendor]["total"] += total
            vendor_data[vendor]["count"] += 1

    vendor_trends = {}
    for vendor, data in vendor_data.items():
        if data["count"] < 2:
            continue

        invoices_list = sorted(data["invoices"], key=lambda x: x["date"])
        first_total = invoices_list[0]["total"]
        last_total = invoices_list[-1]["total"]
        change_pct = ((last_total - first_total) / first_total * 100) if first_total > 0 else 0

        vendor_trends[vendor] = {
            "invoice_count": data["count"],
            "total_spent": data["total"],
            "average_invoice": data["total"] / data["count"],
            "first_invoice_total": first_total,
            "last_invoice_total": last_total,
            "change_percent": change_pct,
        }

    return {
        "vendor_trends": vendor_trends,
        "total_vendors": len(vendor_data),
    }


def calculate_growth_rate(data_points: List[float], periods: int = 1) -> float:
    """
    Calculate compound annual growth rate.

    Args:
        data_points: List of values over time
        periods: Number of periods between first and last value

    Returns:
        Growth rate as percentage
    """
    if len(data_points) < 2 or periods <= 0:
        return 0.0

    first = data_points[0]
    last = data_points[-1]

    if first <= 0:
        return 0.0

    cagr = ((last / first) ** (1 / periods) - 1) * 100
    return cagr


def forecast_next_period(historical_data: List[float], method: str = "linear") -> float:
    """
    Forecast next period value based on historical data.

    Args:
        historical_data: List of historical values
        method: Forecasting method ("linear" or "moving_average")

    Returns:
        Forecasted value
    """
    if not historical_data:
        return 0.0

    if method == "moving_average":
        window = min(3, len(historical_data))
        return sum(historical_data[-window:]) / window

    if len(historical_data) < 2:
        return historical_data[-1]

    n = len(historical_data)
    x_mean = (n - 1) / 2
    y_mean = sum(historical_data) / n

    numerator = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(historical_data))
    denominator = sum((i - x_mean) ** 2 for i in range(n))

    if denominator == 0:
        return historical_data[-1]

    slope = numerator / denominator
    intercept = y_mean - slope * x_mean

    return slope * n + intercept
