import asyncio

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.monitoring import MonitoringLog, SystemAlert
from app.models.organization import Organization
from app.services import backup_service


async def _first_organization_id(db):
    result = await db.execute(select(Organization.id).where(Organization.is_active.is_(True)).limit(1))
    return result.scalar_one_or_none()


async def _daily_full_backup() -> dict:
    async with SessionLocal() as db:
        organization_id = await _first_organization_id(db)
        try:
            manifest = await backup_service.run_full_backup(db, organization_id=organization_id)
            if organization_id:
                db.add(MonitoringLog(organization_id=organization_id, event_type="backup_completed", service_name="backup_worker", status_code=200, token_usage=manifest.model_dump(mode="json")))
            await db.commit()
            return manifest.model_dump(mode="json")
        except Exception as exc:
            if organization_id:
                db.add(MonitoringLog(organization_id=organization_id, event_type="backup_failed", service_name="backup_worker", status_code=500, error_message=str(exc)))
            await db.commit()
            return {"error": str(exc)}


async def _weekly_integrity_check() -> dict:
    async with SessionLocal() as db:
        organization_id = await _first_organization_id(db)
        history = await backup_service.get_backup_history()
        if not history.backups:
            return {"checked": False, "reason": "no backups"}
        report = await backup_service.verify_backup_integrity(history.backups[0].backup_id)
        if organization_id:
            if not report.all_passed:
                db.add(SystemAlert(organization_id=organization_id, alert_type="backup_integrity_failed", severity="critical", title="Backup integrity check failed", description=str(report.failed_checks), affected_service="backup"))
            db.add(MonitoringLog(organization_id=organization_id, event_type="backup_integrity_checked", service_name="backup_worker", status_code=200 if report.all_passed else 500, token_usage=report.model_dump(mode="json")))
        await db.commit()
        return report.model_dump(mode="json")


async def _monthly_cleanup() -> dict:
    async with SessionLocal() as db:
        organization_id = await _first_organization_id(db)
        result = await backup_service.cleanup_old_backups(db, organization_id=organization_id)
        if organization_id:
            db.add(MonitoringLog(organization_id=organization_id, event_type="backup_cleanup_completed", service_name="backup_worker", status_code=200, token_usage=result))
        await db.commit()
        return result


def daily_full_backup_task() -> dict:
    return asyncio.run(_daily_full_backup())


def weekly_backup_integrity_check_task() -> dict:
    return asyncio.run(_weekly_integrity_check())


def monthly_backup_cleanup_task() -> dict:
    return asyncio.run(_monthly_cleanup())
