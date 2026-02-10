"""
Streamlit page for uploading documents.
"""
import streamlit as st
import time
from datetime import datetime

from src.api.models.extraction import ExtractionStatus


def render_upload_page():
    """Render the document upload page."""
    st.header("Upload Documents")

    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=["pdf"],
        help="Upload a PDF document to process"
    )

    if uploaded_file is not None:
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("File Details")
            st.write(f"**Filename:** {uploaded_file.name}")
            st.write(f"**Size:** {uploaded_file.size / 1024:.1f} KB")

            document_type = st.selectbox(
                "Document Type",
                ["invoice", "contract", "receipt", "form", "auto-detect"],
                help="Select the type of document or let the system auto-detect"
            )

            priority = st.selectbox(
                "Priority",
                ["normal", "high", "urgent"],
                index=0
            )

        with col2:
            st.subheader("Processing Options")
            enable_analysis = st.checkbox("Enable Analysis", value=True, help="Run anomaly detection after extraction")
            require_approval = st.checkbox("Require Approval", value=False, help="Require human approval for actions")

        if st.button("Process Document", type="primary"):
            with st.spinner("Processing document..."):
                # Simulate document processing
                progress_bar = st.progress(0)

                for i in range(100):
                    time.sleep(0.02)
                    progress_bar.progress(i + 1)

                # Show results
                st.success("Document processed successfully!")

                # Display mock extraction result
                st.subheader("Extraction Results")

                result_tab1, result_tab2, result_tab3 = st.tabs(["Summary", "Details", "Raw JSON"])

                with result_tab1:
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("Status", "Completed")
                        st.metric("Confidence", "95%")
                    with col_b:
                        st.metric("Processing Time", "2.3s")
                        st.metric("Pages", "1")

                with result_tab2:
                    st.write("**Vendor:** Acme Corp")
                    st.write("**Invoice #:** INV-2026-001")
                    st.write("**Date:** 2026-01-15")
                    st.write("**Total:** $1,250.00")
                    st.write("**Items:** 5 line items")

                with result_tab3:
                    st.json({
                        "document_id": "doc_abc123",
                        "status": "completed",
                        "confidence": 0.95,
                        "extracted_data": {
                            "vendor_name": "Acme Corp",
                            "invoice_number": "INV-2026-001",
                            "total": 1250.00
                        }
                    })

                if enable_analysis:
                    st.divider()
                    st.subheader("Analysis Results")

                    analysis_tab1, analysis_tab2 = st.tabs(["Anomalies", "Insights"])

                    with analysis_tab1:
                        st.info("No anomalies detected")

                    with analysis_tab2:
                        st.write("**Spending Trend:** +12% vs. previous month")
                        st.write("**Vendor Ranking:** #3 of 15 vendors")

    else:
        st.info("Please upload a PDF document to get started.")

        with st.expander("Supported Document Types"):
            st.write("""
            - **Invoices**: Vendor invoices, purchase orders
            - **Contracts**: Service agreements, NDAs
            - **Receipts**: Purchase receipts, expense receipts
            - **Forms**: Application forms, intake forms
            """)


__all__ = ["render_upload_page"]
