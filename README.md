# Enterprise-AI-Knowledge-Base-Document-Intelligence-System
# Enterprise AI Knowledge Base & Document Intelligence System

## Ent_RAG Phase 1 Foundation

Ent_RAG is an enterprise AI knowledge base and document intelligence system designed for secure, multi-tenant document ingestion, retrieval augmented generation, user access management, and operational monitoring.

## Tech Stack

- Backend: FastAPI, SQLAlchemy, Alembic, Celery, Redis, PostgreSQL
- AI and retrieval: LangChain, Qdrant, sentence-transformers, Cerebras Cloud SDK
- Document processing: PyMuPDF, pdfplumber, python-docx, openpyxl, python-magic, clamd
- Frontend: React 18, Vite, Tailwind CSS, React Router, Axios, lucide-react
- Infrastructure: Docker, Docker Compose, Nginx, PostgreSQL 15, Redis 7, Qdrant
- Testing and quality: pytest

## Folder Structure

```text
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
```

## Local Development

1. Copy the environment template:

```bash
cp .env.example .env
```

2. Replace placeholder values in `.env` with development-safe values.

3. Start the local stack:

```bash
docker compose -f deployment/docker-compose.yml up --build
```

4. Open the services:

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- Backend health check: `http://localhost:8000/api/health`
- Qdrant: `http://localhost:6333`

## Environment Variables

`.env.example` contains placeholder-only values for database access, Qdrant, Redis, Cerebras API credentials, SMTP, JWT, encryption, service URLs, environment mode, tenant isolation, and rate limits. Do not commit real `.env` files or secret material.

## Multi-Tenancy Architecture

Ent_RAG uses strict tenant isolation. Organizations are the top-level tenant boundary, and departments, documents, users, permissions, ingestion jobs, retrieval logs, and AI access are scoped beneath them.

Every application database query must filter by `organization_id`. Every vector search must include an `organization_id` payload filter in Qdrant. This prevents cross-tenant exposure across relational data, document chunks, embeddings, retrieval context, and generated answers.

Phase 2 will expand this foundation with organization-scoped PostgreSQL schemas, document ingestion workflows, vector payload policies, audit logging, role-based access control, and tenant-level monitoring.
