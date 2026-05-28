# Ent_RAG Administrator Guide
## Production: https://docintel.space

---

## Getting Started as Super Admin

1. Navigate to `https://docintel.space`
2. Log in with your Super Admin credentials
3. You will be directed to the Super Admin workspace at `/superadmin/dashboard`

---

## Creating Organizations and Departments

### Create an Organization
1. Go to **Super Admin > Dashboard**
2. Use the setup endpoint to create an organization:
   ```bash
   curl -X POST https://docintel.space/api/v1/setup/organization \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"name": "Acme Corp", "slug": "acme-corp"}'
   ```

### Create Departments
Departments are scoped to organizations. Use the Departments API:
```bash
curl -X POST https://docintel.space/api/v1/departments \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Engineering", "description": "Engineering department"}'
```

---

## Managing Users

### Create a Single User
1. Go to **Super Admin > User Management**
2. Click **Create User**, fill in the form
3. The system will send a temporary password to the user's email
4. User must change password on first login

### Bulk Upload Users (Excel)
1. Download the template: **User Management > Download Template**
2. Fill in columns: `first_name`, `last_name`, `email`, `role`, `department`
3. Upload the file via **Bulk Upload**
4. Review the error report for any invalid rows

### Activate / Deactivate Users
- **Deactivate**: User cannot log in; data is preserved
- **Activate**: Restores login access

### Unlock a Locked Account
If a user exceeds 5 failed login attempts, their account is locked for 30 minutes.
An admin can unlock immediately via **User Management > Unlock Account**.

### Reset User Password
1. Go to **User Management > User Detail**
2. Click **Reset Password**
3. A new temporary password is emailed; user must change it on next login

---

## Managing Documents

### Upload a Document
1. Go to **Admin > Document Management**
2. Click **Upload**
3. Select a file (PDF, DOCX, XLSX, TXT — max 50 MB)
4. The document enters the processing pipeline automatically:
   - Malware scan
   - Text extraction (OCR for scanned PDFs)
   - Hybrid chunking
   - Embedding generation and Qdrant storage

### Approve or Reject a Document
1. Go to **Admin > Approval Queue**
2. Documents in `reviewed` status are waiting for approval
3. Click **Approve** to make available for AI search
4. Click **Reject** with a reason to exclude from search

### Document Versioning
1. In **Document Management**, click **Versions** on any document
2. Upload a new version — the old version is preserved
3. Use **Rollback** to revert to a previous version

### Access Rules
Restrict specific documents to certain departments or users:
1. Open a document's detail view
2. Add an **Access Rule** for a department or user

---

## Monitoring: Daily Admin Tasks

### Check the Monitoring Dashboard
- Navigate to `https://docintel.space/monitoring`
- Review: error rate, AI query volume, active users, hallucination risk

### Review Alerts
- Open **Monitoring > Alerts**
- Investigate any `critical` or `high` severity alerts
- Update alert status to `acknowledged` or `resolved`

### Review AI Quality
- Navigate to **AI Trust Report**
- Monitor: average confidence score, hallucination risk trend, user feedback

---

## Troubleshooting Guide

| Symptom | Likely Cause | Action |
|---------|-------------|--------|
| Document stuck in `processing` | Celery worker down | Check `docker logs ent_rag_celery` |
| AI returns fallback answers | No approved documents | Approve documents in Approval Queue |
| User can't log in | Account locked or inactive | Unlock/activate in User Management |
| High hallucination risk alerts | Chunk quality issue | Re-process affected documents |
| Backup failed alert | Disk space or permission | Check `/opt/ent_rag/backups/` directory |
| SSL expired | Certbot renewal failed | Run `certbot renew` and reload Nginx |
