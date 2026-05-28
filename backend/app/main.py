"""
Ent_RAG multi-tenant architecture foundation

Tenant isolation covers organizations, departments, documents, users, and AI
retrieval access. Every database query and vector search is scoped by
organization_id to ensure zero cross-tenant data exposure.
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.auth import router as auth_router
from app.api.v1.backup import router as backup_router
from app.api.v1.admin.access_rules import router as admin_access_rules_router
from app.api.v1.monitoring import router as monitoring_router
from app.api.v1.rag_analytics import router as rag_analytics_router
from app.api.v1.superadmin.users import router as superadmin_users_router
from app.api.v1.admin.approvals import router as admin_approvals_router
from app.api.v1.admin.documents import dashboard_router as admin_dashboard_router
from app.api.v1.admin.documents import router as admin_documents_router
from app.api.v1.admin.versions import router as admin_versions_router
from app.api.v1.chat import router as chat_router
from app.api.v1.compliance import router as compliance_router
from app.api.v1.departments import router as departments_router
from app.api.v1.roles import router as roles_router
from app.api.v1.security import router as security_router
from app.api.v1.setup import router as setup_router
from app.api.v1.users import router as users_router
from app.core.cors_config import get_cors_settings
from app.core.data_isolation import IsolationViolationError
from app.core.file_storage import ensure_upload_directory
from app.services.backup_service import ensure_backup_directories
from app.middleware.auth_middleware import JWTAuthenticationMiddleware, PasswordExpiryMiddleware
from app.middleware.monitoring_middleware import MonitoringMiddleware
from app.middleware.rate_limit_middleware import RateLimitMiddleware
from app.middleware.rbac_middleware import RBACMiddleware
from app.middleware.security_middleware import (
    RequestValidationMiddleware,
    SQLInjectionProtectionMiddleware,
    SecurityHeadersMiddleware,
)

logger = logging.getLogger("ent_rag")

api_router = APIRouter(prefix="/api")


@api_router.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "ent_rag_backend"}


@api_router.get("/v1/tenancy/status", tags=["tenancy"])
async def tenancy_status() -> dict[str, str]:
    return {
        "tenant_isolation_mode": os.getenv("TENANT_ISOLATION_MODE", "strict"),
        "scope_key": "organization_id",
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    ensure_upload_directory()
    ensure_backup_directories()
    logger.info("Starting Ent_RAG API in %s mode", os.getenv("ENVIRONMENT", "development"))
    yield
    logger.info("Stopping Ent_RAG API")


app = FastAPI(
    title="Ent_RAG API",
    description="Enterprise AI Knowledge Base and Document Intelligence System",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    **get_cors_settings(),
)

# Starlette applies middleware in reverse registration order.
app.add_middleware(JWTAuthenticationMiddleware)
app.add_middleware(RBACMiddleware)
app.add_middleware(PasswordExpiryMiddleware)
app.add_middleware(MonitoringMiddleware)
app.add_middleware(RequestValidationMiddleware)
app.add_middleware(SQLInjectionProtectionMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)


@app.get("/health", tags=["health"])
async def root_health_check() -> dict[str, str]:
    return await health_check()


app.include_router(api_router)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(setup_router, prefix="/api/v1")
app.include_router(roles_router, prefix="/api/v1")
app.include_router(departments_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(admin_documents_router, prefix="/api/v1")
app.include_router(admin_dashboard_router, prefix="/api/v1")
app.include_router(admin_approvals_router, prefix="/api/v1")
app.include_router(admin_versions_router, prefix="/api/v1")
app.include_router(admin_access_rules_router, prefix="/api/v1")
app.include_router(superadmin_users_router, prefix="/api/v1")
app.include_router(rag_analytics_router, prefix="/api/v1")
app.include_router(monitoring_router, prefix="/api/v1")
app.include_router(compliance_router, prefix="/api/v1")
app.include_router(security_router, prefix="/api/v1")
app.include_router(backup_router, prefix="/api/v1")


@app.exception_handler(IsolationViolationError)
async def isolation_violation_handler(request: Request, exc: IsolationViolationError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": exc.message})


@app.exception_handler(PermissionError)
async def permission_denied_handler(request: Request, exc: PermissionError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": str(exc) or "Permission denied"})


@app.get("/", tags=["root"])
async def root() -> dict[str, str]:
    return {"message": "Ent_RAG backend is running"}
