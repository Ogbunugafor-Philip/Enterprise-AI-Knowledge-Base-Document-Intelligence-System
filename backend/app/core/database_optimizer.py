"""
Database index analysis and slow-query recommendations.
Index creation is handled by the Alembic migration add_performance_indexes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession


# ---------------------------------------------------------------------------
# Expected indexes (must match the Alembic migration)
# ---------------------------------------------------------------------------

EXPECTED_INDEXES: dict[str, list[str]] = {
    "users": ["ix_users_email", "ix_users_organization_id", "ix_users_is_active", "ix_users_role_id"],
    "documents": ["ix_documents_organization_id", "ix_documents_status", "ix_documents_department_id", "ix_documents_created_at"],
    "document_chunks": ["ix_document_chunks_document_id", "ix_document_chunks_organization_id"],
    "messages": ["ix_messages_session_id", "ix_messages_user_id", "ix_messages_organization_id", "ix_messages_created_at"],
    "audit_logs": ["ix_audit_logs_organization_id", "ix_audit_logs_user_id", "ix_audit_logs_action", "ix_audit_logs_created_at"],
    "monitoring_logs": ["ix_monitoring_logs_organization_id", "ix_monitoring_logs_event_type", "ix_monitoring_logs_created_at"],
    "chat_sessions": ["ix_chat_sessions_user_id", "ix_chat_sessions_organization_id", "ix_chat_sessions_created_at"],
}

SLOW_QUERY_THRESHOLD_MS = 1000


@dataclass
class IndexCheckResult:
    table: str
    index_name: str
    exists: bool
    recommendation: str = ""


@dataclass
class SlowQueryReport:
    query: str
    avg_duration_ms: float
    calls: int
    recommendation: str


@dataclass
class PerformanceReport:
    index_checks: list[IndexCheckResult] = field(default_factory=list)
    slow_queries: list[SlowQueryReport] = field(default_factory=list)
    missing_index_count: int = 0
    all_indexes_present: bool = False


async def analyze_query_performance(db: AsyncSession) -> PerformanceReport:
    """Check which expected indexes are present in the live database."""
    report = PerformanceReport()

    try:
        for table, index_names in EXPECTED_INDEXES.items():
            result = await db.execute(
                text(
                    "SELECT indexname FROM pg_indexes WHERE tablename = :table"
                ).bindparams(table=table)
            )
            existing: set[str] = {row[0] for row in result.fetchall()}

            for idx_name in index_names:
                present = idx_name in existing
                check = IndexCheckResult(
                    table=table,
                    index_name=idx_name,
                    exists=present,
                    recommendation="" if present else f"Run Alembic migration to create {idx_name}",
                )
                report.index_checks.append(check)

        report.missing_index_count = sum(1 for c in report.index_checks if not c.exists)
        report.all_indexes_present = report.missing_index_count == 0

    except Exception:
        # Non-fatal — return partial report
        pass

    return report


async def get_slow_queries(db: AsyncSession) -> list[SlowQueryReport]:
    """Return queries exceeding SLOW_QUERY_THRESHOLD_MS using pg_stat_statements if available."""
    slow: list[SlowQueryReport] = []
    try:
        result = await db.execute(
            text(
                """
                SELECT query,
                       mean_exec_time,
                       calls
                FROM   pg_stat_statements
                WHERE  mean_exec_time > :threshold
                ORDER  BY mean_exec_time DESC
                LIMIT  20
                """
            ).bindparams(threshold=SLOW_QUERY_THRESHOLD_MS)
        )
        for row in result.fetchall():
            slow.append(
                SlowQueryReport(
                    query=row[0][:200],
                    avg_duration_ms=round(row[1], 2),
                    calls=row[2],
                    recommendation="Consider adding an index or rewriting the query.",
                )
            )
    except Exception:
        pass
    return slow
