from worker.celery_config import celery_app


@celery_app.task(name="backup.daily_full_backup")
def daily_full_backup_task():
    from app.workers.backup_tasks import daily_full_backup_task as run_task
    return run_task()


@celery_app.task(name="backup.weekly_integrity_check")
def weekly_backup_integrity_check_task():
    from app.workers.backup_tasks import weekly_backup_integrity_check_task as run_task
    return run_task()


@celery_app.task(name="backup.monthly_cleanup")
def monthly_backup_cleanup_task():
    from app.workers.backup_tasks import monthly_backup_cleanup_task as run_task
    return run_task()
