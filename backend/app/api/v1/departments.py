from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import TenantContext, get_tenant_context, require_role
from app.core.database import get_db
from app.core.permissions import RoleEnum
from app.models.audit import AuditLog
from app.models.department import Department
from app.schemas.rbac import DepartmentCreate, DepartmentResponse, DepartmentUpdate

router = APIRouter(prefix="/departments", tags=["departments"])


def _department_response(department: Department) -> DepartmentResponse:
    return DepartmentResponse(
        id=department.id,
        name=department.name,
        description=department.description,
        organization_id=department.organization_id,
        is_active=department.is_active,
    )


def _audit(action: str, department: Department) -> AuditLog:
    return AuditLog(
        organization_id=department.organization_id,
        user_id=None,
        action=action,
        resource_type="department",
        resource_id=str(department.id),
        status="success",
        new_value={"name": department.name},
    )


@router.get("", response_model=list[DepartmentResponse], dependencies=[Depends(require_role([RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN]))])
async def list_departments(
    db: Annotated[AsyncSession, Depends(get_db)],
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
) -> list[DepartmentResponse]:
    query = select(Department)
    if tenant.organization_id is not None:
        query = query.where(Department.organization_id == tenant.organization_id)
    result = await db.execute(query)
    return [_department_response(department) for department in result.scalars().all()]


@router.post("", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role([RoleEnum.SUPER_ADMIN]))])
async def create_department(
    payload: DepartmentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
) -> DepartmentResponse:
    if tenant.organization_id is not None and payload.organization_id != tenant.organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organization mismatch")
    department = Department(
        organization_id=payload.organization_id,
        name=payload.name,
        description=payload.description,
    )
    db.add(department)
    await db.flush()
    db.add(_audit("department_created", department))
    await db.commit()
    await db.refresh(department)
    return _department_response(department)


@router.put("/{dept_id}", response_model=DepartmentResponse, dependencies=[Depends(require_role([RoleEnum.SUPER_ADMIN]))])
async def update_department(
    dept_id: UUID,
    payload: DepartmentUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
) -> DepartmentResponse:
    result = await db.execute(select(Department).where(Department.id == dept_id))
    department = result.scalar_one_or_none()
    if department is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    if tenant.organization_id is not None and department.organization_id != tenant.organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organization mismatch")
    if payload.name is not None:
        department.name = payload.name
    if payload.description is not None:
        department.description = payload.description
    db.add(_audit("department_updated", department))
    await db.commit()
    await db.refresh(department)
    return _department_response(department)


@router.delete("/{dept_id}", dependencies=[Depends(require_role([RoleEnum.SUPER_ADMIN]))])
async def delete_department(
    dept_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
) -> dict[str, str]:
    result = await db.execute(select(Department).where(Department.id == dept_id))
    department = result.scalar_one_or_none()
    if department is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    if tenant.organization_id is not None and department.organization_id != tenant.organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organization mismatch")
    db.add(_audit("department_deleted", department))
    await db.delete(department)
    await db.commit()
    return {"message": "Department deleted"}
