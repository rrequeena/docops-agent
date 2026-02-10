"""
Streamlit UI entry point for DocOps Agent demo.
"""
import streamlit as st

from src.ui.pages.upload import render_upload_page
from src.ui.pages.documents import render_documents_page
from src.ui.pages.analysis import render_analysis_page
from src.ui.pages.approvals import render_approvals_page


# Page configuration
st.set_page_config(
    page_title="DocOps Agent",
    page_icon="📄",
    layout="wide"
)


def main():
    """Main Streamlit app."""

    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to",
        ["Home", "Upload", "Documents", "Analysis", "Approvals", "Settings"]
    )

    if page == "Home":
        render_home()
    elif page == "Upload":
        render_upload_page()
    elif page == "Documents":
        render_documents_page()
    elif page == "Analysis":
        render_analysis_page()
    elif page == "Approvals":
        render_approvals_page()
    elif page == "Settings":
        render_settings()


def render_home():
    """Render the home page."""
    st.title("DocOps Agent - Document Intelligence System")
    st.markdown("""
    Welcome to the DocOps Agent demo! This is a multi-agent document intelligence system
    that can ingest, extract, analyze, and act on documents like invoices, contracts, and more.

    ## Features

    - **Multi-Agent Architecture**: Specialized agents for ingestion, extraction, analysis, and action
    - **Human-in-the-Loop**: Approval gates for high-stakes actions
    - **Full Observability**: LangSmith integration for tracing
    - **Anomaly Detection**: Automatic detection of price spikes, duplicate charges, and more

    ## Getting Started

    Use the sidebar to navigate to different pages:
    - **Upload**: Upload documents for processing
    - **Documents**: View uploaded documents
    - **Analysis**: View analysis results
    - **Approvals**: Review pending approval requests
    - **Settings**: Configure the application

    """)

    # Quick stats
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Documents Processed", "127")
    with col2:
        st.metric("Pending Approvals", "3")
    with col3:
        st.metric("Anomalies Detected", "8")
    with col4:
        st.metric("Active Vendors", "23")


def render_settings():
    """Render the settings page."""
    st.header("Settings")

    st.subheader("API Configuration")
    st.text_input("Anthropic API Key", type="password", value="sk-ant-...")
    st.text_input("OpenAI API Key", type="password", value="sk-...")

    st.subheader("LangSmith")
    st.text_input("LangSmith API Key", type="password")
    st.checkbox("Enable Tracing", value=False)

    st.subheader("Processing")
    st.slider("Confidence Threshold", 0.5, 1.0, 0.8, 0.05)
    st.number_input("Max Concurrent Jobs", min_value=1, max_value=10, value=3)

    st.subheader("Notifications")
    st.checkbox("Email Notifications", value=True)
    st.text_input("Email Address", value="user@example.com")

    if st.button("Save Settings", type="primary"):
        st.success("Settings saved successfully!")


if __name__ == "__main__":
    main()
