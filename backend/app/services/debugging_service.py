import json
import re
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.monitoring import MonitoringLog, SystemAlert
from app.schemas.monitoring import DebuggingAnalysis


def _fallback_analysis(error_entry: dict) -> DebuggingAnalysis:
    error_msg = (
        error_entry.get("error_message")
        or error_entry.get("description")
        or "An error occurred in the system."
    )
    service = error_entry.get("service_name") or error_entry.get("affected_service") or "unknown"
    endpoint = error_entry.get("endpoint") or error_entry.get("affected_endpoint")
    status = error_entry.get("status_code", 500)

    if isinstance(status, int) and status >= 500:
        severity = "high"
    elif isinstance(status, int) and status >= 400:
        severity = "medium"
    else:
        severity = "low"

    return DebuggingAnalysis(
        plain_english_explanation=f"An error occurred in the {service} service: {error_msg[:200]}",
        possible_cause="The system encountered an unexpected condition. Check service logs for details.",
        affected_service=service,
        affected_endpoint=endpoint,
        business_impact="Users may experience degraded functionality or errors.",
        recommended_steps=[
            "Check the service error logs",
            "Verify service dependencies are running",
            "Review recent configuration changes",
            "Restart the affected service if the issue persists",
        ],
        severity=severity,
    )


def _parse_llm_to_analysis(raw: str, error_entry: dict) -> DebuggingAnalysis:
    try:
        json_match = re.search(r"\{.*\}", raw, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            steps = data.get("recommended_steps", [])
            if isinstance(steps, str):
                steps = [s.strip() for s in steps.split("\n") if s.strip()]
            return DebuggingAnalysis(
                plain_english_explanation=str(data.get("plain_english_explanation", "")),
                possible_cause=str(data.get("possible_cause", "")),
                affected_service=str(data.get("affected_service", "unknown")),
                affected_endpoint=data.get("affected_endpoint"),
                business_impact=str(data.get("business_impact", "")),
                recommended_steps=steps[:5] if steps else ["Review system logs"],
                severity=str(data.get("severity", "medium")).lower(),
            )
    except Exception:
        pass
    return _fallback_analysis(error_entry)


def analyze_error_log(error_entry: dict) -> DebuggingAnalysis:
    try:
        from app.services.rag_service import call_cerebras_llm

        system_prompt = (
            "You are an expert system reliability engineer. "
            "Analyze the provided error log entry and respond ONLY with a JSON object containing: "
            "plain_english_explanation (what happened in simple terms), "
            "possible_cause (most likely reason), "
            "affected_service (which service), "
            "affected_endpoint (which endpoint, or null), "
            "business_impact (effect on users and business), "
            "recommended_steps (array of 3-5 practical steps), "
            "severity (low/medium/high/critical)."
        )
        user_prompt = f"Error log entry:\n{json.dumps(error_entry, indent=2, default=str)}"
        raw, _ = call_cerebras_llm(system_prompt, user_prompt)
        if raw and not raw.startswith("LLM unavailable"):
            return _parse_llm_to_analysis(raw, error_entry)
    except Exception:
        pass
    return _fallback_analysis(error_entry)


async def process_new_errors(db: AsyncSession, organization_id: UUID) -> int:
    since = datetime.now(timezone.utc) - timedelta(minutes=10)
    result = await db.execute(
        select(MonitoringLog).where(
            and_(
                MonitoringLog.organization_id == organization_id,
                MonitoringLog.status_code >= 500,
                MonitoringLog.created_at >= since,
                MonitoringLog.error_message.isnot(None),
            )
        ).limit(20)
    )
    error_logs = list(result.scalars().all())

    processed = 0
    for log in error_logs:
        entry = {
            "service_name": log.service_name,
            "endpoint": log.endpoint,
            "method": log.method,
            "status_code": log.status_code,
            "error_message": log.error_message,
            "event_type": log.event_type,
        }
        analysis = analyze_error_log(entry)
        db.add(
            SystemAlert(
                organization_id=organization_id,
                alert_type=f"auto_analyzed_{log.event_type}",
                severity=analysis.severity,
                title=analysis.plain_english_explanation[:255],
                description=f"Cause: {analysis.possible_cause}\n\nImpact: {analysis.business_impact}",
                affected_service=analysis.affected_service,
                recommended_action="\n".join(analysis.recommended_steps[:3]),
                business_impact=analysis.business_impact,
            )
        )
        processed += 1

    if processed > 0:
        await db.flush()
    return processed


async def get_debugging_history(
    db: AsyncSession,
    organization_id: UUID,
    severity: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> list[dict]:
    offset = (page - 1) * page_size
    filters = [
        SystemAlert.organization_id == organization_id,
        SystemAlert.alert_type.like("auto_analyzed_%"),
    ]
    if severity:
        filters.append(SystemAlert.severity == severity)

    result = await db.execute(
        select(SystemAlert)
        .where(*filters)
        .order_by(SystemAlert.created_at.desc())
        .limit(page_size)
        .offset(offset)
    )
    alerts = list(result.scalars().all())
    return [
        {
            "id": str(a.id),
            "title": a.title,
            "description": a.description,
            "severity": a.severity,
            "affected_service": a.affected_service,
            "recommended_action": a.recommended_action,
            "created_at": a.created_at.isoformat(),
        }
        for a in alerts
    ]


async def generate_incident_summary(
    db: AsyncSession,
    incident_id: UUID,
    organization_id: UUID,
) -> str:
    from app.models.monitoring import IncidentReport

    result = await db.execute(
        select(IncidentReport).where(
            IncidentReport.id == incident_id,
            IncidentReport.organization_id == organization_id,
        )
    )
    incident = result.scalar_one_or_none()
    if incident is None:
        return "Incident not found."

    alerts_result = await db.execute(
        select(SystemAlert).where(
            SystemAlert.organization_id == organization_id,
            SystemAlert.title.contains(incident.title[:30] if incident.title else ""),
        ).limit(10)
    )
    related_alerts = list(alerts_result.scalars().all())

    try:
        from app.services.rag_service import call_cerebras_llm

        incident_data = {
            "title": incident.title,
            "description": incident.description,
            "severity": incident.severity,
            "error_count": incident.error_count,
            "first_occurrence": incident.first_occurrence.isoformat() if incident.first_occurrence else None,
            "last_occurrence": incident.last_occurrence.isoformat() if incident.last_occurrence else None,
            "related_alerts_count": len(related_alerts),
        }
        system_prompt = (
            "You are an incident response specialist. "
            "Generate a comprehensive incident summary with: timeline, business impact, and resolution steps."
        )
        user_prompt = f"Incident data:\n{json.dumps(incident_data, indent=2)}"
        raw, _ = call_cerebras_llm(system_prompt, user_prompt)
        if raw and not raw.startswith("LLM unavailable"):
            return raw
    except Exception:
        pass

    return (
        f"Incident: {incident.title}\n"
        f"Severity: {incident.severity}\n"
        f"Error count: {incident.error_count}\n"
        f"First seen: {incident.first_occurrence}\n"
        f"Last seen: {incident.last_occurrence}\n"
        f"Status: {incident.status}"
    )
