# Ent_RAG Phase 2 Schema Documentation

## Tenant Isolation Strategy

`organizations` is the top-level tenant table. Every tenant-owned table includes a non-null `organization_id` foreign key to `organizations.id`, including junction, authentication, monitoring, chat, audit, document, and access-control tables. Application queries and Qdrant vector searches must always filter by `organization_id` before returning data.

This strategy prevents cross-tenant data exposure by making the tenant boundary explicit in relational data and by mirroring the same `organization_id` in document chunk/vector payloads.

## Tables

### organizations

Top-level tenant model.

| Field | Type | Notes |
| --- | --- | --- |
| id | UUID | Primary key |
| name | String(255) | Organization display name |
| slug | String(120) | Unique tenant slug |
| description | Text | Optional description |
| logo_url | String(1024) | Optional logo URL |
| is_active | Boolean | Active tenant flag |
| subscription_plan | String(50) | Plan identifier |
| max_users | Integer | Tenant user limit |
| max_documents | Integer | Tenant document limit |
| storage_limit_mb | Integer | Tenant storage limit |
| created_at | Timestamp with timezone | Creation time |
| updated_at | Timestamp with timezone | Last update time |

Relationships: owns departments, users, roles, permissions, documents, and all tenant-scoped records through `organization_id`.

### departments

| Field | Type | Notes |
| --- | --- | --- |
| id | UUID | Primary key |
| organization_id | UUID | FK to organizations.id, tenant scope |
| name | String(255) | Department name, unique per organization |
| description | Text | Optional description |
| is_active | Boolean | Active flag |
| created_at | Timestamp with timezone | Creation time |
| updated_at | Timestamp with timezone | Last update time |

Relationships: belongs to organization; has users and documents.

### roles

| Field | Type | Notes |
| --- | --- | --- |
| id | UUID | Primary key |
| organization_id | UUID | FK to organizations.id, tenant scope |
| name | String(120) | Role name, unique per organization |
| description | Text | Optional description |
| is_system_role | Boolean | Marks built-in roles |
| created_at | Timestamp with timezone | Creation time |
| updated_at | Timestamp with timezone | Last update time |

Relationships: belongs to organization; connected to permissions through role_permissions and users through user_roles.

### permissions

| Field | Type | Notes |
| --- | --- | --- |
| id | UUID | Primary key |
| organization_id | UUID | FK to organizations.id, tenant scope |
| name | String(150) | Permission name |
| description | Text | Optional description |
| resource | String(100) | Protected resource |
| action | String(100) | Allowed action |
| created_at | Timestamp with timezone | Creation time |
| updated_at | Timestamp with timezone | Last update time |

Relationships: belongs to organization; linked to roles through role_permissions.

### role_permissions

| Field | Type | Notes |
| --- | --- | --- |
| id | UUID | Primary key |
| organization_id | UUID | FK to organizations.id, tenant scope |
| role_id | UUID | FK to roles.id |
| permission_id | UUID | FK to permissions.id |

Relationships: joins roles and permissions. `organization_id` must match both referenced records.

### user_roles

| Field | Type | Notes |
| --- | --- | --- |
| id | UUID | Primary key |
| organization_id | UUID | FK to organizations.id, tenant scope |
| user_id | UUID | FK to users.id |
| role_id | UUID | FK to roles.id |
| assigned_at | Timestamp with timezone | Assignment time |
| assigned_by | UUID | Optional FK to users.id |

Relationships: joins users and roles for multi-role assignment.

### users

| Field | Type | Notes |
| --- | --- | --- |
| id | UUID | Primary key |
| organization_id | UUID | FK to organizations.id, tenant scope |
| department_id | UUID | Optional FK to departments.id |
| role_id | UUID | Optional primary role FK to roles.id |
| first_name | String(120) | First name |
| last_name | String(120) | Last name |
| email | String(255) | Email, unique per organization |
| hashed_password | String(255) | Password hash |
| is_active | Boolean | Active user flag |
| is_verified | Boolean | Email/account verification flag |
| is_first_login | Boolean | First login workflow flag |
| must_change_password | Boolean | Forced password reset flag |
| failed_login_attempts | Integer | Login failure counter |
| locked_until | Timestamp with timezone | Optional lock expiry |
| last_login | Timestamp with timezone | Last login time |
| password_changed_at | Timestamp with timezone | Last password change |
| created_at | Timestamp with timezone | Creation time |
| updated_at | Timestamp with timezone | Last update time |

