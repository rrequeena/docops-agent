"""
Streamlit UI entry point for DocOps Agent demo.
"""
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="DocOps Agent",
    page_icon="📄",
    layout="wide"
)


def main():
    """Main Streamlit app."""
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
    - **Settings**: Configure the application

    """)


if __name__ == "__main__":
    main()
