from worker.celery_config import celery_app


@celery_app.task(name="compliance.run_chat_retention")
def run_chat_retention_task():
    from app.workers.compliance_tasks import run_chat_retention_task as run_task

    return run_task()


@celery_app.task(name="compliance.run_document_retention")
def run_document_retention_task():
    from app.workers.compliance_tasks import run_document_retention_task as run_task

    return run_task()


@celery_app.task(name="compliance.run_monitoring_cleanup")
def run_monitoring_cleanup_task():
    from app.workers.compliance_tasks import run_monitoring_cleanup_task as run_task

    return run_task()


@celery_app.task(name="compliance.run_audit_integrity_check")
def run_audit_integrity_check_task():
    from app.workers.compliance_tasks import run_audit_integrity_check_task as run_task

    return run_task()
