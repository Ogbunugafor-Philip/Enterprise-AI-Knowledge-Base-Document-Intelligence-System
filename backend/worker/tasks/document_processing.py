from worker.celery_config import celery_app


@celery_app.task(name="document_processing.process_document")
def process_document(document_id: str, organization_id: str) -> dict[str, str]:
    return {
        "status": "queued",
        "document_id": document_id,
        "organization_id": organization_id,
    }
