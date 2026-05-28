import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select

from app.core.database import SessionLocal
from app.models.monitoring import MonitoringLog
from app.models.organization import Organization


async def _run_alert_checks() -> dict:
    async with SessionLocal() as db:
        orgs_result = await db.execute(
            select(Organization.id).where(Organization.is_active.is_(True))
        )
        org_ids = list(orgs_result.scalars().all())
        total_alerts = 0
        for org_id in org_ids:
            from app.services.alert_service import check_and_create_alerts
            alerts = await check_and_create_alerts(db, org_id)
            total_alerts += len(alerts)
            await db.commit()
    return {"alerts_created": total_alerts, "orgs_checked": len(org_ids)}


async def _process_error_analysis() -> dict:
    async with SessionLocal() as db:
        orgs_result = await db.execute(
            select(Organization.id).where(Organization.is_active.is_(True))
        )
        org_ids = list(orgs_result.scalars().all())
        total_processed = 0
        for org_id in org_ids:
            from app.services.debugging_service import process_new_errors
            count = await process_new_errors(db, org_id)
            total_processed += count
            if count > 0:
                await db.commit()
    return {"errors_analyzed": total_processed}


async def _cleanup_old_logs() -> dict:
    cutoff = datetime.now(timezone.utc) - timedelta(days=90)
    async with SessionLocal() as db:
        result = await db.execute(
            delete(MonitoringLog).where(MonitoringLog.created_at < cutoff)
        )
        await db.commit()
        deleted = result.rowcount
    return {"deleted_logs": deleted, "cutoff_date": cutoff.isoformat()}


def run_alert_checks_task() -> dict:
    return asyncio.run(_run_alert_checks())


def process_error_analysis_task() -> dict:
    return asyncio.run(_process_error_analysis())


def cleanup_old_monitoring_logs_task() -> dict:
    return asyncio.run(_cleanup_old_logs())
