import json
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession


def _llm(system_prompt: str, user_prompt: str) -> str:
    try:
        from app.services.rag_service import call_cerebras_llm
        answer, _ = call_cerebras_llm(system_prompt, user_prompt)
        if answer and not answer.startswith("LLM unavailable"):
            return answer
    except Exception:
        pass
    return ""


async def generate_system_health_summary(
    db: AsyncSession, organization_id: UUID
) -> str:
    from app.services.monitoring_service import get_system_metrics
    from app.services.alert_service import get_active_alerts

    try:
        metrics = await get_system_metrics(db, organization_id, period="1h")
        alerts = await get_active_alerts(db, organization_id)
        alert_summary = [{"type": a.alert_type, "severity": a.severity} for a in alerts[:5]]

        system_prompt = (
            "You are an enterprise system health monitor. "
            "You receive system metrics and alert data. "
            "Summarize the system health in 3 to 5 plain English sentences. "
            "Highlight concerning trends and what is working well. "
            "Be factual, concise, and professional."
        )
        user_prompt = (
            f"Current metrics (last 1 hour):\n{json.dumps(metrics, indent=2)}\n\n"
            f"Active alerts: {json.dumps(alert_summary, indent=2)}\n\n"
            "Summarize system health."
        )
        result = _llm(system_prompt, user_prompt)
        if result:
            return result
    except Exception:
        pass
    return (
        "System health data is available for review. "
        "AI summarization is temporarily unavailable. "
        "Please review the metrics and alerts directly."
    )


async def generate_usage_trend_summary(
    db: AsyncSession, organization_id: UUID
) -> str:
    from app.services.monitoring_service import get_system_metrics

    try:
        metrics = await get_system_metrics(db, organization_id, period="7d")
        system_prompt = (
            "You are a business analytics assistant. "
            "Summarize the platform usage trends in plain English. "
            "Focus on patterns, growth, and anomalies."
        )
        user_prompt = (
            f"Usage data for last 7 days:\n{json.dumps(metrics, indent=2)}\n\n"
            "Describe usage patterns and notable trends."
        )
        result = _llm(system_prompt, user_prompt)
        if result:
            return result
    except Exception:
        pass
    return "Usage trend data is available. AI summarization is temporarily unavailable."


async def generate_ai_trust_report(
    db: AsyncSession, organization_id: UUID
) -> str:
    from app.services.rag_logging_service import get_ai_quality_analytics

    try:
        analytics = await get_ai_quality_analytics(db, organization_id, days=30)
        system_prompt = (
            "You are an AI reliability auditor. "
            "Generate a concise trust and reliability report for administrators. "
            "Include confidence levels, hallucination rates, and recommendations."
        )
        user_prompt = (
            f"AI quality analytics (last 30 days):\n{json.dumps(analytics, indent=2)}\n\n"
            "Generate a trust and reliability report."
        )
        result = _llm(system_prompt, user_prompt)
        if result:
            return result
    except Exception:
        pass
    return "AI trust report data is available. AI summarization is temporarily unavailable."


async def analyze_system_risk(
    db: AsyncSession, organization_id: UUID
) -> dict:
    from app.services.alert_service import get_active_alerts
    from app.services.monitoring_service import get_system_metrics

    try:
        metrics = await get_system_metrics(db, organization_id, period="1h")
        alerts = await get_active_alerts(db, organization_id)
        alert_data = [
            {"type": a.alert_type, "severity": a.severity, "title": a.title}
            for a in alerts
        ]

        system_prompt = (
            "You are a system risk analyst. "
            "Analyze the provided metrics and alerts. "
            "Return a JSON object with: "
            "overall_risk_level (low/medium/high/critical), "
            "top_risk_factors (list of 3 strings), "
            "immediate_actions (list of 3 strings), "
            "predicted_impact (string)."
        )
        user_prompt = (
            f"Metrics:\n{json.dumps(metrics, indent=2)}\n\n"
            f"Active alerts:\n{json.dumps(alert_data, indent=2)}\n\n"
            "Analyze risk."
        )
        raw = _llm(system_prompt, user_prompt)
        if raw:
            import re
            json_match = re.search(r"\{.*\}", raw, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
    except Exception:
        pass

    critical_count = sum(1 for a in alerts if a.severity == "critical") if alerts else 0
    high_count = sum(1 for a in alerts if a.severity == "high") if alerts else 0

    if critical_count > 0:
        level = "critical"
    elif high_count > 0:
        level = "high"
    elif (alerts or 0) and len(alerts) > 3:
        level = "medium"
    else:
        level = "low"

    return {
        "overall_risk_level": level,
        "top_risk_factors": [
            f"Active alerts: {len(alerts) if alerts else 0}",
            f"Error rate: {metrics.get('error_rate_percent', 0):.1f}%",
            f"Failed AI calls: {metrics.get('failed_ai_calls', 0)}",
        ],
        "immediate_actions": [
            "Review active alerts",
            "Check system error logs",
            "Verify AI service connectivity",
        ],
        "predicted_impact": "System degradation may affect user experience if not addressed.",
    }
