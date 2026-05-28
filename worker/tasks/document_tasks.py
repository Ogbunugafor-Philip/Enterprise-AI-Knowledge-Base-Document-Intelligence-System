from worker.celery_config import celery_app


@celery_app.task(name="document_processing.process_document_task", bind=True, max_retries=3)
def process_document_task(self, document_id: str):
    from app.workers.document_tasks import process_document_task as run_task

    return run_task(document_id)


@celery_app.task(name="document_processing.reprocess_document_task", bind=True, max_retries=3)
def reprocess_document_task(self, document_id: str):
    from app.workers.document_tasks import reprocess_document_task as run_task

    return run_task(document_id)


@celery_app.task(name="document_processing.delete_document_embeddings_task", bind=True, max_retries=3)
def delete_document_embeddings_task(self, organization_id: str, document_id: str):
    from app.workers.document_tasks import delete_document_embeddings_task as run_task

    return run_task(organization_id, document_id)
