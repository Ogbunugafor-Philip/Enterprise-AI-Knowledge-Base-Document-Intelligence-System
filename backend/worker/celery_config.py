import os

from celery import Celery
from celery.schedules import crontab

redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "ent_rag_worker",
    broker=redis_url,
    backend=redis_url,
    include=[
        "worker.tasks.document_processing",
        "worker.tasks.document_tasks",
        "worker.tasks.embedding_generation",
        "worker.tasks.monitoring",
        "worker.tasks.compliance",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "document_processing.*": {"queue": "document_processing"},
        "document_processing.process_document_task": {"queue": "document_queue"},
        "document_processing.reprocess_document_task": {"queue": "document_queue"},
        "document_processing.delete_document_embeddings_task": {"queue": "document_queue"},
        "embedding_generation.*": {"queue": "embedding_generation"},
        "monitoring.*": {"queue": "monitoring"},
        "compliance.*": {"queue": "compliance"},
    },
    task_default_queue="default",
    task_default_retry_delay=30,
    task_time_limit=600,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    beat_schedule={
        "run-alert-checks": {
            "task": "monitoring.run_alert_checks",
            "schedule": 300.0,
        },
        "process-error-analysis": {
            "task": "monitoring.process_error_analysis",
            "schedule": 600.0,
        },
        "cleanup-old-monitoring-logs": {
            "task": "monitoring.cleanup_old_monitoring_logs",
            "schedule": crontab(hour=2, minute=0),
        },
        "compliance-monitoring-cleanup": {
            "task": "compliance.run_monitoring_cleanup",
            "schedule": crontab(hour=2, minute=0),
        },
        "compliance-chat-retention": {
            "task": "compliance.run_chat_retention",
            "schedule": crontab(hour=3, minute=0),
        },
        "compliance-document-retention": {
            "task": "compliance.run_document_retention",
            "schedule": crontab(hour=3, minute=0),
        },
        "compliance-audit-integrity-check": {
            "task": "compliance.run_audit_integrity_check",
            "schedule": crontab(hour=1, minute=0, day_of_week="sun"),
        },
    },
)
