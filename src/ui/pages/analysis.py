"""
Streamlit page for viewing analysis results.
"""
import streamlit as st
from datetime import datetime, timedelta
import random


def render_analysis_page():
    """Render the analysis dashboard page."""
    st.header("Analysis Dashboard")

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Documents", "127", "+12")
    with col2:
        st.metric("Total Value", "$245K", "+18%")
    with col3:
        st.metric("Active Vendors", "23", "+2")
    with col4:
        st.metric("Anomalies", "8", "-3")

    st.divider()

    # Charts section
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.subheader("Monthly Spending")
        months = ["Oct", "Nov", "Dec", "Jan", "Feb"]
        values = [42000, 48000, 51000, 55000, 62000]
        st.bar_chart(values, labels={i: m for i, m in enumerate(months)})

    with col_chart2:
        st.subheader("Documents by Type")
        chart_data = {"Invoice": 78, "Contract": 24, "Receipt": 18, "Form": 7}
        st.bar_chart(chart_data)

    st.divider()

    # Anomalies section
    st.subheader("Detected Anomalies")

    # Mock anomalies
    anomalies = [
        {
            "type": "price_spike",
            "severity": "warning",
            "description": "Price 67% above vendor average",
            "vendor": "Acme Corp",
            "invoice": "INV-2026-0156",
            "amount": 2450.00,
            "average": 1465.00,
            "documents": ["doc_005", "doc_008"]
        },
        {
            "type": "duplicate_charge",
            "severity": "critical",
            "description": "Potential duplicate charges detected",
            "vendor": "TechSupply Inc",
            "invoice": "INV-2026-0089, INV-2026-0090",
            "amount": 1500.00,
            "documents": ["doc_012", "doc_013"]
        },
        {
            "type": "tax_anomaly",
            "severity": "warning",
            "description": "Tax calculation mismatch",
            "vendor": "Office Depot",
            "invoice": "RCT-2026-0234",
            "amount": 45.50,
            "documents": ["doc_018"]
        },
    ]

    # Filter by severity
    severity_filter = st.selectbox("Filter by Severity", ["all", "critical", "warning", "info"])

    filtered_anomalies = anomalies
    if severity_filter != "all":
        filtered_anomalies = [a for a in filtered_anomalies if a["severity"] == severity_filter]

    for i, anomaly in enumerate(filtered_anomalies):
        severity_color = {
            "critical": "🔴",
            "warning": "🟡",
            "info": "🔵"
        }.get(anomaly["severity"], "⚪")

        with st.expander(f"{severity_color} {anomaly['type'].replace('_', ' ').title()} - {anomaly['vendor']}", expanded=True):
            col_a, col_b = st.columns(2)

            with col_a:
                st.write(f"**Description:** {anomaly['description']}")
                st.write(f"**Invoice(s):** {anomaly['invoice']}")

            with col_b:
                st.write(f"**Severity:** {anomaly['severity'].title()}")
                if "amount" in anomaly:
                    st.write(f"**Amount:** ${anomaly['amount']:,.2f}")
                if "average" in anomaly:
                    st.write(f"**Average:** ${anomaly['average']:,.2f}")

            col_act1, col_act2, col_act3 = st.columns(3)
            with col_act1:
                st.button("Review", key=f"review_{i}")
            with col_act2:
                st.button("Dismiss", key=f"dismiss_{i}")
            with col_act3:
                st.button("Flag for Approval", key=f"flag_{i}")

    st.divider()

    # Vendor analysis
    st.subheader("Vendor Analysis")

    vendor_data = {
        "Acme Corp": {"invoices": 34, "total": 85000, "avg": 2500, "anomalies": 3},
        "TechSupply Inc": {"invoices": 22, "total": 62000, "avg": 2818, "anomalies": 2},
        "CloudServices LLC": {"invoices": 15, "total": 45000, "avg": 3000, "anomalies": 0},
        "Office Depot": {"invoices": 28, "total": 28000, "avg": 1000, "anomalies": 1},
    }

    for vendor, data in vendor_data.items():
        with st.expander(f"{vendor}"):
            col_v1, col_v2, col_v3, col_v4 = st.columns(4)

            with col_v1:
                st.metric("Invoices", data["invoices"])
            with col_v2:
                st.metric("Total Value", f"${data['total']:,}")
            with col_v3:
                st.metric("Avg Invoice", f"${data['avg']:,.0f}")
            with col_v4:
                st.metric("Anomalies", data["anomalies"], delta=-data["anomalies"] if data["anomalies"] > 0 else 0)


__all__ = ["render_analysis_page"]
