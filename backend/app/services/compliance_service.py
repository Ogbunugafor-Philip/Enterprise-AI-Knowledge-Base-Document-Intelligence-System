import csv
import io
from collections import Counter, defaultdict
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog
from app.models.organization import Organization
from app.schemas.compliance import ComplianceReport


def _date_filters(query, date_from: datetime | None, date_to: datetime | None):
    if date_from:
        query = query.where(AuditLog.created_at >= date_from)
    if date_to:
        query = query.where(AuditLog.created_at <= date_to)
    return query


async def _logs(
    db: AsyncSession,
    organization_id: UUID | None,
    date_from: datetime | None,
    date_to: datetime | None,
    actions: list[str] | None = None,
) -> list[AuditLog]:
    query = select(AuditLog)
    if organization_id is not None:
        query = query.where(AuditLog.organization_id == organization_id)
    if actions:
        query = query.where(AuditLog.action.in_(actions))
    query = _date_filters(query, date_from, date_to)
    result = await db.execute(query.order_by(AuditLog.created_at.desc()))
    return list(result.scalars().all())


def _entry(log: AuditLog) -> dict:
    return {
        "id": str(log.id),
        "organization_id": str(log.organization_id) if log.organization_id else None,
        "user_id": str(log.user_id) if log.user_id else None,
        "action": log.action,
        "resource_type": log.resource_type,
        "resource_id": log.resource_id,
        "status": log.status,
        "ip_address": log.ip_address,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }


