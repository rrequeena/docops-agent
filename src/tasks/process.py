"""
Document processing tasks.
"""
from src.tasks.celery import celery_app


@celery_app.task(name="process_document")
def process_document(document_id: str):
    """
    Process a document through the agent pipeline.
    """
    # TODO: Implement document processing
    pass


@celery_app.task(name="process_batch")
def process_batch(document_ids: list[str]):
    """
    Process multiple documents in batch.
    """
    # TODO: Implement batch processing
    pass
