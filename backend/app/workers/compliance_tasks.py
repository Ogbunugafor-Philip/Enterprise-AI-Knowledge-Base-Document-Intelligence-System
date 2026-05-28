import asyncio
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.monitoring import SystemAlert
from app.models.organization import Organization
from app.services import audit_service, data_privacy_service


async def _organization_ids(db):
    result = await db.execute(select(Organization.id).where(Organization.is_active.is_(True)))
    return list(result.scalars().all())


async def _run_chat_retention() -> dict:
    async with SessionLocal() as db:
        total = 0
        for organization_id in await _organization_ids(db):
            total += await data_privacy_service.apply_chat_retention_policy(
                db,
                organization_id,
                data_privacy_service.RETENTION_SETTINGS.chat_retention_days,
            )
        await db.commit()
        return {"deleted_sessions": total}


async def _run_document_retention() -> dict:
    async with SessionLocal() as db:
        total = 0
        for organization_id in await _organization_ids(db):
            total += await data_privacy_service.apply_document_retention_policy(
                db,
                organization_id,
                data_privacy_service.RETENTION_SETTINGS.document_retention_days,
            )
        await db.commit()
        return {"archived_documents": total}


async def _run_monitoring_cleanup() -> dict:
    async with SessionLocal() as db:
        total = 0
        for organization_id in await _organization_ids(db):
            total += await data_privacy_service.apply_monitoring_log_retention(
                db,
                organization_id,
                data_privacy_service.RETENTION_SETTINGS.monitoring_log_retention_days,
            )
        await db.commit()
        return {"deleted_monitoring_logs": total}


async def _run_audit_integrity_check() -> dict:
    async with SessionLocal() as db:
        result = await audit_service.verify_audit_log_integrity(db)
        if not result["valid"]:
            organization_ids = await _organization_ids(db)
            for organization_id in organization_ids:
                db.add(
                    SystemAlert(
                        organization_id=organization_id,
                        alert_type="audit_integrity_violation",
                        severity="critical",
                        title="Audit log integrity violation detected",
                        description=f"Audit hash chain verification failed at {datetime.now(timezone.utc).isoformat()}",
                        affected_service="compliance",
                        recommended_action="Review audit log storage immediately and investigate possible tampering.",
                        business_impact="Compliance audit trail may be unreliable.",
                    )
                )
            await db.commit()
        return result


def run_chat_retention_task() -> dict:
    return asyncio.run(_run_chat_retention())


def run_document_retention_task() -> dict:
    return asyncio.run(_run_document_retention())


def run_monitoring_cleanup_task() -> dict:
    return asyncio.run(_run_monitoring_cleanup())


def run_audit_integrity_check_task() -> dict:
    return asyncio.run(_run_audit_integrity_check())
