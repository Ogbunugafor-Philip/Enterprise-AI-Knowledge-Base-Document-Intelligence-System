from worker.celery_config import celery_app


@celery_app.task(name="embedding_generation.generate_embeddings")
def generate_embeddings(document_id: str, organization_id: str) -> dict[str, str]:
    return {
        "status": "queued",
        "document_id": document_id,
        "organization_id": organization_id,
    }
