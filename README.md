# Ent_RAG — Enterprise AI Knowledge Base & Document Intelligence System

**Live URL:** https://docintel.space  
**API Docs:** https://docintel.space/docs  
**Health:** https://docintel.space/health  

---

## Overview

Ent_RAG is a production-grade, multi-tenant enterprise platform for secure document ingestion, Retrieval Augmented Generation (RAG), AI-powered chat, user management, and operational monitoring. Organisations upload and approve documents; users query them through a guarded AI chat interface with full audit trails.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, SQLAlchemy (async), Alembic, Pydantic v2 |
| Database | PostgreSQL 15 |
| Vector Store | Qdrant (per-org collections) |
| AI / LLM | Cerebras Cloud SDK, sentence-transformers (all-MiniLM-L6-v2) |
| Task Queue | Celery + Redis |
| Frontend | React 18, Vite, Tailwind CSS, React Router v6 |
| Infrastructure | Docker Compose, Nginx (reverse proxy + SSL), Let's Encrypt |
| Security | JWT auth, RBAC, OTP verification, rate limiting, SQL injection protection |

---

## 15-Phase Development Summary

| Phase | Description |
|-------|-------------|
| 1 | Project scaffold, Docker Compose, Nginx, multi-tenant architecture |
| 2 | Database models (18 models), Alembic migrations |
| 3 | JWT auth, OTP verification, password policy, account lockout |
| 4 | RBAC (3 roles, 27 permissions), strict tenant data isolation |
| 5 | User workspace: chat interface, history, onboarding, sample questions |
| 6 | Admin document pipeline: upload → malware scan → OCR → chunk → embed → Qdrant |
| 7 | Document approval workflows, versioning, access rules, governance |
| 8 | Super Admin workspace, bulk user management, organisation administration |
| 9 | RAG pipeline: vector search, Cerebras LLM, hallucination guard, confidence scoring |
| 10 | AI monitoring dashboard, intelligent alerts, debugging assistant, incident management |
| 11 | Audit logging, GDPR compliance, data retention policies, encryption at rest |
| 12 | Security hardening: rate limiting, SQL injection protection, CORS restriction, security headers |
| 13 | Automated backups, restore procedures, disaster recovery, Celery Beat scheduled tasks |
| 14 | Production Docker config, Nginx SSL for docintel.space, deployment scripts, load testing |
| 15 | Final integration tests, Redis caching, DB performance indexes, frontend optimisation |

---

## Quick Start (Local Development)

```bash
# Clone the repository
git clone https://github.com/Ogbunugafor-Philip/Enterprise-AI-Knowledge-Base-Document-Intelligence-System.git
cd Enterprise-AI-Knowledge-Base-Document-Intelligence-System

# Copy environment config
cp .env.example .env
# Edit .env with your values

# Start development stack
docker-compose -f deployment/docker-compose.yml up -d

# Run migrations
PYTHONPATH=backend .venv/bin/alembic upgrade head

# Run tests
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/ -q
```

---

## Production Deployment

See [docs/go_live_guide.md](docs/go_live_guide.md) for the complete step-by-step deployment guide.

```bash
# On the production server
cd /opt/ent_rag
git pull origin main
./deployment/scripts/deploy.sh
```

---

## Project Structure

```
Ent_RAG/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # 17 API routers
│   │   ├── core/            # Config, DB, RBAC, cache, security
│   │   ├── middleware/       # Auth, RBAC, rate limit, monitoring
│   │   ├── models/          # 18 SQLAlchemy models
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   └── services/        # 27 service modules
│   └── tests/               # 213+ tests (100% passing)
├── frontend/
│   └── src/
│       ├── pages/           # 17 React page components
│       ├── services/        # API service layer
│       └── components/      # Shared UI components
├── worker/                  # Celery tasks (6 modules)
├── deployment/
│   ├── docker-compose.prod.yml
│   ├── nginx/nginx.conf
│   └── scripts/             # 5 deployment scripts
└── docs/                    # SLA, guides, checklists
```

---

## Key Metrics

- **Tests:** 213+ passing, 0 failing
- **API Routes:** 50+
- **Frontend Pages:** 17
- **Services:** 27
- **Celery Tasks:** 6 modules, 10 scheduled jobs

---

## Documentation

- [Go-Live Guide](docs/go_live_guide.md)
- [Admin Guide](docs/admin_guide.md)
- [SLA & Performance](docs/sla_and_performance.md)
- [Production Checklist](docs/production_checklist.md)
- [Backup & Restore Guide](docs/backup_restore_guide.md)
- [Disaster Recovery](docs/disaster_recovery.md)
