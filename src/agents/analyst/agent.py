"""
Analyst agent for cross-document analysis.
"""
from typing import List, Dict, Any, Optional
from src.agents.analyst.comparison import (
    ComparisonResult,
    compare_invoices,
    compare_vendor_pricing,
    detect_pricing_trends,
)
from src.agents.analyst.trends import (
    TrendReport,
    analyze_spending_trends,
    analyze_vendor_trends,
    calculate_growth_rate,
    forecast_next_period,
)
from src.agents.analyst.metrics import (
    AnalysisMetrics,
    calculate_invoice_metrics,
    calculate_vendor_metrics,
    calculate_monthly_metrics,
    calculate_summary_statistics,
)


class AnalystAgent:
    """
    Performs cross-document analysis including:
    - Comparing multiple documents
    - Detecting anomalies
    - Summarizing trends
    - Generating insights
    """

    def __init__(self):
        self.comparison = compare_invoices
        self.vendor_pricing = compare_vendor_pricing
        self.trends = detect_pricing_trends
        self.spending_trends = analyze_spending_trends
        self.vendor_trends = analyze_vendor_trends
        self.metrics = calculate_invoice_metrics
        self.summary = calculate_summary_statistics

    def analyze(
        self,
        documents: List[Dict[str, Any]],
        analysis_type: str = "comparison",
    ) -> Dict[str, Any]:
        """
        Perform analysis on documents.

        Args:
            documents: List of document extractions
            analysis_type: Type of analysis to perform

        Returns:
            Analysis results
        """
        if analysis_type == "comparison":
            return {
                "comparison": self.comparison(documents).__dict__,
                "pricing_trends": self.trends(documents),
            }
        elif analysis_type == "trend":
            return {
                "spending_trends": self.spending_trends(documents).__dict__,
                "vendor_trends": self.vendor_trends(documents),
            }
        elif analysis_type == "metrics":
            return self.summary(documents)
        else:
            return {"error": f"Unknown analysis type: {analysis_type}"}


__all__ = [
    "AnalystAgent",
    "ComparisonResult",
    "compare_invoices",
    "compare_vendor_pricing",
    "detect_pricing_trends",
    "TrendReport",
    "analyze_spending_trends",
    "analyze_vendor_trends",
    "calculate_growth_rate",
    "forecast_next_period",
    "AnalysisMetrics",
    "calculate_invoice_metrics",
    "calculate_vendor_metrics",
    "calculate_monthly_metrics",
    "calculate_summary_statistics",
]