async def generate_activity_report(
    db: AsyncSession,
    organization_id: UUID | None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> dict:
    logs = await _logs(db, organization_id, date_from, date_to)
    by_user: dict[str, list[dict]] = defaultdict(list)
    by_action = Counter(log.action for log in logs)
    for log in logs:
        by_user[str(log.user_id) if log.user_id else "system"].append(_entry(log))
    return {
        "total_actions": len(logs),
        "actions_by_type": dict(by_action),
        "actions_by_user": dict(by_user),
        "login_history": [_entry(log) for log in logs if "LOGIN" in log.action],
        "document_access": [_entry(log) for log in logs if log.resource_type == "document"],
        "ai_queries": [_entry(log) for log in logs if log.action == "AI_QUERY_MADE"],
    }


async def generate_access_report(
    db: AsyncSession,
    organization_id: UUID | None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> dict:
    actions = [
        "DOCUMENT_ACCESS_RULE_CREATED",
        "DOCUMENT_ACCESS_RULE_DELETED",
        "PERMISSION_DENIED",
        "ROLE_ASSIGNED",
        "ROLE_BYPASS_ATTEMPTED",
        "ISOLATION_VIOLATION",
    ]
    logs = await _logs(db, organization_id, date_from, date_to, actions)
    return {
        "total_events": len(logs),
        "document_access_events": [_entry(log) for log in logs if "DOCUMENT_ACCESS" in log.action],
        "failed_access_attempts": [_entry(log) for log in logs if log.action in {"PERMISSION_DENIED", "ISOLATION_VIOLATION"}],
        "permission_changes": [_entry(log) for log in logs if log.action in {"ROLE_ASSIGNED", "DOCUMENT_ACCESS_RULE_CREATED", "DOCUMENT_ACCESS_RULE_DELETED"}],
    }


async def generate_document_report(
    db: AsyncSession,
    organization_id: UUID | None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> dict:
    actions = [
        "DOCUMENT_UPLOADED",
        "DOCUMENT_APPROVED",
        "DOCUMENT_REJECTED",
        "DOCUMENT_ARCHIVED",
        "DOCUMENT_DELETED",
        "DOCUMENT_REPROCESSED",
        "DOCUMENT_VERSION_CREATED",
        "DOCUMENT_VERSION_ROLLBACK",
        "DOCUMENT_PROCESSING_STARTED",
        "DOCUMENT_PROCESSING_COMPLETED",
        "DOCUMENT_PROCESSING_FAILED",
    ]
    logs = await _logs(db, organization_id, date_from, date_to, actions)
    return {
        "total_events": len(logs),
        "lifecycle_events": [_entry(log) for log in logs],
        "version_history": [_entry(log) for log in logs if "VERSION" in log.action],
        "approval_history": [_entry(log) for log in logs if log.action in {"DOCUMENT_APPROVED", "DOCUMENT_REJECTED"}],
    }


async def generate_security_report(
    db: AsyncSession,
    organization_id: UUID | None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> dict:
    actions = [
        "LOGIN_FAILED",
        "ACCOUNT_LOCKED",
        "ACCOUNT_UNLOCKED",
        "PERMISSION_DENIED",
        "ROLE_BYPASS_ATTEMPTED",
        "ISOLATION_VIOLATION",
        "PASSWORD_RESET_REQUESTED",
        "PASSWORD_RESET_COMPLETED",
        "ADMIN_PASSWORD_RESET",
    ]
    logs = await _logs(db, organization_id, date_from, date_to, actions)
    return {
        "total_events": len(logs),
        "failed_logins": [_entry(log) for log in logs if log.action == "LOGIN_FAILED"],
        "account_lockouts": [_entry(log) for log in logs if log.action in {"ACCOUNT_LOCKED", "ACCOUNT_UNLOCKED"}],
        "permission_violations": [_entry(log) for log in logs if log.action in {"PERMISSION_DENIED", "ROLE_BYPASS_ATTEMPTED", "ISOLATION_VIOLATION"}],
        "password_resets": [_entry(log) for log in logs if "PASSWORD_RESET" in log.action or log.action == "ADMIN_PASSWORD_RESET"],
    }


async def generate_compliance_report(
    db: AsyncSession,
    report_type: str,
    organization_id: UUID | None,
    generated_by: UUID,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> ComplianceReport:
    generators = {
        "activity": generate_activity_report,
        "access": generate_access_report,
        "document": generate_document_report,
        "security": generate_security_report,
    }
    data = await generators[report_type](db, organization_id, date_from, date_to)
    summary = {
        "report_type": report_type,
        "total_records": data.get("total_actions", data.get("total_events", 0)),
        "date_from": date_from.isoformat() if date_from else None,
        "date_to": date_to.isoformat() if date_to else None,
    }
    return ComplianceReport(
        report_type=report_type,
        organization_id=organization_id,
        date_from=date_from,
        date_to=date_to,
        generated_at=datetime.now(timezone.utc),
        generated_by=generated_by,
        summary=summary,
        data=data,
    )


async def _organization_name(db: AsyncSession, organization_id: UUID | None) -> str:
    if organization_id is None:
        return "All Organizations"
    try:
        result = await db.execute(select(Organization.name).where(Organization.id == organization_id))
        return result.scalar_one_or_none() or str(organization_id)
    except Exception:
        return str(organization_id)


async def export_compliance_report_pdf(db: AsyncSession, report: ComplianceReport) -> bytes:
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        y = height - 72
        org_name = await _organization_name(db, report.organization_id)
        lines = [
            "Ent_RAG Compliance Report",
            f"Organization: {org_name}",
            f"Report type: {report.report_type}",
            f"Date range: {report.date_from or 'beginning'} to {report.date_to or 'now'}",
            f"Generated at: {report.generated_at.isoformat()}",
            f"Summary: {report.summary}",
        ]
        for line in lines:
            pdf.drawString(72, y, str(line)[:110])
            y -= 18
        y -= 18
        for line in str(report.data).splitlines() or [str(report.data)]:
            if y < 72:
                pdf.showPage()
                y = height - 72
            pdf.drawString(72, y, line[:110])
            y -= 14
        pdf.save()
        return buffer.getvalue()
    except Exception:
        return str(report.model_dump()).encode("utf-8")


def export_compliance_report_csv(report: ComplianceReport) -> bytes:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["report_type", "organization_id", "generated_at", "summary"])
    writer.writerow([report.report_type, report.organization_id, report.generated_at.isoformat(), report.summary])
    writer.writerow([])
    writer.writerow(["section", "value"])
    for key, value in report.data.items() if isinstance(report.data, dict) else enumerate(report.data):
        writer.writerow([key, value])
    return output.getvalue().encode("utf-8")
