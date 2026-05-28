# DocIntel — Enterprise AI Knowledge Base & Document Intelligence System

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)
![React](https://img.shields.io/badge/React-18-blue.svg)
![Live](https://img.shields.io/badge/live-docintel.space-brightgreen.svg)

> An enterprise-grade AI-powered knowledge platform that lets organizations query their documents using Retrieval-Augmented Generation with hallucination controls, multi-tenancy, and bank-grade security.

**Live URL:** https://docintel.space  
**API Docs:** https://docintel.space/docs  
**Health Check:** https://docintel.space/health

---

## Table of Contents

- [Overview](#overview)
- [Problem Statement](#problem-statement)
- [Key Capabilities](#key-capabilities)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [Development Phases](#development-phases)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Deployment](#deployment)
- [Security](#security)
- [Conclusion](#conclusion)
- [Author](#author)

---

## Overview

DocIntel is a production-deployed enterprise AI system that transforms how organizations retrieve knowledge from internal documents. Instead of employees spending hours searching through files, they ask a question in natural language and receive a precise, sourced answer — with every response carrying a confidence score, retrieval relevance score, and hallucination risk indicator.

The system is built on a Retrieval-Augmented Generation (RAG) pipeline that physically blocks the AI from answering outside the approved knowledge base. No guessing. No fabrication. Every answer is traceable to a source document.

---

## Problem Statement

Organizations handle large volumes of documents daily, but retrieving accurate information quickly remains a major challenge. Important knowledge is scattered across files, folders, and departments, leading to slow decision-making and reduced productivity.

The three core problems this system solves:

1. **Poor and slow document retrieval** — employees waste hours searching; answers may still be wrong or outdated
2. **Lack of secure, role-based access control** — no enforcement of who can see which documents
3. **No intelligent search or AI-driven extraction** — keyword search cannot understand meaning or context

---

## Key Capabilities

### Security
- Multi-tenant isolation — organization A cannot see a single byte of organization B data
- Malware scanning on every uploaded file before processing
- Account lockout after 5 failed login attempts with brute-force detection
- Zero plain-text secrets — bcrypt password hashing, Fernet encryption at rest
- Full authentication chain: JWT + OTP + forced password change + 30-day expiry
- Live security checklist dashboard with PASS/FAIL status for every control

### AI / RAG Engine
- No source, no answer — AI is blocked from responding without approved document support
- Hallucination risk score on every response (0.0–1.0), rejecting responses above 0.7
- Permission-filtered vector search — results scoped to what each user can actually access
- Hybrid chunking combining semantic and hierarchical strategies
- Independent confidence scoring: retrieval confidence, response confidence, hallucination risk
- User feedback loop: Correct, Incorrect, Unclear, Report Hallucination on every response

### Document Management
- 5-stage approval workflow: Uploaded → Processing → Reviewed → Approved → Available for AI
- OCR support — scanned images and PDFs become searchable AI knowledge
- Document versioning with automatic archiving and rollback
- Granular access rules by organization, department, role, or individual user
- Background processing via Celery so uploads return instantly

### Monitoring
- AI-generated system health summary in plain English
- 8 intelligent alert rules covering brute force, high error rate, AI failures, hallucination spikes
- AI debugging assistant converts raw error logs into plain English with business impact and fix steps
- Response time and error rate live charts refreshing every 30 seconds
- Incident grouping to prevent dashboard noise

### User and Organization Management
- Bulk Excel onboarding — upload 500 employees and all accounts are created automatically
- Full multi-tenancy — one infrastructure serves multiple enterprises simultaneously
- 20+ granular permissions assignable per role
- Complete account lifecycle: activate, deactivate, unlock, reset password, anonymize on delete

### Compliance and Backup
- Complete audit trail with old and new values on every action
- GDPR right-to-access data export per user
- Four compliance report types: Activity, Access, Document, Security
- Automated daily backups: PostgreSQL, Qdrant vectors, files, encrypted environment config
- Restore dry-run to test recovery before executing
- Configurable retention policies per data type

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Tailwind CSS, Recharts |
| Backend API | FastAPI, Python 3.11 |
| Database | PostgreSQL 15 |
| Vector Database | Qdrant |
| LLM | Cerebras API (llama3.1-8b) |
| Embeddings | Sentence Transformers (all-MiniLM-L6-v2) |
| AI Orchestration | LangChain |
| Background Jobs | Celery + Redis |
| Document Processing | PyMuPDF, pdfplumber, python-docx, Tesseract OCR |
| Authentication | JWT + OTP + RBAC |
| Reverse Proxy | Nginx |
| Deployment | Docker + Docker Compose |
| Infrastructure | Contabo VPS, Ubuntu 22.04 |
| Version Control | Git + GitHub |

---

## Architecture

```
Internet
    │
    ▼
 Nginx (SSL / reverse proxy)
    │
    ├──► React Frontend  (port 3001)
    │
    └──► FastAPI Backend (port 8010)
              │
              ├──► PostgreSQL 15   (relational data, auth, audit logs)
              ├──► Qdrant           (vector embeddings, semantic search)
              ├──► Redis            (cache, Celery task queue)
              ├──► Cerebras API     (LLM inference — llama3.1-8b)
              └──► Celery Workers   (document ingestion, monitoring, backups)
```

Every database query and vector search is scoped by `organization_id`. There is no query path that can return data from a different organization — isolation is enforced at the ORM and vector collection level, not just in application logic.

---

## Project Structure

```
Ent_RAG/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── auth.py              # Login, OTP, password management
│   │   │   ├── chat.py              # RAG query endpoint
│   │   │   ├── users.py             # User profile and preferences
│   │   │   ├── monitoring.py        # Health, alerts, incidents, AI trust
│   │   │   ├── compliance.py        # Audit logs, reports, retention
│   │   │   ├── security.py          # Checklist, rate limits, events
│   │   │   ├── backup.py            # Backup, restore, integrity
│   │   │   ├── departments.py       # Department management
│   │   │   ├── roles.py             # Role and permission management
│   │   │   ├── admin/
│   │   │   │   ├── documents.py     # Document upload and approval
│   │   │   │   ├── approvals.py     # Approval queue management
│   │   │   │   ├── access_rules.py  # Granular access control
│   │   │   │   └── versions.py      # Document versioning
│   │   │   └── superadmin/
│   │   │       └── users.py         # Super admin user management
│   │   ├── models/                  # SQLAlchemy ORM models
│   │   ├── services/                # Business logic layer
│   │   ├── core/                    # Config, security, middleware
│   │   └── main.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/                   # 20 React page components
│   │   ├── components/
│   │   │   ├── Layout/AppLayout.jsx # Sidebar navigation shell
│   │   │   └── UI/                  # DataTable, Modal, StatsCard, PageHeader
│   │   ├── services/                # API client modules per domain
│   │   └── context/AuthContext.jsx  # JWT auth state
│   └── package.json
├── worker/                          # Celery task definitions
├── ai_service/                      # RAG pipeline and LLM orchestration
├── deployment/
│   ├── docker-compose.prod.yml
│   └── docker-compose.yml
├── nginx/                           # Nginx config and SSL
├── backups/                         # Backup storage (gitignored)
├── uploads/                         # Document uploads (gitignored)
├── monitoring/                      # Monitoring scripts
└── .env                             # Environment config (gitignored)
```

---

## Quick Start

### Prerequisites

- Docker 24+ and Docker Compose v2
- Python 3.11 (for local backend development)
- Node.js 20+ (for local frontend development)
- A Cerebras API key (free tier available)
- An SMTP account for email delivery

### 1. Clone the repository

```bash
git clone https://github.com/Ogbunugafor-Philip/Enterprise-AI-Knowledge-Base-Document-Intelligence-System.git
cd Enterprise-AI-Knowledge-Base-Document-Intelligence-System
```

### 2. Configure environment variables

```bash
cp .env.example .env
# Edit .env with your values — see Environment Variables section below
```

### 3. Build and start all services

```bash
docker compose -f deployment/docker-compose.prod.yml --env-file .env up -d --build
```

### 4. Create the Super Admin account

```bash
docker exec -it ent_rag_backend python app/setup_superadmin.py
```

### 5. Verify all containers are healthy

```bash
docker compose -f deployment/docker-compose.prod.yml ps
curl http://localhost:8010/health
```

### 6. Open the application

Navigate to `http://localhost:3001` (or your configured domain).

---

## Environment Variables

Create a `.env` file at the project root. The following variables are required:

```env
# Database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=Ent_RAG
POSTGRES_USER=admin
POSTGRES_PASSWORD=your_secure_password

# Vector Database
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# Cache and Queue
REDIS_URL=redis://redis:6379/0

# LLM
CEREBRAS_API_KEY=your_cerebras_api_key

# Security
JWT_SECRET_KEY=your_jwt_secret_minimum_32_chars
ENCRYPTION_KEY=your_fernet_key_base64

# Email (OTP delivery)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@email.com
SMTP_PASSWORD=your_app_password

# Application
ENVIRONMENT=production
FRONTEND_URL=https://yourdomain.com
BACKEND_URL=https://yourdomain.com/api
TENANT_ISOLATION_MODE=strict
JWT_ALGORITHM=HS256
JWT_EXPIRY_DAYS=30

# Rate Limiting
API_RATE_LIMIT_PER_ORG=1000
API_RATE_LIMIT_PER_USER=100
```

---

## Development Phases

The system was built across 15 structured phases:

| Phase | Focus | Key Deliverables |
|---|---|---|
| 1 | Foundation | FastAPI skeleton, PostgreSQL models, Alembic migrations, Docker Compose |
| 2 | Authentication | JWT login, OTP email, bcrypt hashing, account lockout, forced password reset |
| 3 | Multi-tenancy | Organization model, strict tenant isolation, department hierarchy |
| 4 | Document Pipeline | Upload endpoint, Celery workers, PyMuPDF/pdfplumber parsing, OCR |
| 5 | RAG Engine | Qdrant integration, Sentence Transformer embeddings, LangChain RAG chain |
| 6 | AI Quality | Hallucination risk scoring, confidence thresholds, response rejection |
| 7 | Access Control | 20+ permissions, RBAC, granular document access rules |
| 8 | Admin System | Approval workflow, document versioning, admin dashboard APIs |
| 9 | Super Admin | Bulk user upload, full lifecycle management, platform statistics |
| 10 | Monitoring | Alert engine, incident grouping, AI health summary, debugging assistant |
| 11 | Compliance | Audit trail, GDPR export, report generation, retention policies |
| 12 | Security Layer | Security checklist, rate limiting, brute force detection, malware scan |
| 13 | Backup System | Automated backups, integrity verification, restore dry-run |
| 14 | Frontend | React 18, Tailwind CSS, AppLayout sidebar, 20 pages, recharts |
| 15 | Production | Nginx + SSL, CPU-only PyTorch, performance tuning, go-live at docintel.space |

---
## Project Implementation Steps
### Phase 1: Project Initialization & Architecture Setup
1.	Create the backend, frontend, database, AI service, worker, monitoring, and deployment folder structure.
2.	Initialize Git and connect the project to GitHub.
3.	Create the Python virtual environment and install backend dependencies.
4.	Set up React.js frontend with Tailwind CSS.
5.	Configure environment variables for PostgreSQL, Qdrant, Cerebras API, Redis, SMTP, JWT secrets, encryption keys, and application URLs.
6.	Configure Docker and Docker Compose for local development.
7.	Define the system architecture for User, Admin, and Super Admin workspaces.
8.	Document the development setup and project structure.
9.	Design the platform using multi-tenancy architecture to support multiple organizations securely on the same infrastructure.
10.	Define tenant isolation strategy for:
i. Organizations
ii. Departments
iii. Documents
iv. Users
v. AI retrieval access
11.	Define tenant-aware database and vector search architecture.
12.	Define API rate-limiting strategy per organization and per user.
13.	Define system scalability strategy for future multi-organization growth.

### Phase 1 Implementation

•	Create a Project folder and change directory into that folder;
```
mkdir Ent_RAG
cd Ent_RAG
```

•	Initialize codex and paste the below:
```
I am building an Enterprise AI Knowledge Base & Document Intelligence System called Ent_RAG. I am already inside the project folder. Git is already initialized, README.md already exists, and the remote origin is already set to https://github.com/Ogbunugafor-Philip/Enterprise-AI-Knowledge-Base-Document-Intelligence-System.git

Do the following completely without asking questions:

1. Create the complete folder structure:

backend/
  app/
    api/
    core/
    models/
    schemas/
    services/
    workers/
    monitoring/
    main.py
  requirements.txt
  Dockerfile

frontend/
  src/
    components/
    pages/
    services/
    App.jsx
  package.json
  tailwind.config.js
  Dockerfile

database/
  migrations/
  init.sql

ai_service/
  rag/
  embeddings/
  chunking/
  llm/

worker/
  tasks/
  celery_config.py

monitoring/
  dashboard/
  alerts/

deployment/
  nginx/
    nginx.conf
  docker-compose.yml
  docker-compose.prod.yml

.env.example

2. Create .gitignore with the following content to protect all secrets and sensitive files:
# Environment and secrets
.env
.env.local
.env.production
.env.staging
*.env

# Python
__pycache__/
*.py[cod]
*.pyo
venv/
.venv/
env/
*.egg-info/
dist/
build/
.pytest_cache/
*.log
.coverage
htmlcov/

# Node
node_modules/
dist/
build/
.npm/

# Uploads and data
uploads/
media/
*.db
*.sqlite3

# Docker
.docker/

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
*.swp
*.swo

# SSL certificates
*.pem
*.key
*.crt
*.csr

# Backup files
*.bak
*.backup
*.dump

# JWT and encryption keys
*.secret
secrets/

3. Create .dockerignore with the following content:
# Secrets and environment
.env
.env.*
*.env
secrets/
*.pem
*.key
*.crt

# Python
__pycache__/
*.pyc
*.pyo
venv/
.venv/
*.egg-info/
.pytest_cache/
.coverage
htmlcov/

# Node
node_modules/
npm-debug.log

# Git
.git/
.gitignore

# Docs and non-essential files
README.md
*.md
docs/

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/

# Logs
*.log
logs/

# Uploads
uploads/
media/

4. Create .env.example with all required environment variables showing placeholder values only, never real secrets:
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=ent_rag_db
POSTGRES_USER=ent_rag_user
POSTGRES_PASSWORD=your_secure_password_here
QDRANT_HOST=qdrant
QDRANT_PORT=6333
CEREBRAS_API_KEY=your_cerebras_api_key_here
REDIS_URL=redis://redis:6379/0
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_smtp_password_here
JWT_SECRET_KEY=your_jwt_secret_key_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENCRYPTION_KEY=your_encryption_key_here
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
ENVIRONMENT=development
TENANT_ISOLATION_MODE=strict
API_RATE_LIMIT_PER_ORG=1000
API_RATE_LIMIT_PER_USER=100

5. Create backend/app/main.py as a fully working FastAPI entry point with CORS middleware, router includes, and startup event. Add a comment block at the top describing the multi-tenant architecture: tenant isolation covers organizations, departments, documents, users, and AI retrieval access. Every database query and vector search is scoped by organization_id to ensure zero cross-tenant data exposure.

6. Create backend/requirements.txt with these packages:
fastapi, uvicorn, sqlalchemy, alembic, psycopg2-binary, python-jose, passlib, bcrypt, python-multipart, celery, redis, langchain, langchain-community, qdrant-client, sentence-transformers, pymupdf, pdfplumber, python-docx, cerebras-cloud-sdk, pydantic-settings, httpx, pytest, pillow, openpyxl, python-magic, clamd

7. Create backend/Dockerfile using Python 3.11 slim image, install requirements, run uvicorn on port 8000

8. Create frontend/package.json with React 18, Tailwind CSS, axios, react-router-dom, lucide-react

9. Create frontend/tailwind.config.js with standard config and correct content paths for src folder

10. Create frontend/src/App.jsx as a working React app shell with react-router-dom routing placeholders for User, Admin, and Super Admin workspaces

11. Create frontend/Dockerfile using Node 18 alpine, builds React app, serves on port 3000

12. Create deployment/nginx/nginx.conf as a fully working reverse proxy routing /api requests to backend:8000 and all other requests to frontend:3000, with SSL placeholder config and security headers

13. Create deployment/docker-compose.yml as a complete working Docker Compose file with these services:
- backend (builds from backend/, port 8000, depends on postgres, redis, qdrant)
- frontend (builds from frontend/, port 3000, depends on backend)
- postgres (image postgres:15, persistent volume, env vars from .env)
- redis (image redis:7-alpine, persistent volume)
- qdrant (image qdrant/qdrant, port 6333, persistent volume)
- celery_worker (builds from backend/, runs celery worker, depends on postgres and redis)
- nginx (builds from deployment/nginx/, ports 80 and 443, depends on backend and frontend)
Include named volumes, a shared network called ent_rag_network, environment variable references, restart policies, and health checks for postgres and redis.

14. Create deployment/docker-compose.prod.yml as a production variant with resource limits, stricter restart policies, and production environment settings

15. Create worker/celery_config.py as a working Celery configuration file connected to Redis broker with task routing for document processing, embedding generation, and monitoring tasks

16. Create database/init.sql as a placeholder with a detailed comment block describing the full multi-tenant PostgreSQL schema to be built in Phase 2

17. Create README.md content with project title, description, full tech stack, folder structure, local development setup using Docker Compose, environment variable setup guide, and multi-tenancy architecture explanation. Do not overwrite the existing README.md, append to it.

After creating all files and folders run these commands in order:
git add .
git commit -m "Phase 1 complete: Project initialization, folder structure, architecture setup, Docker Compose, .gitignore, .dockerignore, and multi-tenant design foundation"
git push origin main

Confirm completion of every step.
```
 <img width="1058" height="464" alt="image" src="https://github.com/user-attachments/assets/6e59a837-febe-4f53-aec2-5beced66b903" />


### Phase 2: Database Design & Core Data Models
1.	Design PostgreSQL schema for organizations, departments, users, roles, permissions, documents, chat sessions, messages, audit logs, OTP verification, password history, monitoring logs, and system alerts.
2.	Create database migrations.
3.	Build organization and department models.
4.	Build user, role, and permission models.
5.	Build chat session and message models so each user only sees their own chat history.
6.	Build document metadata, document chunks, document approval status, and document access models.
7.	Build audit log, system activity, and monitoring log models.
8.	Test all database relationships and access rules.

### Phase 2 Implementation

•	Paste this into Codex to begin Phase 2:

```
I am building an Enterprise AI Knowledge Base & Document Intelligence System called Ent_RAG. Phase 1 is complete. I am now starting Phase 2: Database Design & Core Data Models.

The project uses FastAPI, SQLAlchemy, Alembic, and PostgreSQL. The system is multi-tenant, meaning every table must include organization_id to ensure strict tenant isolation. All database queries will be scoped by organization_id so no organization can ever see another organization's data.

Do the following completely without asking questions:

1. Create backend/app/core/database.py
- SQLAlchemy async engine setup
- SessionLocal factory
- Base declarative model
- get_db dependency function for FastAPI
- Read all database credentials from .env using pydantic-settings
- Include connection pooling configuration

2. Create backend/app/core/config.py
- Pydantic Settings class reading all variables from .env
- Include PostgreSQL, Qdrant, Redis, Cerebras, SMTP, JWT, encryption, and rate limiting settings
- Single settings instance exported for use across the application

3. Create backend/app/models/organization.py
- Organization table with fields:
  id, name, slug, description, logo_url, is_active, subscription_plan,
  max_users, max_documents, storage_limit_mb,
  created_at, updated_at
- This is the top-level tenant model. Every other table references this.

4. Create backend/app/models/department.py
- Department table with fields:
  id, organization_id (FK to organizations), name, description,
  is_active, created_at, updated_at
- Include relationship to Organization

5. Create backend/app/models/user.py
- User table with fields:
  id, organization_id (FK), department_id (FK), role_id (FK),
  first_name, last_name, email, hashed_password, is_active,
  is_verified, is_first_login, must_change_password,
  failed_login_attempts, locked_until, last_login,
  password_changed_at, created_at, updated_at
- Include relationships to Organization, Department, Role

6. Create backend/app/models/role.py
- Role table with fields:
  id, organization_id (FK), name, description, is_system_role,
  created_at, updated_at
- Permission table with fields:
  id, organization_id (FK), name, description, resource, action,
  created_at, updated_at
- RolePermission junction table:
  id, role_id (FK), permission_id (FK)
- UserRole junction table:
  id, user_id (FK), role_id (FK), assigned_at, assigned_by

7. Create backend/app/models/document.py
- Document table with fields:
  id, organization_id (FK), department_id (FK), uploaded_by (FK to users),
  title, description, file_name, file_path, file_type, file_size_mb,
  status (uploaded, processing, reviewed, approved, rejected, archived),
  is_approved, approved_by (FK to users), approved_at,
  version_number, parent_document_id (self FK for versioning),
  malware_scan_status, malware_scan_result,
  chunk_count, embedding_status,
  created_at, updated_at
- DocumentChunk table with fields:
  id, document_id (FK), organization_id (FK), chunk_index,
  chunk_text, chunk_hash, token_count,
  embedding_status, qdrant_point_id,
  created_at
- DocumentAccess table with fields:
  id, document_id (FK), organization_id (FK), department_id (FK),
  role_id (FK), user_id (FK), access_type,
  granted_by (FK to users), granted_at

8. Create backend/app/models/chat.py
- ChatSession table with fields:
  id, user_id (FK), organization_id (FK),
  title, is_active, created_at, updated_at
- Message table with fields:
  id, session_id (FK), user_id (FK), organization_id (FK),
  role (user or assistant), content,
  source_documents (JSON), confidence_score, retrieval_score,
  hallucination_risk_score, response_rejected,
  feedback (correct, incorrect, unclear, hallucination),
  feedback_submitted_at, created_at

9. Create backend/app/models/audit.py
- AuditLog table with fields:
  id, organization_id (FK), user_id (FK),
  action, resource_type, resource_id,
  old_value (JSON), new_value (JSON),
  ip_address, user_agent, status,
  created_at
- This table must be protected from editing or deletion by normal users

10. Create backend/app/models/auth.py
- OTPVerification table with fields:
  id, user_id (FK), otp_code, otp_type,
  is_used, expires_at, created_at
- PasswordHistory table with fields:
  id, user_id (FK), hashed_password, created_at

11. Create backend/app/models/monitoring.py
- MonitoringLog table with fields:
  id, organization_id (FK), event_type, service_name,
  endpoint, method, status_code, response_time_ms,
  error_message, user_id (FK), ip_address,
  token_usage, created_at
- SystemAlert table with fields:
  id, organization_id (FK), alert_type, severity (low, medium, high, critical),
  title, description, affected_service,
  status (open, investigating, resolved, ignored),
  recommended_action, business_impact,
  created_at, updated_at, resolved_at, resolved_by (FK to users)
- IncidentReport table with fields:
  id, organization_id (FK), title, description,
  severity, status, affected_services (JSON),
  error_count, first_occurrence, last_occurrence,
  root_cause, resolution_steps, business_impact,
  created_at, updated_at

12. Create backend/app/models/__init__.py
- Import all models so they are registered with SQLAlchemy Base

13. Configure Alembic:
- Run: alembic init backend/alembic
- Update alembic.ini to read database URL from .env
- Update backend/alembic/env.py to:
  - Import all models
  - Use SQLAlchemy Base.metadata for autogenerate
  - Read database URL from .env using pydantic-settings

14. Create the first Alembic migration:
- Run: alembic revision --autogenerate -m "initial_schema_all_tables"
- This generates the migration file for all tables

15. Create database/schema_documentation.md documenting every table, every field, data types, relationships, and tenant isolation strategy. Explain how organization_id enforces multi-tenancy across every table.

16. Test all database relationships and models by creating backend/tests/test_models.py that:
- Tests that every model can be imported without errors
- Tests that every model has organization_id where required
- Tests that relationships between models are correctly defined
- Does not require a live database connection to run import tests

After completing all steps run:
git add .
git commit -m "Phase 2 complete: Database design, all core data models, multi-tenant schema, Alembic migrations configured"
git push origin main

Confirm completion of every step.
``` 
<img width="975" height="346" alt="image" src="https://github.com/user-attachments/assets/8895ce35-8af3-46c9-9468-6e3d3f79cb7a" />


### Phase 3: Authentication, OTP & Password Security
1.	Build JWT authentication system.
2.	Implement secure login API.
3.	Create Super Admin setup workflow.
4.	Implement OTP email verification.
5.	Restrict login until OTP verification is completed.
6.	Generate temporary passwords for newly created users.
7.	Force first-time users to change temporary passwords.
8.	Configure secure password hashing.
9.	Add forgot-password and password reset workflow.
10.	Enforce mandatory password reset every 30 days.
11.	Add account lockout after repeated failed login attempts.
12.	Track login, logout, failed login, OTP verification, password reset, and password changes in audit logs.
13.	Redirect first-time users to mandatory password change before accessing the platform.
14.	Prevent users from accessing dashboards until temporary passwords are changed.
15.	Enforce strong password policy:
i. Minimum of 8 characters
ii. At least 1 uppercase letter
iii. At least 1 lowercase letter
iv. At least 1 number
v. At least 1 special character
16.	Validate password strength during password creation and password reset.
17.	Prevent reuse of previously used passwords using password history validation.

### Phase 3 Implementation

•	Paste this into Codex to begin Phase 3:
```
I am building an Enterprise AI Knowledge Base & Document Intelligence System called Ent_RAG. Phases 1 and 2 are complete. I am now starting Phase 3: Authentication, OTP & Password Security.

The project uses FastAPI, SQLAlchemy, JWT, bcrypt, and PostgreSQL. The system is multi-tenant. Every auth operation must be scoped by organization_id.

Do the following completely without asking questions:

1. Create backend/app/core/security.py with:
- Password hashing using bcrypt via passlib
- Password verification function
- JWT access token creation function reading JWT_SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES from settings
- JWT token decoding and validation function
- Function to generate a random secure temporary password
- Function to generate a 6-digit OTP code
- Function to check if OTP is expired
- Fernet encryption and decryption functions using ENCRYPTION_KEY from settings
- Password strength validator enforcing:
  Minimum 8 characters
  At least 1 uppercase letter
  At least 1 lowercase letter
  At least 1 number
  At least 1 special character
- Password history checker to prevent reuse of last 5 passwords

2. Create backend/app/core/email.py with:
- Async email sending function using SMTP settings from .env
- send_otp_verification_email function
- send_temporary_password_email function
- send_password_reset_email function
- send_account_locked_email function
- All emails use HTML templates with professional formatting
- All email functions are async and non-blocking

3. Create backend/app/schemas/auth.py with Pydantic schemas for:
- LoginRequest: email, password
- LoginResponse: access_token, token_type, user info, must_change_password flag
- OTPVerifyRequest: email, otp_code
- PasswordChangeRequest: current_password, new_password, confirm_password
- PasswordResetRequest: email
- PasswordResetConfirm: reset_token, new_password, confirm_password
- TokenData: user_id, organization_id, role, email
- UserResponse: id, email, first_name, last_name, organization_id, department_id, role, is_active, is_verified, is_first_login

4. Create backend/app/api/deps.py with FastAPI dependency functions:
- get_current_user: decodes JWT token, fetches user from database, returns user object
- get_current_active_user: checks user is active and verified
- require_role: dependency factory that checks user has required role
- get_organization_id: extracts organization_id from current user for tenant scoping
- check_account_not_locked: verifies account is not locked before login

5. Create backend/app/api/v1/auth.py with these endpoints:
POST /api/v1/auth/login
- Validate email and password
- Check account is not locked
- Check organization is active
- Verify password using bcrypt
- On failed login increment failed_login_attempts
- Lock account after 5 failed attempts for 30 minutes
- Log failed login to AuditLog
- On success generate JWT token
- If user is_first_login or must_change_password return flag in response
- Log successful login to AuditLog
- Return LoginResponse

POST /api/v1/auth/verify-otp
- Validate OTP code for the user
- Check OTP is not expired (10 minute expiry)
- Check OTP has not been used
- Mark OTP as used
- Mark user as is_verified = True
- Log OTP verification to AuditLog
- Return success response

POST /api/v1/auth/resend-otp
- Generate new OTP code
- Invalidate previous unused OTPs for this user
- Send new OTP verification email
- Log to AuditLog
- Return success response

POST /api/v1/auth/change-password (requires authentication)
- Validate current password
- Enforce password strength policy
- Check new password not in password history
- Hash new password
- Save old password to PasswordHistory
- Update user password
- Set must_change_password = False
- Set is_first_login = False
- Set password_changed_at = now
- Log password change to AuditLog
- Return success response

POST /api/v1/auth/forgot-password
- Check email exists in the system
- Generate secure password reset token
- Send password reset email with token
- Log to AuditLog
- Return success response without revealing if email exists

POST /api/v1/auth/reset-password
- Validate reset token
- Check token not expired
- Enforce password strength policy
- Check new password not in password history
- Hash and save new password
- Save old password to PasswordHistory
- Set password_changed_at = now
- Invalidate reset token
- Log to AuditLog
- Return success response

POST /api/v1/auth/logout (requires authentication)
- Log logout event to AuditLog
- Return success response

GET /api/v1/auth/me (requires authentication)
- Return current user profile as UserResponse

6. Create backend/app/services/auth_service.py with business logic functions:
- authenticate_user: full login logic
- create_otp_for_user: generates and saves OTP
- verify_user_otp: validates OTP
- change_user_password: full password change logic
- check_password_history: checks if password was used before
- handle_failed_login: increments counter and locks if needed
- reset_failed_login_attempts: resets counter on success
- enforce_30_day_password_expiry: checks if password needs reset
- generate_password_reset_token: creates secure reset token
- validate_password_reset_token: validates reset token

7. Create backend/app/middleware/auth_middleware.py with:
- JWT authentication middleware
- Extracts and validates Bearer token from Authorization header
- Attaches user context to request state
- Returns 401 for missing or invalid tokens
- Returns 403 for insufficient permissions

8. Update backend/app/main.py to:
- Include auth router at /api/v1/auth
- Add authentication middleware
- Add 30-day password expiry check middleware that flags users who need password reset

9. Create backend/tests/test_auth.py with tests for:
- Password hashing and verification
- JWT token creation and decoding
- Password strength validation accepting strong passwords
- Password strength validation rejecting weak passwords
- OTP generation producing 6-digit codes
- Password history check blocking reused passwords
- All tests must run without a live database connection

After completing all steps run:
git add .
git commit -m "Phase 3 complete: JWT authentication, OTP verification, password security, account lockout, 30-day password expiry, audit logging"
git push origin main

Confirm completion of every step.
```
<img width="1062" height="377" alt="image" src="https://github.com/user-attachments/assets/2808de80-019a-4870-88b4-a3ad065d1e7b" />

### Phase 4: Role-Based Access Control & Data Isolation
1.	Implement role-based access control for User, Admin, and Super Admin.
2.	Restrict access based on organization, department, role, and permission level.
3.	Ensure normal users only access their own chat history.
4.	Ensure users only retrieve answers from documents they are permitted to access.
5.	Ensure Admins manage only approved document and knowledge-base operations.
6.	Ensure Super Admins manage users, roles, access, monitoring, and system governance.
7.	Protect all backend routes using authentication and permission middleware.
8.	Test for unauthorized access, role bypass, and cross-user data exposure.

### Phase 4 Implementation
•	Paste this into Codex to begin Phase 4:
```
I am building an Enterprise AI Knowledge Base & Document Intelligence System called Ent_RAG. Phases 1, 2, and 3 are complete. I am now starting Phase 4: Role-Based Access Control & Data Isolation.

The system has three role levels: USER, ADMIN, and SUPER_ADMIN. The system is multi-tenant. Every access check must be scoped by organization_id to ensure zero cross-tenant data exposure.

Do the following completely without asking questions:

1. Create backend/app/core/permissions.py with:
- RoleEnum with values: USER, ADMIN, SUPER_ADMIN
- PermissionEnum with all system permissions:
  CHAT_ASK_QUESTION
  CHAT_VIEW_OWN_HISTORY
  DOCUMENT_UPLOAD
  DOCUMENT_VIEW
  DOCUMENT_APPROVE
  DOCUMENT_REJECT
  DOCUMENT_DELETE
  DOCUMENT_MANAGE
  USER_CREATE
  USER_VIEW
  USER_UPDATE
  USER_DELETE
  USER_MANAGE
  ROLE_CREATE
  ROLE_UPDATE
  ROLE_DELETE
  ROLE_MANAGE
  DEPARTMENT_CREATE
  DEPARTMENT_UPDATE
  DEPARTMENT_DELETE
  DEPARTMENT_MANAGE
  ORGANIZATION_VIEW
  ORGANIZATION_MANAGE
  MONITORING_VIEW
  MONITORING_MANAGE
  AUDIT_LOG_VIEW
  SYSTEM_GOVERNANCE
  SUPER_ADMIN_ONLY

- ROLE_PERMISSIONS dictionary mapping each role to its allowed permissions:
  USER role permissions:
    CHAT_ASK_QUESTION
    CHAT_VIEW_OWN_HISTORY
    DOCUMENT_VIEW

  ADMIN role permissions:
    CHAT_ASK_QUESTION
    CHAT_VIEW_OWN_HISTORY
    DOCUMENT_UPLOAD
    DOCUMENT_VIEW
    DOCUMENT_APPROVE
    DOCUMENT_REJECT
    DOCUMENT_DELETE
    DOCUMENT_MANAGE
    USER_VIEW
    DEPARTMENT_VIEW
    MONITORING_VIEW
    AUDIT_LOG_VIEW

  SUPER_ADMIN role permissions:
    All permissions including SYSTEM_GOVERNANCE and SUPER_ADMIN_ONLY

- has_permission function: checks if a role has a specific permission
- require_permission decorator factory for FastAPI route protection

2. Update backend/app/api/deps.py with new dependency functions:
- require_role(allowed_roles: list) — dependency factory that:
  Checks current user role is in allowed_roles
  Checks user organization_id matches request context
  Returns 403 if role not allowed
  Returns 403 if organization mismatch

- require_permission(permission: PermissionEnum) — dependency factory that:
  Checks current user role has the required permission
  Returns 403 if permission not granted

- get_tenant_context — dependency that:
  Extracts organization_id from current user
  Returns tenant context object with organization_id
  Ensures all queries will be scoped to this organization only

- verify_same_organization(target_organization_id) — function that:
  Checks requesting user belongs to same organization as target resource
  Returns 403 if organization mismatch
  Prevents cross-tenant data access

- verify_own_resource(resource_user_id, current_user_id) — function that:
  Checks USER role can only access their own resources
  ADMIN and SUPER_ADMIN can access org-scoped resources
  Returns 403 if USER tries to access another user's resource

3. Create backend/app/middleware/rbac_middleware.py with:
- RBACMiddleware class that:
  Runs on every request
  Extracts JWT token and decodes user role and organization_id
  Attaches role, permissions, and organization_id to request state
  Logs access attempts to MonitoringLog
  Returns 401 for unauthenticated requests to protected routes
  Returns 403 for insufficient role or permission
  Whitelists public routes: /api/v1/auth/login, /api/v1/auth/verify-otp, /api/v1/auth/forgot-password, /api/v1/auth/reset-password, /api/v1/setup/super-admin, /docs, /health

4. Create backend/app/services/rbac_service.py with:
- get_user_permissions: returns list of permissions for a user based on their role
- check_document_access: verifies user can access a specific document based on:
  organization_id match
  department_id match if document is department-restricted
  role permission level
  DocumentAccess table rules
  Returns True or False
- check_chat_isolation: verifies user can only access their own chat sessions
  USER role: can only access sessions where session.user_id == current_user.id
  ADMIN role: can access all sessions in their organization
  SUPER_ADMIN role: can access all sessions across all organizations
- get_accessible_documents: returns list of document IDs a user is allowed to access based on:
  organization_id
  department_id
  role permissions
  DocumentAccess table
  Approved status only
- filter_by_tenant: utility function that adds organization_id filter to any SQLAlchemy query

5. Create backend/app/api/v1/roles.py with these endpoints all protected by require_role([SUPER_ADMIN]):
GET /api/v1/roles — list all roles in the organization
POST /api/v1/roles — create a new role
PUT /api/v1/roles/{role_id} — update a role
DELETE /api/v1/roles/{role_id} — delete a role
POST /api/v1/roles/{role_id}/permissions — assign permissions to a role
GET /api/v1/roles/{role_id}/permissions — list permissions for a role

All endpoints must:
- Scope queries by organization_id
- Log actions to AuditLog
- Validate role belongs to same organization before update or delete

6. Create backend/app/api/v1/departments.py with these endpoints:
GET /api/v1/departments — list departments, requires ADMIN or SUPER_ADMIN
POST /api/v1/departments — create department, requires SUPER_ADMIN
PUT /api/v1/departments/{dept_id} — update department, requires SUPER_ADMIN
DELETE /api/v1/departments/{dept_id} — delete department, requires SUPER_ADMIN

All endpoints must:
- Scope queries by organization_id
- Log actions to AuditLog
- Validate department belongs to same organization

7. Create backend/app/schemas/rbac.py with Pydantic schemas for:
- RoleCreate: name, description, organization_id
- RoleUpdate: name, description
- RoleResponse: id, name, description, organization_id, permissions list
- PermissionResponse: id, name, resource, action
- DepartmentCreate: name, description, organization_id
- DepartmentUpdate: name, description
- DepartmentResponse: id, name, description, organization_id, is_active

8. Create data isolation enforcement rules:
Create backend/app/core/data_isolation.py with:
- TenantScope class that:
  Wraps SQLAlchemy queries to always add organization_id filter
  Raises IsolationViolationError if query attempts cross-tenant access
  Logs isolation violations to AuditLog with HIGH severity alert

- ChatIsolation class that:
  Enforces USER role can only query ChatSession where user_id == current_user.id
  Enforces ADMIN role can only query ChatSession where organization_id == current_user.organization_id
  Enforces SUPER_ADMIN can query all ChatSessions

- DocumentIsolation class that:
  Enforces document queries always filter by organization_id
  Enforces department-level document restrictions
  Enforces role-level document access rules
  Blocks access to unapproved, archived, deleted, or expired documents
  Enforces DocumentAccess table rules

9. Update backend/app/main.py to:
- Register RBACMiddleware
- Include roles router at /api/v1/roles
- Include departments router at /api/v1/departments
- Add global exception handler for IsolationViolationError returning 403
- Add global exception handler for permission denied errors returning 403

10. Create backend/tests/test_rbac.py with tests for:
- USER role has CHAT_ASK_QUESTION permission
- USER role does NOT have DOCUMENT_APPROVE permission
- ADMIN role has DOCUMENT_APPROVE permission
- ADMIN role does NOT have SYSTEM_GOVERNANCE permission
- SUPER_ADMIN role has all permissions
- has_permission returns correct results for each role
- verify_own_resource blocks USER from accessing another user's resource
- verify_own_resource allows ADMIN to access org-scoped resource
- check_chat_isolation blocks USER from accessing another user's chat
- TenantScope raises IsolationViolationError on cross-tenant query attempt
- All tests run without live database connection

After completing all steps run:
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/test_rbac.py -v
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/test_auth.py -v
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/test_models.py -v

Report all test results then run:
git add .
git commit -m "Phase 4 complete: RBAC implementation, role permissions, data isolation, tenant scoping, chat isolation, document access control"
git push origin main

Confirm completion of every step.
```
<img width="975" height="365" alt="image" src="https://github.com/user-attachments/assets/c59cfbd4-1321-4367-b303-aeaac8fd2a35" />

### Phase 5: User Workspace
1.	Build normal user dashboard.
2.	Build AI question-and-answer interface.
3.	Allow users to start new chat sessions.
4.	Allow users to view only their own previous chats.
5.	Store user questions and AI responses under the correct user account.
6.	Display AI answers with source references from approved documents.
7.	Add search for previous personal conversations.
8.	Track AI usage per user for monitoring and analytics.
9.	Add “no source, no answer” rule so the AI does not guess outside approved knowledge.
10.	Display AI confidence score for each response.
11.	Display retrieval relevance score for retrieved documents.
12.	Display hallucination risk indicator for weak or unsupported responses.
13.	Add user feedback buttons:
i. Correct answer
ii. Incorrect answer
iii. Unclear answer
iv. Report hallucination
14.	Prevent the AI from answering from expired, archived, deleted, or restricted documents.
15.	Add first-time user onboarding after login to guide new employees through the AI Q&A interface.
16.	Add a short-guided tour showing users how to ask questions, read source references, understand confidence scores, and report wrong answers.
17.	Add contextual tips inside the chat interface to help users ask better questions.
18.	Add sample questions based on the user’s department or role.
19.	Add a simple help section explaining what the AI can answer, what it cannot answer, and how to use it safely.

### Phase 5 Implementation
•	Paste this into Codex to begin Phase 5:

```
I am building an Enterprise AI Knowledge Base & Document Intelligence System called Ent_RAG. Phases 1 through 4 are complete. I am now starting Phase 5: User Workspace.

Phase 5 covers the backend API endpoints, schemas, and services for the user workspace. The frontend React components are also included. The system is multi-tenant and all queries must be scoped by organization_id.

Do the following completely without asking questions:

BACKEND SECTION

1. Create backend/app/schemas/chat.py with Pydantic schemas for:
- ChatSessionCreate: title (optional)
- ChatSessionResponse: id, title, created_at, updated_at, message_count
- ChatSessionListResponse: list of ChatSessionResponse, total count
- MessageCreate: content (the user question)
- MessageResponse: id, session_id, role, content, source_documents, confidence_score, retrieval_score, hallucination_risk_score, response_rejected, feedback, created_at
- AskQuestionRequest: session_id (optional, creates new session if not provided), question
- AskQuestionResponse: message_id, answer, source_documents, confidence_score, retrieval_score, hallucination_risk_score, response_rejected, fallback_message
- SourceDocument: document_id, document_title, chunk_text, relevance_score, page_number
- FeedbackRequest: message_id, feedback_type (correct, incorrect, unclear, hallucination), feedback_note (optional)
- FeedbackResponse: message_id, feedback_type, submitted_at
- ChatSearchRequest: query, limit, offset
- ChatSearchResponse: sessions list, messages list, total_results
- SampleQuestionsResponse: department, role, questions list
- OnboardingStatusResponse: is_completed, current_step, total_steps

2. Create backend/app/services/chat_service.py with:
- create_chat_session: creates new ChatSession scoped to user and organization
- get_user_chat_sessions: returns only sessions belonging to current user, scoped by organization_id
- get_session_messages: returns messages for a session, verifies session belongs to current user
- save_user_message: saves user question to Message table under correct user and session
- save_ai_response: saves AI answer with confidence_score, retrieval_score, hallucination_risk_score, source_documents as JSON
- search_user_conversations: searches across user's own chat history only, never other users' history
- submit_message_feedback: saves feedback to Message table, logs to AuditLog
- track_ai_usage: logs AI query to MonitoringLog with token_usage, response_time, user_id, organization_id
- get_sample_questions: returns sample questions based on user department and role
- get_onboarding_status: checks if user has completed onboarding tour
- complete_onboarding_step: marks onboarding step as complete
- complete_onboarding: marks full onboarding as done, updates user record

3. Create backend/app/services/ai_guard_service.py with:
- validate_document_eligibility: checks document is approved, not archived, not deleted, not expired, user has access permission. Returns True or False with reason.
- enforce_no_source_no_answer: if no eligible source documents retrieved above threshold, block AI from answering. Return safe fallback message instead.
- calculate_confidence_score: calculates response confidence score from 0.0 to 1.0 based on retrieval quality
- calculate_retrieval_score: calculates retrieval relevance score from 0.0 to 1.0
- calculate_hallucination_risk: calculates hallucination risk score from 0.0 to 1.0. Higher score means higher risk.
- should_reject_response: returns True if confidence_score is below 0.5 or hallucination_risk is above 0.7
- get_fallback_message: returns safe fallback message when no reliable source found
- filter_eligible_documents: filters retrieved document chunks to only include eligible ones before sending to LLM

4. Create backend/app/api/v1/chat.py with these endpoints all requiring authentication and USER role minimum:

POST /api/v1/chat/sessions
- Creates new chat session for current user
- Scopes to current user and organization_id
- Returns ChatSessionResponse

GET /api/v1/chat/sessions
- Returns only current user's chat sessions
- Never returns other users sessions
- Supports pagination
- Returns ChatSessionListResponse

GET /api/v1/chat/sessions/{session_id}
- Returns session details and messages
- Verifies session belongs to current user
- Returns 403 if session belongs to another user
- Returns messages with confidence scores and source references

DELETE /api/v1/chat/sessions/{session_id}
- Deletes session and all messages
- Verifies session belongs to current user
- Logs to AuditLog

POST /api/v1/chat/ask
- Accepts AskQuestionRequest
- Creates new session if session_id not provided
- Checks user permissions before retrieval
- Calls ai_guard_service.filter_eligible_documents
- Calls ai_guard_service.enforce_no_source_no_answer
- If no eligible sources: returns fallback message, saves rejected response to Message table
- If eligible sources found: generates AI answer (placeholder for now, real RAG in Phase 9)
- Calls ai_guard_service.calculate_confidence_score
- Calls ai_guard_service.calculate_retrieval_score
- Calls ai_guard_service.calculate_hallucination_risk
- Calls ai_guard_service.should_reject_response
- If response rejected: saves rejected flag to Message, returns safe fallback
- Saves user question and AI response to Message table
- Tracks usage via chat_service.track_ai_usage
- Returns AskQuestionResponse with answer, sources, scores

POST /api/v1/chat/feedback
- Accepts FeedbackRequest
- Verifies message belongs to current user
- Saves feedback to Message table
- Logs feedback to AuditLog
- Returns FeedbackResponse

GET /api/v1/chat/search
- Searches current user's own conversations only
- Never searches other users conversations
- Accepts query, limit, offset
- Returns matching sessions and messages
- Returns ChatSearchResponse

GET /api/v1/chat/sample-questions
- Returns sample questions based on user department and role
- No authentication bypass possible
- Returns SampleQuestionsResponse

GET /api/v1/chat/onboarding-status
- Returns current onboarding status for user
- Returns OnboardingStatusResponse

POST /api/v1/chat/onboarding/complete-step
- Marks an onboarding step as complete
- Accepts step_number
- Returns updated onboarding status

POST /api/v1/chat/onboarding/complete
- Marks full onboarding as complete
- Updates user record
- Returns success response

5. Create backend/app/api/v1/users.py with:
GET /api/v1/users/me — returns current user profile
PUT /api/v1/users/me — updates current user profile (name only, not role or organization)
GET /api/v1/users/me/usage-stats — returns AI usage statistics for current user:
  Total questions asked
  Total sessions created
  Most active day
  Average confidence score received
  Number of feedback submissions

6. Update backend/app/main.py to:
- Include chat router at /api/v1/chat
- Include users router at /api/v1/users

7. Create backend/tests/test_chat.py with tests for:
- create_chat_session creates session with correct user_id and organization_id
- get_user_chat_sessions never returns sessions from other users
- search_user_conversations scoped to current user only
- submit_message_feedback saves correct feedback type
- ai_guard_service.should_reject_response returns True for low confidence score below 0.5
- ai_guard_service.should_reject_response returns True for hallucination risk above 0.7
- ai_guard_service.should_reject_response returns False for good scores
- get_fallback_message returns non-empty string
- enforce_no_source_no_answer blocks response when no sources provided
- All tests run without live database or AI service connections

FRONTEND SECTION

8. Create frontend/src/pages/UserDashboard.jsx with:
- Clean professional dashboard layout using Tailwind CSS
- Welcome message with user first name
- Quick stats: total questions asked, sessions created, last active
- Recent chat sessions list with titles and timestamps
- Quick ask input box to start a new question immediately
- Navigation links to: New Chat, Chat History, Help
- Onboarding banner for first-time users with Start Tour button
- Responsive layout for desktop and mobile

9. Create frontend/src/pages/ChatInterface.jsx with:
- Full chat interface layout
- Message thread showing user questions and AI answers
- Each AI answer displays:
  Answer text
  Source references list with document title and page number
  Confidence score badge (green above 0.8, yellow 0.5 to 0.8, red below 0.5)
  Retrieval relevance score
  Hallucination risk indicator (low, medium, high)
  Feedback buttons: Correct, Incorrect, Unclear, Report Hallucination
- Rejected response displays safe fallback message in amber warning box
- Input box at bottom with Send button
- New Chat button in header
- Chat history sidebar showing previous sessions
- Contextual tips panel showing prompting advice
- Loading spinner while AI is generating response
- Empty state when no messages yet

10. Create frontend/src/pages/ChatHistory.jsx with:
- List of all user's previous chat sessions
- Search bar to search across conversations
- Each session shows title, date, message count
- Click session to open full conversation
- Delete session button with confirmation dialog
- Pagination for long history lists
- Empty state when no history exists

11. Create frontend/src/components/OnboardingTour.jsx with:
- Step-by-step guided tour overlay component
- 5 tour steps:
  Step 1: Welcome - explain what the AI knowledge base does
  Step 2: How to ask questions - show the input box and give examples
  Step 3: Reading answers - explain source references and confidence scores
  Step 4: Feedback buttons - explain how to report wrong answers
  Step 5: Help section - show where to find help
- Progress indicator showing current step and total steps
- Next, Previous, and Skip Tour buttons
- Stores completion status so tour does not repeat
- Triggered automatically for is_first_login users

12. Create frontend/src/components/SampleQuestions.jsx with:
- Displays sample questions relevant to user department and role
- Clicking a sample question populates the chat input automatically
- Shows 5 to 8 sample questions at a time
- Refresh button to load different samples
- Displayed inside chat interface as a helper panel

13. Create frontend/src/components/HelpSection.jsx with:
- What the AI can answer: questions about approved company documents
- What the AI cannot answer: questions outside uploaded documents, general knowledge, personal opinions
- How to use it safely: verify important answers with source documents, report wrong answers
- How confidence scores work: green means high confidence, red means low confidence
- How to report a problem: use the Report Hallucination button
- Contact admin section

14. Create frontend/src/services/chatApi.js with:
- createSession: POST /api/v1/chat/sessions
- getSessions: GET /api/v1/chat/sessions
- getSession: GET /api/v1/chat/sessions/{id}
- deleteSession: DELETE /api/v1/chat/sessions/{id}
- askQuestion: POST /api/v1/chat/ask
- submitFeedback: POST /api/v1/chat/feedback
- searchConversations: GET /api/v1/chat/search
- getSampleQuestions: GET /api/v1/chat/sample-questions
- getOnboardingStatus: GET /api/v1/chat/onboarding-status
- completeOnboardingStep: POST /api/v1/chat/onboarding/complete-step
- completeOnboarding: POST /api/v1/chat/onboarding/complete
- getUserStats: GET /api/v1/users/me/usage-stats
- All functions include Authorization Bearer token header
- All functions handle errors and return structured responses

15. Update frontend/src/App.jsx to add routes:
- /dashboard — UserDashboard (protected, USER role)
- /chat — ChatInterface (protected, USER role)
- /chat/:sessionId — ChatInterface with specific session (protected, USER role)
- /history — ChatHistory (protected, USER role)
- /help — HelpSection (protected, USER role)

After completing all steps run:
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/test_chat.py -v
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/test_rbac.py -v
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/test_auth.py -v
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/test_models.py -v

Report all test results then run:
git add .
git commit -m "Phase 5 complete: User workspace, chat interface, AI guard service, onboarding tour, sample questions, help section, feedback system"
git push origin main

Confirm completion of every step.
```
<img width="975" height="358" alt="image" src="https://github.com/user-attachments/assets/503cf275-5f25-44fb-98bd-686fe0a0c2df" />


### Phase 6: Admin Workspace & Document Management
1.	Build Admin dashboard.
2.	Build secure document upload API.
3.	Support PDF, DOCX, TXT, Excel, and scanned image uploads.
4.	Validate uploaded files by file type, size, and content.
5.	Scan uploaded files for malware before processing.
6.	Store document metadata in PostgreSQL.
7.	Extract document text using OCR and document parsers.
8.	Clean and preprocess extracted content.
9.	Chunk documents into AI-searchable sections.
10.	Generate embeddings for processed chunks.
11.	Store embeddings in Qdrant.
12.	Allow Admins to view uploaded documents, ingestion status, failed uploads, and processed files.

### Phase 6 Implementation
•	Paste this into Codex to begin Phase 6:
```
I am building an Enterprise AI Knowledge Base & Document Intelligence System called Ent_RAG. Phases 1 through 5 are complete. I am now starting Phase 6: Admin Workspace & Document Management.

The system is multi-tenant. All operations must be scoped by organization_id. Document processing runs as background Celery tasks so uploads are non-blocking.

Do the following completely without asking questions:

BACKEND SECTION

1. Create backend/app/schemas/document.py with Pydantic schemas for:
- DocumentUploadResponse: id, title, file_name, file_type, file_size_mb, status, malware_scan_status, created_at
- DocumentResponse: id, title, description, file_name, file_type, file_size_mb, status, is_approved, approved_by, approved_at, version_number, chunk_count, embedding_status, malware_scan_status, malware_scan_result, uploaded_by, department_id, organization_id, created_at, updated_at
- DocumentListResponse: documents list, total count, page, page_size
- DocumentStatusResponse: id, file_name, status, malware_scan_status, embedding_status, chunk_count, error_message, updated_at
- DocumentFilterRequest: status, file_type, department_id, date_from, date_to, search_query, page, page_size
- IngestionStatusResponse: document_id, file_name, current_stage, progress_percent, error_message, started_at, completed_at
- FailedUploadResponse: id, file_name, failure_reason, failure_stage, created_at
- AdminDashboardStats: total_documents, pending_approval, approved_documents, failed_uploads, total_chunks, documents_by_status, documents_by_type, recent_uploads list

2. Create backend/app/services/file_validation_service.py with:
- validate_file_type: checks file extension and MIME type against allowed list
  Allowed types: PDF, DOCX, TXT, XLSX, XLS, PNG, JPG, JPEG, TIFF
  Returns True or False with reason
- validate_file_size: checks file does not exceed max size limit (default 50MB)
  Returns True or False with reason
- validate_file_content: checks file is not empty and content matches declared type
  Detects file type spoofing where extension does not match actual content
  Returns True or False with reason
- validate_file_name: checks file name for dangerous characters and path traversal attempts
  Returns sanitized file name
- run_all_validations: runs all validation checks and returns combined result with list of all failures

3. Create backend/app/services/malware_scan_service.py with:
- scan_file_with_clamd: scans file using ClamAV clamd socket
  Returns scan_result: clean or infected
  Returns threat_name if infected
  Returns scan_status: completed, failed, unavailable
- scan_file_fallback: if ClamAV unavailable uses basic signature checking
  Checks for common malicious file signatures
  Returns scan_result and scan_status
- update_document_scan_result: updates Document table with scan result and status
- quarantine_infected_file: moves infected file to quarantine folder and marks document as rejected
- is_safe_to_process: returns True only if scan_result is clean and scan_status is completed

4. Create backend/app/services/document_processor_service.py with:
- extract_text_from_pdf: extracts text using PyMuPDF with pdfplumber fallback
  Handles encrypted PDFs gracefully
  Returns extracted text and page count
- extract_text_from_docx: extracts text using python-docx
  Preserves paragraph structure
  Returns extracted text
- extract_text_from_txt: reads plain text file with encoding detection
  Returns extracted text
- extract_text_from_excel: extracts text from Excel using openpyxl
  Converts tables to readable text format
  Returns extracted text
- extract_text_from_image: performs OCR on scanned images using pytesseract or easyocr
  Returns extracted text and confidence score
- route_extraction: automatically routes document to correct extractor based on file type
  Returns extracted text, page count, extraction method used
- clean_extracted_text: removes excessive whitespace, null characters, encoding artifacts
  Normalizes unicode characters
  Returns cleaned text
- preprocess_for_chunking: prepares cleaned text for chunking
  Identifies document structure: headings, sections, paragraphs
  Returns structured text ready for chunking

5. Create backend/app/services/chunking_service.py with:
- semantic_chunk: splits text into semantically meaningful chunks
  Uses sentence boundary detection
  Target chunk size 300 to 500 tokens
  Maintains context overlap of 50 tokens between chunks
  Returns list of chunk texts with metadata
- hierarchical_chunk: splits document preserving heading and section hierarchy
  Level 1: document sections
  Level 2: subsections
  Level 3: paragraphs
  Returns hierarchical chunk structure
- hybrid_chunk: combines semantic and hierarchical chunking
  Uses hierarchical structure to identify sections
  Uses semantic chunking within each section
  This is the primary chunking method
  Returns list of chunks with section context
- calculate_chunk_hash: generates SHA256 hash for each chunk for deduplication
- save_chunks_to_db: saves all chunks to DocumentChunk table with organization_id, document_id, chunk_index, chunk_text, chunk_hash, token_count
- get_token_count: estimates token count for a text string

6. Create backend/app/services/embedding_service.py with:
- load_embedding_model: loads SentenceTransformer model (model: all-MiniLM-L6-v2)
  Caches model after first load
  Returns model instance
- generate_embedding: generates embedding vector for a single text chunk
  Returns numpy array
- generate_embeddings_batch: generates embeddings for a list of chunks in batches of 32
  Returns list of embedding vectors
- store_embeddings_in_qdrant: stores embedding vectors in Qdrant
  Collection name: ent_rag_{organization_id}
  Each point includes: chunk_id, document_id, organization_id, department_id, chunk_text, chunk_index, document_title
  Uses organization_id as payload filter for tenant isolation
  Returns list of Qdrant point IDs
- create_qdrant_collection: creates Qdrant collection for organization if it does not exist
  Vector size: 384 (all-MiniLM-L6-v2 output)
  Distance metric: Cosine
- update_chunk_qdrant_ids: updates DocumentChunk table with Qdrant point IDs after storage
- delete_document_embeddings: removes all Qdrant points for a document when document is deleted

7. Create backend/app/workers/document_tasks.py with Celery tasks:
- process_document_task: main document processing pipeline task
  Step 1: Update document status to processing
  Step 2: Run malware scan, if infected quarantine and fail
  Step 3: Extract text using document_processor_service
  Step 4: Clean and preprocess extracted text
  Step 5: Run hybrid chunking using chunking_service
  Step 6: Save chunks to DocumentChunk table
  Step 7: Generate embeddings using embedding_service
  Step 8: Store embeddings in Qdrant
  Step 9: Update document status to reviewed and embedding_status to completed
  Step 10: Log completion to MonitoringLog
  On any failure: update document status to failed, save error message, log to MonitoringLog
  
- reprocess_document_task: reprocesses a previously failed document
  Deletes existing chunks and embeddings first
  Runs full process_document_task pipeline again

- delete_document_embeddings_task: async task to remove embeddings from Qdrant when document deleted

8. Create backend/app/api/v1/admin/documents.py with these endpoints all requiring ADMIN or SUPER_ADMIN role:

POST /api/v1/admin/documents/upload
- Accepts multipart file upload
- Runs file_validation_service.run_all_validations
- If validation fails return 400 with detailed failure reasons
- Save file to secure uploads directory organized by organization_id/department_id/
- Save document metadata to PostgreSQL with status = uploaded
- Queue process_document_task as background Celery task
- Return DocumentUploadResponse immediately without waiting for processing

GET /api/v1/admin/documents
- Returns paginated list of documents for current organization
- Supports filtering by status, file_type, department_id, date range, search query
- Scoped by organization_id
- Returns DocumentListResponse

GET /api/v1/admin/documents/{document_id}
- Returns full document details
- Verifies document belongs to current organization
- Returns DocumentResponse

GET /api/v1/admin/documents/{document_id}/status
- Returns current ingestion status and processing progress
- Returns IngestionStatusResponse

GET /api/v1/admin/documents/failed
- Returns list of all failed uploads for current organization
- Includes failure reason and stage
- Returns list of FailedUploadResponse

POST /api/v1/admin/documents/{document_id}/reprocess
- Queues reprocess_document_task for a failed document
- Verifies document belongs to current organization
- Returns success response

DELETE /api/v1/admin/documents/{document_id}
- Soft deletes document by setting status to deleted
- Queues delete_document_embeddings_task
- Logs to AuditLog
- Returns success response

GET /api/v1/admin/dashboard/stats
- Returns AdminDashboardStats for current organization
- Counts documents by status
- Counts documents by type
- Returns recent uploads list
- All scoped by organization_id

9. Create backend/app/api/v1/admin/__init__.py as empty init file

10. Create secure file storage structure:
Create backend/app/core/file_storage.py with:
- get_upload_path: returns secure file path organized as uploads/{organization_id}/{department_id}/{document_id}/{filename}
- save_uploaded_file: saves file to correct path, creates directories if needed
- delete_file: safely deletes file from storage
- get_file_path: returns full path for a document_id
- ensure_upload_directory: creates upload directory structure if not exists
- UPLOAD_BASE_DIR set to uploads/ relative to project root

11. Update backend/app/main.py to:
- Include admin documents router at /api/v1/admin/documents
- Include admin dashboard router at /api/v1/admin/dashboard
- Ensure uploads directory is created on startup

12. Update worker/celery_config.py to:
- Register document_tasks module
- Set task routing for document processing tasks to document_queue
- Configure task retry policy: max 3 retries with exponential backoff
- Set task time limit to 600 seconds for large document processing

FRONTEND SECTION

13. Create frontend/src/pages/AdminDashboard.jsx with:
- Professional admin dashboard layout using Tailwind CSS
- Stats cards showing: total documents, pending approval, approved documents, failed uploads
- Documents by status chart (visual breakdown)
- Documents by file type breakdown
- Recent uploads table with file name, type, status, uploaded by, date
- Quick action buttons: Upload Document, View All Documents, View Failed Uploads
- System health indicator
- Navigation links to: Documents, Approvals, Users (Super Admin only), Monitoring

14. Create frontend/src/pages/DocumentManagement.jsx with:
- Documents list table with columns: title, file type, size, status, department, uploaded by, date, actions
- Filter bar: filter by status, file type, department, date range
- Search bar for document title search
- Upload button that opens upload modal
- Status badges with colors: uploaded=blue, processing=yellow, reviewed=purple, approved=green, rejected=red, failed=red
- Actions per document: View Details, Reprocess (if failed), Delete
- Pagination controls
- Bulk selection and bulk delete option

15. Create frontend/src/components/DocumentUploadModal.jsx with:
- Drag and drop file upload area
- Supported file types displayed: PDF, DOCX, TXT, Excel, Images
- File size limit displayed: 50MB maximum
- Department selector dropdown
- Document title and description fields
- Upload progress indicator
- Validation error messages displayed clearly
- Processing status updates after upload
- Success and error states

16. Create frontend/src/components/DocumentStatusTracker.jsx with:
- Real-time status display for a document being processed
- Progress stages: Uploaded, Malware Scan, Text Extraction, Chunking, Embedding, Complete
- Current stage highlighted
- Error message displayed if processing failed
- Retry button for failed documents
- Estimated completion indicator

17. Create frontend/src/services/adminApi.js with:
- uploadDocument: POST /api/v1/admin/documents/upload with multipart form data
- getDocuments: GET /api/v1/admin/documents with filter params
- getDocument: GET /api/v1/admin/documents/{id}
- getDocumentStatus: GET /api/v1/admin/documents/{id}/status
- getFailedUploads: GET /api/v1/admin/documents/failed
- reprocessDocument: POST /api/v1/admin/documents/{id}/reprocess
- deleteDocument: DELETE /api/v1/admin/documents/{id}
- getDashboardStats: GET /api/v1/admin/dashboard/stats
- All functions include Authorization Bearer token header
- All functions handle errors and return structured responses

18. Update frontend/src/App.jsx to add routes:
- /admin/dashboard — AdminDashboard (protected, ADMIN role minimum)
- /admin/documents — DocumentManagement (protected, ADMIN role minimum)

19. Create backend/tests/test_document_processing.py with tests for:
- file_validation_service validates correct file types
- file_validation_service rejects disallowed file types
- file_validation_service rejects files exceeding size limit
- file_validation_service detects file type spoofing
- chunking_service hybrid_chunk returns non-empty list for sample text
- chunking_service calculates correct token count
- chunking_service generates unique chunk hashes
- chunking_service chunk overlap is maintained between adjacent chunks
- embedding_service load_embedding_model returns model instance
- embedding_service generate_embedding returns correct vector dimensions (384)
- document_processor_service clean_extracted_text removes excessive whitespace
- All tests run without live database, Qdrant, or ClamAV connections

After completing all steps run:
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/test_document_processing.py -v
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/test_chat.py -v
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/test_rbac.py -v
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/test_auth.py -v
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/test_models.py -v

Report all test results then run:
git add .
git commit -m "Phase 6 complete: Admin workspace, secure document upload, malware scanning, OCR text extraction, hybrid chunking, embedding generation, Qdrant storage, background Celery tasks"
git push origin main

Confirm completion of every step.
``` 
<img width="975" height="444" alt="image" src="https://github.com/user-attachments/assets/c5ffcff3-5dbe-4600-ad1a-2177a01bdbe2" />

### Phase 7: Document Approval & Knowledge Governance
1.	Add document approval workflow: Uploaded → Processing → Reviewed → Approved → Available for AI Search.
2.	Prevent unapproved documents from being used by the AI.
3.	Allow Admins or Super Admins to approve or reject documents.
4.	Track document uploader, reviewer, approval status, and approval date.
5.	Allow document versioning when updated documents are uploaded.
6.	Keep audit logs for document upload, approval, rejection, deletion, and reprocessing.
7.	Add document access rules by organization, department, role, and permission.
8.	Test that restricted documents cannot appear in AI answers for unauthorized users.

### Phase 7 Implementation
•	Paste this into Codex to begin Phase 7:
```
I am building an Enterprise AI Knowledge Base & Document Intelligence System called Ent_RAG. Phases 1 through 6 are complete. I am now starting Phase 7: Document Approval & Knowledge Governance.

The system is multi-tenant. All operations must be scoped by organization_id.

Do the following completely without asking questions:

BACKEND SECTION

1. Create backend/app/schemas/approval.py with Pydantic schemas for:
- DocumentApprovalRequest: document_id, action (approve or reject), rejection_reason (required if rejecting), access_level (organization, department, role, user)
- DocumentApprovalResponse: document_id, file_name, status, approved_by, approved_at, rejection_reason
- DocumentVersionCreate: parent_document_id, title, description, department_id
- DocumentVersionResponse: id, title, version_number, parent_document_id, status, created_at
- DocumentVersionListResponse: versions list, current_version, total_versions
- DocumentAccessRuleCreate: document_id, access_type (organization, department, role, user), department_id (optional), role_id (optional), user_id (optional)
- DocumentAccessRuleResponse: id, document_id, access_type, department_id, role_id, user_id, granted_by, granted_at
- ApprovalQueueResponse: documents list, total_pending, total_reviewed, page, page_size
- KnowledgeGovernanceStats: total_approved, total_rejected, total_pending_review, approval_rate_percent, avg_approval_time_hours, most_active_reviewer

2. Create backend/app/services/approval_service.py with:
- get_approval_queue: returns all documents with status reviewed or uploaded for current organization, scoped by organization_id
- approve_document: 
  Sets document status to approved
  Sets is_approved = True
  Sets approved_by = current_user.id
  Sets approved_at = now
  Makes document available for AI search
  Logs to AuditLog with action DOCUMENT_APPROVED
  Sends notification if email configured
  Returns updated document
- reject_document:
  Sets document status to rejected
  Sets is_approved = False
  Saves rejection_reason
  Removes any existing embeddings from Qdrant via delete_document_embeddings_task
  Logs to AuditLog with action DOCUMENT_REJECTED
  Returns updated document
- get_document_approval_history: returns full approval audit trail for a document
- get_governance_stats: returns KnowledgeGovernanceStats for current organization
- enforce_approval_gate: checks document status is approved before allowing AI to use it. Returns True only if status is approved and is_approved is True. This is called by AI guard service.

3. Update backend/app/services/ai_guard_service.py:
- Update validate_document_eligibility to call approval_service.enforce_approval_gate
- Ensure AI never uses documents with status: uploaded, processing, reviewed, rejected, archived, deleted, failed
- Only documents with status approved and is_approved True can be used by AI
- Add check for document expiry if expiry date is set

4. Create backend/app/services/versioning_service.py with:
- create_document_version:
  Accepts new file upload for existing document
  Sets parent_document_id on new document to link versions
  Increments version_number automatically
  Old version status set to archived
  New version goes through full approval workflow
  Logs to AuditLog with action DOCUMENT_VERSION_CREATED
  Returns new document version
- get_document_versions: returns all versions of a document ordered by version_number
- get_current_version: returns the latest approved version of a document
- rollback_to_version: allows Super Admin to restore a previous version as current active version

5. Create backend/app/services/access_rule_service.py with:
- create_access_rule: creates DocumentAccess record for a document
  Validates document belongs to current organization
  Validates department, role, or user belongs to same organization
  Logs to AuditLog with action DOCUMENT_ACCESS_RULE_CREATED
- get_document_access_rules: returns all access rules for a document
- delete_access_rule: removes an access rule
  Logs to AuditLog
- check_user_document_access: comprehensive access check combining:
  Organization-level access
  Department-level access
  Role-level access
  User-level access
  DocumentAccess table rules
  Returns True if user has access, False otherwise
- get_user_accessible_document_ids: returns list of all document IDs accessible to a user
  Used by RAG pipeline to filter vector search results

6. Update backend/app/services/rbac_service.py:
- Update check_document_access to call access_rule_service.check_user_document_access
- Update get_accessible_documents to call access_rule_service.get_user_accessible_document_ids

7. Create backend/app/api/v1/admin/approvals.py with these endpoints requiring ADMIN or SUPER_ADMIN role:

GET /api/v1/admin/approvals/queue
- Returns paginated approval queue
- Documents with status reviewed or uploaded
- Scoped by organization_id
- Returns ApprovalQueueResponse

POST /api/v1/admin/approvals/approve
- Approves a document
- Calls approval_service.approve_document
- Requires DOCUMENT_APPROVE permission
- Logs to AuditLog
- Returns DocumentApprovalResponse

POST /api/v1/admin/approvals/reject
- Rejects a document
- Rejection reason required
- Calls approval_service.reject_document
- Requires DOCUMENT_REJECT permission
- Logs to AuditLog
- Returns DocumentApprovalResponse

GET /api/v1/admin/approvals/{document_id}/history
- Returns full approval history for a document
- Returns list of AuditLog entries for this document

GET /api/v1/admin/approvals/stats
- Returns KnowledgeGovernanceStats
- Scoped by organization_id

8. Create backend/app/api/v1/admin/versions.py with these endpoints requiring ADMIN or SUPER_ADMIN role:

POST /api/v1/admin/documents/{document_id}/versions
- Uploads new version of existing document
- Calls versioning_service.create_document_version
- Queues processing pipeline for new version
- Returns DocumentVersionResponse

GET /api/v1/admin/documents/{document_id}/versions
- Returns all versions of a document
- Returns DocumentVersionListResponse

POST /api/v1/admin/documents/{document_id}/versions/{version_id}/rollback
- Rolls back to a specific version
- Requires SUPER_ADMIN role
- Calls versioning_service.rollback_to_version
- Logs to AuditLog

9. Create backend/app/api/v1/admin/access_rules.py with these endpoints requiring ADMIN or SUPER_ADMIN role:

POST /api/v1/admin/documents/{document_id}/access-rules
- Creates access rule for a document
- Calls access_rule_service.create_access_rule
- Returns DocumentAccessRuleResponse

GET /api/v1/admin/documents/{document_id}/access-rules
- Returns all access rules for a document
- Returns list of DocumentAccessRuleResponse

DELETE /api/v1/admin/documents/{document_id}/access-rules/{rule_id}
- Deletes an access rule
- Logs to AuditLog

10. Update backend/app/main.py to include:
- Approvals router at /api/v1/admin/approvals
- Versions router at /api/v1/admin/documents
- Access rules router at /api/v1/admin/documents

FRONTEND SECTION

11. Create frontend/src/pages/ApprovalQueue.jsx with:
- Table of documents pending approval
- Columns: title, file type, department, uploaded by, upload date, status
- Preview document details on row click
- Approve button per document (green)
- Reject button per document (red) with rejection reason modal
- Bulk approve option for multiple documents
- Filter by department and file type
- Stats bar showing total pending, approved today, rejected today

12. Create frontend/src/pages/DocumentVersions.jsx with:
- Version history timeline for a document
- Each version shows: version number, status, uploaded by, upload date, approval status
- Current active version highlighted
- Rollback button for Super Admin only
- Upload new version button
- Version comparison summary

13. Create frontend/src/components/AccessRuleManager.jsx with:
- Current access rules list for a document
- Add access rule form with:
  Access type selector: organization-wide, department, role, specific user
  Conditional fields based on access type
- Remove access rule button per rule
- Visual display of who can access this document

14. Create frontend/src/components/ApprovalModal.jsx with:
- Document preview panel showing title, type, size, uploader, department
- Approve button with confirmation
- Reject button requiring rejection reason text input
- Rejection reason validation (minimum 20 characters)
- Success and error states

15. Update frontend/src/services/adminApi.js to add:
- getApprovalQueue: GET /api/v1/admin/approvals/queue
- approveDocument: POST /api/v1/admin/approvals/approve
- rejectDocument: POST /api/v1/admin/approvals/reject
- getApprovalHistory: GET /api/v1/admin/approvals/{id}/history
- getGovernanceStats: GET /api/v1/admin/approvals/stats
- uploadDocumentVersion: POST /api/v1/admin/documents/{id}/versions
- getDocumentVersions: GET /api/v1/admin/documents/{id}/versions
- rollbackVersion: POST /api/v1/admin/documents/{id}/versions/{versionId}/rollback
- createAccessRule: POST /api/v1/admin/documents/{id}/access-rules
- getAccessRules: GET /api/v1/admin/documents/{id}/access-rules
- deleteAccessRule: DELETE /api/v1/admin/documents/{id}/access-rules/{ruleId}

16. Update frontend/src/App.jsx to add routes:
- /admin/approvals — ApprovalQueue (protected, ADMIN role minimum)
- /admin/documents/:documentId/versions — DocumentVersions (protected, ADMIN role minimum)

17. Create backend/tests/test_approval.py with tests for:
- approve_document sets correct status and approval fields
- reject_document sets rejected status and saves rejection reason
- enforce_approval_gate returns False for unapproved document
- enforce_approval_gate returns True only for approved document
- create_document_version increments version number correctly
- get_current_version returns latest approved version
- check_user_document_access returns False for restricted document
- check_user_document_access returns True for accessible document
- AI guard service blocks unapproved document from AI answers
- AI guard service blocks archived document from AI answers
- AI guard service blocks rejected document from AI answers
- All tests run without live database connections

After completing all steps run:
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/test_approval.py backend/tests/test_document_processing.py backend/tests/test_chat.py backend/tests/test_rbac.py backend/tests/test_auth.py backend/tests/test_models.py -v --tb=short -q

Report all test results then run:
git add .
git commit -m "Phase 7 complete: Document approval workflow, knowledge governance, document versioning, access rules, AI approval gate enforcement"
git push origin main

Confirm completion of every step.
```
<img width="975" height="416" alt="image" src="https://github.com/user-attachments/assets/d1a6e1f1-0e70-420f-a84e-f9d612470b73" />
 

### Phase 8: Super Admin User Management System
1.	Build Super Admin dashboard.
2.	Allow Super Admin to create users by name, email, department, organization, and role.
3.	Build Excel upload system for bulk user onboarding.
4.	Extract names, emails, departments, and roles from uploaded Excel files.
5.	Automatically create pending user accounts from Excel uploads.
6.	Send OTP verification emails to newly created users.
7.	Send temporary login credentials securely by email.
8.	Allow Super Admin to activate, disable, delete, and update users.
9.	Allow Super Admin to reset user passwords and force password changes.
10.	Track all Super Admin actions in audit logs.

### Phase 8 Implementation
•	Paste this into Codex to begin Phase 8:
```
I am building an Enterprise AI Knowledge Base & Document Intelligence System called Ent_RAG. Phases 1 through 7 are complete. I am now starting Phase 8: Super Admin User Management System.

The system is multi-tenant. All operations must be scoped by organization_id. Only SUPER_ADMIN role can access these endpoints.

Do the following completely without asking questions:

BACKEND SECTION

1. Create backend/app/schemas/user_management.py with Pydantic schemas for:
- UserCreateRequest: first_name, last_name, email, department_id, organization_id, role_id, send_welcome_email (default True)
- UserCreateResponse: id, first_name, last_name, email, department_id, organization_id, role, is_active, is_verified, created_at
- UserUpdateRequest: first_name, last_name, department_id, role_id, is_active
- UserDetailResponse: id, first_name, last_name, email, department_id, organization_id, role, is_active, is_verified, is_first_login, must_change_password, failed_login_attempts, locked_until, last_login, password_changed_at, created_at, updated_at
- UserListResponse: users list, total_count, page, page_size
- UserFilterRequest: organization_id, department_id, role, is_active, is_verified, search_query, page, page_size
- BulkUserUploadResponse: total_rows, successfully_created, failed_rows, errors list, created_users list
- BulkUserError: row_number, email, error_reason
- PasswordResetByAdminRequest: user_id, force_change_on_login (default True)
- PasswordResetByAdminResponse: user_id, email, temporary_password_sent, force_change_on_login
- UserActivationRequest: user_id, is_active, reason
- UserActivationResponse: user_id, email, is_active, updated_at
- SuperAdminDashboardStats: total_organizations, total_users, active_users, inactive_users, unverified_users, locked_accounts, users_created_today, users_created_this_month, departments_count, recent_user_activity list

2. Create backend/app/services/user_management_service.py with:
- create_user:
  Validates email is unique within organization
  Validates department belongs to organization
  Validates role exists
  Generates temporary password using security.generate_temporary_password
  Hashes temporary password
  Creates User record with is_active=True, is_verified=False, is_first_login=True, must_change_password=True
  Saves temporary password to PasswordHistory
  Creates OTP for email verification
  Sends OTP verification email via email service
  Sends temporary credentials email via email service
  Logs to AuditLog with action USER_CREATED
  Returns created user

- update_user:
  Validates department belongs to same organization
  Validates role exists
  Updates allowed fields only
  Cannot change email or organization_id
  Logs to AuditLog with action USER_UPDATED with old and new values
  Returns updated user

- activate_user:
  Sets is_active = True
  Resets failed_login_attempts to 0
  Clears locked_until
  Logs to AuditLog with action USER_ACTIVATED
  Returns updated user

- deactivate_user:
  Sets is_active = False
  Logs to AuditLog with action USER_DEACTIVATED with reason
  Returns updated user

- delete_user:
  Soft deletes by setting is_active = False and appending _deleted_{timestamp} to email
  Anonymizes personal data
  Logs to AuditLog with action USER_DELETED
  Returns success

- reset_user_password_by_admin:
  Generates new temporary password
  Hashes and saves new password
  Saves old password to PasswordHistory
  Sets must_change_password = True if force_change_on_login is True
  Sets password_changed_at = now
  Sends temporary credentials email to user
  Logs to AuditLog with action ADMIN_PASSWORD_RESET
  Returns PasswordResetByAdminResponse

- unlock_user_account:
  Clears locked_until field
  Resets failed_login_attempts to 0
  Logs to AuditLog with action USER_ACCOUNT_UNLOCKED
  Returns updated user

- get_user_list:
  Returns paginated user list scoped by organization_id
  Supports filtering by department, role, is_active, is_verified, search by name or email
  Returns UserListResponse

- get_user_detail:
  Returns full user details
  Verifies user belongs to same organization
  Returns UserDetailResponse

- get_superadmin_dashboard_stats:
  Returns SuperAdminDashboardStats
  For SUPER_ADMIN: stats across all organizations
  For ADMIN: stats scoped to their organization

3. Create backend/app/services/bulk_user_service.py with:
- parse_excel_file:
  Reads Excel file using openpyxl
  Expects columns: first_name, last_name, email, department_name, role_name
  Validates header row exists with correct column names
  Returns list of parsed user rows and list of parsing errors

- validate_bulk_user_row:
  Validates first_name and last_name are not empty
  Validates email format is correct
  Validates email is not duplicate within the file
  Validates email is not already registered in the organization
  Validates department_name exists in the organization
  Validates role_name is valid
  Returns validation result and error message

- process_bulk_upload:
  Calls parse_excel_file
  For each valid row calls user_management_service.create_user
  Tracks successfully created users
  Tracks failed rows with row number and reason
  Sends bulk creation summary to Super Admin email
  Logs bulk upload to AuditLog with action BULK_USER_UPLOAD
  Returns BulkUserUploadResponse

- generate_bulk_upload_template:
  Creates Excel file with correct headers and example row
  Returns file as bytes for download

4. Create backend/app/api/v1/superadmin/users.py with these endpoints all requiring SUPER_ADMIN role:

GET /api/v1/superadmin/dashboard/stats
- Returns SuperAdminDashboardStats
- For SUPER_ADMIN: all organizations
- Returns stats response

GET /api/v1/superadmin/users
- Returns paginated user list
- Supports all filters from UserFilterRequest
- Returns UserListResponse

GET /api/v1/superadmin/users/{user_id}
- Returns full user details
- Returns UserDetailResponse

POST /api/v1/superadmin/users
- Creates a new user
- Calls user_management_service.create_user
- Returns UserCreateResponse

PUT /api/v1/superadmin/users/{user_id}
- Updates user details
- Calls user_management_service.update_user
- Returns UserDetailResponse

POST /api/v1/superadmin/users/{user_id}/activate
- Activates a user account
- Calls user_management_service.activate_user
- Logs to AuditLog
- Returns UserActivationResponse

POST /api/v1/superadmin/users/{user_id}/deactivate
- Deactivates a user account
- Requires reason in request body
- Calls user_management_service.deactivate_user
- Logs to AuditLog
- Returns UserActivationResponse

DELETE /api/v1/superadmin/users/{user_id}
- Soft deletes user
- Calls user_management_service.delete_user
- Logs to AuditLog
- Returns success response

POST /api/v1/superadmin/users/{user_id}/reset-password
- Resets user password
- Calls user_management_service.reset_user_password_by_admin
- Logs to AuditLog
- Returns PasswordResetByAdminResponse

POST /api/v1/superadmin/users/{user_id}/unlock
- Unlocks locked user account
- Calls user_management_service.unlock_user_account
- Logs to AuditLog
- Returns success response

POST /api/v1/superadmin/users/bulk-upload
- Accepts Excel file upload
- Calls bulk_user_service.process_bulk_upload
- Returns BulkUserUploadResponse

GET /api/v1/superadmin/users/bulk-upload/template
- Returns Excel template file for download
- Calls bulk_user_service.generate_bulk_upload_template

5. Create backend/app/api/v1/superadmin/__init__.py as empty init file

6. Update backend/app/main.py to include:
- Superadmin router at /api/v1/superadmin

FRONTEND SECTION

7. Create frontend/src/pages/SuperAdminDashboard.jsx with:
- Professional super admin dashboard layout using Tailwind CSS
- Stats cards: total organizations, total users, active users, inactive users, unverified users, locked accounts
- Users created today and this month counters
- Recent user activity feed
- Quick action buttons: Create User, Bulk Upload Users, View All Users, View Organizations
- System governance summary panel
- Navigation to: Users, Organizations, Roles, Monitoring, Audit Logs

8. Create frontend/src/pages/UserManagement.jsx with:
- Full user management table with columns: name, email, department, role, status, verified, last login, actions
- Filter bar: filter by organization, department, role, active status, verified status
- Search bar for name or email search
- Create User button opening create user modal
- Bulk Upload button opening bulk upload modal
- Actions per user: View Details, Edit, Activate/Deactivate, Reset Password, Unlock, Delete
- Status badges: active=green, inactive=gray, locked=red, unverified=yellow
- Pagination controls

9. Create frontend/src/components/CreateUserModal.jsx with:
- Form fields: first name, last name, email, organization selector, department selector, role selector
- Department options load based on selected organization
- Send welcome email toggle (default on)
- Form validation with clear error messages
- Success state showing user created and email sent confirmation

10. Create frontend/src/components/BulkUploadModal.jsx with:
- Download template button
- Drag and drop Excel file upload area
- File validation: only .xlsx and .xls accepted
- Upload progress indicator
- Results display showing:
  Total rows processed
  Successfully created users count
  Failed rows count
  Error details table with row number, email, error reason
- Retry failed rows option

11. Create frontend/src/components/UserDetailPanel.jsx with:
- Full user profile display
- Account status indicators: active, verified, locked, must change password
- Login history summary: last login, failed attempts
- Password status: days since last change, expiry warning
- Action buttons: Edit, Activate/Deactivate, Reset Password, Unlock, Delete
- Audit log section showing recent actions for this user

12. Create frontend/src/services/superAdminApi.js with:
- getDashboardStats: GET /api/v1/superadmin/dashboard/stats
- getUsers: GET /api/v1/superadmin/users with filter params
- getUser: GET /api/v1/superadmin/users/{id}
- createUser: POST /api/v1/superadmin/users
- updateUser: PUT /api/v1/superadmin/users/{id}
- activateUser: POST /api/v1/superadmin/users/{id}/activate
- deactivateUser: POST /api/v1/superadmin/users/{id}/deactivate
- deleteUser: DELETE /api/v1/superadmin/users/{id}
- resetUserPassword: POST /api/v1/superadmin/users/{id}/reset-password
- unlockUser: POST /api/v1/superadmin/users/{id}/unlock
- bulkUploadUsers: POST /api/v1/superadmin/users/bulk-upload
- downloadBulkTemplate: GET /api/v1/superadmin/users/bulk-upload/template
- All functions include Authorization Bearer token header
- All functions handle errors and return structured responses

13. Update frontend/src/App.jsx to add routes:
- /superadmin/dashboard — SuperAdminDashboard (protected, SUPER_ADMIN role only)
- /superadmin/users — UserManagement (protected, SUPER_ADMIN role only)

14. Create backend/tests/test_user_management.py with tests for:
- create_user generates temporary password correctly
- create_user sets is_first_login True and must_change_password True
- create_user sets is_verified False on creation
- update_user cannot change email or organization_id
- activate_user sets is_active True and clears lockout
- deactivate_user sets is_active False
- reset_user_password_by_admin generates new temporary password
- reset_user_password_by_admin sets must_change_password True
- bulk_user_service parse_excel_file returns correct rows from valid Excel
- bulk_user_service validate_bulk_user_row rejects invalid email format
- bulk_user_service validate_bulk_user_row rejects duplicate emails
- All tests run without live database connections

After completing all steps run:
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/test_user_management.py backend/tests/test_approval.py backend/tests/test_document_processing.py backend/tests/test_chat.py backend/tests/test_rbac.py backend/tests/test_auth.py backend/tests/test_models.py -v --tb=short -q

Report all test results then run:
git add .
git commit -m "Phase 8 complete: Super Admin dashboard, user management, bulk Excel upload, password reset, account activation, audit logging"
git push origin main

Confirm completion of every step.
``` 
<img width="975" height="467" alt="image" src="https://github.com/user-attachments/assets/2f0a0dc9-9c7e-4bf9-ba97-6fe6be25fae8" />

### Phase 9: RAG Pipeline & AI Knowledge Engine
1.	Generate embeddings using Sentence Transformers.
2.	Store vector embeddings in Qdrant.
3.	Build semantic similarity search pipeline.
4.	Filter retrieved documents based on user permissions before AI response generation.
5.	Connect retrieved document chunks to Cerebras LLM.
6.	Generate grounded AI responses only from approved company documents.
7.	Return source references alongside every AI answer.
8.	Store AI queries, responses, retrieval results, and usage logs.
9.	Add fallback response when no reliable document source is found.
10.	Calculate retrieval confidence score for every response.
11.	Calculate AI response confidence score before returning answers.
12.	Calculate hallucination risk score for weak or unsupported answers.
13.	Reject low-confidence responses before displaying them to users.
14.	Prevent AI from responding when source relevance is below the allowed threshold.
15.	Store confidence scores, hallucination scores, and source reliability metrics in PostgreSQL.
16.	Flag repeated low-confidence responses for admin review.
17.	Generate AI quality analytics for monitoring dashboard reporting.
18.	Test answer quality, retrieval accuracy, source grounding, hallucination control, and permission filtering.
19.	Use a hybrid chunking strategy combining semantic chunking and hierarchical chunking, instead of only fixed-size chunking, to improve retrieval accuracy for policies, reports, manuals, and long enterprise documents.
20.	Test chunking quality against real company questions to measure answer accuracy, source relevance, and hallucination reduction.

### Phase 9 Implementation
•	Paste this into Codex to begin Phase 9:
```
I am building an Enterprise AI Knowledge Base & Document Intelligence System called Ent_RAG. Phases 1 through 8 are complete. I am now starting Phase 9: RAG Pipeline & AI Knowledge Engine.

The system is multi-tenant. All vector searches must be filtered by organization_id. Only approved documents can be used by the AI.

Do the following completely without asking questions:

BACKEND SECTION

1. Create backend/app/services/vector_search_service.py with:
- initialize_qdrant_client: creates Qdrant client using QDRANT_HOST and QDRANT_PORT from settings
- search_similar_chunks:
  Accepts query_text, organization_id, user_id, top_k (default 5)
  Generates query embedding using embedding_service
  Searches Qdrant collection ent_rag_{organization_id}
  Filters by organization_id in payload for tenant isolation
  Filters by approved document IDs only using access_rule_service.get_user_accessible_document_ids
  Returns list of ScoredChunk objects with chunk_text, document_id, relevance_score, chunk_index
- search_with_permission_filter:
  Calls search_similar_chunks
  Applies additional department and role filters
  Removes chunks from documents user cannot access
  Returns filtered list of ScoredChunk objects
- rerank_chunks:
  Reranks retrieved chunks by relevance score
  Removes duplicate chunks from same document section
  Returns top_k reranked chunks
- format_context_for_llm:
  Formats retrieved chunks into clean context string for LLM prompt
  Includes document title and section reference for each chunk
  Returns formatted context string and source list

2. Create backend/app/services/rag_service.py with:
- build_rag_prompt:
  Accepts user_question and context_chunks list
  Builds system prompt instructing LLM to:
    Answer only from provided context
    Never guess or use outside knowledge
    Always cite source documents
    Say I cannot find this information if no relevant context found
    Be concise and professional
  Builds user prompt combining question and formatted context
  Returns system_prompt and user_prompt

- call_cerebras_llm:
  Calls Cerebras API using CEREBRAS_API_KEY from settings
  Model: llama3.1-8b
  Sends system_prompt and user_prompt
  Sets temperature to 0.1 for factual responses
  Sets max_tokens to 1024
  Handles API errors gracefully
  Returns raw LLM response text and token usage

- extract_answer_and_sources:
  Parses LLM response to extract clean answer text
  Extracts cited source references if present
  Returns answer_text and cited_sources list

- calculate_retrieval_confidence:
  Calculates confidence score from 0.0 to 1.0 based on:
    Average relevance score of retrieved chunks
    Number of chunks retrieved vs requested
    Chunk score distribution
  Returns float confidence score

- calculate_response_confidence:
  Calculates response confidence from 0.0 to 1.0 based on:
    Retrieval confidence score
    Number of source documents cited
    Answer length relative to context length
    Presence of uncertainty phrases in answer
  Returns float confidence score

- calculate_hallucination_risk:
  Calculates hallucination risk from 0.0 to 1.0 based on:
    Low retrieval confidence increases risk
    Answer contains claims not supported by retrieved chunks
    Answer significantly longer than context suggests
    Presence of specific numbers or dates not in context
  Higher score means higher hallucination risk
  Returns float risk score

- should_reject_response:
  Returns True if response_confidence below 0.5
  Returns True if hallucination_risk above 0.7
  Returns True if retrieval_confidence below 0.4
  Returns False if all scores acceptable

- generate_rag_response:
  Main orchestration function for full RAG pipeline:
  Step 1: Call vector_search_service.search_with_permission_filter
  Step 2: Call ai_guard_service.filter_eligible_documents on results
  Step 3: If no eligible chunks call enforce_no_source_no_answer and return fallback
  Step 4: Call rerank_chunks
  Step 5: Call format_context_for_llm
  Step 6: Call build_rag_prompt
  Step 7: Call call_cerebras_llm
  Step 8: Call extract_answer_and_sources
  Step 9: Call calculate_retrieval_confidence
  Step 10: Call calculate_response_confidence
  Step 11: Call calculate_hallucination_risk
  Step 12: Call should_reject_response
  Step 13: If rejected return fallback response with rejection flag True
  Step 14: Save full RAG result to database via rag_logging_service
  Step 15: Return RAGResponse object

3. Create backend/app/schemas/rag.py with Pydantic schemas for:
- RAGResponse: answer, source_documents list, retrieval_confidence, response_confidence, hallucination_risk, response_rejected, fallback_message, token_usage, processing_time_ms
- RAGSourceDocument: document_id, document_title, chunk_text, relevance_score, chunk_index, page_number
- ScoredChunk: chunk_id, document_id, document_title, chunk_text, relevance_score, chunk_index
- RAGQualityMetrics: retrieval_confidence, response_confidence, hallucination_risk, chunks_retrieved, chunks_used, token_usage, processing_time_ms
- LowConfidenceFlag: document_id, question, confidence_score, hallucination_risk, flagged_at, reviewed

4. Create backend/app/services/rag_logging_service.py with:
- save_rag_result:
  Saves complete RAG query result to Message table
  Saves source_documents as JSON
  Saves confidence_score, retrieval_score, hallucination_risk_score
  Saves response_rejected flag
  Saves token_usage to MonitoringLog
  Returns saved message id

- save_usage_metrics:
  Logs to MonitoringLog with:
    user_id, organization_id
    token_usage
    response_time_ms
    retrieval_confidence
    hallucination_risk
    response_rejected flag

- flag_low_confidence_response:
  If response_confidence below 0.5 or hallucination_risk above 0.7
  Creates SystemAlert with severity HIGH
  Alert title: Low confidence AI response detected
  Includes question, scores, document sources
  Groups repeated flags from same document into one incident
  Logs to IncidentReport if same document flagged 3 or more times

- get_ai_quality_analytics:
  Returns analytics for monitoring dashboard:
    Average confidence score over time period
    Average hallucination risk over time period
    Total responses rejected
    Total responses with valid sources
    Most problematic documents by low confidence frequency
    Response quality trend over last 30 days
  Scoped by organization_id

- get_low_confidence_flags:
  Returns list of flagged low confidence responses
  Scoped by organization_id
  Supports pagination

5. Update backend/app/api/v1/chat.py:
- Update POST /api/v1/chat/ask to:
  Replace placeholder AI response with real call to rag_service.generate_rag_response
  Pass user question, user_id, organization_id, department_id to RAG service
  Use RAGResponse to populate MessageResponse
  Return full AskQuestionResponse with all scores and sources

6. Create backend/app/api/v1/rag_analytics.py with endpoints requiring ADMIN or SUPER_ADMIN:

GET /api/v1/rag/analytics
- Returns AI quality analytics from rag_logging_service.get_ai_quality_analytics
- Supports date range filter
- Scoped by organization_id

GET /api/v1/rag/low-confidence-flags
- Returns flagged low confidence responses
- Supports pagination
- Returns list of LowConfidenceFlag

POST /api/v1/rag/low-confidence-flags/{flag_id}/review
- Marks a flag as reviewed
- Logs to AuditLog
- Returns updated flag

7. Update backend/app/main.py to include:
- RAG analytics router at /api/v1/rag

8. Create backend/app/core/rag_config.py with:
- RAG configuration constants:
  MIN_RETRIEVAL_CONFIDENCE = 0.4
  MIN_RESPONSE_CONFIDENCE = 0.5
  MAX_HALLUCINATION_RISK = 0.7
  TOP_K_CHUNKS = 5
  CHUNK_OVERLAP_TOKENS = 50
  MAX_CONTEXT_TOKENS = 3000
  LLM_TEMPERATURE = 0.1
  LLM_MAX_TOKENS = 1024
  CEREBRAS_MODEL = llama3.1-8b
  FALLBACK_MESSAGE = I could not find reliable information in the approved company documents to answer your question. Please contact your administrator or check if the relevant documents have been uploaded and approved.
  LOW_CONFIDENCE_FLAG_THRESHOLD = 3

9. Create backend/tests/test_rag_pipeline.py with tests for:
- build_rag_prompt returns non-empty system and user prompts
- build_rag_prompt includes no outside knowledge instruction
- calculate_retrieval_confidence returns 0.0 for empty chunks list
- calculate_retrieval_confidence returns value between 0.0 and 1.0 for valid chunks
- calculate_hallucination_risk returns higher risk for empty context
- should_reject_response returns True for confidence 0.3 and risk 0.8
- should_reject_response returns False for confidence 0.8 and risk 0.2
- should_reject_response returns True when only confidence is low
- should_reject_response returns True when only hallucination risk is high
- format_context_for_llm returns formatted string with document references
- enforce_no_source_no_answer blocks response when chunks list is empty
- get_fallback_message returns the configured fallback message string
- flag_low_confidence_response creates SystemAlert for low confidence score
- All tests run without live Qdrant, Cerebras, or database connections

After completing all steps run:
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/test_rag_pipeline.py backend/tests/test_user_management.py backend/tests/test_approval.py backend/tests/test_document_processing.py backend/tests/test_chat.py backend/tests/test_rbac.py backend/tests/test_auth.py backend/tests/test_models.py -v --tb=short -q

Report all test results then run:
git add .
git commit -m "Phase 9 complete: Full RAG pipeline, Cerebras LLM integration, semantic vector search, confidence scoring, hallucination detection, permission-filtered retrieval, AI quality analytics"
git push origin main

Confirm completion of every step.
```
<img width="975" height="483" alt="image" src="https://github.com/user-attachments/assets/61691cbc-1364-4311-b811-f7a6a05488a1" />

### Phase 10: AI Operations Monitoring & System Intelligence
1.	Build AI-powered monitoring dashboard inside the application.
2.	Track active users, logins, failed logins, document uploads, AI queries, API calls, failed requests, and system errors.
3.	Monitor API-specific logs for this application, not the entire VPS.
4.	Track backend response time, failed AI calls, token usage, request volume, and database performance.
5.	Store monitoring logs in PostgreSQL.
6.	Generate AI summaries of system health and usage trends.
7.	Build intelligent alerts for suspicious activity, high traffic, API errors, failed document ingestion, and system risk.
8.	Add system risk analysis to detect slow response time, high load, and possible instability.
9.	Provide AI-recommended actions for Admins and Super Admins.
10.	Display AI response confidence score analytics.
11.	Display hallucination risk analytics.
12.	Display low-confidence response trends.
13.	Display document retrieval accuracy metrics.
14.	Display number of responses with valid sources.
15.	Display number of rejected low-confidence AI responses.
16.	Display reported hallucinations from users.
17.	Display most problematic documents causing weak AI responses.
18.	Generate AI trust and reliability reports for administrators.
19.	Build an AI debugging assistant inside the Super Admin monitoring dashboard.
20.	Detect application errors, failed API calls, failed document ingestion, database errors, authentication issues, and AI service failures.
21.	Convert technical error logs into simple English explanations for the Super Admin.
22.	Show the possible cause of each problem.
23.	Show the affected service, endpoint, user action, and time of occurrence.
24.	Show the likely business impact of the issue.
25.	Recommend practical next steps to resolve the issue.
26.	Classify issues by severity: Low, Medium, High, and Critical.
27.	Group repeated errors into one incident to avoid dashboard noise.
28.	Track whether each issue is open, investigating, resolved, or ignored.
29.	Store debugging history and incident reports in PostgreSQL.
30.	Generate AI-powered incident summaries for Admins and Super Admins.

### Phase 10 Implementation
•	Paste this into Codex to begin Phase 10:
```
I am building an Enterprise AI Knowledge Base & Document Intelligence System called Ent_RAG. Phases 1 through 9 are complete. I am now starting Phase 10: AI Operations Monitoring & System Intelligence.

The system is multi-tenant. All monitoring data must be scoped by organization_id. The monitoring dashboard uses the Cerebras LLM to generate AI summaries and debugging explanations.

Do the following completely without asking questions:

BACKEND SECTION

1. Create backend/app/services/monitoring_service.py with:
- track_api_request:
  Called on every API request via middleware
  Logs to MonitoringLog: endpoint, method, status_code, response_time_ms, user_id, organization_id, ip_address
  Does not log health check or docs endpoints
  
- track_ai_query:
  Logs AI query event to MonitoringLog
  Records token_usage, response_time_ms, confidence_score, hallucination_risk, response_rejected
  
- track_document_event:
  Logs document upload, processing start, processing complete, processing failed events
  Records document_id, file_name, event_type, error_message if failed

- track_auth_event:
  Logs login, failed login, logout, account locked, OTP verified events
  Records user_id, organization_id, ip_address, event_type

- get_active_users:
  Returns count of users with activity in last 15 minutes
  Scoped by organization_id

- get_system_metrics:
  Returns for a time period:
    Total API calls
    Failed API calls count and percentage
    Average response time ms
    Total AI queries
    Failed AI calls
    Total token usage
    Total document uploads
    Failed document ingestion count
    Total login events
    Failed login events
    Active user count
  Scoped by organization_id

- get_response_time_trend:
  Returns average response time grouped by hour for last 24 hours
  Scoped by organization_id

- get_error_trend:
  Returns error count grouped by hour for last 24 hours
  Scoped by organization_id

- get_ai_quality_trend:
  Returns average confidence score and hallucination risk grouped by day for last 30 days
  Scoped by organization_id

- get_top_endpoints:
  Returns top 10 most called endpoints with call count and average response time
  Scoped by organization_id

- get_database_performance_metrics:
  Returns slow query count (over 1000ms)
  Returns average query time
  Reads from MonitoringLog table

2. Create backend/app/services/alert_service.py with:
- check_and_create_alerts:
  Runs alert rules against current metrics
  Creates SystemAlert records for triggered rules
  Groups repeated alerts into existing open incidents
  Called periodically by Celery beat scheduler

- alert_rules:
  Rule 1: High error rate — if failed API calls exceed 10 percent in last 5 minutes create HIGH alert
  Rule 2: Slow response time — if average response time exceeds 3000ms create MEDIUM alert
  Rule 3: High failed logins — if failed logins exceed 20 in 10 minutes create HIGH alert (possible brute force)
  Rule 4: Failed document ingestion — if 3 or more documents fail in 1 hour create MEDIUM alert
  Rule 5: AI service failure — if Cerebras API calls fail 5 or more times in 10 minutes create CRITICAL alert
  Rule 6: High hallucination risk trend — if average hallucination risk exceeds 0.6 in last hour create HIGH alert
  Rule 7: No active users anomaly — if active users drop to 0 during business hours create LOW alert
  Rule 8: Database slow queries — if slow queries exceed 50 in 1 hour create MEDIUM alert

- create_alert:
  Creates SystemAlert record
  Sets severity, title, description, affected_service, recommended_action, business_impact
  Checks if similar open alert already exists before creating duplicate
  Returns created alert

- group_into_incident:
  If same error type occurs 3 or more times
  Creates or updates IncidentReport
  Links SystemAlert to IncidentReport
  Updates error_count, last_occurrence
  Returns incident

- get_active_alerts:
  Returns all open and investigating alerts
  Scoped by organization_id
  Ordered by severity then created_at

- update_alert_status:
  Updates alert status to investigating, resolved, or ignored
  Logs to AuditLog
  Returns updated alert

3. Create backend/app/services/ai_monitoring_service.py with:
- generate_system_health_summary:
  Collects current system metrics from monitoring_service
  Calls Cerebras LLM with metrics data
  Prompt instructs LLM to:
    Summarize system health in 3 to 5 plain English sentences
    Highlight any concerning trends
    Note what is working well
    Be factual and concise
  Returns AI-generated summary text

- generate_usage_trend_summary:
  Collects usage trend data for last 7 days
  Calls Cerebras LLM
  Returns plain English summary of usage patterns and trends

- generate_ai_trust_report:
  Collects AI quality metrics: confidence scores, hallucination rates, rejection rates
  Calls Cerebras LLM
  Returns formatted trust and reliability report for administrators

- analyze_system_risk:
  Collects all active alerts and recent metrics
  Calls Cerebras LLM
  Returns risk analysis with:
    Overall risk level: low, medium, high, critical
    Top 3 risk factors
    Recommended immediate actions
    Predicted impact if not addressed

4. Create backend/app/services/debugging_service.py with:
- analyze_error_log:
  Accepts raw error log entry from MonitoringLog or SystemAlert
  Calls Cerebras LLM with error details
  Prompt instructs LLM to respond in JSON with:
    plain_english_explanation: what happened in simple terms
    possible_cause: most likely reason for the error
    affected_service: which service or component is affected
    affected_endpoint: which API endpoint if applicable
    business_impact: what this means for users and the business
    recommended_steps: list of 3 to 5 practical next steps
    severity: low, medium, high, or critical
  Parses LLM JSON response
  Returns DebuggingAnalysis object

- process_new_errors:
  Fetches unanalyzed errors from MonitoringLog
  Calls analyze_error_log for each
  Saves analysis to SystemAlert with debugging details
  Groups repeated errors into incidents
  Marks errors as analyzed

- get_debugging_history:
  Returns list of analyzed errors with explanations
  Scoped by organization_id
  Supports filtering by severity and status
  Supports pagination

- generate_incident_summary:
  Accepts IncidentReport id
  Collects all related SystemAlerts
  Calls Cerebras LLM
  Returns AI-powered incident summary with timeline, impact, and resolution steps

5. Create backend/app/schemas/monitoring.py with Pydantic schemas for:
- SystemMetricsResponse: all metrics fields from get_system_metrics
- AlertResponse: id, alert_type, severity, title, description, affected_service, status, recommended_action, business_impact, created_at, updated_at
- AlertUpdateRequest: status, resolution_notes
- IncidentResponse: id, title, description, severity, status, affected_services, error_count, first_occurrence, last_occurrence, root_cause, resolution_steps, business_impact
- DebuggingAnalysis: plain_english_explanation, possible_cause, affected_service, affected_endpoint, business_impact, recommended_steps, severity
- SystemHealthSummary: summary_text, risk_level, generated_at
- AITrustReport: avg_confidence_score, avg_hallucination_risk, total_responses, rejected_responses, rejection_rate_percent, problematic_documents list, trust_level, report_text, generated_at
- MonitoringDashboardData: system_metrics, active_alerts, health_summary, ai_quality_trend, response_time_trend, error_trend, top_endpoints
- ErrorTrendPoint: timestamp, error_count, endpoint
- ResponseTimeTrendPoint: timestamp, avg_response_time_ms
- AIQualityTrendPoint: date, avg_confidence, avg_hallucination_risk, rejection_count

6. Create backend/app/api/v1/monitoring.py with endpoints:

GET /api/v1/monitoring/dashboard
- Requires ADMIN or SUPER_ADMIN
- Returns MonitoringDashboardData with all metrics, alerts, trends
- Scoped by organization_id for ADMIN
- All organizations for SUPER_ADMIN

GET /api/v1/monitoring/metrics
- Returns SystemMetricsResponse
- Supports time_period filter: 1h, 6h, 24h, 7d, 30d

GET /api/v1/monitoring/alerts
- Returns list of active alerts
- Supports severity filter
- Returns list of AlertResponse

GET /api/v1/monitoring/alerts/{alert_id}
- Returns single alert details with debugging analysis
- Returns AlertResponse with DebuggingAnalysis

PUT /api/v1/monitoring/alerts/{alert_id}/status
- Updates alert status
- Requires ADMIN or SUPER_ADMIN
- Logs to AuditLog

GET /api/v1/monitoring/incidents
- Returns list of incident reports
- Supports status filter
- Returns list of IncidentResponse

GET /api/v1/monitoring/incidents/{incident_id}
- Returns incident details with AI summary
- Calls debugging_service.generate_incident_summary
- Returns IncidentResponse with summary

GET /api/v1/monitoring/health-summary
- Returns AI-generated system health summary
- Calls ai_monitoring_service.generate_system_health_summary
- Returns SystemHealthSummary

GET /api/v1/monitoring/risk-analysis
- Returns AI risk analysis
- Calls ai_monitoring_service.analyze_system_risk
- Returns risk analysis response

GET /api/v1/monitoring/ai-trust-report
- Returns AI trust and reliability report
- Calls ai_monitoring_service.generate_ai_trust_report
- Returns AITrustReport

GET /api/v1/monitoring/debugging/history
- Returns debugging analysis history
- Requires SUPER_ADMIN
- Returns list of DebuggingAnalysis with alert context

GET /api/v1/monitoring/ai-quality
- Returns AI quality analytics
- Calls rag_logging_service.get_ai_quality_analytics
- Supports date range filter

7. Create backend/app/middleware/monitoring_middleware.py with:
- MonitoringMiddleware class that:
  Runs on every request after RBACMiddleware
  Records request start time
  On response: calculates response_time_ms
  Calls monitoring_service.track_api_request
  Does not monitor health check, docs, or static file endpoints
  Handles errors gracefully so monitoring never breaks the application

8. Create backend/app/workers/monitoring_tasks.py with Celery beat scheduled tasks:
- run_alert_checks_task:
  Runs every 5 minutes
  Calls alert_service.check_and_create_alerts
  
- process_error_analysis_task:
  Runs every 10 minutes
  Calls debugging_service.process_new_errors
  Analyzes unprocessed error logs

- cleanup_old_monitoring_logs_task:
  Runs daily at 2am
  Deletes MonitoringLog entries older than 90 days
  Keeps SystemAlert and IncidentReport indefinitely

9. Update worker/celery_config.py to:
- Add Celery beat schedule for monitoring tasks
- run_alert_checks_task every 5 minutes
- process_error_analysis_task every 10 minutes
- cleanup_old_monitoring_logs_task daily at 2am

10. Update backend/app/main.py to:
- Include monitoring router at /api/v1/monitoring
- Register MonitoringMiddleware after RBACMiddleware

FRONTEND SECTION

11. Create frontend/src/pages/MonitoringDashboard.jsx with:
- Professional monitoring dashboard layout using Tailwind CSS
- System health banner with AI-generated summary and overall risk level
- Color coded risk: green=low, yellow=medium, orange=high, red=critical
- Stats row: active users, total API calls, error rate percent, avg response time, total AI queries
- Response time trend line chart using recharts
- Error rate trend line chart using recharts
- AI quality metrics: avg confidence score, avg hallucination risk, rejection rate
- Active alerts panel with severity badges
- Top endpoints table with call counts and response times
- Refresh button and last updated timestamp

12. Create frontend/src/pages/AlertsPanel.jsx with:
- Full alerts list with filtering by severity and status
- Each alert shows: title, severity badge, affected service, created time, status
- Click alert to see full details including AI debugging explanation
- Status update buttons: Mark Investigating, Mark Resolved, Ignore
- Incidents section showing grouped error incidents
- Alert severity badges: critical=red, high=orange, medium=yellow, low=blue

13. Create frontend/src/pages/DebuggingAssistant.jsx with:
- Super Admin only page
- Recent errors list with plain English explanations
- Each error card shows:
  What happened in simple English
  Possible cause
  Affected service and endpoint
  Business impact
  Recommended next steps as numbered list
  Severity badge
  Time of occurrence
- Incident reports section with AI summaries
- Filter by severity and time range
- Export report button

14. Create frontend/src/pages/AITrustReport.jsx with:
- AI trust and reliability report page
- Confidence score trend chart
- Hallucination risk trend chart
- Rejection rate over time chart
- Most problematic documents table
- Overall trust level indicator
- Reported hallucinations from users list
- Low confidence response trends
- AI-generated trust report text section

15. Create frontend/src/services/monitoringApi.js with:
- getDashboard: GET /api/v1/monitoring/dashboard
- getMetrics: GET /api/v1/monitoring/metrics
- getAlerts: GET /api/v1/monitoring/alerts
- getAlert: GET /api/v1/monitoring/alerts/{id}
- updateAlertStatus: PUT /api/v1/monitoring/alerts/{id}/status
- getIncidents: GET /api/v1/monitoring/incidents
- getIncident: GET /api/v1/monitoring/incidents/{id}
- getHealthSummary: GET /api/v1/monitoring/health-summary
- getRiskAnalysis: GET /api/v1/monitoring/risk-analysis
- getAITrustReport: GET /api/v1/monitoring/ai-trust-report
- getDebuggingHistory: GET /api/v1/monitoring/debugging/history
- getAIQuality: GET /api/v1/monitoring/ai-quality
- All functions include Authorization Bearer token header

16. Update frontend/src/App.jsx to add routes:
- /monitoring — MonitoringDashboard (protected, ADMIN minimum)
- /monitoring/alerts — AlertsPanel (protected, ADMIN minimum)
- /monitoring/debugging — DebuggingAssistant (protected, SUPER_ADMIN only)
- /monitoring/ai-trust — AITrustReport (protected, ADMIN minimum)

17. Create backend/tests/test_monitoring.py with tests for:
- monitoring_service.get_system_metrics returns correct structure
- alert_service alert rules trigger correctly for high error rate
- alert_service does not create duplicate alerts for same open issue
- alert_service groups repeated errors into incidents after 3 occurrences
- debugging_service analyze_error_log returns DebuggingAnalysis with all required fields
- ai_monitoring_service generate_system_health_summary returns non-empty string
- MonitoringMiddleware records response time correctly
- cleanup task identifies logs older than 90 days
- All tests run without live database or Cerebras API connections

After completing all steps run:
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/test_monitoring.py backend/tests/test_rag_pipeline.py backend/tests/test_user_management.py backend/tests/test_approval.py backend/tests/test_document_processing.py backend/tests/test_chat.py backend/tests/test_rbac.py backend/tests/test_auth.py backend/tests/test_models.py -v --tb=short -q

Report all test results then run:
git add .
git commit -m "Phase 10 complete: AI monitoring dashboard, intelligent alerts, system risk analysis, AI debugging assistant, incident management, AI trust reports, Celery beat scheduled tasks"
git push origin main

Confirm completion of every step.
``` 
<img width="975" height="423" alt="image" src="https://github.com/user-attachments/assets/73d4868f-4f86-400d-9868-218d23c3c382" />

### Phase 11: Audit Logs, Compliance & Data Protection
1.	Track every major user, admin, and super admin action.
2.	Log user creation, role changes, document uploads, document approval, document deletion, login events, password resets, and AI queries.
3.	Protect audit logs from editing or deletion by normal users.
4.	Add data privacy rules for user chat history and company documents.
5.	Encrypt sensitive system data.
6.	Secure environment variables and API keys.
7.	Configure secure database access policies.
8.	Add retention rules for logs, chats, uploaded documents, and AI usage records.
9.	Prepare compliance-ready reports for system activity and access history.


### Phase 11 Implementation
•	Paste this into Codex to begin Phase 11:
```
I am building an Enterprise AI Knowledge Base & Document Intelligence System called Ent_RAG. Phases 1 through 10 are complete. I am now starting Phase 11: Audit Logs, Compliance & Data Protection.

The system is multi-tenant. All compliance data must be scoped by organization_id.

Do the following completely without asking questions:

BACKEND SECTION

1. Create backend/app/services/audit_service.py with:
- log_action:
  Central function called by all services to write audit entries
  Accepts: user_id, organization_id, action, resource_type, resource_id, old_value, new_value, ip_address, user_agent, status
  Saves to AuditLog table
  Never raises exceptions so audit logging never breaks application flow
  Runs as fire-and-forget to avoid slowing down main operations

- get_audit_logs:
  Returns paginated audit logs
  Supports filtering by: user_id, action, resource_type, date_from, date_to
  SUPER_ADMIN: can query all organizations
  ADMIN: scoped to their organization only
  USER: cannot access audit logs at all
  Returns AuditLogListResponse

- get_audit_log_detail:
  Returns single audit log entry with full old_value and new_value
  Requires ADMIN or SUPER_ADMIN

- export_audit_logs:
  Exports audit logs to CSV format for compliance reporting
  Supports same filters as get_audit_logs
  Returns CSV file bytes

- verify_audit_log_integrity:
  Checks audit log records have not been tampered with
  Uses hash chain verification
  Reports any integrity violations

- get_user_activity_report:
  Returns complete activity history for a specific user
  Includes all actions taken, resources accessed, login history
  Used for compliance and user behavior analysis

2. Update ALL existing services to use audit_service.log_action consistently:
Verify and add missing audit log calls in:

backend/app/services/auth_service.py — ensure these are logged:
  LOGIN_SUCCESS, LOGIN_FAILED, LOGIN_BLOCKED_UNVERIFIED
  LOGOUT, OTP_VERIFIED, OTP_RESENT
  PASSWORD_CHANGED, PASSWORD_RESET_REQUESTED, PASSWORD_RESET_COMPLETED
  ACCOUNT_LOCKED, ACCOUNT_UNLOCKED

backend/app/services/user_management_service.py — ensure these are logged:
  USER_CREATED, USER_UPDATED, USER_ACTIVATED, USER_DEACTIVATED
  USER_DELETED, ADMIN_PASSWORD_RESET, BULK_USER_UPLOAD
  ROLE_ASSIGNED, DEPARTMENT_CHANGED

backend/app/services/approval_service.py — ensure these are logged:
  DOCUMENT_APPROVED, DOCUMENT_REJECTED, DOCUMENT_ARCHIVED

backend/app/workers/document_tasks.py — ensure these are logged:
  DOCUMENT_UPLOADED, DOCUMENT_PROCESSING_STARTED
  DOCUMENT_PROCESSING_COMPLETED, DOCUMENT_PROCESSING_FAILED
  DOCUMENT_DELETED, DOCUMENT_REPROCESSED, DOCUMENT_VERSION_CREATED

backend/app/services/versioning_service.py — ensure these are logged:
  DOCUMENT_VERSION_CREATED, DOCUMENT_VERSION_ROLLBACK

backend/app/services/access_rule_service.py — ensure these are logged:
  DOCUMENT_ACCESS_RULE_CREATED, DOCUMENT_ACCESS_RULE_DELETED

backend/app/services/chat_service.py — ensure these are logged:
  AI_QUERY_MADE, CHAT_SESSION_CREATED, CHAT_SESSION_DELETED
  FEEDBACK_SUBMITTED, HALLUCINATION_REPORTED

backend/app/services/rbac_service.py — ensure these are logged:
  PERMISSION_DENIED, ROLE_BYPASS_ATTEMPTED, ISOLATION_VIOLATION

3. Create backend/app/services/data_privacy_service.py with:
- anonymize_user_data:
  Called when user is deleted
  Replaces personal data with anonymized values
  Keeps audit log entries but replaces name and email with ANONYMIZED_USER_{id}
  Preserves organizational data and system logs
  Logs GDPR_ANONYMIZATION action to AuditLog

- apply_chat_retention_policy:
  Deletes chat sessions and messages older than retention_days setting
  Default retention: 365 days for chat history
  Logs retention cleanup to AuditLog

- apply_document_retention_policy:
  Archives documents older than retention_days setting
  Does not delete, only archives unless explicitly configured
  Logs retention action to AuditLog

- apply_monitoring_log_retention:
  Deletes MonitoringLog entries older than 90 days
  Keeps SystemAlert and IncidentReport indefinitely
  Logs cleanup to AuditLog

- get_user_data_export:
  Exports all data belonging to a user for GDPR right to access
  Includes: profile, chat history, AI queries, audit log entries
  Returns structured JSON export

- mask_sensitive_field:
  Masks email addresses for display: j***@example.com
  Masks phone numbers: ***-***-1234
  Used in audit log displays for privacy

4. Create backend/app/core/encryption.py with:
- encrypt_field:
  Encrypts sensitive string data using Fernet symmetric encryption
  Uses ENCRYPTION_KEY from settings
  Returns encrypted string safe for database storage

- decrypt_field:
  Decrypts encrypted field value
  Returns original string
  Handles decryption errors gracefully

- encrypt_dict:
  Encrypts specified fields in a dictionary
  Returns dict with encrypted values

- hash_sensitive_data:
  One-way hash for data that needs verification but not retrieval
  Uses SHA256 with salt
  Returns hash string

- generate_secure_token:
  Generates cryptographically secure random token
  Default 32 bytes
  Returns URL-safe base64 encoded string

5. Update backend/app/models to add encryption for sensitive fields:
- In User model add encrypted_email property that stores email encrypted at rest
- In OTPVerification model ensure otp_code is hashed not stored plain
- In PasswordHistory ensure only hashed passwords are stored

6. Create backend/app/services/compliance_service.py with:
- generate_compliance_report:
  Accepts report_type: activity, access, document, security
  Accepts date range
  Collects relevant audit log data
  Formats as structured compliance report
  Returns ComplianceReport object

- generate_activity_report:
  All user actions in date range
  Grouped by user and action type
  Includes login history, document access, AI queries

- generate_access_report:
  All document access events
  Who accessed what documents and when
  Failed access attempts
  Permission changes

- generate_document_report:
  All document lifecycle events
  Upload, approval, rejection, deletion history
  Version history

- generate_security_report:
  Failed logins, account lockouts
  Permission violations, role bypass attempts
  Suspicious activity alerts
  Password reset history

- export_compliance_report_pdf:
  Converts compliance report to PDF format
  Includes organization name, date range, report type
  Returns PDF bytes

- export_compliance_report_csv:
  Converts compliance report to CSV
  Returns CSV bytes

7. Create backend/app/schemas/compliance.py with Pydantic schemas for:
- AuditLogResponse: id, user_id, user_email_masked, organization_id, action, resource_type, resource_id, ip_address, status, created_at
- AuditLogDetailResponse: all fields including old_value and new_value
- AuditLogListResponse: logs list, total_count, page, page_size
- AuditLogFilterRequest: user_id, action, resource_type, date_from, date_to, page, page_size
- ComplianceReport: report_type, organization_id, date_from, date_to, generated_at, generated_by, summary, data
- ComplianceReportRequest: report_type, date_from, date_to, format (pdf or csv)
- DataRetentionSettings: chat_retention_days, document_retention_days, monitoring_log_retention_days, audit_log_retention_days
- UserDataExport: user_id, export_date, profile_data, chat_history, ai_queries, audit_entries

8. Create backend/app/api/v1/compliance.py with endpoints:

GET /api/v1/compliance/audit-logs
- Requires ADMIN or SUPER_ADMIN
- Returns paginated audit logs with masked sensitive fields
- Supports all filters from AuditLogFilterRequest
- USER role returns 403

GET /api/v1/compliance/audit-logs/{log_id}
- Returns full audit log detail
- Requires ADMIN or SUPER_ADMIN

GET /api/v1/compliance/audit-logs/export
- Exports audit logs as CSV
- Requires SUPER_ADMIN
- Returns CSV file download

POST /api/v1/compliance/reports/generate
- Generates compliance report
- Requires SUPER_ADMIN
- Accepts ComplianceReportRequest
- Returns report download in requested format

GET /api/v1/compliance/reports/activity
- Returns activity report data
- Requires ADMIN or SUPER_ADMIN
- Supports date range filter

GET /api/v1/compliance/reports/security
- Returns security report data
- Requires SUPER_ADMIN
- Supports date range filter

GET /api/v1/compliance/user/{user_id}/activity
- Returns complete activity history for a user
- Requires SUPER_ADMIN
- Returns user activity report

GET /api/v1/compliance/user/{user_id}/data-export
- Exports all data for a user (GDPR right to access)
- Requires SUPER_ADMIN
- Returns UserDataExport

PUT /api/v1/compliance/retention-settings
- Updates data retention settings
- Requires SUPER_ADMIN
- Returns updated DataRetentionSettings

GET /api/v1/compliance/retention-settings
- Returns current data retention settings
- Requires ADMIN or SUPER_ADMIN

9. Create backend/app/workers/compliance_tasks.py with Celery beat scheduled tasks:
- run_chat_retention_task:
  Runs daily at 3am
  Calls data_privacy_service.apply_chat_retention_policy

- run_document_retention_task:
  Runs daily at 3am
  Calls data_privacy_service.apply_document_retention_policy

- run_monitoring_cleanup_task:
  Runs daily at 2am
  Calls data_privacy_service.apply_monitoring_log_retention

- run_audit_integrity_check_task:
  Runs weekly on Sunday at 1am
  Calls audit_service.verify_audit_log_integrity
  Creates SystemAlert if integrity violation found

10. Update worker/celery_config.py to add:
- All compliance_tasks to Celery beat schedule

11. Update backend/app/main.py to include:
- Compliance router at /api/v1/compliance

FRONTEND SECTION

12. Create frontend/src/pages/AuditLogs.jsx with:
- Full audit log viewer table
- Columns: timestamp, user, action, resource type, resource id, status, ip address
- Filter bar: filter by user, action type, resource type, date range
- Search functionality
- Export to CSV button
- Click row to see full details with old and new values
- Color coded actions: create=green, update=blue, delete=red, security=orange
- Pagination controls

13. Create frontend/src/pages/ComplianceReports.jsx with:
- Report type selector: Activity, Access, Document, Security
- Date range picker
- Format selector: PDF or CSV
- Generate Report button with loading state
- Recent reports list
- Download button per report
- Report preview for activity and access reports

14. Create frontend/src/components/DataRetentionSettings.jsx with:
- Settings form for retention periods
- Chat history retention days input
- Document retention days input
- Monitoring log retention days input
- Audit log retention days input
- Save settings button
- Warning message explaining data will be permanently deleted after retention period

15. Create frontend/src/services/complianceApi.js with:
- getAuditLogs: GET /api/v1/compliance/audit-logs with filter params
- getAuditLogDetail: GET /api/v1/compliance/audit-logs/{id}
- exportAuditLogs: GET /api/v1/compliance/audit-logs/export
- generateReport: POST /api/v1/compliance/reports/generate
- getActivityReport: GET /api/v1/compliance/reports/activity
- getSecurityReport: GET /api/v1/compliance/reports/security
- getUserActivity: GET /api/v1/compliance/user/{id}/activity
- getUserDataExport: GET /api/v1/compliance/user/{id}/data-export
- getRetentionSettings: GET /api/v1/compliance/retention-settings
- updateRetentionSettings: PUT /api/v1/compliance/retention-settings
- All functions include Authorization Bearer token header

16. Update frontend/src/App.jsx to add routes:
- /compliance/audit-logs — AuditLogs (protected, ADMIN minimum)
- /compliance/reports — ComplianceReports (protected, SUPER_ADMIN only)
- /compliance/retention — DataRetentionSettings (protected, SUPER_ADMIN only)

17. Create backend/tests/test_compliance.py with tests for:
- audit_service.log_action saves correct action and resource fields
- audit_service.log_action never raises exceptions on failure
- audit_service USER role cannot access audit logs
- data_privacy_service.anonymize_user_data replaces personal data correctly
- data_privacy_service.mask_sensitive_field masks email correctly
- data_privacy_service.mask_sensitive_field masks phone correctly
- encryption.encrypt_field returns different value from input
- encryption.decrypt_field returns original value after encryption
- encryption.generate_secure_token returns string of correct length
- compliance_service.generate_activity_report returns correct structure
- audit_log_retention respects configured retention days
- All tests run without live database connections

After completing all steps run:
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/test_compliance.py backend/tests/test_monitoring.py backend/tests/test_rag_pipeline.py backend/tests/test_user_management.py backend/tests/test_approval.py backend/tests/test_document_processing.py backend/tests/test_chat.py backend/tests/test_rbac.py backend/tests/test_auth.py backend/tests/test_models.py -v --tb=short -q

Report all test results then run:
git add .
git commit -m "Phase 11 complete: Audit logging, compliance reports, data privacy, encryption, retention policies, GDPR data export, security reporting"
git push origin main

Confirm completion of every step.
``` 
<img width="975" height="436" alt="image" src="https://github.com/user-attachments/assets/1c648a8b-93fa-4544-8dd5-42591ef7c7a2" />

### Phase 12: Security Hardening
1.	Secure all backend APIs with authentication middleware.
2.	Configure HTTPS and SSL using Nginx.
3.	Add rate limiting and brute-force login protection.
4.	Add request validation for all backend endpoints.
5.	Protect against SQL injection, file upload attacks, role bypass, and exposed secrets.
6.	Add malware protection for uploaded files.
7.	Restrict CORS to approved frontend domains.
8.	Disable unnecessary public ports.
9.	Perform security testing and vulnerability checks.
10.	Fix all critical and high-risk security issues before production deployment.

### Phase 12 Implementation
•	Paste this into Codex to begin Phase 12:
```
I am building an Enterprise AI Knowledge Base & Document Intelligence System called Ent_RAG. Phases 1 through 11 are complete. I am now starting Phase 12: Security Hardening.

Do the following completely without asking questions:

BACKEND SECTION

1. Create backend/app/middleware/security_middleware.py with:
- SecurityHeadersMiddleware class that adds these headers to every response:
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  X-XSS-Protection: 1; mode=block
  Strict-Transport-Security: max-age=31536000; includeSubDomains
  Content-Security-Policy: default-src 'self'
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: geolocation=(), microphone=(), camera=()

- RequestValidationMiddleware class that:
  Checks Content-Type header is correct for POST and PUT requests
  Rejects requests with suspicious headers
  Validates request size does not exceed 100MB
  Logs suspicious requests to MonitoringLog with HIGH severity

- SQLInjectionProtectionMiddleware class that:
  Scans query parameters and path parameters for SQL injection patterns
  Detects patterns: UNION SELECT, DROP TABLE, INSERT INTO, OR 1=1, comments --, xp_cmdshell
  Returns 400 and logs attempt if SQL injection pattern detected
  Logs to MonitoringLog and creates SystemAlert with HIGH severity

2. Create backend/app/core/rate_limiter.py with:
- RateLimiter class using Redis as backend storage:
  rate_limit_by_ip: limits requests per IP address
    Default: 100 requests per minute per IP
    Returns 429 Too Many Requests if exceeded
  
  rate_limit_by_user: limits requests per authenticated user
    Default: 200 requests per minute per user
    Returns 429 if exceeded
  
  rate_limit_by_organization: limits requests per organization
    Reads API_RATE_LIMIT_PER_ORG from settings
    Default: 1000 requests per minute per organization
    Returns 429 if exceeded
  
  rate_limit_login: strict rate limiting for login endpoint
    Maximum 10 login attempts per IP per 15 minutes
    Maximum 5 login attempts per email per 15 minutes
    Returns 429 with retry_after header if exceeded
  
  rate_limit_file_upload: limits file uploads per user
    Maximum 20 file uploads per hour per user
    Returns 429 if exceeded

  get_rate_limit_status: returns current rate limit usage for debugging
  reset_rate_limit: admin function to reset rate limit for a specific key

3. Create backend/app/middleware/rate_limit_middleware.py with:
- RateLimitMiddleware class that:
  Applies rate_limit_by_ip to all requests
  Applies rate_limit_by_user to authenticated requests
  Applies rate_limit_by_organization to organization-scoped requests
  Applies rate_limit_login specifically to POST /api/v1/auth/login
  Applies rate_limit_file_upload to document upload endpoints
  Adds rate limit headers to responses:
    X-RateLimit-Limit
    X-RateLimit-Remaining
    X-RateLimit-Reset
  Logs rate limit violations to MonitoringLog
  Creates SystemAlert for repeated rate limit violations from same IP

4. Update deployment/nginx/nginx.conf with full security configuration:
- HTTPS configuration with SSL certificate paths
- HTTP to HTTPS redirect (301)
- SSL protocols: TLSv1.2 and TLSv1.3 only
- Strong SSL cipher suites only
- ssl_session_cache and ssl_session_timeout settings
- HSTS header configuration
- Proxy headers for FastAPI: X-Real-IP, X-Forwarded-For, X-Forwarded-Proto
- Client max body size: 100m
- Request timeout settings: proxy_connect_timeout 60s, proxy_read_timeout 300s
- Rate limiting at Nginx level: limit_req_zone and limit_req directives
- Block common attack patterns in location blocks
- Block access to hidden files (.git, .env)
- Disable server tokens: server_tokens off
- Add security headers at Nginx level
- Gzip compression for responses
- CORS configuration allowing only FRONTEND_URL domain

5. Create backend/app/core/cors_config.py with:
- get_cors_origins function:
  Reads FRONTEND_URL from settings
  Returns list of allowed origins
  In development also allows localhost:3000 and localhost:5173
  In production allows only the configured FRONTEND_URL
  Never allows wildcard * in production

- get_cors_settings function:
  Returns complete CORS configuration:
    allow_origins from get_cors_origins
    allow_credentials: True
    allow_methods: GET, POST, PUT, DELETE, OPTIONS
    allow_headers: Authorization, Content-Type, X-Request-ID
    max_age: 3600

6. Update backend/app/main.py to:
- Replace existing CORS with secure cors_config settings
- Register SecurityHeadersMiddleware
- Register RequestValidationMiddleware
- Register SQLInjectionProtectionMiddleware
- Register RateLimitMiddleware
- Middleware order must be:
  1. SecurityHeadersMiddleware (outermost)
  2. RateLimitMiddleware
  3. SQLInjectionProtectionMiddleware
  4. RequestValidationMiddleware
  5. MonitoringMiddleware
  6. RBACMiddleware
  7. AuthMiddleware (innermost)

7. Create backend/app/core/secret_protection.py with:
- scan_for_exposed_secrets function:
  Scans request and response data for accidentally exposed secrets
  Detects patterns: API keys, JWT tokens in response bodies, passwords in logs
  Removes or masks detected secrets before logging
  
- sanitize_log_entry function:
  Removes sensitive fields from log entries before saving
  Fields to remove: password, hashed_password, otp_code, api_key, secret_key, token
  Replaces with REDACTED
  
- validate_environment_secrets function:
  Checks all required secrets in .env are set and not placeholder values
  Checks JWT_SECRET_KEY is at least 32 characters
  Checks ENCRYPTION_KEY is valid Fernet key format
  Returns list of security warnings

8. Create backend/app/services/security_scan_service.py with:
- run_security_checklist:
  Runs comprehensive security check and returns SecurityChecklistReport
  Checks:
    All authentication middleware active: PASS or FAIL
    CORS restricted to approved domains: PASS or FAIL
    Rate limiting active on login endpoint: PASS or FAIL
    SQL injection protection active: PASS or FAIL
    File upload malware scanning active: PASS or FAIL
    Security headers configured: PASS or FAIL
    Environment secrets not placeholders: PASS or FAIL
    JWT secret key strong enough: PASS or FAIL
    HTTPS configured in Nginx: PASS or FAIL
    Database not exposed on public port: PASS or FAIL

- check_for_vulnerable_dependencies:
  Reads requirements.txt
  Returns list of packages with known vulnerabilities if any
  Note: performs static check only, no external API calls

- generate_security_report:
  Runs run_security_checklist
  Returns formatted SecurityChecklistReport
  Highlights critical and high risk failures

9. Create backend/app/schemas/security.py with Pydantic schemas for:
- SecurityChecklistReport: checks list, critical_failures, high_failures, medium_failures, overall_status, generated_at
- SecurityCheckItem: check_name, status, severity, description, recommendation
- RateLimitStatus: endpoint, limit, remaining, reset_at
- SecurityEvent: event_type, severity, ip_address, endpoint, description, created_at

10. Create backend/app/api/v1/security.py with endpoints:
GET /api/v1/security/checklist
- Requires SUPER_ADMIN
- Runs and returns SecurityChecklistReport
- Returns full security posture report

GET /api/v1/security/rate-limit-status
- Requires SUPER_ADMIN
- Returns current rate limit status for all limiters

POST /api/v1/security/rate-limit/reset
- Requires SUPER_ADMIN
- Resets rate limit for specified IP or user
- Logs to AuditLog

GET /api/v1/security/events
- Requires SUPER_ADMIN
- Returns recent security events from MonitoringLog
- Filters by event_type: sql_injection, rate_limit_exceeded, role_bypass, isolation_violation

11. Update backend/app/main.py to include:
- Security router at /api/v1/security

FRONTEND SECTION

12. Create frontend/src/pages/SecurityDashboard.jsx with:
- Security checklist display with PASS/FAIL badges
- Critical failures highlighted in red with recommendations
- Rate limit status display
- Recent security events table
- Security score indicator based on checklist results
- Export security report button

13. Create frontend/src/services/securityApi.js with:
- getSecurityChecklist: GET /api/v1/security/checklist
- getRateLimitStatus: GET /api/v1/security/rate-limit-status
- resetRateLimit: POST /api/v1/security/rate-limit/reset
- getSecurityEvents: GET /api/v1/security/events
- All functions include Authorization Bearer token header

14. Update frontend/src/App.jsx to add route:
- /security — SecurityDashboard (protected, SUPER_ADMIN only)

15. Create backend/tests/test_security.py with tests for:
- SecurityHeadersMiddleware adds X-Content-Type-Options header
- SecurityHeadersMiddleware adds X-Frame-Options header
- SQLInjectionProtectionMiddleware detects UNION SELECT pattern
- SQLInjectionProtectionMiddleware detects OR 1=1 pattern
- SQLInjectionProtectionMiddleware allows clean requests through
- rate_limiter.rate_limit_login blocks after 10 attempts
- cors_config.get_cors_origins never returns wildcard in production mode
- cors_config.get_cors_origins returns configured FRONTEND_URL
- secret_protection.sanitize_log_entry removes password field
- secret_protection.sanitize_log_entry removes otp_code field
- security_scan_service.run_security_checklist returns SecurityChecklistReport
- validate_environment_secrets flags weak JWT secret
- All tests run without live Redis or database connections

After completing all steps run:
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/test_security.py backend/tests/test_compliance.py backend/tests/test_monitoring.py backend/tests/test_rag_pipeline.py backend/tests/test_user_management.py backend/tests/test_approval.py backend/tests/test_document_processing.py backend/tests/test_chat.py backend/tests/test_rbac.py backend/tests/test_auth.py backend/tests/test_models.py -v --tb=short -q

Report all test results then run:
git add .
git commit -m "Phase 12 complete: Security hardening, rate limiting, SQL injection protection, security headers, CORS restriction, Nginx SSL config, secret protection, security checklist"
git push origin main

Confirm completion of every step.
```
<img width="975" height="405" alt="image" src="https://github.com/user-attachments/assets/54b20584-e534-471d-92f0-91ae474ccd98" />


### Phase 13: Backup, Recovery & Reliability
1.	Configure automated PostgreSQL backups.
2.	Configure Qdrant vector database backups.
3.	Back up uploaded documents securely.
4.	Back up environment configuration securely.
5.	Create restore procedures for PostgreSQL, Qdrant, and uploaded files.
6.	Test backup restoration before go-live.
7.	Configure restart policies for backend, frontend, workers, Redis, Qdrant, and database services.
8.	Add disaster recovery documentation.
9.	Create a rollback plan for failed deployments.

### Phase 13 Implementation
•	Paste this into Codex to begin Phase 13:
```
I am building an Enterprise AI Knowledge Base & Document Intelligence System called Ent_RAG. Phases 1 through 12 are complete. I am now starting Phase 13: Backup, Recovery & Reliability.

Do the following completely without asking questions:

BACKEND SECTION

1. Create backend/app/services/backup_service.py with:
- backup_postgresql:
  Runs pg_dump using PostgreSQL credentials from settings
  Output file named: ent_rag_db_backup_{timestamp}.sql.gz
  Compresses backup using gzip
  Saves to backups/postgresql/ directory
  Verifies backup file was created and is not empty
  Logs backup event to AuditLog with action DATABASE_BACKUP_CREATED
  Returns backup file path and file size

- backup_qdrant:
  Uses Qdrant REST API snapshot endpoint to create collection snapshots
  Creates snapshot for each organization collection: ent_rag_{organization_id}
  Downloads snapshot files to backups/qdrant/ directory
  File named: qdrant_{collection}_{timestamp}.snapshot
  Verifies snapshot file created and not empty
  Logs backup event to AuditLog
  Returns list of snapshot file paths

- backup_uploaded_documents:
  Creates compressed archive of entire uploads/ directory
  Output file named: documents_backup_{timestamp}.tar.gz
  Saves to backups/documents/ directory
  Verifies archive integrity using tar test flag
  Logs backup event to AuditLog
  Returns backup file path and total size

- backup_environment_config:
  Creates encrypted backup of .env file
  Uses encryption_service.encrypt_field to encrypt entire file contents
  Saves encrypted backup to backups/config/ directory
  File named: env_backup_{timestamp}.enc
  NEVER saves plain text .env to backup
  Logs config backup to AuditLog
  Returns backup file path

- run_full_backup:
  Calls all four backup functions in sequence
  Creates backup manifest file listing all backup files created
  Manifest includes: timestamp, file paths, file sizes, checksums
  Saves manifest to backups/manifests/ directory
  Returns BackupManifest object

- get_backup_history:
  Returns list of all backup manifests from backups/manifests/ directory
  Returns most recent 30 backups
  Returns BackupHistoryResponse

- verify_backup_integrity:
  Reads backup manifest
  Checks each listed backup file exists
  Checks file sizes match manifest
  Checks SHA256 checksums match
  Returns BackupIntegrityReport

- cleanup_old_backups:
  Deletes backup files older than 30 days
  Keeps at least 5 most recent backups regardless of age
  Logs cleanup to AuditLog

2. Create backend/app/services/restore_service.py with:
- restore_postgresql:
  Accepts backup file path
  Stops application write operations before restore
  Runs pg_restore or psql to restore from backup file
  Verifies restore succeeded by checking table counts
  Logs restore event to AuditLog with action DATABASE_RESTORED
  Returns RestoreResult with success flag and details

- restore_qdrant:
  Accepts snapshot file path and collection name
  Uses Qdrant REST API to restore from snapshot
  Verifies collection exists and has correct vector count after restore
  Logs restore event to AuditLog
  Returns RestoreResult

- restore_uploaded_documents:
  Accepts backup archive path
  Extracts archive to uploads/ directory
  Verifies file count matches expected count
  Logs restore event to AuditLog
  Returns RestoreResult

- restore_environment_config:
  Accepts encrypted config backup file path
  Decrypts using encryption_service.decrypt_field
  Writes decrypted content to .env file
  Logs restore event to AuditLog
  Returns RestoreResult

- run_restore_dry_run:
  Tests restore procedure without actually restoring
  Checks backup files exist and are readable
  Checks sufficient disk space available
  Checks database connection available
  Returns DryRunResult with list of checks and pass/fail status

3. Create backend/app/schemas/backup.py with Pydantic schemas for:
- BackupManifest: backup_id, timestamp, postgresql_backup, qdrant_backups, documents_backup, config_backup, total_size_mb, checksums dict
- BackupHistoryResponse: backups list, total_count, oldest_backup, newest_backup
- BackupIntegrityReport: backup_id, timestamp, checks list, all_passed, failed_checks list
- RestoreResult: success, restored_from, restore_time_seconds, records_restored, error_message
- DryRunResult: checks list, all_passed, failed_checks, estimated_restore_time_minutes
- BackupCheckItem: check_name, status, details

4. Create backend/app/workers/backup_tasks.py with Celery beat scheduled tasks:
- daily_full_backup_task:
  Runs every day at 1am
  Calls backup_service.run_full_backup
  Creates SystemAlert if any backup fails
  Logs completion to MonitoringLog

- weekly_backup_integrity_check_task:
  Runs every Sunday at 2am
  Calls backup_service.verify_backup_integrity on most recent backup
  Creates CRITICAL SystemAlert if integrity check fails
  Logs result to MonitoringLog

- monthly_backup_cleanup_task:
  Runs first day of each month at 3am
  Calls backup_service.cleanup_old_backups
  Logs cleanup to MonitoringLog

5. Update worker/celery_config.py to add:
- All backup_tasks to Celery beat schedule
- daily_full_backup_task at 1am daily
- weekly_backup_integrity_check_task Sunday 2am
- monthly_backup_cleanup_task first of month 3am

6. Create backend/app/api/v1/backup.py with endpoints requiring SUPER_ADMIN:

POST /api/v1/backup/run
- Triggers immediate full backup
- Calls backup_service.run_full_backup
- Returns BackupManifest

GET /api/v1/backup/history
- Returns backup history
- Returns BackupHistoryResponse

GET /api/v1/backup/{backup_id}/integrity
- Runs integrity check on specific backup
- Returns BackupIntegrityReport

POST /api/v1/backup/restore/dry-run
- Runs restore dry run
- Accepts backup_id
- Returns DryRunResult

POST /api/v1/backup/restore/postgresql
- Restores PostgreSQL from backup
- Accepts backup file path
- Requires explicit confirmation field set to CONFIRM_RESTORE
- Logs to AuditLog with full details
- Returns RestoreResult

POST /api/v1/backup/restore/qdrant
- Restores Qdrant from snapshot
- Requires explicit confirmation field set to CONFIRM_RESTORE
- Returns RestoreResult

POST /api/v1/backup/restore/documents
- Restores uploaded documents from archive
- Requires explicit confirmation field set to CONFIRM_RESTORE
- Returns RestoreResult

7. Update backend/app/main.py to include:
- Backup router at /api/v1/backup
- Create backup directory structure on startup:
  backups/postgresql/
  backups/qdrant/
  backups/documents/
  backups/config/
  backups/manifests/

DOCKER AND INFRASTRUCTURE SECTION

8. Update deployment/docker-compose.yml to add restart policies for all services:
- backend: restart: unless-stopped
- frontend: restart: unless-stopped
- postgres: restart: unless-stopped
- redis: restart: unless-stopped
- qdrant: restart: unless-stopped
- celery_worker: restart: unless-stopped
- nginx: restart: unless-stopped

Add health checks for all services:
- backend healthcheck: GET /health every 30s timeout 10s retries 3
- postgres healthcheck: pg_isready every 30s timeout 5s retries 5
- redis healthcheck: redis-cli ping every 30s timeout 5s retries 3
- qdrant healthcheck: GET /healthz every 30s timeout 10s retries 3

Add depends_on with condition: service_healthy for all dependent services

9. Update deployment/docker-compose.prod.yml with production reliability settings:
- All restart policies: restart: always
- Resource limits for each service:
  backend: memory 1g, cpus 1.0
  frontend: memory 512m, cpus 0.5
  postgres: memory 2g, cpus 2.0
  redis: memory 512m, cpus 0.5
  qdrant: memory 2g, cpus 2.0
  celery_worker: memory 1g, cpus 1.0
  nginx: memory 256m, cpus 0.5
- Logging configuration with max-size 100m and max-file 3 for all services
- Production environment variables

10. Create deployment/nginx/nginx.conf health check endpoint:
- Add /health location that returns 200 OK
- Add /nginx-status for internal monitoring only (not public)

DOCUMENTATION SECTION

11. Create docs/disaster_recovery.md with:
- Overview of backup strategy
- Backup schedule: daily full backup at 1am, weekly integrity check
- Backup retention: 30 days with minimum 5 backups kept
- Backup storage locations for each component
- Step by step recovery procedures:
  Section 1: PostgreSQL Recovery
    Prerequisites
    Step by step restore commands
    Verification steps
    Estimated recovery time: 15 to 30 minutes
  Section 2: Qdrant Recovery
    Prerequisites
    Step by step restore commands
    Verification steps
    Estimated recovery time: 10 to 20 minutes
  Section 3: Uploaded Documents Recovery
    Prerequisites
    Step by step restore commands
    Verification steps
    Estimated recovery time: 5 to 15 minutes
  Section 4: Full System Recovery
    Order of operations for complete system restore
    Total estimated recovery time
    Post-recovery verification checklist
- Contact information placeholders for escalation
- RTO target: 2 hours
- RPO target: 24 hours (daily backup)

12. Create docs/rollback_plan.md with:
- Rollback strategy overview
- Pre-deployment checklist before any deployment
- Rollback triggers: when to rollback vs when to fix forward
- Step by step rollback procedures:
  Section 1: Application Rollback
    Git revert or checkout previous tag
    Rebuild Docker images
    Docker Compose down and up with previous images
    Verify health checks pass
  Section 2: Database Rollback
    When to use database rollback
    Alembic downgrade commands
    Restore from backup procedure
  Section 3: Full Environment Rollback
    Complete rollback including database and files
    Estimated time: 30 to 60 minutes
- Post-rollback verification checklist
- Communication template for notifying stakeholders during rollback

13. Create docs/backup_restore_guide.md with:
- Complete guide for running manual backups
- How to verify backup integrity
- How to run restore dry run before actual restore
- How to perform each type of restore
- How to decrypt environment config backup
- Troubleshooting common backup and restore errors

FRONTEND SECTION

14. Create frontend/src/pages/BackupManagement.jsx with:
- Backup status dashboard
- Last backup time and status
- Run backup now button
- Backup history table with: date, size, integrity status, components backed up
- Run integrity check button per backup
- Run dry run button
- Restore section with confirmation requirement
- Restore type selector: PostgreSQL, Qdrant, Documents
- Confirmation input requiring user to type CONFIRM_RESTORE

15. Create frontend/src/services/backupApi.js with:
- runBackup: POST /api/v1/backup/run
- getBackupHistory: GET /api/v1/backup/history
- checkIntegrity: GET /api/v1/backup/{id}/integrity
- runDryRun: POST /api/v1/backup/restore/dry-run
- restorePostgresql: POST /api/v1/backup/restore/postgresql
- restoreQdrant: POST /api/v1/backup/restore/qdrant
- restoreDocuments: POST /api/v1/backup/restore/documents
- All functions include Authorization Bearer token header

16. Update frontend/src/App.jsx to add route:
- /backup — BackupManagement (protected, SUPER_ADMIN only)

17. Create backend/tests/test_backup.py with tests for:
- backup_service.verify_backup_integrity returns report with correct structure
- backup_service.cleanup_old_backups keeps minimum 5 backups
- restore_service.run_restore_dry_run returns DryRunResult with checks list
- backup manifest contains all required fields
- backup file naming uses correct timestamp format
- restore endpoint requires CONFIRM_RESTORE confirmation string
- restore endpoint returns 400 if confirmation string missing or wrong
- All tests run without live database or file system connections

After completing all steps run:
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/test_backup.py backend/tests/test_security.py backend/tests/test_compliance.py backend/tests/test_monitoring.py backend/tests/test_rag_pipeline.py backend/tests/test_user_management.py backend/tests/test_approval.py backend/tests/test_document_processing.py backend/tests/test_chat.py backend/tests/test_rbac.py backend/tests/test_auth.py backend/tests/test_models.py -v --tb=short -q

Report all test results then run:
git add .
git commit -m "Phase 13 complete: Automated backups, restore procedures, disaster recovery docs, rollback plan, Docker restart policies, health checks, production reliability config"
git push origin main

Confirm completion of every step.
``` 
<img width="975" height="354" alt="image" src="https://github.com/user-attachments/assets/7eac6f0e-bd3a-41a9-99d6-5e03f3641d8a" />



### Phase 14: Deployment & Production Infrastructure
1.	Dockerize backend, frontend, PostgreSQL, Redis, Qdrant, background workers, and AI services.
2.	Configure Nginx reverse proxy.
3.	Deploy services on Contabo VPS infrastructure.
4.	Configure domain name and SSL certificates.
5.	Configure background task processing with Celery and Redis.
6.	Set production environment variables.
7.	Configure automated backups.
8.	Configure service restart and recovery policies.
9.	Perform production load testing.
10.	Run final end-to-end testing and go-live deployment.
11.	Define system SLA and uptime targets for production deployment.
12.	Configure monitoring and recovery systems to support uptime commitments.
13.	Define acceptable response-time targets for AI retrieval and API requests.
14.	Define infrastructure scaling strategy for high organizational traffic and future expansion.
15.	Configure organization-level API rate limiting to prevent abuse and resource exhaustion.

### Phase 14 Implementation
•	Paste this into Codex to begin Phase 14:
```
I am building an Enterprise AI Knowledge Base & Document Intelligence System called Ent_RAG. Phases 1 through 13 are complete. I am now starting Phase 14: Deployment & Production Infrastructure.

Production server details:
- Server IP: 185.193.17.27
- Domain: docintel.space
- SSL Email: philiposita1041@gmail.com
- OS: Ubuntu 22.04
- Frontend URL: https://docintel.space
- Backend URL: https://docintel.space/api
- API Domain: api.docintel.space

Do the following completely without asking questions:

DOCKER SECTION

1. Review and finalize backend/Dockerfile for production:
- Use Python 3.11 slim base image
- Install system dependencies: gcc, libpq-dev, libmagic1, tesseract-ocr, clamav, clamav-daemon
- Copy requirements.txt and install all Python packages
- Copy application code
- Create non-root user called appuser and run as appuser
- Expose port 8000
- CMD: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

2. Review and finalize frontend/Dockerfile for production:
- Stage 1 build: Node 18 alpine, install dependencies, run npm run build
- Stage 2 serve: Nginx alpine, copy built files from stage 1
- Copy custom nginx config for serving React SPA
- Expose port 80
- Serve built React app

3. Create deployment/docker-compose.prod.yml as complete production file:
Services:
  backend:
    build: ./backend
    container_name: ent_rag_backend
    restart: always
    environment: reads from .env file
    volumes: ./uploads:/app/uploads, ./backups:/app/backups
    networks: ent_rag_network
    depends_on: postgres, redis, qdrant
    deploy resources: memory 1g, cpus 1.0
    logging: max-size 100m, max-file 3
    healthcheck: curl -f http://localhost:8000/health every 30s

  frontend:
    build: ./frontend
    container_name: ent_rag_frontend
    restart: always
    networks: ent_rag_network
    depends_on: backend
    deploy resources: memory 512m, cpus 0.5
    logging: max-size 50m, max-file 3

  postgres:
    image: postgres:15-alpine
    container_name: ent_rag_postgres
    restart: always
    environment:
      POSTGRES_DB from .env
      POSTGRES_USER from .env
      POSTGRES_PASSWORD from .env
    volumes: postgres_data:/var/lib/postgresql/data
    networks: ent_rag_network
    deploy resources: memory 2g, cpus 2.0
    healthcheck: pg_isready -U from .env every 30s

  redis:
    image: redis:7-alpine
    container_name: ent_rag_redis
    restart: always
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes: redis_data:/data
    networks: ent_rag_network
    deploy resources: memory 512m, cpus 0.5
    healthcheck: redis-cli ping every 30s

  qdrant:
    image: qdrant/qdrant:latest
    container_name: ent_rag_qdrant
    restart: always
    volumes: qdrant_data:/qdrant/storage
    networks: ent_rag_network
    deploy resources: memory 2g, cpus 2.0
    healthcheck: curl -f http://localhost:6333/healthz every 30s

  celery_worker:
    build: ./backend
    container_name: ent_rag_celery
    restart: always
    command: celery -A app.workers.celery_app worker --loglevel=info --concurrency=4
    environment: reads from .env file
    volumes: ./uploads:/app/uploads, ./backups:/app/backups
    networks: ent_rag_network
    depends_on: postgres, redis
    deploy resources: memory 1g, cpus 1.0
    logging: max-size 100m, max-file 3

  celery_beat:
    build: ./backend
    container_name: ent_rag_celery_beat
    restart: always
    command: celery -A app.workers.celery_app beat --loglevel=info
    environment: reads from .env file
    networks: ent_rag_network
    depends_on: postgres, redis
    deploy resources: memory 256m, cpus 0.25
    logging: max-size 50m, max-file 3

  nginx:
    image: nginx:alpine
    container_name: ent_rag_nginx
    restart: always
    ports: 80:80, 443:443
    volumes:
      ./deployment/nginx/nginx.conf:/etc/nginx/nginx.conf
      ./deployment/nginx/ssl:/etc/nginx/ssl
      ./deployment/nginx/certbot/www:/var/www/certbot
      certbot_data:/etc/letsencrypt
    networks: ent_rag_network
    depends_on: backend, frontend
    deploy resources: memory 256m, cpus 0.5
    logging: max-size 50m, max-file 3

  certbot:
    image: certbot/certbot
    container_name: ent_rag_certbot
    volumes:
      certbot_data:/etc/letsencrypt
      ./deployment/nginx/certbot/www:/var/www/certbot
    entrypoint: /bin/sh -c "trap exit TERM; while :; do certbot renew; sleep 12h & wait; done"

Named volumes: postgres_data, redis_data, qdrant_data, certbot_data
Network: ent_rag_network bridge driver

4. Update deployment/nginx/nginx.conf for production with domain docintel.space:
- HTTP server block on port 80:
  server_name docintel.space www.docintel.space
  Location /.well-known/acme-challenge/ serves from /var/www/certbot for Let's Encrypt
  All other HTTP requests redirect 301 to https://docintel.space

- HTTPS server block on port 443:
  server_name docintel.space www.docintel.space
  ssl_certificate /etc/letsencrypt/live/docintel.space/fullchain.pem
  ssl_certificate_key /etc/letsencrypt/live/docintel.space/privkey.pem
  ssl_protocols TLSv1.2 TLSv1.3
  ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384
  ssl_prefer_server_ciphers off
  ssl_session_cache shared:SSL:10m
  ssl_session_timeout 10m
  add_header Strict-Transport-Security max-age=63072000 always
  
  Location /api:
    proxy_pass http://backend:8000
    proxy_set_header Host $host
    proxy_set_header X-Real-IP $remote_addr
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for
    proxy_set_header X-Forwarded-Proto $scheme
    proxy_connect_timeout 60s
    proxy_read_timeout 300s
    client_max_body_size 100m
  
  Location /docs: proxy to backend (FastAPI docs)
  Location /health: proxy to backend health endpoint
  
  Location /: 
    proxy_pass http://frontend:80
    proxy_set_header Host $host
  
  Gzip compression enabled for text, json, javascript, css
  server_tokens off
  Security headers as configured in Phase 12

DEPLOYMENT SCRIPTS SECTION

5. Create deployment/scripts/install_server.sh:
Full server setup script for fresh Ubuntu 22.04 VPS at 185.193.17.27:
#!/bin/bash
set -e

echo "=== Ent_RAG Server Installation Script ==="
echo "=== Server: 185.193.17.27 | Domain: docintel.space ==="

# Update system
apt-get update && apt-get upgrade -y

# Install required packages
apt-get install -y curl wget git ufw fail2ban htop unzip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
systemctl start docker
systemctl enable docker

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Configure UFW firewall
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Configure fail2ban for brute force protection
systemctl start fail2ban
systemctl enable fail2ban

# Create application directory
mkdir -p /opt/ent_rag
chown $USER:$USER /opt/ent_rag

echo "=== Server installation complete ==="
echo "=== Docker version: $(docker --version) ==="
echo "=== Docker Compose version: $(docker-compose --version) ==="

6. Create deployment/scripts/deploy.sh:
Full deployment script:
#!/bin/bash
set -e

echo "=== Deploying Ent_RAG to docintel.space ==="

PROJECT_DIR=/opt/ent_rag
DOMAIN=docintel.space
EMAIL=philiposita1041@gmail.com

cd $PROJECT_DIR

# Pull latest code
git pull origin main

# Create required directories
mkdir -p uploads backups/postgresql backups/qdrant backups/documents backups/config backups/manifests
mkdir -p deployment/nginx/certbot/www deployment/nginx/ssl

# Check .env exists
if [ ! -f .env ]; then
  echo "ERROR: .env file not found. Copy .env.example to .env and fill in values."
  exit 1
fi

# Build and start services
docker-compose -f deployment/docker-compose.prod.yml build --no-cache
docker-compose -f deployment/docker-compose.prod.yml up -d postgres redis qdrant

echo "=== Waiting for database to be ready ==="
sleep 15

# Run database migrations
docker-compose -f deployment/docker-compose.prod.yml run --rm backend alembic upgrade head

echo "=== Starting all services ==="
docker-compose -f deployment/docker-compose.prod.yml up -d

echo "=== Waiting for services to start ==="
sleep 20

# Issue SSL certificate
echo "=== Requesting SSL certificate for docintel.space ==="
docker-compose -f deployment/docker-compose.prod.yml run --rm certbot certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email philiposita1041@gmail.com \
  --agree-tos \
  --no-eff-email \
  -d docintel.space \
  -d www.docintel.space

# Reload Nginx with SSL
docker-compose -f deployment/docker-compose.prod.yml exec nginx nginx -s reload

# Run health checks
echo "=== Running health checks ==="
sleep 5
curl -f https://docintel.space/health && echo "Backend health: OK" || echo "Backend health: FAILED"
curl -f https://docintel.space && echo "Frontend health: OK" || echo "Frontend health: FAILED"

echo "=== Deployment complete ==="
echo "=== Application available at: https://docintel.space ==="

7. Create deployment/scripts/rollback.sh:
#!/bin/bash
set -e

echo "=== Rolling back Ent_RAG deployment ==="

PROJECT_DIR=/opt/ent_rag
ROLLBACK_TAG=$1

if [ -z "$ROLLBACK_TAG" ]; then
  echo "Usage: ./rollback.sh <git-tag-or-commit>"
  exit 1
fi

cd $PROJECT_DIR

echo "=== Stopping current services ==="
docker-compose -f deployment/docker-compose.prod.yml down

echo "=== Checking out version: $ROLLBACK_TAG ==="
git checkout $ROLLBACK_TAG

echo "=== Rebuilding with previous version ==="
docker-compose -f deployment/docker-compose.prod.yml build --no-cache

echo "=== Starting previous version ==="
docker-compose -f deployment/docker-compose.prod.yml up -d

echo "=== Waiting for services ==="
sleep 20

echo "=== Verifying rollback ==="
curl -f https://docintel.space/health && echo "Health check: OK" || echo "Health check: FAILED"

echo "=== Rollback complete to version: $ROLLBACK_TAG ==="

8. Create deployment/scripts/backup_now.sh:
#!/bin/bash
echo "=== Running manual backup ==="
PROJECT_DIR=/opt/ent_rag
cd $PROJECT_DIR
docker-compose -f deployment/docker-compose.prod.yml exec backend python -c "
from app.services.backup_service import backup_service
import asyncio
result = asyncio.run(backup_service.run_full_backup())
print(f'Backup complete: {result}')
"
echo "=== Backup complete ==="

9. Create deployment/scripts/health_check.sh:
#!/bin/bash
echo "=== Ent_RAG Health Check ==="
echo "Domain: docintel.space"
echo "Server: 185.193.17.27"
echo ""

check_service() {
  local name=$1
  local url=$2
  if curl -sf "$url" > /dev/null 2>&1; then
    echo "✓ $name: OK"
  else
    echo "✗ $name: FAILED"
  fi
}

check_service "Frontend" "https://docintel.space"
check_service "Backend API" "https://docintel.space/health"
check_service "API Docs" "https://docintel.space/docs"

echo ""
echo "=== Docker Container Status ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "=== Disk Usage ==="
df -h /opt/ent_rag

echo ""
echo "=== Memory Usage ==="
free -h

LOAD TESTING SECTION

10. Create deployment/load_testing/locustfile.py:
Full Locust load testing file targeting https://docintel.space:
- HealthCheckUser class: hits /health endpoint
- AuthenticatedUser class:
  On start: logs in with test credentials and stores JWT token
  Tasks with weights:
    ask_question (weight 40): POST /api/v1/chat/ask with sample question
    get_sessions (weight 20): GET /api/v1/chat/sessions
    get_dashboard (weight 15): GET /api/v1/users/me
    search_conversations (weight 10): GET /api/v1/chat/search
    get_sample_questions (weight 15): GET /api/v1/chat/sample-questions
- AdminUser class:
  On start: logs in as admin user
  Tasks:
    get_documents (weight 30): GET /api/v1/admin/documents
    get_dashboard_stats (weight 30): GET /api/v1/admin/dashboard/stats
    get_approval_queue (weight 40): GET /api/v1/admin/approvals/queue

- Load test configuration comments:
  Baseline test: 10 users, spawn rate 2, run 5 minutes
  Stress test: 50 users, spawn rate 5, run 10 minutes
  Peak test: 100 users, spawn rate 10, run 5 minutes

11. Create deployment/load_testing/requirements.txt:
locust==2.17.0

SLA AND PERFORMANCE SECTION

12. Create docs/sla_and_performance.md:
# Ent_RAG Service Level Agreement
## Production Environment: docintel.space
## Server: 185.193.17.27

### Uptime Targets
- API Availability: 99.5% monthly uptime
- Scheduled Maintenance Window: Sundays 2am to 4am WAT
- Maximum Unplanned Downtime: 3.6 hours per month

### Response Time Targets
- Health check endpoint: under 100ms
- Authentication endpoints: under 500ms
- Chat/AI query endpoint: under 8 seconds (includes RAG pipeline)
- Document upload endpoint: under 2 seconds (async processing)
- Dashboard and listing endpoints: under 1 second
- Search endpoints: under 2 seconds

### Throughput Targets
- Concurrent users supported: 100
- AI queries per minute: 50
- Document uploads per hour: 100
- API requests per minute total: 1000

### Recovery Targets
- RTO (Recovery Time Objective): 2 hours
- RPO (Recovery Point Objective): 24 hours
- Backup frequency: Daily at 1am WAT

### Rate Limits
- Per IP: 100 requests per minute
- Per user: 200 requests per minute
- Per organization: 1000 requests per minute
- Login attempts: 10 per IP per 15 minutes

### Scaling Strategy
- Vertical scaling: upgrade Contabo VPS plan for increased CPU and RAM
- Horizontal scaling path: migrate to Docker Swarm or Kubernetes when exceeding 500 concurrent users
- Database scaling: add PostgreSQL read replica when query volume exceeds current capacity
- Vector search scaling: add Qdrant cluster nodes when collection size exceeds 10 million vectors
- Multi-region expansion: add regional VPS nodes in Lagos or Johannesburg for African market

### Monitoring and Alerting
- System monitored 24/7 via internal monitoring dashboard at https://docintel.space/monitoring
- Critical alerts trigger immediate response
- High alerts addressed within 4 hours
- Medium alerts addressed within 24 hours

13. Create docs/production_checklist.md:
Complete pre-launch checklist:
## Pre-Launch Production Checklist for docintel.space

### Infrastructure
- [ ] Contabo VPS 185.193.17.27 provisioned and accessible via SSH
- [ ] Ubuntu 22.04 updated to latest patches
- [ ] Docker and Docker Compose installed
- [ ] UFW firewall configured: only ports 22, 80, 443 open
- [ ] Fail2ban configured for SSH and login protection
- [ ] Minimum 40GB disk space available

### Domain and SSL
- [ ] docintel.space DNS A record pointing to 185.193.17.27
- [ ] www.docintel.space DNS A record pointing to 185.193.17.27
- [ ] SSL certificate issued for docintel.space via Let's Encrypt
- [ ] HTTPS redirect working from http to https
- [ ] SSL Labs test score A or better

### Application
- [ ] All 15 phases of development complete
- [ ] All test suites passing: 0 failures
- [ ] .env file configured with production values
- [ ] No placeholder values remaining in .env
- [ ] JWT_SECRET_KEY is strong random value minimum 32 characters
- [ ] ENCRYPTION_KEY is valid Fernet key
- [ ] CEREBRAS_API_KEY is valid and tested
- [ ] SMTP credentials tested and working
- [ ] Super Admin account created via setup endpoint

### Database
- [ ] PostgreSQL running and healthy
- [ ] Alembic migrations applied: alembic upgrade head
- [ ] Database connection verified
- [ ] Initial data seeded if required

### Security
- [ ] Security checklist at /api/v1/security/checklist all passing
- [ ] CORS restricted to docintel.space only
- [ ] Rate limiting active and tested
- [ ] SQL injection protection active
- [ ] Security headers verified via securityheaders.com

### Backups
- [ ] Backup directories created
- [ ] Manual backup test run successful
- [ ] Backup integrity check passing
- [ ] Automated backup schedule active

### Monitoring
- [ ] Monitoring dashboard accessible at https://docintel.space/monitoring
- [ ] Alert rules active
- [ ] Celery beat scheduler running
- [ ] Health check endpoint returning 200

### Load Testing
- [ ] Baseline load test passed: 10 users no errors
- [ ] Stress test passed: 50 users under 8 second response time
- [ ] No memory leaks observed during load test

### Go-Live
- [ ] All checklist items above checked
- [ ] Team notified of go-live
- [ ] Rollback plan reviewed and ready
- [ ] First backup taken post go-live

FRONTEND SECTION

14. Update frontend/src/services/chatApi.js and all API service files:
- Replace all instances of http://localhost:8000 with https://docintel.space/api
- Replace all instances of http://localhost:3000 with https://docintel.space
- Ensure all API calls use HTTPS in production

15. Create frontend/src/config/environment.js with:
- API_BASE_URL: reads from REACT_APP_API_URL env var, defaults to https://docintel.space/api
- APP_URL: reads from REACT_APP_URL env var, defaults to https://docintel.space
- ENVIRONMENT: reads from REACT_APP_ENV env var, defaults to production

16. Create backend/app/api/v1/health.py with:
GET /health endpoint:
- Returns: status ok, version 1.0.0, environment, timestamp
- Does not require authentication
- Returns database connection status
- Returns Redis connection status
- Returns Qdrant connection status
- Returns 200 if all healthy, 503 if any critical service down

GET /health/detailed endpoint:
- Requires SUPER_ADMIN authentication
- Returns detailed health for all services
- Includes response times for each service check
- Returns disk usage and memory usage

Update backend/app/main.py to include health router

TESTING SECTION

17. Create backend/tests/test_deployment.py with tests for:
- health endpoint returns correct structure with status field
- health endpoint returns 200 for healthy state
- environment config reads API_BASE_URL correctly
- production CORS allows docintel.space origin
- production CORS blocks unknown origins
- SLA response time targets are defined and reasonable
- All deployment scripts exist and are executable
- Docker compose prod file contains all required services
- All tests run without live server connections

After completing all steps run:
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/test_deployment.py backend/tests/test_backup.py backend/tests/test_security.py backend/tests/test_compliance.py backend/tests/test_monitoring.py backend/tests/test_rag_pipeline.py backend/tests/test_user_management.py backend/tests/test_approval.py backend/tests/test_document_processing.py backend/tests/test_chat.py backend/tests/test_rbac.py backend/tests/test_auth.py backend/tests/test_models.py -v --tb=short -q

Report all test results then run:
chmod +x deployment/scripts/install_server.sh
chmod +x deployment/scripts/deploy.sh
chmod +x deployment/scripts/rollback.sh
chmod +x deployment/scripts/backup_now.sh
chmod +x deployment/scripts/health_check.sh

git add .
git commit -m "Phase 14 complete: Production Docker config, Nginx SSL for docintel.space, deployment scripts, load testing, SLA documentation, production checklist, health endpoints"
git push origin main

Confirm completion of every step.
``` 
<img width="975" height="381" alt="image" src="https://github.com/user-attachments/assets/dd50cb7d-fec2-4bbb-8a5d-123bc4d7194b" />

### Phase 15: Final Testing, Optimization & Handover
1.	Test login, OTP verification, password reset, and 30-day password expiration.
2.	Test role-based access for User, Admin, and Super Admin.
3.	Test personal chat history isolation for each user.
4.	Test document upload, malware scanning, ingestion, chunking, embedding, approval, and retrieval.
5.	Test “no source, no answer” AI behavior.
6.	Test source referencing in AI answers.
7.	Test Super Admin user creation and Excel bulk onboarding.
8.	Test monitoring dashboard, alerts, logs, and AI system summaries.
9.	Optimize frontend speed, backend response time, database queries, and vector search performance.

### Phase 15 Implementation
•	Paste this into Codex to begin Phase 15:
```
I am already inside the project folder on the production server <ip_address>. I am already SSH'd in. The domain docintel.space is already pointing to this server. Do not include any SSH commands.

I am doing Phase 15: Final Testing, Optimization & Go-Live.

Do the following completely without asking questions:

TESTING SECTION

1. Create backend/tests/test_phase15_integration.py with comprehensive integration tests:

AUTH AND LOGIN TESTS:
- test_login_with_valid_credentials_returns_jwt_token
- test_login_with_invalid_password_returns_401
- test_login_with_unverified_account_blocks_and_sends_otp
- test_login_increments_failed_attempts_on_wrong_password
- test_login_locks_account_after_5_failed_attempts
- test_otp_verification_marks_user_as_verified
- test_otp_verification_with_expired_otp_returns_400
- test_otp_verification_with_used_otp_returns_400
- test_password_reset_request_sends_email
- test_password_reset_with_valid_token_updates_password
- test_password_reset_enforces_strong_password_policy
- test_30_day_password_expiry_flags_user_for_reset
- test_first_login_must_change_password_flag_is_true
- test_changed_password_clears_must_change_password_flag
- test_password_history_prevents_reuse_of_last_5_passwords

RBAC TESTS:
- test_user_role_can_access_chat_endpoints
- test_user_role_cannot_access_admin_endpoints_returns_403
- test_user_role_cannot_access_superadmin_endpoints_returns_403
- test_admin_role_can_access_document_management_endpoints
- test_admin_role_cannot_access_superadmin_endpoints_returns_403
- test_superadmin_role_can_access_all_endpoints
- test_unauthenticated_request_returns_401
- test_expired_jwt_token_returns_401
- test_user_from_org_a_cannot_access_org_b_data_returns_403
- test_role_bypass_attempt_is_logged_to_audit

CHAT ISOLATION TESTS:
- test_user_can_only_see_own_chat_sessions
- test_user_cannot_access_another_users_session_returns_403
- test_user_cannot_search_another_users_conversations
- test_chat_session_scoped_to_correct_organization_id
- test_message_stored_under_correct_user_and_session
- test_deleted_session_not_returned_in_list

DOCUMENT PIPELINE TESTS:
- test_file_validation_rejects_disallowed_file_type
- test_file_validation_rejects_oversized_file
- test_file_validation_detects_file_type_spoofing
- test_malware_scan_marks_clean_file_as_safe
- test_malware_scan_quarantines_infected_file
- test_document_upload_queues_celery_task
- test_text_extraction_from_pdf_returns_non_empty_text
- test_text_extraction_from_docx_returns_non_empty_text
- test_hybrid_chunking_returns_chunks_within_token_limit
- test_chunking_maintains_overlap_between_adjacent_chunks
- test_embeddings_generated_with_correct_dimensions_384
- test_unapproved_document_not_available_for_ai_search
- test_approved_document_available_for_ai_search
- test_rejected_document_not_available_for_ai_search
- test_archived_document_not_available_for_ai_search
- test_document_approval_workflow_status_transitions

RAG AND AI TESTS:
- test_no_source_no_answer_returns_fallback_when_no_chunks
- test_ai_response_includes_source_references
- test_low_confidence_response_is_rejected
- test_high_hallucination_risk_response_is_rejected
- test_good_confidence_response_is_returned
- test_confidence_score_between_0_and_1
- test_hallucination_risk_score_between_0_and_1
- test_retrieval_filtered_by_user_permissions
- test_unapproved_document_excluded_from_retrieval
- test_fallback_message_is_non_empty_string
- test_feedback_correct_saves_to_message_table
- test_feedback_hallucination_saves_to_message_table
- test_low_confidence_flag_creates_system_alert

USER MANAGEMENT TESTS:
- test_superadmin_can_create_user_with_correct_fields
- test_created_user_has_must_change_password_true
- test_created_user_has_is_verified_false
- test_created_user_receives_temporary_password_email
- test_bulk_excel_upload_creates_users_for_valid_rows
- test_bulk_upload_reports_errors_for_invalid_rows
- test_bulk_upload_rejects_duplicate_emails
- test_superadmin_can_activate_deactivated_user
- test_superadmin_can_deactivate_active_user
- test_superadmin_reset_password_sets_must_change_password
- test_superadmin_unlock_clears_failed_attempts
- test_all_superadmin_actions_logged_to_audit

MONITORING TESTS:
- test_monitoring_dashboard_returns_system_metrics
- test_alert_created_for_high_error_rate
- test_duplicate_alerts_not_created_for_same_open_issue
- test_repeated_errors_grouped_into_incident
- test_debugging_assistant_returns_plain_english_explanation
- test_ai_trust_report_returns_confidence_analytics
- test_audit_log_captures_all_required_events
- test_audit_log_user_role_access_returns_403
- test_compliance_report_generates_correctly
- test_data_retention_policy_deletes_old_records

All tests must run without live database, Qdrant, Cerebras, or SMTP connections.
Use mocks and fixtures for all external dependencies.

2. Create backend/tests/conftest.py with shared pytest fixtures:
- mock_db_session: mocked SQLAlchemy session
- mock_current_user: User object with USER role
- mock_admin_user: User object with ADMIN role
- mock_superadmin_user: User object with SUPER_ADMIN role
- mock_organization: Organization object
- mock_document: approved Document object
- mock_chat_session: ChatSession object
- mock_message: Message object with confidence scores
- mock_qdrant_client: mocked Qdrant client
- mock_cerebras_client: mocked Cerebras API response
- mock_email_service: mocked email sender
- mock_redis_client: mocked Redis client
- sample_pdf_bytes: minimal valid PDF bytes
- sample_excel_bytes: minimal valid Excel bytes with user columns

OPTIMIZATION SECTION

3. Create backend/app/core/database_optimizer.py with:
- add_database_indexes for:
  users: email, organization_id, is_active, role_id
  documents: organization_id, status, department_id, created_at
  document_chunks: document_id, organization_id
  messages: session_id, user_id, organization_id, created_at
  audit_logs: organization_id, user_id, action, created_at
  monitoring_logs: organization_id, event_type, created_at
  chat_sessions: user_id, organization_id, created_at
- get_slow_queries: returns queries over 1000ms with recommendations
- analyze_query_performance: checks all indexes exist

4. Create new Alembic migration for performance indexes:
Run: alembic revision -m "add_performance_indexes"
Add all indexes in upgrade function
Add drop indexes in downgrade function

5. Create backend/app/core/cache_config.py with:
- CacheManager class using Redis:
  cache_response: stores with TTL
  get_cached_response: retrieves cached
  invalidate_cache: clears by key pattern
  invalidate_organization_cache: clears org cache
- TTL settings:
  dashboard_stats: 60 seconds
  document_list: 30 seconds
  user_profile: 300 seconds
  sample_questions: 3600 seconds
  organization_settings: 600 seconds

6. Add Redis caching to these endpoints:
- GET /api/v1/admin/dashboard/stats: 60 seconds
- GET /api/v1/superadmin/dashboard/stats: 60 seconds
- GET /api/v1/chat/sample-questions: 3600 seconds
- GET /api/v1/monitoring/metrics: 30 seconds

7. Create backend/app/core/connection_pool_config.py with optimized SQLAlchemy settings:
- pool_size: 10
- max_overflow: 20
- pool_timeout: 30
- pool_recycle: 3600
- pool_pre_ping: True
Update database.py to use these settings

8. Create backend/app/core/qdrant_optimizer.py with:
- optimize_collection_settings: HNSW m=16, ef_construct=100
- create_payload_indexes: indexes on organization_id and document_id
- get_collection_stats: vector count, memory usage per collection

FRONTEND OPTIMIZATION SECTION

9. Create frontend/src/utils/performance.js with:
- lazyLoadComponent: React.lazy wrapper with error boundary
- debounce: 300ms default
- throttle: for scroll and resize
- memoizeApiCall: 30 second memory cache
- formatRelativeTime: lightweight date formatting

10. Update frontend/src/pages/ChatInterface.jsx:
- Add React.memo
- Virtualize message lists over 50 messages
- Debounce search 300ms
- Add loading skeleton components
- Lazy load HelpSection and SampleQuestions

11. Update frontend/src/pages/DocumentManagement.jsx:
- Add React.memo
- Virtualize document list
- Debounce filters and search
- Pagination with 10, 25, 50 options

12. Create frontend/src/components/LoadingSkeleton.jsx with:
- Skeletons for: stats cards, document rows, chat messages, user rows
- Tailwind animate-pulse effect
- Matches real component layouts

13. Create frontend/src/utils/errorBoundary.jsx with:
- ErrorBoundary class component
- Friendly error message display
- Try Again button
- Error logging
Wrap all main pages in App.jsx with ErrorBoundary

GO-LIVE SECTION

14. Create docs/go_live_guide.md with:
- Complete deployment steps starting from inside the server
- Step 1: Navigate to project folder
- Step 2: Pull latest code: git pull origin main
- Step 3: Verify .env: grep -r "your_" .env
- Step 4: Run deployment: ./deployment/scripts/deploy.sh
- Step 5: Verify containers: docker ps
- Step 6: Check health: curl https://docintel.space/health
- Step 7: Create Super Admin via API call
- Step 8: Login at https://docintel.space
- Step 9: Run security checklist
- Step 10: Take first backup
- Post go-live monitoring instructions
- Troubleshooting common issues

15. Create docs/admin_guide.md with:
- Getting started as Super Admin at docintel.space
- Creating organizations and departments
- Managing users: create, bulk upload, activate, deactivate
- Managing documents: upload, approve, reject, version
- Monitoring: daily tasks, alerts, AI quality
- Troubleshooting guide

16. Update README.md:
- Live URL: https://docintel.space
- API docs: https://docintel.space/docs
- All 15 phases summary
- Tech stack
- Quick start guide

FINAL VERIFICATION SECTION

17. Run complete test suite:
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/ -v --tb=short -q
Report total passing and failing

18. Run code quality check:
PYTHONPATH=backend .venv/bin/python -m compileall backend/app -q

19. Verify all API routes registered:
PYTHONPATH=backend .venv/bin/python -c "
from app.main import app
routes = [r.path for r in app.routes]
print(f'Total routes: {len(routes)}')
for r in sorted(routes):
    print(r)
"

20. Verify all frontend pages exist and report FOUND or MISSING:
frontend/src/pages/UserDashboard.jsx
frontend/src/pages/ChatInterface.jsx
frontend/src/pages/ChatHistory.jsx
frontend/src/pages/AdminDashboard.jsx
frontend/src/pages/DocumentManagement.jsx
frontend/src/pages/ApprovalQueue.jsx
frontend/src/pages/SuperAdminDashboard.jsx
frontend/src/pages/UserManagement.jsx
frontend/src/pages/MonitoringDashboard.jsx
frontend/src/pages/AlertsPanel.jsx
frontend/src/pages/DebuggingAssistant.jsx
frontend/src/pages/AITrustReport.jsx
frontend/src/pages/SecurityDashboard.jsx
frontend/src/pages/BackupManagement.jsx
frontend/src/pages/AuditLogs.jsx
frontend/src/pages/ComplianceReports.jsx
frontend/src/pages/DocumentVersions.jsx

DEPLOYMENT SECTION

21. Run database migrations:
docker-compose -f deployment/docker-compose.prod.yml run --rm backend alembic upgrade head

22. Build and start all production services:
docker-compose -f deployment/docker-compose.prod.yml build --no-cache
docker-compose -f deployment/docker-compose.prod.yml up -d

23. Wait 30 seconds then verify all containers are running:
sleep 30
docker ps

24. Issue SSL certificate for docintel.space:
docker-compose -f deployment/docker-compose.prod.yml run --rm certbot certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email philiposita1041@gmail.com \
  --agree-tos \
  --no-eff-email \
  -d docintel.space \
  -d www.docintel.space

25. Reload Nginx with SSL:
docker-compose -f deployment/docker-compose.prod.yml exec nginx nginx -s reload

26. Run final health checks:
curl -f https://docintel.space/health && echo "Backend: OK" || echo "Backend: FAILED"
curl -f https://docintel.space && echo "Frontend: OK" || echo "Frontend: FAILED"

27. Create Super Admin account:
curl -X POST https://docintel.space/api/v1/setup/super-admin \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Philip",
    "last_name": "Ogbunugafor",
    "email": "philiposita1041@gmail.com",
    "password": "<password>"
  }'

28. Run first backup:
docker-compose -f deployment/docker-compose.prod.yml exec backend python -c "
import asyncio
from app.services.backup_service import backup_service
result = asyncio.run(backup_service.run_full_backup())
print(f'First backup complete: {result}')
"

After all steps complete run:
git add .
git commit -m "Phase 15 complete: Final integration tests, performance optimization, database indexes, Redis caching, frontend optimization, go-live complete, docintel.space live"
git push origin main

Then produce this final report:

FINAL PROJECT COMPLETION REPORT
=================================
Phase 1  - Project Setup & Architecture: COMPLETE
Phase 2  - Database Design & Models: COMPLETE
Phase 3  - Authentication & Security: COMPLETE
Phase 4  - RBAC & Data Isolation: COMPLETE
Phase 5  - User Workspace: COMPLETE
Phase 6  - Admin Workspace & Documents: COMPLETE
Phase 7  - Document Approval & Governance: COMPLETE
Phase 8  - Super Admin User Management: COMPLETE
Phase 9  - RAG Pipeline & AI Engine: COMPLETE
Phase 10 - AI Monitoring & Intelligence: COMPLETE
Phase 11 - Audit Logs & Compliance: COMPLETE
Phase 12 - Security Hardening: COMPLETE
Phase 13 - Backup & Recovery: COMPLETE
Phase 14 - Deployment & Infrastructure: COMPLETE
Phase 15 - Final Testing & Optimization: COMPLETE

Total Tests: X passing / X failing
Total API Routes: X
Total Frontend Pages: X
Total Services: X
Total Celery Tasks: X

LIVE URL: https://docintel.space
API DOCS: https://docintel.space/docs
HEALTH: https://docintel.space/health
SUPER ADMIN EMAIL: <email>

APPLICATION STATUS: LIVE AND PRODUCTION READY
``` 
<img width="975" height="476" alt="image" src="https://github.com/user-attachments/assets/0a4bc094-fbec-4379-bc63-90b49b11fdc8" />


## API Documentation

The full interactive API documentation is available at **https://docintel.space/docs** (Swagger UI).

### Core Endpoint Groups

| Prefix | Description |
|---|---|
| `POST /api/v1/auth/login` | Authenticate and receive JWT |
| `POST /api/v1/auth/verify-otp` | Complete MFA verification |
| `POST /api/v1/chat/query` | Submit a RAG query against documents |
| `GET  /api/v1/chat/history` | Retrieve conversation history |
| `POST /api/v1/admin/documents/upload` | Upload a document for processing |
| `GET  /api/v1/admin/approvals` | List pending approval queue |
| `POST /api/v1/admin/approvals/{id}/approve` | Approve a document for AI use |
| `GET  /api/v1/monitoring/dashboard` | System health overview |
| `GET  /api/v1/monitoring/alerts` | Active alerts list |
| `GET  /api/v1/compliance/audit-logs` | Full audit trail |
| `POST /api/v1/compliance/reports/generate` | Generate compliance report |
| `GET  /api/v1/security/checklist` | Security posture checklist |
| `POST /api/v1/backup/run` | Trigger manual backup |
| `GET  /api/v1/superadmin/dashboard/stats` | Platform-wide statistics |
| `POST /api/v1/superadmin/users/bulk-upload` | Bulk user onboarding via Excel |

### RAG Query Request / Response

**Request:**
```json
POST /api/v1/chat/query
{
  "query": "What is the expense reimbursement policy?",
  "organization_id": "acme-corp"
}
```

**Response:**
```json
{
  "answer": "Employees may claim up to $500 per month in approved business expenses...",
  "sources": [
    {
      "document_title": "Employee Handbook v3.2",
      "page": 14,
      "relevance_score": 0.91
    }
  ],
  "confidence_score": 0.88,
  "hallucination_risk": 0.04,
  "retrieval_confidence": 0.91,
  "query_id": "q_20260528_abc123"
}
```

---

## Testing

### Run backend unit and integration tests

```bash
docker exec -it ent_rag_backend pytest tests/ -v
```

### Run a specific test module

```bash
docker exec -it ent_rag_backend pytest tests/test_auth.py -v
```

### Test the RAG pipeline end-to-end

```bash
docker exec -it ent_rag_backend python tests/test_rag_pipeline.py
```

### Check API health

```bash
curl -s https://docintel.space/health | python3 -m json.tool
```

### Load testing

```bash
cd load_testing
locust -f locustfile.py --host=https://docintel.space
```

---

## Deployment

The system runs on a Contabo VPS (Ubuntu 22.04) with all services containerized in Docker.

### Production deployment

```bash
# Pull latest code
git pull origin main

# Rebuild and restart frontend only
docker compose -f deployment/docker-compose.prod.yml --env-file .env build frontend
docker compose -f deployment/docker-compose.prod.yml --env-file .env up -d frontend

# Rebuild all services
docker compose -f deployment/docker-compose.prod.yml --env-file .env up -d --build

# View logs
docker logs ent_rag_backend --tail 50 -f
docker logs ent_rag_frontend --tail 20

# Run database migrations
docker exec -it ent_rag_backend alembic upgrade head
```

### Service ports

| Service | Internal Port | External |
|---|---|---|
| Backend API | 8010 | via Nginx |
| Frontend | 3001 | via Nginx |
| PostgreSQL | 5432 | internal only |
| Qdrant | 6333 | internal only |
| Redis | 6379 | internal only |
| Celery | — | worker only |

### SSL

SSL is managed by Certbot / Let's Encrypt and renewed automatically:

```bash
certbot renew --quiet
```

---

## Security

The system is hardened across multiple layers:

| Control | Implementation |
|---|---|
| Authentication | JWT (HS256) + TOTP OTP via email, 30-day expiry |
| Password policy | bcrypt hashing, minimum 8 chars, forced rotation |
| Brute force | Lockout after 5 failures, IP-level rate limiting |
| Tenant isolation | `organization_id` scoped on every DB query and vector search |
| Encryption at rest | Fernet symmetric encryption for sensitive fields |
| File security | Malware scan + MIME type validation before storage |
| API rate limiting | Per-org (1000/hr) and per-user (100/hr) limits |
| Audit trail | Immutable log of every action with old/new values, IP, user agent |
| TLS | Let's Encrypt SSL, HTTP redirected to HTTPS |
| Secrets | No secrets in code or Docker images — all via `.env` |

To view the live security posture:

```bash
curl -H "Authorization: Bearer <token>" https://docintel.space/api/v1/security/checklist
```

---

## Conclusion

DocIntel demonstrates how a complete enterprise AI platform can be designed, built, and deployed by a single engineer working from a structured phase plan. It is not a prototype, it handles multi-tenant data isolation, AI hallucination prevention, granular RBAC, automated compliance reporting, and disaster recovery, all running in production at [docintel.space](https://docintel.space).

The architecture is built for scale: adding a new organization requires no infrastructure changes, adding a new document type requires adding a parser plugin, and the monitoring system alerts on degradation before users notice.

---
 
Live Project: [docintel.space](https://docintel.space)
