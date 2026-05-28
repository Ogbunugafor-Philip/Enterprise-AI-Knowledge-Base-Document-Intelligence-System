from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, require_role
from app.core.database import get_db
from app.core.permissions import RoleEnum
from app.models.user import User
from app.schemas.approval import DocumentAccessRuleCreate, DocumentAccessRuleResponse
from app.services import access_rule_service

router = APIRouter(prefix="/admin/documents", tags=["admin-access-rules"])


def _rule_response(rule) -> DocumentAccessRuleResponse:
    return DocumentAccessRuleResponse(
        id=rule.id,
        document_id=rule.document_id,
        access_type=rule.access_type,
        department_id=rule.department_id,
        role_id=rule.role_id,
        user_id=rule.user_id,
        granted_by=rule.granted_by,
        granted_at=rule.granted_at,
    )


@router.post(
    "/{document_id}/access-rules",
    response_model=DocumentAccessRuleResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role([RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN]))],
)
async def create_access_rule(
    document_id: UUID,
    payload: DocumentAccessRuleCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> DocumentAccessRuleResponse:
    rule = await access_rule_service.create_access_rule(
        db=db,
        document_id=document_id,
        current_user=current_user,
        access_type=payload.access_type,
        department_id=payload.department_id,
        role_id=payload.role_id,
        user_id=payload.user_id,
    )
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    await db.commit()
    await db.refresh(rule)
    return _rule_response(rule)


@router.get(
    "/{document_id}/access-rules",
    response_model=list[DocumentAccessRuleResponse],
    dependencies=[Depends(require_role([RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN]))],
)
async def list_access_rules(
    document_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> list[DocumentAccessRuleResponse]:
    rules = await access_rule_service.get_document_access_rules(
        db, document_id, current_user.organization_id
    )
    return [_rule_response(rule) for rule in rules]


@router.delete(
    "/{document_id}/access-rules/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role([RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN]))],
)
async def delete_access_rule(
    document_id: UUID,
    rule_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> None:
    deleted = await access_rule_service.delete_access_rule(
        db, rule_id, current_user.organization_id, current_user
    )
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Access rule not found")
    await db.commit()
