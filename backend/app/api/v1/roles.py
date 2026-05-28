from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import TenantContext, get_tenant_context, require_role, verify_same_organization
from app.core.database import get_db
from app.core.permissions import RoleEnum
from app.models.audit import AuditLog
from app.models.role import Permission, Role, RolePermission
from app.models.user import User
from app.schemas.rbac import PermissionAssignRequest, PermissionResponse, RoleCreate, RoleResponse, RoleUpdate

router = APIRouter(prefix="/roles", tags=["roles"])


async def _role_response(db: AsyncSession, role: Role) -> RoleResponse:
    result = await db.execute(
        select(Permission)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .where(RolePermission.role_id == role.id)
    )
    permissions = [
        PermissionResponse(id=permission.id, name=permission.name, resource=permission.resource, action=permission.action)
        for permission in result.scalars().all()
    ]
    return RoleResponse(
        id=role.id,
        name=role.name,
        description=role.description,
        organization_id=role.organization_id,
        permissions=permissions,
    )


def _audit(action: str, role: Role, user: User | None = None) -> AuditLog:
    return AuditLog(
        organization_id=role.organization_id,
        user_id=user.id if user else None,
        action=action,
        resource_type="role",
        resource_id=str(role.id),
        status="success",
        new_value={"name": role.name},
    )


@router.get("", response_model=list[RoleResponse], dependencies=[Depends(require_role([RoleEnum.SUPER_ADMIN]))])
async def list_roles(
    db: Annotated[AsyncSession, Depends(get_db)],
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
) -> list[RoleResponse]:
    query = select(Role)
    if tenant.organization_id is not None:
        query = query.where(Role.organization_id == tenant.organization_id)
    result = await db.execute(query)
    return [await _role_response(db, role) for role in result.scalars().all()]


@router.post("", response_model=RoleResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role([RoleEnum.SUPER_ADMIN]))])
async def create_role(
    payload: RoleCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
) -> RoleResponse:
    if tenant.organization_id is not None and payload.organization_id != tenant.organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organization mismatch")
    role = Role(organization_id=payload.organization_id, name=payload.name, description=payload.description)
    db.add(role)
    await db.flush()
    db.add(_audit("role_created", role))
    await db.commit()
    await db.refresh(role)
    return await _role_response(db, role)


@router.put("/{role_id}", response_model=RoleResponse, dependencies=[Depends(require_role([RoleEnum.SUPER_ADMIN]))])
async def update_role(
    role_id: UUID,
    payload: RoleUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
) -> RoleResponse:
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    if tenant.organization_id is not None and role.organization_id != tenant.organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organization mismatch")
    if payload.name is not None:
        role.name = payload.name
    if payload.description is not None:
        role.description = payload.description
    db.add(_audit("role_updated", role))
    await db.commit()
    await db.refresh(role)
    return await _role_response(db, role)


@router.delete("/{role_id}", dependencies=[Depends(require_role([RoleEnum.SUPER_ADMIN]))])
async def delete_role(
    role_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
) -> dict[str, str]:
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    if tenant.organization_id is not None and role.organization_id != tenant.organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organization mismatch")
    db.add(_audit("role_deleted", role))
    await db.delete(role)
    await db.commit()
    return {"message": "Role deleted"}


@router.post("/{role_id}/permissions", response_model=RoleResponse, dependencies=[Depends(require_role([RoleEnum.SUPER_ADMIN]))])
async def assign_permissions(
    role_id: UUID,
    payload: PermissionAssignRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
) -> RoleResponse:
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    verify_same_organization(role.organization_id, type("CurrentUser", (), {"organization_id": tenant.organization_id, "role": type("RoleObj", (), {"name": tenant.role})})())
    await db.execute(delete(RolePermission).where(RolePermission.role_id == role.id))
    for permission_id in payload.permission_ids:
        permission_result = await db.execute(select(Permission).where(Permission.id == permission_id))
        permission = permission_result.scalar_one_or_none()
        if permission is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")
        if tenant.organization_id is not None and permission.organization_id != tenant.organization_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organization mismatch")
        db.add(RolePermission(organization_id=role.organization_id, role_id=role.id, permission_id=permission.id))
    db.add(_audit("role_permissions_assigned", role))
    await db.commit()
    await db.refresh(role)
    return await _role_response(db, role)


@router.get("/{role_id}/permissions", response_model=list[PermissionResponse], dependencies=[Depends(require_role([RoleEnum.SUPER_ADMIN]))])
async def list_role_permissions(
    role_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
) -> list[PermissionResponse]:
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    if tenant.organization_id is not None and role.organization_id != tenant.organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organization mismatch")
    response = await _role_response(db, role)
    return response.permissions
