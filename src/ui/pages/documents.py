"""
Streamlit page for viewing documents.
"""
import streamlit as st
from datetime import datetime, timedelta


def render_documents_page():
    """Render the documents listing page."""
    st.header("Documents")

    # Mock document data
    documents = [
        {
            "id": "doc_001",
            "name": "invoice_acme_001.pdf",
            "type": "invoice",
            "status": "completed",
            "uploaded_at": "2026-02-10 09:30",
            "vendor": "Acme Corp",
            "total": 1250.00,
            "confidence": 0.95
        },
        {
            "id": "doc_002",
            "name": "invoice_techsup_002.pdf",
            "type": "invoice",
            "status": "completed",
            "uploaded_at": "2026-02-10 10:15",
            "vendor": "TechSupply Inc",
            "total": 3400.50,
            "confidence": 0.92
        },
        {
            "id": "doc_003",
            "name": "contract_service_001.pdf",
            "type": "contract",
            "status": "pending_approval",
            "uploaded_at": "2026-02-11 14:20",
            "vendor": "CloudServices LLC",
            "total": 15000.00,
            "confidence": 0.88
        },
        {
            "id": "doc_004",
            "name": "receipt_office_001.pdf",
            "type": "receipt",
            "status": "completed",
            "uploaded_at": "2026-02-12 11:45",
            "vendor": "Office Depot",
            "total": 234.99,
            "confidence": 0.97
        },
        {
            "id": "doc_005",
            "name": "invoice_acme_002.pdf",
            "type": "invoice",
            "status": "analyzed",
            "uploaded_at": "2026-02-13 08:00",
            "vendor": "Acme Corp",
            "total": 1890.00,
            "confidence": 0.91,
            "anomalies": 2
        },
    ]

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        filter_type = st.selectbox("Document Type", ["all", "invoice", "contract", "receipt", "form"])

    with col2:
        filter_status = st.selectbox("Status", ["all", "completed", "pending_approval", "analyzed", "failed"])

    with col3:
        search = st.text_input("Search", placeholder="Search by name or vendor...")

    # Apply filters
    filtered_docs = documents
    if filter_type != "all":
        filtered_docs = [d for d in filtered_docs if d["type"] == filter_type]
    if filter_status != "all":
        filtered_docs = [d for d in filtered_docs if d["status"] == filter_status]
    if search:
        filtered_docs = [d for d in filtered_docs if search.lower() in d["name"].lower() or search.lower() in d.get("vendor", "").lower()]

    st.divider()

    # Display documents
    st.write(f"Showing {len(filtered_docs)} documents")

    for doc in filtered_docs:
        with st.expander(f"{doc['name']} - {doc['vendor']}", expanded=False):
            col_left, col_right = st.columns([3, 1])

            with col_left:
                st.write(f"**Type:** {doc['type'].title()}")
                st.write(f"**Uploaded:** {doc['uploaded_at']}")
                if "vendor" in doc:
                    st.write(f"**Vendor:** {doc['vendor']}")
                if "total" in doc:
                    st.write(f"**Total:** ${doc['total']:,.2f}")

            with col_right:
                status_color = {
                    "completed": "green",
                    "pending_approval": "orange",
                    "analyzed": "blue",
                    "failed": "red"
                }.get(doc["status"], "gray")

                st.markdown(f"<span style='color:{status_color}'>●</span> {doc['status'].replace('_', ' ').title()}", unsafe_allow_html=True)

                if "confidence" in doc:
                    st.metric("Confidence", f"{doc['confidence']*100:.0f}%")

                if "anomalies" in doc and doc["anomalies"] > 0:
                    st.error(f"{doc['anomalies']} anomalies")

            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.button("View Details", key=f"view_{doc['id']}")
            with col_b:
                st.button("Re-process", key=f"reprocess_{doc['id']}")
            with col_c:
                st.button("Delete", key=f"delete_{doc['id']}")


__all__ = ["render_documents_page"]