Relationships: belongs to organization, department, and primary role; uploads/approves documents; owns chat sessions and messages.

### documents

| Field | Type | Notes |
| --- | --- | --- |
| id | UUID | Primary key |
| organization_id | UUID | FK to organizations.id, tenant scope |
| department_id | UUID | Optional FK to departments.id |
| uploaded_by | UUID | FK to users.id |
| title | String(255) | Document title |
| description | Text | Optional description |
| file_name | String(255) | Original file name |
| file_path | String(1024) | Storage path |
| file_type | String(100) | MIME/type label |
| file_size_mb | Numeric(12,2) | File size in MB |
| status | Enum | uploaded, processing, reviewed, approved, rejected, archived |
| is_approved | Boolean | Approval flag |
| approved_by | UUID | Optional FK to users.id |
| approved_at | Timestamp with timezone | Approval time |
| version_number | Integer | Version number |
| parent_document_id | UUID | Optional self FK |
| malware_scan_status | Enum | pending, clean, infected, failed |
| malware_scan_result | Text | Scan result detail |
| chunk_count | Integer | Number of chunks |
| embedding_status | Enum | pending, processing, completed, failed |
| created_at | Timestamp with timezone | Creation time |
| updated_at | Timestamp with timezone | Last update time |

Relationships: belongs to organization, department, uploader, approver, optional parent document; owns chunks and access rules.

### document_chunks

| Field | Type | Notes |
| --- | --- | --- |
| id | UUID | Primary key |
| document_id | UUID | FK to documents.id |
| organization_id | UUID | FK to organizations.id, tenant scope |
| chunk_index | Integer | Chunk order |
| chunk_text | Text | Chunk content |
| chunk_hash | String(128) | Dedup/integrity hash |
| token_count | Integer | Token count |
| embedding_status | Enum | pending, processing, completed, failed |
| qdrant_point_id | String(255) | Vector point identifier |
| created_at | Timestamp with timezone | Creation time |

Relationships: belongs to document. Qdrant payloads must include this `organization_id`.

### document_access

| Field | Type | Notes |
| --- | --- | --- |
| id | UUID | Primary key |
| document_id | UUID | FK to documents.id |
| organization_id | UUID | FK to organizations.id, tenant scope |
| department_id | UUID | Optional FK to departments.id |
| role_id | UUID | Optional FK to roles.id |
| user_id | UUID | Optional FK to users.id |
| access_type | String(50) | Access level |
| granted_by | UUID | Optional FK to users.id |
| granted_at | Timestamp with timezone | Grant time |

Relationships: grants document access to department, role, or user within one organization.

### chat_sessions

| Field | Type | Notes |
| --- | --- | --- |
| id | UUID | Primary key |
| user_id | UUID | FK to users.id |
| organization_id | UUID | FK to organizations.id, tenant scope |
| title | String(255) | Session title |
| is_active | Boolean | Active flag |
| created_at | Timestamp with timezone | Creation time |
| updated_at | Timestamp with timezone | Last update time |

Relationships: belongs to user and organization; owns messages.

### messages

| Field | Type | Notes |
| --- | --- | --- |
| id | UUID | Primary key |
| session_id | UUID | FK to chat_sessions.id |
| user_id | UUID | FK to users.id |
| organization_id | UUID | FK to organizations.id, tenant scope |
| role | Enum | user or assistant |
| content | Text | Message content |
| source_documents | JSONB | Retrieved sources |
| confidence_score | Numeric(5,4) | Confidence score |
| retrieval_score | Numeric(5,4) | Retrieval score |
| hallucination_risk_score | Numeric(5,4) | Risk score |
| response_rejected | Boolean | Rejection flag |
| feedback | Enum | correct, incorrect, unclear, hallucination |
| feedback_submitted_at | Timestamp with timezone | Feedback time |
| created_at | Timestamp with timezone | Creation time |

