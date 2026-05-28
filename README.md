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

DocIntel demonstrates how a complete enterprise AI platform can be designed, built, and deployed by a single engineer working from a structured phase plan. It is not a prototype — it handles multi-tenant data isolation, AI hallucination prevention, granular RBAC, automated compliance reporting, and disaster recovery, all running in production at [docintel.space](https://docintel.space).

The architecture is built for scale: adding a new organization requires no infrastructure changes, adding a new document type requires adding a parser plugin, and the monitoring system alerts on degradation before users notice.

---

## Author

**Philip Osita Ogbunugafor**  
Full-Stack AI Systems Engineer  
Email: philiposita1041@gmail.com  
GitHub: [Ogbunugafor-Philip](https://github.com/Ogbunugafor-Philip)  
Live Project: [docintel.space](https://docintel.space)
