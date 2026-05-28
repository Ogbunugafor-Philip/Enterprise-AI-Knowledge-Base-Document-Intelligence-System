# Rollback Plan

## Strategy

Rollback restores service quickly when a deployment causes severe user impact, data integrity risk, or security exposure. Prefer fix-forward only when the issue is understood, low risk, and faster than rollback.

## Pre-Deployment Checklist

- Confirm latest full backup completed.
- Confirm backup integrity check passed.
- Record current Git commit and Docker image tags.
- Confirm Alembic migration plan and downgrade path.
- Confirm health checks pass before deployment.

## Rollback Triggers

Rollback when:
- Authentication or tenant isolation fails.
- Database migration corrupts or blocks critical data.
- API health checks fail after deployment.
- RAG answers leak cross-tenant data.
- Security controls are disabled or bypassed.

Fix forward when:
- Issue is cosmetic.
- One endpoint has a small isolated bug.
- Patch is already tested and lower risk than rollback.

## Application Rollback

1. Identify previous stable commit or tag.
2. Revert or checkout:
   ```bash
   git checkout <previous-stable-tag>
   ```
3. Rebuild images:
   ```bash
   docker compose -f deployment/docker-compose.yml build
   ```
4. Restart:
   ```bash
   docker compose -f deployment/docker-compose.yml down
   docker compose -f deployment/docker-compose.yml up -d
   ```
5. Verify backend, frontend, worker, Redis, Postgres, Qdrant, and Nginx health checks.

## Database Rollback

Use database rollback when schema/data changes are incompatible with the previous app.

Alembic downgrade:
```bash
docker compose -f deployment/docker-compose.yml exec backend alembic downgrade -1
```

Restore from backup if downgrade is unsafe:
1. Stop backend and workers.
2. Restore selected PostgreSQL backup.
3. Restart services.
4. Verify table counts and user workflows.

## Full Environment Rollback

1. Stop all services.
2. Restore PostgreSQL backup.
3. Restore Qdrant snapshots.
4. Restore uploaded documents.
5. Checkout previous app version.
6. Rebuild and restart Docker Compose.

Estimated time: 30 to 60 minutes.

## Post-Rollback Verification

- `/api/health` returns OK.
- Super Admin login works.
- User login works.
- Document search and chat work.
- Monitoring shows no critical alerts.
- Audit log records rollback activities.

## Stakeholder Template

Subject: Ent_RAG rollback in progress

We detected an issue with the latest deployment affecting `<impact>`. We are rolling back to the previous stable release. Expected recovery time is `<ETA>`. Next update will be sent by `<time>`.
