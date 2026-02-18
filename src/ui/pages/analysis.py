"""
Streamlit page for viewing analysis results.
"""
import streamlit as st
import requests


API_BASE_URL = "http://api:8000"


def render_analysis_page():
    """Render the analysis dashboard page."""
    st.header("Analysis Dashboard")

    # Fetch documents from API
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/documents", timeout=10)
        if response.status_code == 200:
            data = response.json()
            documents = data.get("documents", [])
            # Filter to only show processed documents with extractions
            docs_with_extraction = [d for d in documents if d.get("extraction")]
        else:
            st.error(f"Failed to fetch documents: {response.text}")
            docs_with_extraction = []
    except Exception as e:
        st.error(f"Error connecting to API: {e}")
        docs_with_extraction = []

    # Summary metrics
    total_docs = len(documents)
    total_value = sum(
        float(d.get("extraction", {}).get("data", {}).get("total", 0) or 0)
        for d in docs_with_extraction
    )
    vendors = set(
        d.get("extraction", {}).get("data", {}).get("vendor_name")
        for d in docs_with_extraction if d.get("extraction", {}).get("data", {}).get("vendor_name")
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Documents", str(total_docs))
    with col2:
        st.metric("Total Value", f"${total_value:,.2f}")
    with col3:
        st.metric("Active Vendors", str(len(vendors)))
    with col4:
        st.metric("Processed", str(len(docs_with_extraction)))

    st.divider()

    # Documents with extractions
    if not docs_with_extraction:
        st.info("No processed documents with extractions yet. Upload and process a document first.")
        return

    # Allow selecting a document to analyze
    doc_options = {d["id"]: f"{d['filename']} - {d.get('extraction', {}).get('data', {}).get('vendor_name', 'N/A')}" for d in docs_with_extraction}
    selected_doc_id = st.selectbox("Select Document", list(doc_options.keys()), format_func=lambda x: doc_options[x])

    if selected_doc_id:
        # Fetch analysis for selected document
        try:
            analysis_response = requests.get(f"{API_BASE_URL}/api/v1/analysis/document/{selected_doc_id}", timeout=10)
            if analysis_response.status_code == 200:
                analysis_data = analysis_response.json()
            else:
                analysis_data = {"anomalies": [], "metrics": {}, "summary": "No analysis available"}
        except:
            analysis_data = {"anomalies": [], "metrics": {}, "summary": "Error fetching analysis"}

        anomalies = analysis_data.get("anomalies", [])
        metrics = analysis_data.get("metrics", {})

        # Anomalies section
        st.subheader("Detected Anomalies")

        if not anomalies:
            st.success("No anomalies detected!")
        else:
            # Filter by severity
            severity_filter = st.selectbox("Filter by Severity", ["all", "critical", "warning", "info"])

            filtered_anomalies = anomalies
            if severity_filter != "all":
                filtered_anomalies = [a for a in filtered_anomalies if a.get("severity") == severity_filter]

            for i, anomaly in enumerate(filtered_anomalies):
                severity = anomaly.get("severity", "info")
                severity_emoji = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(severity, "⚪")

                with st.expander(f"{severity_emoji} {anomaly.get('anomaly_type', 'Unknown').replace('_', ' ').title()}", expanded=True):
                    st.write(f"**Description:** {anomaly.get('description', 'N/A')}")
                    st.write(f"**Severity:** {severity.title()}")

                    details = anomaly.get("details", {})
                    for key, value in details.items():
                        st.write(f"**{key}:** {value}")

                    if anomaly.get("recommendation"):
                        st.write(f"**Recommendation:** {anomaly['recommendation']}")

    st.divider()

    # All documents analysis
    st.subheader("All Document Metrics")

    for doc in docs_with_extraction:
        extraction = doc.get("extraction", {})
        data = extraction.get("data", {})

        with st.expander(f"{doc['filename']} - {data.get('vendor_name', 'N/A')}"):
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Invoice #", data.get("invoice_number", "N/A"))
            with col2:
                st.metric("Total", f"${float(data.get('total', 0)):,.2f}")
            with col3:
                st.metric("Confidence", f"{extraction.get('confidence', 0) * 100:.0f}%")
            with col4:
                date = data.get("invoice_date", "N/A")
                st.metric("Date", str(date))


__all__ = ["render_analysis_page"]
