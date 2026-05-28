import os

from celery import Celery

redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "ent_rag_worker",
    broker=redis_url,
    backend=redis_url,
    include=[
        "worker.tasks.document_processing",
        "worker.tasks.embedding_generation",
        "worker.tasks.monitoring",
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
        "embedding_generation.*": {"queue": "embedding_generation"},
        "monitoring.*": {"queue": "monitoring"},
    },
    task_default_queue="default",
)
