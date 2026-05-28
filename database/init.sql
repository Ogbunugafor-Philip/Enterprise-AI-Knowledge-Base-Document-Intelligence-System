/*
Ent_RAG PostgreSQL multi-tenant schema foundation

Phase 2 will define the full production schema for:
- organizations: top-level tenant boundary and billing/security owner.
- departments: organization-scoped subdivisions used for policy inheritance.
- users: organization-scoped identities with role and department mappings.
- documents: organization-scoped source files, metadata, lifecycle status, and ownership.
- document_chunks: normalized text fragments linked to documents and vector records.
- retrieval_audit_logs: immutable records of AI retrieval, prompt context, and answer provenance.
- access_policies: role, department, and document-level permissions.
- api_keys and service_accounts: scoped automation credentials.
- ingestion_jobs: asynchronous document processing and embedding generation state.
- monitoring_events: tenant-scoped operational and security events.

Every table that stores tenant-owned data will include organization_id, and every
application query must filter by organization_id. Foreign keys will preserve tenant
boundaries, and vector-store payloads will mirror organization_id for retrieval
filtering in Qdrant.
*/
