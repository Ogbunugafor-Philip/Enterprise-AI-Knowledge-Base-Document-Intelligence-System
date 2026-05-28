from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, require_permission, require_role
from app.core.database import get_db
from app.core.permissions import PermissionEnum, RoleEnum
from app.models.user import User
from app.schemas.approval import (
    ApprovalQueueResponse,
    DocumentApprovalRequest,
    DocumentApprovalResponse,
    KnowledgeGovernanceStats,
)
from app.services import approval_service

router = APIRouter(prefix="/admin/approvals", tags=["admin-approvals"])


def _approval_response(document) -> DocumentApprovalResponse:
    return DocumentApprovalResponse(
        document_id=document.id,
        file_name=document.file_name,
        status=document.status,
        approved_by=document.approved_by,
        approved_at=document.approved_at,
        rejection_reason=document.rejection_reason,
    )


@router.get(
    "/queue",
    response_model=ApprovalQueueResponse,
    dependencies=[Depends(require_role([RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN]))],
)
async def get_approval_queue(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ApprovalQueueResponse:
    result = await approval_service.get_approval_queue(
        db, current_user.organization_id, page=page, page_size=page_size
    )
    return ApprovalQueueResponse(**result)


@router.post(
    "/approve",
    response_model=DocumentApprovalResponse,
    dependencies=[Depends(require_permission(PermissionEnum.DOCUMENT_APPROVE))],
)
async def approve_document(
    payload: DocumentApprovalRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> DocumentApprovalResponse:
    if payload.action != "approve":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Use /reject endpoint for rejection")
    document = await approval_service.approve_document(
        db, payload.document_id, current_user, payload.access_level
    )
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    await db.commit()
    await db.refresh(document)
    return _approval_response(document)


@router.post(
    "/reject",
    response_model=DocumentApprovalResponse,
    dependencies=[Depends(require_permission(PermissionEnum.DOCUMENT_REJECT))],
)
async def reject_document(
    payload: DocumentApprovalRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> DocumentApprovalResponse:
    if payload.action != "reject":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Use /approve endpoint for approval")
    if not payload.rejection_reason or not payload.rejection_reason.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="rejection_reason is required")
    document = await approval_service.reject_document(
        db, payload.document_id, current_user, payload.rejection_reason
    )
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    await db.commit()
    await db.refresh(document)
    return _approval_response(document)


@router.get(
    "/{document_id}/history",
    dependencies=[Depends(require_role([RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN]))],
)
async def get_approval_history(
    document_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> list[dict]:
    logs = await approval_service.get_document_approval_history(
        db, document_id, current_user.organization_id
    )
    return [
        {
            "id": str(log.id),
            "action": log.action,
            "user_id": str(log.user_id) if log.user_id else None,
            "new_value": log.new_value,
            "status": log.status,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]


@router.get(
    "/stats",
    response_model=KnowledgeGovernanceStats,
    dependencies=[Depends(require_role([RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN]))],
)
async def get_governance_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> KnowledgeGovernanceStats:
    return await approval_service.get_governance_stats(db, current_user.organization_id)
