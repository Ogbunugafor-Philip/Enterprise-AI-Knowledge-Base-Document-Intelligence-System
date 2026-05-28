from worker.celery_config import celery_app


@celery_app.task(name="monitoring.capture_health_snapshot")
def capture_health_snapshot() -> dict[str, str]:
    return {"status": "queued", "task": "capture_health_snapshot"}


@celery_app.task(name="monitoring.run_alert_checks", bind=True, max_retries=3)
def run_alert_checks(self) -> dict:
    from app.workers.monitoring_tasks import run_alert_checks_task
    return run_alert_checks_task()


@celery_app.task(name="monitoring.process_error_analysis", bind=True, max_retries=3)
def process_error_analysis(self) -> dict:
    from app.workers.monitoring_tasks import process_error_analysis_task
    return process_error_analysis_task()


@celery_app.task(name="monitoring.cleanup_old_monitoring_logs")
def cleanup_old_monitoring_logs() -> dict:
    from app.workers.monitoring_tasks import cleanup_old_monitoring_logs_task
    return cleanup_old_monitoring_logs_task()
