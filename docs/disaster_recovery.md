# Disaster Recovery

## Overview

Ent_RAG protects PostgreSQL data, Qdrant vector collections, uploaded documents, and encrypted environment configuration with scheduled full backups. Backups are tenant-aware through application audit logging and are stored by component under the local `backups/` directory.

## Backup Schedule

- Daily full backup: 1:00 AM UTC.
- Weekly integrity check: Sunday at 2:00 AM UTC.
- Monthly cleanup: first day of each month at 3:00 AM UTC.
- Retention: 30 days, with at least 5 most recent backups always kept.

## Backup Storage

- PostgreSQL: `backups/postgresql/`
- Qdrant snapshots: `backups/qdrant/`
- Uploaded documents: `backups/documents/`
- Encrypted environment config: `backups/config/`
- Manifests and checksums: `backups/manifests/`

## PostgreSQL Recovery

Prerequisites:
- Access to the server and `.env` credentials.
- PostgreSQL service running.
- Selected `ent_rag_db_backup_*.sql.gz` file.

Steps:
1. Stop application write traffic.
2. Run restore dry run from the backup UI or API.
3. Restore:
   ```bash
   gunzip -c backups/postgresql/ent_rag_db_backup_TIMESTAMP.sql.gz | psql -h postgres -U "$POSTGRES_USER" "$POSTGRES_DB"
   ```
4. Restart backend and Celery workers.

Verification:
- Confirm `/api/health` returns OK.
- Confirm organizations, users, documents, and audit logs are present.
- Run smoke tests for login, document list, and chat retrieval.

Estimated recovery time: 15 to 30 minutes.

## Qdrant Recovery

Prerequisites:
- Qdrant service running.
- Selected `qdrant_*.snapshot` file.
- Target collection name, for example `ent_rag_{organization_id}`.

Steps:
1. Stop ingestion and embedding workers.
2. Upload the snapshot to Qdrant restore endpoint or use the backup API.
3. Restart ingestion workers.

Verification:
- Confirm collection exists.
- Confirm vector count is non-zero and consistent with document chunks.
- Run a test RAG query against approved documents.

Estimated recovery time: 10 to 20 minutes.

## Uploaded Documents Recovery

Prerequisites:
- Selected `documents_backup_*.tar.gz` archive.
- Write access to the app working directory.

Steps:
1. Stop backend and workers.
2. Extract archive:
   ```bash
   tar -xzf backups/documents/documents_backup_TIMESTAMP.tar.gz -C .
   ```
3. Restart backend and workers.

Verification:
- Confirm `uploads/` exists.
- Confirm document file paths referenced by database rows exist.
- Reprocess failed documents if needed.

Estimated recovery time: 5 to 15 minutes.

## Full System Recovery

Order of operations:
1. Restore `.env` from encrypted config backup.
2. Start PostgreSQL, Redis, and Qdrant.
3. Restore PostgreSQL.
4. Restore Qdrant snapshots.
5. Restore uploaded documents.
6. Start backend, workers, frontend, and Nginx.
7. Run post-recovery verification.

Total estimated recovery time: 30 to 90 minutes.

Post-recovery checklist:
- `/api/health` and `/health` pass.
- Login works for Super Admin.
- Audit logs are visible.
- Document listing works.
- RAG query returns sources.
- Monitoring dashboard shows no critical startup failures.

## Targets

- RTO target: 2 hours.
- RPO target: 24 hours.

## Escalation Contacts

- Incident commander: `<name / phone / email>`
- Database owner: `<name / phone / email>`
- Infrastructure owner: `<name / phone / email>`
- Security owner: `<name / phone / email>`
