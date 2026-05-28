from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, require_role
from app.core.database import get_db
from app.core.permissions import RoleEnum
from app.models.user import User
from app.schemas.backup import BackupHistoryResponse, BackupIntegrityReport, BackupManifest, DryRunResult, RestoreResult
from app.services import backup_service, restore_service
from app.services.audit_service import log_action

router = APIRouter(prefix="/backup", tags=["backup"])
_SUPER_ADMIN = Depends(require_role([RoleEnum.SUPER_ADMIN]))
CONFIRM = "CONFIRM_RESTORE"


class BackupIdRequest(BaseModel):
    backup_id: str


class RestorePostgresRequest(BaseModel):
    backup_file_path: str
    confirmation: str


class RestoreQdrantRequest(BaseModel):
    snapshot_file_path: str
    collection_name: str
    confirmation: str


class RestoreDocumentsRequest(BaseModel):
    backup_archive_path: str
    confirmation: str


def _require_confirmation(value: str) -> None:
    if value != CONFIRM:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Explicit confirmation required")


@router.post("/run", response_model=BackupManifest, dependencies=[_SUPER_ADMIN])
async def run_backup(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> BackupManifest:
    manifest = await backup_service.run_full_backup(db, current_user.id, current_user.organization_id)
    await db.commit()
    return manifest


@router.get("/history", response_model=BackupHistoryResponse, dependencies=[_SUPER_ADMIN])
async def history(current_user: Annotated[User, Depends(get_current_active_user)]) -> BackupHistoryResponse:
    return await backup_service.get_backup_history()


@router.get("/{backup_id}/integrity", response_model=BackupIntegrityReport, dependencies=[_SUPER_ADMIN])
async def integrity(backup_id: str, current_user: Annotated[User, Depends(get_current_active_user)]) -> BackupIntegrityReport:
    return await backup_service.verify_backup_integrity(backup_id)


@router.post("/restore/dry-run", response_model=DryRunResult, dependencies=[_SUPER_ADMIN])
async def dry_run(payload: BackupIdRequest, current_user: Annotated[User, Depends(get_current_active_user)]) -> DryRunResult:
    manifest = next((m for m in (await backup_service.get_backup_history()).backups if m.backup_id == payload.backup_id), None)
    if manifest is None:
        raise HTTPException(status_code=404, detail="Backup not found")
    files = [p for p in [manifest.postgresql_backup, manifest.documents_backup, manifest.config_backup] if p] + manifest.qdrant_backups
    return await restore_service.run_restore_dry_run(files)


@router.post("/restore/postgresql", response_model=RestoreResult, dependencies=[_SUPER_ADMIN])
async def restore_postgresql(
    payload: RestorePostgresRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> RestoreResult:
    _require_confirmation(payload.confirmation)
    await log_action(db, user_id=current_user.id, organization_id=current_user.organization_id, action="DATABASE_RESTORE_REQUESTED", resource_type="restore", resource_id=payload.backup_file_path)
    result = await restore_service.restore_postgresql(db, payload.backup_file_path, current_user.id, current_user.organization_id)
    await db.commit()
    return result


@router.post("/restore/qdrant", response_model=RestoreResult, dependencies=[_SUPER_ADMIN])
async def restore_qdrant(
    payload: RestoreQdrantRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> RestoreResult:
    _require_confirmation(payload.confirmation)
    result = await restore_service.restore_qdrant(db, payload.snapshot_file_path, payload.collection_name, current_user.id, current_user.organization_id)
    await db.commit()
    return result


@router.post("/restore/documents", response_model=RestoreResult, dependencies=[_SUPER_ADMIN])
async def restore_documents(
    payload: RestoreDocumentsRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> RestoreResult:
    _require_confirmation(payload.confirmation)
    result = await restore_service.restore_uploaded_documents(db, payload.backup_archive_path, current_user.id, current_user.organization_id)
    await db.commit()
    return result
