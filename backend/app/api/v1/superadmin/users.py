from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, require_role
from app.core.cache_config import CacheManager, TTL_DASHBOARD_STATS, get_redis_client, make_cache_key
from app.core.database import get_db
from app.core.permissions import RoleEnum
from app.models.user import User
from app.schemas.user_management import (
    BulkUserUploadResponse,
    PasswordResetByAdminRequest,
    PasswordResetByAdminResponse,
    SuperAdminDashboardStats,
    UserActivationRequest,
    UserActivationResponse,
    UserCreateRequest,
    UserCreateResponse,
    UserDetailResponse,
    UserListResponse,
    UserUpdateRequest,
)
from app.services import bulk_user_service, user_management_service

router = APIRouter(prefix="/superadmin", tags=["superadmin"])

_SUPER_ADMIN_DEP = Depends(require_role([RoleEnum.SUPER_ADMIN]))


# ── Dashboard ──────────────────────────────────────────────────────────────

@router.get(
    "/dashboard/stats",
    response_model=SuperAdminDashboardStats,
    dependencies=[_SUPER_ADMIN_DEP],
)
async def dashboard_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    redis=Depends(get_redis_client),
) -> SuperAdminDashboardStats:
    cache_key = make_cache_key("superadmin_dashboard_stats", "global")
    if redis:
        cached = await CacheManager(redis).get_cached_response(cache_key)
        if cached:
            return SuperAdminDashboardStats(**cached)
    stats = await user_management_service.get_superadmin_dashboard_stats(db)
    if redis:
        await CacheManager(redis).cache_response(cache_key, stats.model_dump(), TTL_DASHBOARD_STATS)
    return stats


# ── Bulk upload (must be declared before /{user_id}) ─────────────────────

@router.get(
    "/users/bulk-upload/template",
    dependencies=[_SUPER_ADMIN_DEP],
)
async def download_bulk_template(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> Response:
    content = bulk_user_service.generate_bulk_upload_template()
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=bulk_user_template.xlsx"},
    )


@router.post(
    "/users/bulk-upload",
    response_model=BulkUserUploadResponse,
    dependencies=[_SUPER_ADMIN_DEP],
)
async def bulk_upload_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    file: UploadFile = File(...),
) -> BulkUserUploadResponse:
    if file.filename and not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only .xlsx and .xls files accepted")
    content = await file.read()
    result = await bulk_user_service.process_bulk_upload(
        db=db,
        organization_id=current_user.organization_id,
        file_bytes=content,
        created_by_user_id=current_user.id,
    )
    await db.commit()
    return result


# ── User list & create ────────────────────────────────────────────────────

@router.get(
    "/users",
    response_model=UserListResponse,
    dependencies=[_SUPER_ADMIN_DEP],
)
async def list_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    organization_id: UUID | None = Query(default=None),
    department_id: UUID | None = Query(default=None),
    role: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    is_verified: bool | None = Query(default=None),
    search_query: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> UserListResponse:
    return await user_management_service.get_user_list(
        db=db,
        organization_id=organization_id,
        department_id=department_id,
        role=role,
        is_active=is_active,
        is_verified=is_verified,
        search_query=search_query,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/users",
    response_model=UserCreateResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[_SUPER_ADMIN_DEP],
)
async def create_user(
    payload: UserCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserCreateResponse:
    user = await user_management_service.create_user(
        db=db,
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=str(payload.email),
        organization_id=payload.organization_id,
        role_id=payload.role_id,
        department_id=payload.department_id,
        send_welcome_email=payload.send_welcome_email,
        created_by_user_id=current_user.id,
    )
    response = user_management_service._user_create_response(user)
    await db.commit()
    return response


# ── Single-user endpoints (/{user_id} LAST to avoid prefix collisions) ───

@router.get(
    "/users/{user_id}",
    response_model=UserDetailResponse,
    dependencies=[_SUPER_ADMIN_DEP],
)
async def get_user(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserDetailResponse:
    detail = await user_management_service.get_user_detail(db, user_id, organization_id=None)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return detail


@router.put(
    "/users/{user_id}",
    response_model=UserDetailResponse,
    dependencies=[_SUPER_ADMIN_DEP],
)
async def update_user(
    user_id: UUID,
    payload: UserUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserDetailResponse:
    detail = await user_management_service.get_user_detail(db, user_id, organization_id=None)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user = await user_management_service.update_user(
        db=db,
        user_id=user_id,
        organization_id=detail.organization_id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        department_id=payload.department_id,
        role_id=payload.role_id,
        is_active=payload.is_active,
        updated_by_user_id=current_user.id,
    )
    user_detail = user_management_service._user_detail(user)
    await db.commit()
    return user_detail


@router.post(
    "/users/{user_id}/activate",
    response_model=UserActivationResponse,
    dependencies=[_SUPER_ADMIN_DEP],
)
async def activate_user(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserActivationResponse:
    detail = await user_management_service.get_user_detail(db, user_id, organization_id=None)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user = await user_management_service.activate_user(
        db, user_id, detail.organization_id, current_user.id
    )
    await db.commit()
    await db.refresh(user)
    return UserActivationResponse(user_id=user.id, email=user.email, is_active=user.is_active, updated_at=user.updated_at)


@router.post(
    "/users/{user_id}/deactivate",
    response_model=UserActivationResponse,
    dependencies=[_SUPER_ADMIN_DEP],
)
async def deactivate_user(
    user_id: UUID,
    payload: UserActivationRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserActivationResponse:
    detail = await user_management_service.get_user_detail(db, user_id, organization_id=None)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user = await user_management_service.deactivate_user(
        db, user_id, detail.organization_id, payload.reason, current_user.id
    )
    await db.commit()
    await db.refresh(user)
    return UserActivationResponse(user_id=user.id, email=user.email, is_active=user.is_active, updated_at=user.updated_at)


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[_SUPER_ADMIN_DEP],
)
async def delete_user(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict[str, str]:
    detail = await user_management_service.get_user_detail(db, user_id, organization_id=None)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await user_management_service.delete_user(
        db, user_id, detail.organization_id, current_user.id
    )
    await db.commit()
    return {"message": "User deleted"}


@router.post(
    "/users/{user_id}/reset-password",
    response_model=PasswordResetByAdminResponse,
    dependencies=[_SUPER_ADMIN_DEP],
)
async def reset_password(
    user_id: UUID,
    payload: PasswordResetByAdminRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> PasswordResetByAdminResponse:
    detail = await user_management_service.get_user_detail(db, user_id, organization_id=None)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    result = await user_management_service.reset_user_password_by_admin(
        db, user_id, detail.organization_id, payload.force_change_on_login, current_user.id
    )
    await db.commit()
    return result


@router.post(
    "/users/{user_id}/unlock",
    dependencies=[_SUPER_ADMIN_DEP],
)
async def unlock_user(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict[str, str]:
    detail = await user_management_service.get_user_detail(db, user_id, organization_id=None)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user = await user_management_service.unlock_user_account(
        db, user_id, detail.organization_id, current_user.id
    )
    await db.commit()
    return {"message": "Account unlocked", "user_id": str(user.id)}
