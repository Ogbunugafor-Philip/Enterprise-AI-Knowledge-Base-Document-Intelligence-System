from dataclasses import dataclass
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import RoleEnum, normalize_role
from app.models.audit import AuditLog


class IsolationViolationError(Exception):
    def __init__(self, message: str = "Cross-tenant access denied") -> None:
        self.message = message
        super().__init__(message)


@dataclass(frozen=True)
class TenantScope:
    organization_id: UUID | None
    user_id: UUID | None = None
    role: RoleEnum | str | None = None

    def assert_same_tenant(self, target_organization_id: UUID | None) -> None:
        role = normalize_role(self.role)
        if role == RoleEnum.SUPER_ADMIN:
            return
        if self.organization_id is None or target_organization_id != self.organization_id:
            self.log_violation("Tenant isolation violation")
            raise IsolationViolationError("Cross-tenant access denied")

    def apply(self, query: Any, model: Any) -> Any:
        role = normalize_role(self.role)
        if role == RoleEnum.SUPER_ADMIN:
            return query
        if self.organization_id is None:
            self.log_violation("Missing tenant context")
            raise IsolationViolationError("Missing tenant context")
        return query.where(model.organization_id == self.organization_id)

    def log_violation(self, message: str) -> None:
        # Database-backed audit/alert logging is performed by request handlers.
        # This hook keeps pure isolation checks testable without a live DB.
        object.__setattr__(self, "last_violation", {"severity": "HIGH", "message": message})

    async def log_violation_to_audit(
        self,
        db: AsyncSession,
        message: str,
        target_organization_id: UUID | None,
    ) -> None:
        db.add(
            AuditLog(
                organization_id=self.organization_id,
                user_id=self.user_id,
                action="ISOLATION_VIOLATION",
                resource_type="tenant_scope",
                resource_id=str(target_organization_id) if target_organization_id else None,
                status="blocked",
                new_value={"severity": "HIGH", "message": message},
            )
        )


@dataclass(frozen=True)
class ChatIsolation:
    tenant_scope: TenantScope

    def assert_can_access_session(self, session: Any) -> None:
        role = normalize_role(self.tenant_scope.role)
        if role == RoleEnum.SUPER_ADMIN:
            return
        if role == RoleEnum.ADMIN:
            self.tenant_scope.assert_same_tenant(session.organization_id)
            return
        if session.user_id != self.tenant_scope.user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chat access denied")


@dataclass(frozen=True)
class DocumentIsolation:
    tenant_scope: TenantScope

    def assert_can_access_document(self, document: Any, user: Any) -> None:
        role = normalize_role(self.tenant_scope.role)
        if role != RoleEnum.SUPER_ADMIN:
            self.tenant_scope.assert_same_tenant(document.organization_id)
        if document.status in {"archived", "deleted", "expired"} or not document.is_approved:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Document is not accessible")
        if document.department_id and role != RoleEnum.SUPER_ADMIN:
            if getattr(user, "department_id", None) != document.department_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Department document access denied")
