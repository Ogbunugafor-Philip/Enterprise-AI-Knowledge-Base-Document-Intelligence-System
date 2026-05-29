from decimal import Decimal
from pathlib import Path
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, require_role
from app.core.cache_config import CacheManager, TTL_DASHBOARD_STATS, get_redis_client, make_cache_key
from app.core.file_storage import get_upload_path, save_uploaded_file
from app.core.permissions import RoleEnum
from app.core.database import get_db
from app.models.audit import AuditLog
from app.models.document import Document
from app.models.user import User
from app.schemas.document import (
    AdminDashboardStats,
    DocumentListResponse,
    DocumentResponse,
    DocumentStatusResponse,
    DocumentUploadResponse,
    FailedUploadResponse,
    IngestionStatusResponse,
)
from app.services.file_validation_service import run_all_validations

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/documents", tags=["admin-documents"])
dashboard_router = APIRouter(prefix="/admin/dashboard", tags=["admin-dashboard"])


def _doc_response(document: Document) -> DocumentResponse:
    return DocumentResponse(
        id=document.id,
        title=document.title,
        description=document.description,
        file_name=document.file_name,
        file_type=document.file_type,
        file_size_mb=float(document.file_size_mb),
        status=document.status,
        is_approved=document.is_approved,
        approved_by=document.approved_by,
        approved_at=document.approved_at,
        version_number=document.version_number,
        chunk_count=document.chunk_count,
        embedding_status=document.embedding_status,
        malware_scan_status=document.malware_scan_status,
        malware_scan_result=document.malware_scan_result,
        uploaded_by=document.uploaded_by,
        department_id=document.department_id,
        organization_id=document.organization_id,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


@router.post("/upload", response_model=DocumentUploadResponse, dependencies=[Depends(require_role([RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN]))])
async def upload_document(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str | None = Form(default=None),
    department_id: UUID | None = Form(default=None),
) -> DocumentUploadResponse:
    content = await file.read()
    validation = run_all_validations(file.filename or "upload", len(content), content, file.content_type)
    if not validation["is_valid"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=validation["failures"])
    document_id = uuid4()
    file_type = Path(validation["sanitized_file_name"]).suffix.lower().lstrip(".")
    destination = get_upload_path(current_user.organization_id, department_id, document_id, validation["sanitized_file_name"])
    await file.seek(0)
    await save_uploaded_file(file, destination)
    document = Document(
        id=document_id,
        organization_id=current_user.organization_id,
        department_id=department_id,
        uploaded_by=current_user.id,
        title=title,
        description=description,
        file_name=validation["sanitized_file_name"],
        file_path=str(destination),
        file_type=file_type,
        file_size_mb=Decimal(str(round(len(content) / (1024 * 1024), 2))),
        status="uploaded",
        malware_scan_status="pending",
        embedding_status="pending",
    )
    db.add(document)
    from app.services.audit_service import log_action
    await log_action(db, user_id=current_user.id, organization_id=current_user.organization_id, action="DOCUMENT_UPLOADED", resource_type="document", resource_id=str(document.id), new_value={"title": title, "file_name": document.file_name})
    await db.commit()
    try:
        from worker.tasks.document_tasks import process_document_task
        process_document_task.delay(str(document.id))
        logger.info("Queued process_document_task for document %s", document.id)
    except Exception as exc:
        logger.error("Failed to queue process_document_task for document %s: %s", document.id, exc, exc_info=True)
    return DocumentUploadResponse(
        id=document.id,
        title=document.title,
        file_name=document.file_name,
        file_type=document.file_type,
        file_size_mb=float(document.file_size_mb),
        status=document.status,
        malware_scan_status=document.malware_scan_status,
        created_at=document.created_at,
    )


@router.get("/failed", response_model=list[FailedUploadResponse], dependencies=[Depends(require_role([RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN]))])
async def failed_uploads(db: Annotated[AsyncSession, Depends(get_db)], current_user: Annotated[User, Depends(get_current_active_user)]):
    result = await db.execute(select(Document).where(Document.organization_id == current_user.organization_id, Document.status == "failed"))
    return [
        FailedUploadResponse(id=doc.id, file_name=doc.file_name, failure_reason=doc.malware_scan_result, failure_stage=doc.embedding_status, created_at=doc.created_at)
        for doc in result.scalars().all()
    ]


@router.get("", response_model=DocumentListResponse, dependencies=[Depends(require_role([RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN]))])
async def list_documents(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    status_filter: str | None = Query(default=None, alias="status"),
    file_type: str | None = None,
    department_id: UUID | None = None,
    search_query: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> DocumentListResponse:
    filters = [Document.organization_id == current_user.organization_id, Document.status != "deleted"]
    if status_filter:
        filters.append(Document.status == status_filter)
    if file_type:
        filters.append(Document.file_type == file_type)
    if department_id:
        filters.append(Document.department_id == department_id)
    if search_query:
        filters.append(Document.title.ilike(f"%{search_query}%"))
    total = await db.execute(select(func.count()).select_from(Document).where(*filters))
    result = await db.execute(select(Document).where(*filters).limit(page_size).offset((page - 1) * page_size))
    return DocumentListResponse(documents=[_doc_response(doc) for doc in result.scalars().all()], total=int(total.scalar_one()), page=page, page_size=page_size)


@router.get("/{document_id}", response_model=DocumentResponse, dependencies=[Depends(require_role([RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN]))])
async def get_document(document_id: UUID, db: Annotated[AsyncSession, Depends(get_db)], current_user: Annotated[User, Depends(get_current_active_user)]):
    result = await db.execute(select(Document).where(Document.id == document_id, Document.organization_id == current_user.organization_id, Document.status != "deleted"))
    document = result.scalar_one_or_none()
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return _doc_response(document)


@router.get("/{document_id}/status", response_model=IngestionStatusResponse, dependencies=[Depends(require_role([RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN]))])
async def document_status(document_id: UUID, db: Annotated[AsyncSession, Depends(get_db)], current_user: Annotated[User, Depends(get_current_active_user)]):
    result = await db.execute(select(Document).where(Document.id == document_id, Document.organization_id == current_user.organization_id, Document.status != "deleted"))
    document = result.scalar_one_or_none()
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    stage = document.status if document.status != "processing" else "processing"
    progress = {"uploaded": 10, "processing": 50, "reviewed": 90, "approved": 100, "failed": 100}.get(document.status, 0)
    return IngestionStatusResponse(document_id=document.id, file_name=document.file_name, current_stage=stage, progress_percent=progress, error_message=document.malware_scan_result, started_at=document.created_at, completed_at=document.updated_at if document.status in {"reviewed", "approved", "failed"} else None)


@router.post("/{document_id}/reprocess", dependencies=[Depends(require_role([RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN]))])
async def reprocess_document(document_id: UUID, db: Annotated[AsyncSession, Depends(get_db)], current_user: Annotated[User, Depends(get_current_active_user)]):
    result = await db.execute(select(Document).where(Document.id == document_id, Document.organization_id == current_user.organization_id))
    document = result.scalar_one_or_none()
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    try:
        from worker.tasks.document_tasks import reprocess_document_task
        reprocess_document_task.delay(str(document.id))
        logger.info("Queued reprocess_document_task for document %s", document.id)
    except Exception as exc:
        logger.error("Failed to queue reprocess_document_task for document %s: %s", document.id, exc, exc_info=True)
    return {"message": "Reprocessing queued"}


@router.delete("/{document_id}", dependencies=[Depends(require_role([RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN]))])
async def delete_document(document_id: UUID, db: Annotated[AsyncSession, Depends(get_db)], current_user: Annotated[User, Depends(get_current_active_user)]):
    result = await db.execute(select(Document).where(Document.id == document_id, Document.organization_id == current_user.organization_id))
    document = result.scalar_one_or_none()
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    document.status = "deleted"
    from app.services.audit_service import log_action
    await log_action(db, organization_id=current_user.organization_id, user_id=current_user.id, action="DOCUMENT_DELETED", resource_type="document", resource_id=str(document.id))
    await db.commit()
    try:
        from worker.tasks.document_tasks import delete_document_embeddings_task
        delete_document_embeddings_task.delay(str(document.organization_id), str(document.id))
    except Exception as exc:
        logger.error("Failed to queue delete_document_embeddings_task for document %s: %s", document.id, exc, exc_info=True)
    return {"message": "Document deleted"}


@dashboard_router.get("/stats", response_model=AdminDashboardStats, dependencies=[Depends(require_role([RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN]))])
async def dashboard_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    redis=Depends(get_redis_client),
):
    # No caching — always return live counts
    org_id = current_user.organization_id
    base = Document.organization_id == org_id

    # Proper aggregate queries across ALL documents, not just the last 5
    total_approved = int((await db.execute(
        select(func.count()).select_from(Document)
        .where(base, Document.status == "approved", Document.is_approved.is_(True))
    )).scalar_one())

    pending = int((await db.execute(
        select(func.count()).select_from(Document)
        .where(base, Document.status == "reviewed")
    )).scalar_one())

    failed = int((await db.execute(
        select(func.count()).select_from(Document)
        .where(base, Document.status == "failed")
    )).scalar_one())

    total_chunks = int((await db.execute(
        select(func.coalesce(func.sum(Document.chunk_count), 0)).select_from(Document)
        .where(base, Document.status == "approved")
    )).scalar_one())

    # Status breakdown across all non-deleted documents
    status_rows = (await db.execute(
        select(Document.status, func.count()).select_from(Document)
        .where(base, Document.status.not_in(["deleted"]))
        .group_by(Document.status)
    )).all()
    documents_by_status = {row[0]: row[1] for row in status_rows}

    # File type breakdown across approved documents
    type_rows = (await db.execute(
        select(Document.file_type, func.count()).select_from(Document)
        .where(base, Document.status == "approved")
        .group_by(Document.file_type)
    )).all()
    documents_by_type = {row[0]: row[1] for row in type_rows}

    # Recent uploads (last 5, any non-deleted status for visibility)
    recent_result = await db.execute(
        select(Document).where(base, Document.status.not_in(["deleted"]))
        .order_by(Document.created_at.desc()).limit(5)
    )
    recent = list(recent_result.scalars().all())

    stats = AdminDashboardStats(
        total_documents=total_approved,
        pending_approval=pending,
        approved_documents=total_approved,
        failed_uploads=failed,
        total_chunks=total_chunks,
        documents_by_status=documents_by_status,
        documents_by_type=documents_by_type,
        recent_uploads=[_doc_response(doc) for doc in recent],
    )
    return stats
