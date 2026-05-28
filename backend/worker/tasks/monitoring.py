from worker.celery_config import celery_app


@celery_app.task(name="monitoring.capture_health_snapshot")
def capture_health_snapshot() -> dict[str, str]:
    return {"status": "queued", "task": "capture_health_snapshot"}
