"""
Streamlit page for viewing documents.
"""
import streamlit as st
import requests


API_BASE_URL = "http://api:8000"


def render_documents_page():
    """Render the documents listing page."""
    st.header("Documents")

    # Fetch documents from API
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/documents", timeout=10)
        if response.status_code == 200:
            data = response.json()
            documents = data.get("documents", [])
        else:
            st.error(f"Failed to fetch documents: {response.text}")
            documents = []
    except Exception as e:
        st.error(f"Error connecting to API: {e}")
        documents = []

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        filter_type = st.selectbox("Document Type", ["all", "invoice", "contract", "receipt", "form"])

    with col2:
        filter_status = st.selectbox("Status", ["all", "uploaded", "ingesting", "extracting", "analyzing", "awaiting_approval", "processed", "failed"])

    with col3:
        search = st.text_input("Search", placeholder="Search by filename...")

    # Apply filters
    filtered_docs = documents
    if filter_type != "all":
        filtered_docs = [d for d in filtered_docs if d.get("document_type") == filter_type]
    if filter_status != "all":
        filtered_docs = [d for d in filtered_docs if d.get("status") == filter_status]
    if search:
        filtered_docs = [d for d in filtered_docs if search.lower() in d.get("filename", "").lower()]

    st.divider()

    # Display documents
    st.write(f"Showing {len(filtered_docs)} documents")

    if not filtered_docs:
        st.info("No documents found. Upload a document to get started.")
        return

    for doc in filtered_docs:
        extraction = doc.get("extraction", {})
        vendor = extraction.get("data", {}).get("vendor_name", "Unknown") if extraction else "N/A"
        total = extraction.get("data", {}).get("total", 0) if extraction else 0
        confidence = extraction.get("confidence", 0) if extraction else 0

        with st.expander(f"{doc['filename']} - {vendor}", expanded=False):
            col_left, col_right = st.columns([3, 1])

            with col_left:
                st.write(f"**Type:** {doc.get('document_type', 'N/A')}")
                st.write(f"**Uploaded:** {doc.get('uploaded_at', 'N/A')}")
                st.write(f"**Vendor:** {vendor}")
                if total:
                    st.write(f"**Total:** ${float(total):,.2f}")

            with col_right:
                status = doc.get("status", "unknown")
                status_color = {
                    "processed": "green",
                    "awaiting_approval": "orange",
                    "analyzing": "blue",
                    "failed": "red",
                    "ingesting": "yellow",
                    "extracting": "yellow",
                    "uploaded": "gray"
                }.get(status, "gray")

                st.markdown(f"<span style='color:{status_color}'>●</span> {status.replace('_', ' ').title()}", unsafe_allow_html=True)

                if confidence:
                    st.metric("Confidence", f"{confidence*100:.0f}%")

            col_a, col_b, col_c = st.columns(3)
            with col_a:
                if st.button("View Details", key=f"view_{doc['id']}"):
                    st.json(doc)
            with col_b:
                if st.button("Re-process", key=f"reprocess_{doc['id']}"):
                    requests.post(f"{API_BASE_URL}/api/v1/documents/{doc['id']}/process", timeout=30)
                    st.rerun()
            with col_c:
                if st.button("Delete", key=f"delete_{doc['id']}"):
                    requests.delete(f"{API_BASE_URL}/api/v1/documents/{doc['id']}", timeout=10)
                    st.rerun()


__all__ = ["render_documents_page"]
