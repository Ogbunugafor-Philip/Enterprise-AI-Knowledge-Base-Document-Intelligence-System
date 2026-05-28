# Backup and Restore Guide

## Manual Backup

Run a full backup from the Super Admin backup page or call:

```bash
curl -X POST "$BACKEND_URL/api/v1/backup/run" \
  -H "Authorization: Bearer $TOKEN"
```

The backup creates PostgreSQL, Qdrant, uploaded document, and encrypted config artifacts plus a manifest with SHA256 checksums.

## Verify Integrity

Use the backup history page or:

```bash
curl "$BACKEND_URL/api/v1/backup/{backup_id}/integrity" \
  -H "Authorization: Bearer $TOKEN"
```

Every manifest entry must exist, have non-zero size, and match its checksum.

## Restore Dry Run

Always run dry run before restore:

```bash
curl -X POST "$BACKEND_URL/api/v1/backup/restore/dry-run" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"backup_id":"BACKUP_ID"}'
```

Dry run checks file readability, disk space, and restore prerequisites without modifying data.

## PostgreSQL Restore

```bash
curl -X POST "$BACKEND_URL/api/v1/backup/restore/postgresql" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"backup_file_path":"backups/postgresql/file.sql.gz","confirmation":"CONFIRM_RESTORE"}'
```

## Qdrant Restore

```bash
curl -X POST "$BACKEND_URL/api/v1/backup/restore/qdrant" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"snapshot_file_path":"backups/qdrant/file.snapshot","collection_name":"ent_rag_ORG_ID","confirmation":"CONFIRM_RESTORE"}'
```

## Documents Restore

```bash
curl -X POST "$BACKEND_URL/api/v1/backup/restore/documents" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"backup_archive_path":"backups/documents/file.tar.gz","confirmation":"CONFIRM_RESTORE"}'
```

## Decrypt Environment Config Backup

Config backups are encrypted with the app encryption key. Use `restore_environment_config` from `restore_service` or the application restore workflow. Never store decrypted config in backup directories.

## Troubleshooting

- Empty PostgreSQL backup: confirm `pg_dump` is installed and credentials are correct.
- Qdrant snapshot missing: confirm collection name and Qdrant connectivity.
- Document restore incomplete: confirm archive contains `uploads/`.
- Config decrypt fails: confirm `ENCRYPTION_KEY` matches the key used when backup was created.
- Integrity failure: do not restore until the failed artifact is replaced or a newer valid backup is selected.
