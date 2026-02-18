"""
Streamlit page for uploading documents.
"""
import streamlit as st
import requests
from datetime import datetime

API_BASE_URL = "http://api:8000"


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
            with st.spinner("Uploading and processing document..."):
                try:
                    # Upload file to API
                    files = {"files": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                    upload_response = requests.post(
                        f"{API_BASE_URL}/api/v1/documents/upload",
                        files=files,
                        timeout=60
                    )

                    if upload_response.status_code != 202:
                        st.error(f"Upload failed: {upload_response.text}")
                        return

                    upload_data = upload_response.json()
                    document_id = upload_data["documents"][0]["document_id"]

                    st.success(f"Document uploaded! ID: {document_id}")

                    # Trigger processing
                    process_response = requests.post(
                        f"{API_BASE_URL}/api/v1/documents/{document_id}/process",
                        timeout=60
                    )

                    if process_response.status_code == 202:
                        st.info("Processing started...")

                        # Poll for results
                        with st.spinner("Extracting data with Gemini..."):
                            import time
                            for i in range(60):
                                time.sleep(1)
                                status_resp = requests.get(
                                    f"{API_BASE_URL}/api/v1/documents/{document_id}/status",
                                    timeout=10
                                )
                                if status_resp.status_code == 200:
                                    status_data = status_resp.json()
                                    if status_data.get("status") == "processed":
                                        break
                                if i % 10 == 0:
                                    st.write(f"Waiting... {i}s")

                        # Get extraction results
                        extraction_resp = requests.get(
                            f"{API_BASE_URL}/api/v1/extraction/{document_id}",
                            timeout=10
                        )

                        if extraction_resp.status_code == 200:
                            extraction_data = extraction_resp.json()
                            st.success("Document processed successfully!")

                            # Display extraction results
                            st.subheader("Extraction Results")

                            result_tab1, result_tab2, result_tab3 = st.tabs(["Summary", "Details", "Raw JSON"])

                            confidence = extraction_data.get("confidence", 0)
                            confidence_pct = f"{confidence * 100:.0f}%"

                            with result_tab1:
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    st.metric("Status", extraction_data.get("status", "completed"))
                                    st.metric("Confidence", confidence_pct)
                                with col_b:
                                    st.metric("Schema Type", extraction_data.get("schema_type", "N/A"))

                            with result_tab2:
                                extracted_data = extraction_data.get("data", {})
                                for key, value in extracted_data.items():
                                    if value:
                                        st.write(f"**{key}:** {value}")

                            with result_tab3:
                                st.json(extraction_data)

                            # Show analysis if enabled
                            if enable_analysis:
                                st.divider()
                                st.subheader("Analysis Results")

                                # Get analysis
                                analysis_resp = requests.get(
                                    f"{API_BASE_URL}/api/v1/analysis/document/{document_id}",
                                    timeout=10
                                )

                                analysis_tab1, analysis_tab2 = st.tabs(["Anomalies", "Insights"])

                                with analysis_tab1:
                                    if analysis_resp.status_code == 200:
                                        analysis_data = analysis_resp.json()
                                        anomalies = analysis_data.get("anomalies", [])
                                        if anomalies:
                                            for anomaly in anomalies:
                                                severity = anomaly.get("severity", "info")
                                                if severity == "critical":
                                                    st.error(f"**{anomaly.get('anomaly_type', 'Unknown').replace('_', ' ').title()}:** {anomaly.get('description', '')}")
                                                elif severity == "warning":
                                                    st.warning(f"**{anomaly.get('anomaly_type', 'Unknown').replace('_', ' ').title()}:** {anomaly.get('description', '')}")
                                                else:
                                                    st.info(f"**{anomaly.get('anomaly_type', 'Unknown').replace('_', ' ').title()}:** {anomaly.get('description', '')}")
                                        else:
                                            st.success("No anomalies detected!")
                                    else:
                                        st.info("Analysis not available yet")

                                with analysis_tab2:
                                    if analysis_resp.status_code == 200:
                                        analysis_data = analysis_resp.json()
                                        metrics = analysis_data.get("metrics", {})

                                        st.write(f"**Summary:** {analysis_data.get('summary', 'N/A')}")

                                        if metrics:
                                            st.write("**Metrics:**")
                                            for key, value in metrics.items():
                                                st.write(f"- {key}: {value}")
                                    else:
                                        st.info("Analysis not available yet")
                        else:
                            st.warning(f"Extraction status: {extraction_resp.status_code} - {extraction_resp.text}")
                    else:
                        st.error(f"Processing failed ({process_response.status_code}): {process_response.text}")

                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to API. Make sure the API is running at http://localhost:8002")
                except Exception as e:
                    import traceback
                    st.error(f"Error: {str(e)}")
                    with st.expander("Error details"):
                        st.code(traceback.format_exc())

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
