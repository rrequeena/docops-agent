"""
Analysis tasks.
"""
from src.tasks.celery import celery_app


@celery_app.task(name="analyze_documents")
def analyze_documents(document_ids: list[str], analysis_type: str):
    """
    Run analysis on multiple documents.
    """
    # TODO: Implement document analysis
    pass


@celery_app.task(name="detect_anomalies")
def detect_anomalies(document_ids: list[str]):
    """
    Detect anomalies in documents.
    """
    # TODO: Implement anomaly detection
    pass
