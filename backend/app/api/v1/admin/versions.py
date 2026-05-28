from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, require_role
from app.core.database import get_db
from app.core.file_storage import get_upload_path, save_uploaded_file
from app.core.permissions import RoleEnum
from app.models.user import User
from app.schemas.approval import DocumentVersionListResponse, DocumentVersionResponse
from app.services import versioning_service
from app.services.file_validation_service import run_all_validations

router = APIRouter(prefix="/admin/documents", tags=["admin-versions"])


def _version_response(document) -> DocumentVersionResponse:
    return DocumentVersionResponse(
        id=document.id,
        title=document.title,
        version_number=document.version_number,
        parent_document_id=document.parent_document_id,
        status=document.status,
        created_at=document.created_at,
    )


@router.post(
    "/{document_id}/versions",
    response_model=DocumentVersionResponse,
    dependencies=[Depends(require_role([RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN]))],
)
async def upload_new_version(
    document_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str | None = Form(default=None),
    department_id: UUID | None = Form(default=None),
) -> DocumentVersionResponse:
    content = await file.read()
    validation = run_all_validations(file.filename or "upload", len(content), content, file.content_type)
    if not validation["is_valid"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=validation["failures"])

    from uuid import uuid4
    from pathlib import Path

    new_doc_id = uuid4()
    sanitized = validation["sanitized_file_name"]
    file_type = Path(sanitized).suffix.lower().lstrip(".")
    destination = get_upload_path(current_user.organization_id, department_id, new_doc_id, sanitized)
    await file.seek(0)
    await save_uploaded_file(file, destination)

    new_doc = await versioning_service.create_document_version(
        db=db,
        parent_document_id=document_id,
        current_user=current_user,
        file_content=content,
        file_name=sanitized,
        title=title,
        description=description,
        department_id=department_id,
        file_type=file_type,
        file_path=str(destination),
    )
    if new_doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent document not found")

    new_doc.id = new_doc_id
    await db.commit()
    await db.refresh(new_doc)

    try:
        from worker.tasks.document_tasks import process_document_task

        process_document_task.delay(str(new_doc.id))
    except Exception:
        pass

    return _version_response(new_doc)


@router.get(
    "/{document_id}/versions",
    response_model=DocumentVersionListResponse,
    dependencies=[Depends(require_role([RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN]))],
)
async def list_document_versions(
    document_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> DocumentVersionListResponse:
    versions = await versioning_service.get_document_versions(
        db, document_id, current_user.organization_id
    )
    current_version = await versioning_service.get_current_version(
        db, document_id, current_user.organization_id
    )
    return DocumentVersionListResponse(
        versions=[_version_response(v) for v in versions],
        current_version=_version_response(current_version) if current_version else None,
        total_versions=len(versions),
    )


@router.post(
    "/{document_id}/versions/{version_id}/rollback",
    response_model=DocumentVersionResponse,
    dependencies=[Depends(require_role([RoleEnum.SUPER_ADMIN]))],
)
async def rollback_version(
    document_id: UUID,
    version_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> DocumentVersionResponse:
    document = await versioning_service.rollback_to_version(
        db, document_id, version_id, current_user
    )
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")
    await db.commit()
    await db.refresh(document)
    return _version_response(document)
