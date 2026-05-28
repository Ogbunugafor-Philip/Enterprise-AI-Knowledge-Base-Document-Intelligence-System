from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rag_config import LOW_CONFIDENCE_FLAG_THRESHOLD, MAX_HALLUCINATION_RISK, MIN_RESPONSE_CONFIDENCE
from app.models.audit import AuditLog
from app.models.chat import Message
from app.models.monitoring import IncidentReport, MonitoringLog, SystemAlert


async def save_rag_result(
    db: AsyncSession,
    session_id: UUID,
    user_id: UUID,
    organization_id: UUID,
    answer: str,
    source_documents: list[dict],
    retrieval_confidence: float,
    response_confidence: float,
    hallucination_risk: float,
    response_rejected: bool,
    token_usage: dict,
) -> UUID:
    from decimal import Decimal

    message = Message(
        session_id=session_id,
        user_id=user_id,
        organization_id=organization_id,
        role="assistant",
        content=answer,
        source_documents=source_documents,
        confidence_score=Decimal(str(round(response_confidence, 4))),
        retrieval_score=Decimal(str(round(retrieval_confidence, 4))),
        hallucination_risk_score=Decimal(str(round(hallucination_risk, 4))),
        response_rejected=response_rejected,
    )
    db.add(message)
    await db.flush()
    return message.id


async def save_usage_metrics(
    db: AsyncSession,
    user_id: UUID,
    organization_id: UUID,
    token_usage: dict,
    response_time_ms: int,
    retrieval_confidence: float,
    hallucination_risk: float,
    response_rejected: bool,
) -> None:
    db.add(
        MonitoringLog(
            organization_id=organization_id,
            user_id=user_id,
            event_type="rag_query",
            service_name="rag_pipeline",
            endpoint="/api/v1/chat/ask",
            method="POST",
            status_code=200,
            response_time_ms=response_time_ms,
            token_usage={
                **token_usage,
                "retrieval_confidence": retrieval_confidence,
                "hallucination_risk": hallucination_risk,
                "response_rejected": response_rejected,
            },
        )
    )
    await db.flush()


async def flag_low_confidence_response(
    db: AsyncSession,
    organization_id: UUID,
    question: str,
    response_confidence: float,
    hallucination_risk: float,
    source_document_ids: list[str],
) -> None:
    if response_confidence >= MIN_RESPONSE_CONFIDENCE and hallucination_risk <= MAX_HALLUCINATION_RISK:
        return

    alert = SystemAlert(
        organization_id=organization_id,
        alert_type="low_confidence_ai_response",
        severity="high",
        title="Low confidence AI response detected",
        description=(
            f"Question: {question[:200]}\n"
            f"Response confidence: {response_confidence:.2f}\n"
            f"Hallucination risk: {hallucination_risk:.2f}\n"
            f"Source documents: {', '.join(source_document_ids[:5])}"
        ),
        affected_service="rag_pipeline",
        recommended_action="Review and approve relevant source documents. Consider re-indexing document embeddings.",
    )
    db.add(alert)
    await db.flush()

    for doc_id in source_document_ids:
        count_result = await db.execute(
            select(func.count()).select_from(SystemAlert).where(
                SystemAlert.organization_id == organization_id,
                SystemAlert.alert_type == "low_confidence_ai_response",
                SystemAlert.description.contains(doc_id),
            )
        )
        flag_count = int(count_result.scalar_one() or 0)

        if flag_count >= LOW_CONFIDENCE_FLAG_THRESHOLD:
            existing_incident = await db.execute(
                select(IncidentReport).where(
                    IncidentReport.organization_id == organization_id,
                    IncidentReport.title.contains(doc_id),
                    IncidentReport.status == "open",
                )
            )
            incident = existing_incident.scalar_one_or_none()
            if incident:
                incident.error_count += 1
                incident.last_occurrence = datetime.now(timezone.utc)
            else:
                db.add(
                    IncidentReport(
                        organization_id=organization_id,
                        title=f"Repeated low-confidence responses for document {doc_id}",
                        description=f"Document {doc_id} has triggered {flag_count} low-confidence AI responses.",
                        severity="high",
                        status="open",
                        error_count=flag_count,
                        first_occurrence=datetime.now(timezone.utc),
                        last_occurrence=datetime.now(timezone.utc),
                        affected_services={"document_id": doc_id},
                        business_impact="Users are not receiving reliable AI answers from this document.",
                    )
                )
    await db.flush()


async def get_ai_quality_analytics(
    db: AsyncSession,
    organization_id: UUID,
    days: int = 30,
) -> dict:
    since = datetime.now(timezone.utc) - timedelta(days=days)

    logs_result = await db.execute(
        select(MonitoringLog).where(
            MonitoringLog.organization_id == organization_id,
            MonitoringLog.event_type == "rag_query",
            MonitoringLog.created_at >= since,
        )
    )
    logs = list(logs_result.scalars().all())

    if not logs:
        return {
            "total_queries": 0,
            "avg_retrieval_confidence": 0.0,
            "avg_hallucination_risk": 0.0,
            "total_rejected": 0,
            "total_with_sources": 0,
            "response_quality_trend": [],
        }

    confidences = [float(log.token_usage.get("retrieval_confidence", 0)) for log in logs if log.token_usage]
    risks = [float(log.token_usage.get("hallucination_risk", 0)) for log in logs if log.token_usage]
    rejected_count = sum(1 for log in logs if log.token_usage and log.token_usage.get("response_rejected"))

    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    avg_risk = sum(risks) / len(risks) if risks else 0.0

    return {
        "total_queries": len(logs),
        "avg_retrieval_confidence": round(avg_confidence, 3),
        "avg_hallucination_risk": round(avg_risk, 3),
        "total_rejected": rejected_count,
        "total_with_sources": len(logs) - rejected_count,
        "response_quality_trend": [],
    }


async def get_low_confidence_flags(
    db: AsyncSession,
    organization_id: UUID,
    page: int = 1,
    page_size: int = 20,
) -> list[dict]:
    offset = (page - 1) * page_size
    result = await db.execute(
        select(SystemAlert)
        .where(
            SystemAlert.organization_id == organization_id,
            SystemAlert.alert_type == "low_confidence_ai_response",
        )
        .order_by(SystemAlert.created_at.desc())
        .limit(page_size)
        .offset(offset)
    )
    alerts = list(result.scalars().all())
    return [
        {
            "id": str(alert.id),
            "title": alert.title,
            "description": alert.description,
            "severity": alert.severity,
            "status": alert.status,
            "created_at": alert.created_at.isoformat(),
            "reviewed": alert.status in {"resolved", "ignored"},
        }
        for alert in alerts
    ]
