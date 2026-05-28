from datetime import datetime

from pydantic import BaseModel


class BackupCheckItem(BaseModel):
    check_name: str
    status: str
    details: str


class BackupManifest(BaseModel):
    backup_id: str
    timestamp: datetime
    postgresql_backup: str | None
    qdrant_backups: list[str]
    documents_backup: str | None
    config_backup: str | None
    total_size_mb: float
    checksums: dict[str, str]


class BackupHistoryResponse(BaseModel):
    backups: list[BackupManifest]
    total_count: int
    oldest_backup: datetime | None
    newest_backup: datetime | None


class BackupIntegrityReport(BaseModel):
    backup_id: str
    timestamp: datetime
    checks: list[BackupCheckItem]
    all_passed: bool
    failed_checks: list[str]


class RestoreResult(BaseModel):
    success: bool
    restored_from: str
    restore_time_seconds: float
    records_restored: int | None = None
    error_message: str | None = None


class DryRunResult(BaseModel):
    checks: list[BackupCheckItem]
    all_passed: bool
    failed_checks: list[str]
    estimated_restore_time_minutes: int
