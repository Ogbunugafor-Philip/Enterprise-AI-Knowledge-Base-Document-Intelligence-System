import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi import HTTPException

from app.api.v1 import backup as backup_api
from app.schemas.backup import BackupManifest
from app.services import backup_service, restore_service


def test_backup_service_verify_backup_integrity_returns_report_with_correct_structure(tmp_path, monkeypatch):
    monkeypatch.setattr(backup_service, "MANIFEST_DIR", tmp_path)
    file_path = tmp_path / "db.sql.gz"
    file_path.write_text("backup")
    backup_id = "20260528T010000Z"
    manifest = BackupManifest(
        backup_id=backup_id,
        timestamp=datetime.now(timezone.utc),
        postgresql_backup=str(file_path),
        qdrant_backups=[],
        documents_backup=None,
        config_backup=None,
        total_size_mb=0.001,
        checksums={str(file_path): backup_service.sha256_file(file_path)},
    )
    (tmp_path / f"{backup_id}.json").write_text(manifest.model_dump_json())

    report = asyncio.run(backup_service.verify_backup_integrity(backup_id))

    assert report.backup_id == backup_id
    assert report.checks
    assert report.all_passed is True


def test_backup_service_cleanup_old_backups_keeps_minimum_5_backups(tmp_path, monkeypatch):
    monkeypatch.setattr(backup_service, "MANIFEST_DIR", tmp_path)
    monkeypatch.setattr(backup_service, "POSTGRES_DIR", tmp_path)
    monkeypatch.setattr(backup_service, "QDRANT_DIR", tmp_path)
    monkeypatch.setattr(backup_service, "DOCUMENTS_DIR", tmp_path)
    monkeypatch.setattr(backup_service, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(backup_service, "BACKUP_ROOT", tmp_path)

    for idx in range(7):
        file_path = tmp_path / f"backup-{idx}.dat"
        file_path.write_text("backup")
        timestamp = datetime.now(timezone.utc) - timedelta(days=60 + idx)
        backup_id = f"2026010{idx}T010000Z"
        manifest = BackupManifest(
            backup_id=backup_id,
            timestamp=timestamp,
            postgresql_backup=str(file_path),
            qdrant_backups=[],
            documents_backup=None,
            config_backup=None,
            total_size_mb=0.001,
            checksums={str(file_path): backup_service.sha256_file(file_path)},
        )
        manifest_path = tmp_path / f"{backup_id}.json"
        manifest_path.write_text(manifest.model_dump_json())
        old_mtime = (datetime.now(timezone.utc) - timedelta(days=60 + idx)).timestamp()
        Path(manifest_path).touch()
        import os
        os.utime(manifest_path, (old_mtime, old_mtime))

    asyncio.run(backup_service.cleanup_old_backups(retention_days=30))

    assert len(list(tmp_path.glob("*.json"))) >= 5


def test_restore_service_run_restore_dry_run_returns_dry_run_result_with_checks_list(tmp_path):
    backup = tmp_path / "backup.sql.gz"
    backup.write_text("backup")

    result = asyncio.run(restore_service.run_restore_dry_run([str(backup)]))

    assert result.checks
    assert result.all_passed is True


def test_backup_manifest_contains_all_required_fields():
    manifest = BackupManifest(
        backup_id="20260528T010000Z",
        timestamp=datetime.now(timezone.utc),
        postgresql_backup="pg.sql.gz",
        qdrant_backups=["q.snapshot"],
        documents_backup="docs.tar.gz",
        config_backup="env.enc",
        total_size_mb=1.0,
        checksums={"pg.sql.gz": "abc"},
    )

    data = manifest.model_dump()
    for field in ["backup_id", "timestamp", "postgresql_backup", "qdrant_backups", "documents_backup", "config_backup", "total_size_mb", "checksums"]:
        assert field in data


def test_backup_file_naming_uses_correct_timestamp_format():
    name = backup_service.timestamp_slug(datetime(2026, 5, 28, 1, 2, 3, tzinfo=timezone.utc))

    assert name == "20260528T010203Z"


def test_restore_endpoint_requires_confirm_restore_confirmation_string():
    backup_api._require_confirmation("CONFIRM_RESTORE")


def test_restore_endpoint_returns_400_if_confirmation_string_missing_or_wrong():
    with pytest.raises(HTTPException) as exc:
        backup_api._require_confirmation("WRONG")

    assert exc.value.status_code == 400

    with pytest.raises(HTTPException) as exc:
        backup_api._require_confirmation("")

    assert exc.value.status_code == 400
