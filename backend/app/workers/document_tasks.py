import asyncio
from pathlib import Path
from uuid import UUID

from sqlalchemy import delete, select

from app.core.database import SessionLocal
from app.models.document import Document, DocumentChunk
from app.models.monitoring import MonitoringLog
from app.services import chunking_service, document_processor_service, embedding_service, malware_scan_service


async def _process_document(document_id: str) -> None:
    async with SessionLocal() as db:
        result = await db.execute(select(Document).where(Document.id == UUID(document_id)))
        document = result.scalar_one_or_none()
        if document is None:
            return
        try:
            document.status = "processing"
            await db.flush()
            scan = malware_scan_service.scan_file_with_clamd(document.file_path)
            if scan["scan_status"] == "unavailable":
                scan = malware_scan_service.scan_file_fallback(document.file_path)
            malware_scan_service.update_document_scan_result(document, scan)
            if not malware_scan_service.is_safe_to_process(scan):
                malware_scan_service.quarantine_infected_file(document, document.file_path)
                raise ValueError("Malware scan failed or infected file detected")

            extracted = document_processor_service.route_extraction(document.file_path, document.file_type)
            cleaned = document_processor_service.clean_extracted_text(extracted["text"])
            structured = document_processor_service.preprocess_for_chunking(cleaned)
            chunks = chunking_service.hybrid_chunk(structured)
            saved_chunks = await chunking_service.save_chunks_to_db(db, document, chunks)
            embeddings = embedding_service.generate_embeddings_batch([chunk.chunk_text for chunk in saved_chunks])
            point_ids = embedding_service.store_embeddings_in_qdrant(None, document.organization_id, saved_chunks, embeddings, document)
            await embedding_service.update_chunk_qdrant_ids(db, saved_chunks, point_ids)
            document.status = "reviewed"
            document.embedding_status = "completed"
            document.chunk_count = len(saved_chunks)
            db.add(MonitoringLog(organization_id=document.organization_id, event_type="document_processed", service_name="worker", status_code=200))
            await db.commit()
        except Exception as exc:
            document.status = "failed"
            document.embedding_status = "failed"
            document.malware_scan_result = str(exc)
            db.add(MonitoringLog(organization_id=document.organization_id, event_type="document_processing_failed", service_name="worker", error_message=str(exc), status_code=500))
            await db.commit()


def process_document_task(document_id: str) -> None:
    asyncio.run(_process_document(document_id))


async def _reprocess_document(document_id: str) -> None:
    async with SessionLocal() as db:
        result = await db.execute(select(Document).where(Document.id == UUID(document_id)))
        document = result.scalar_one_or_none()
        if document is not None:
            await db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document.id))
            embedding_service.delete_document_embeddings(None, document.organization_id, document.id)
            await db.commit()
    await _process_document(document_id)


def reprocess_document_task(document_id: str) -> None:
    asyncio.run(_reprocess_document(document_id))


def delete_document_embeddings_task(organization_id: str, document_id: str) -> None:
    embedding_service.delete_document_embeddings(None, organization_id, document_id)