Relationships: belongs to chat session, user, and organization.

### audit_logs

Append-only audit records. Normal users must not be allowed to update or delete rows through application services or database privileges.

| Field | Type | Notes |
| --- | --- | --- |
| id | UUID | Primary key |
| organization_id | UUID | FK to organizations.id, tenant scope |
| user_id | UUID | Optional FK to users.id |
| action | String(120) | Action name |
| resource_type | String(120) | Resource category |
| resource_id | String(120) | Resource identifier |
| old_value | JSONB | Previous value |
| new_value | JSONB | New value |
| ip_address | String(64) | Client IP |
| user_agent | Text | Client user agent |
| status | String(50) | Action status |
| created_at | Timestamp with timezone | Creation time |

### otp_verifications

| Field | Type | Notes |
| --- | --- | --- |
| id | UUID | Primary key |
| organization_id | UUID | FK to organizations.id, tenant scope |
| user_id | UUID | FK to users.id |
| otp_code | String(20) | OTP code |
| otp_type | String(50) | OTP purpose |
| is_used | Boolean | Usage flag |
| expires_at | Timestamp with timezone | Expiry time |
| created_at | Timestamp with timezone | Creation time |

### password_history

| Field | Type | Notes |
| --- | --- | --- |
| id | UUID | Primary key |
| organization_id | UUID | FK to organizations.id, tenant scope |
| user_id | UUID | FK to users.id |
| hashed_password | String(255) | Historical password hash |
| created_at | Timestamp with timezone | Creation time |

### monitoring_logs

| Field | Type | Notes |
| --- | --- | --- |
| id | UUID | Primary key |
| organization_id | UUID | FK to organizations.id, tenant scope |
| event_type | String(120) | Event type |
| service_name | String(120) | Service name |
| endpoint | String(512) | Endpoint |
| method | String(20) | HTTP method |
| status_code | Integer | HTTP status |
| response_time_ms | Integer | Response time |
| error_message | Text | Error detail |
| user_id | UUID | Optional FK to users.id |
| ip_address | String(64) | Client IP |
| token_usage | JSONB | AI token usage |
| created_at | Timestamp with timezone | Creation time |

### system_alerts

| Field | Type | Notes |
| --- | --- | --- |
| id | UUID | Primary key |
| organization_id | UUID | FK to organizations.id, tenant scope |
| alert_type | String(120) | Alert type |
| severity | Enum | low, medium, high, critical |
| title | String(255) | Alert title |
| description | Text | Alert detail |
| affected_service | String(120) | Service impacted |
| status | Enum | open, investigating, resolved, ignored |
| recommended_action | Text | Suggested response |
| business_impact | Text | Business impact |
| created_at | Timestamp with timezone | Creation time |
| updated_at | Timestamp with timezone | Last update time |
| resolved_at | Timestamp with timezone | Resolution time |
| resolved_by | UUID | Optional FK to users.id |

### incident_reports

| Field | Type | Notes |
| --- | --- | --- |
| id | UUID | Primary key |
| organization_id | UUID | FK to organizations.id, tenant scope |
| title | String(255) | Incident title |
| description | Text | Incident detail |
| severity | Enum | low, medium, high, critical |
| status | String(50) | Incident status |
| affected_services | JSONB | Affected services |
| error_count | Integer | Error count |
| first_occurrence | Timestamp with timezone | First occurrence |
| last_occurrence | Timestamp with timezone | Last occurrence |
| root_cause | Text | Root cause |
| resolution_steps | Text | Resolution detail |
| business_impact | Text | Business impact |
| created_at | Timestamp with timezone | Creation time |
| updated_at | Timestamp with timezone | Last update time |
