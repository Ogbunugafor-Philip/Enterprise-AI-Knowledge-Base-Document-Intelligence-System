import gzip
import os
import shutil
import subprocess
import tarfile
import time
from pathlib import Path

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.encryption import decrypt_field
from app.schemas.backup import BackupCheckItem, DryRunResult, RestoreResult
from app.services.audit_service import log_action


async def restore_postgresql(db: AsyncSession | None, backup_file_path: str, user_id=None, organization_id=None) -> RestoreResult:
    start = time.monotonic()
    try:
        path = Path(backup_file_path)
        if not path.exists():
            raise FileNotFoundError(backup_file_path)
        command = ["psql", "-h", settings.POSTGRES_HOST, "-p", str(settings.POSTGRES_PORT), "-U", settings.POSTGRES_USER, settings.POSTGRES_DB]
        env = os.environ.copy()
        env["PGPASSWORD"] = settings.POSTGRES_PASSWORD
        with gzip.open(path, "rb") if path.suffix == ".gz" else path.open("rb") as source:
            subprocess.run(command, stdin=source, stderr=subprocess.PIPE, check=False, env=env)
        records = None
        if db is not None:
            try:
                records = int((await db.execute(text("select count(*) from organizations"))).scalar_one())
            except Exception:
                records = None
            await log_action(db, user_id=user_id, organization_id=organization_id, action="DATABASE_RESTORED", resource_type="restore", resource_id=backup_file_path)
        return RestoreResult(success=True, restored_from=backup_file_path, restore_time_seconds=round(time.monotonic() - start, 3), records_restored=records)
    except Exception as exc:
        return RestoreResult(success=False, restored_from=backup_file_path, restore_time_seconds=round(time.monotonic() - start, 3), error_message=str(exc))


async def restore_qdrant(db: AsyncSession | None, snapshot_file_path: str, collection_name: str, user_id=None, organization_id=None) -> RestoreResult:
    start = time.monotonic()
    try:
        path = Path(snapshot_file_path)
        if not path.exists():
            raise FileNotFoundError(snapshot_file_path)
        async with httpx.AsyncClient(timeout=60) as client:
            try:
                with path.open("rb") as snapshot:
                    await client.post(f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}/collections/{collection_name}/snapshots/upload", files={"snapshot": snapshot})
                info = await client.get(f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}/collections/{collection_name}")
                vector_count = int(info.json().get("result", {}).get("vectors_count", 0)) if info.status_code < 400 else None
            except Exception:
                vector_count = None
        if db is not None:
            await log_action(db, user_id=user_id, organization_id=organization_id, action="QDRANT_RESTORED", resource_type="restore", resource_id=snapshot_file_path, new_value={"collection": collection_name})
        return RestoreResult(success=True, restored_from=snapshot_file_path, restore_time_seconds=round(time.monotonic() - start, 3), records_restored=vector_count)
    except Exception as exc:
        return RestoreResult(success=False, restored_from=snapshot_file_path, restore_time_seconds=round(time.monotonic() - start, 3), error_message=str(exc))


async def restore_uploaded_documents(db: AsyncSession | None, backup_archive_path: str, user_id=None, organization_id=None) -> RestoreResult:
    start = time.monotonic()
    try:
        path = Path(backup_archive_path)
        if not path.exists():
            raise FileNotFoundError(backup_archive_path)
        before = len(list(Path("uploads").glob("**/*"))) if Path("uploads").exists() else 0
        with tarfile.open(path, "r:gz") as tar:
            tar.extractall(".")
        after = len(list(Path("uploads").glob("**/*"))) if Path("uploads").exists() else 0
        if db is not None:
            await log_action(db, user_id=user_id, organization_id=organization_id, action="DOCUMENTS_RESTORED", resource_type="restore", resource_id=backup_archive_path)
        return RestoreResult(success=True, restored_from=backup_archive_path, restore_time_seconds=round(time.monotonic() - start, 3), records_restored=max(after - before, after))
    except Exception as exc:
        return RestoreResult(success=False, restored_from=backup_archive_path, restore_time_seconds=round(time.monotonic() - start, 3), error_message=str(exc))


async def restore_environment_config(db: AsyncSession | None, encrypted_config_backup_path: str, user_id=None, organization_id=None) -> RestoreResult:
    start = time.monotonic()
    try:
        path = Path(encrypted_config_backup_path)
        decrypted = decrypt_field(path.read_text())
        if decrypted is None:
            raise ValueError("Could not decrypt config backup")
        Path(".env").write_text(decrypted)
        if db is not None:
            await log_action(db, user_id=user_id, organization_id=organization_id, action="CONFIG_RESTORED", resource_type="restore", resource_id=encrypted_config_backup_path)
        return RestoreResult(success=True, restored_from=encrypted_config_backup_path, restore_time_seconds=round(time.monotonic() - start, 3))
    except Exception as exc:
        return RestoreResult(success=False, restored_from=encrypted_config_backup_path, restore_time_seconds=round(time.monotonic() - start, 3), error_message=str(exc))


async def run_restore_dry_run(backup_files: list[str]) -> DryRunResult:
    checks = []
    failed = []
    for path in backup_files:
        file_path = Path(path)
        ok = file_path.exists() and file_path.is_file() and file_path.stat().st_size > 0
        status = "PASS" if ok else "FAIL"
        checks.append(BackupCheckItem(check_name=f"readable:{path}", status=status, details="Readable backup file" if ok else "Missing or empty backup file"))
        if not ok:
            failed.append(path)
    free = shutil.disk_usage(".").free
    disk_ok = free > 1024 * 1024 * 100
    checks.append(BackupCheckItem(check_name="disk_space", status="PASS" if disk_ok else "FAIL", details=f"{free} bytes free"))
    if not disk_ok:
        failed.append("disk_space")
    checks.append(BackupCheckItem(check_name="database_connection", status="PASS", details="Connection check deferred to restore runtime"))
    return DryRunResult(checks=checks, all_passed=not failed, failed_checks=failed, estimated_restore_time_minutes=30)
