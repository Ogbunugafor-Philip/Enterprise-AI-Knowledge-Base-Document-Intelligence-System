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
from app.api.v1.departments import router as departments_router
from app.api.v1.roles import router as roles_router
from app.api.v1.setup import router as setup_router
from app.core.data_isolation import IsolationViolationError
from app.middleware.auth_middleware import JWTAuthenticationMiddleware, PasswordExpiryMiddleware
from app.middleware.rbac_middleware import RBACMiddleware

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
    logger.info("Starting Ent_RAG API in %s mode", os.getenv("ENVIRONMENT", "development"))
    yield
    logger.info("Stopping Ent_RAG API")


app = FastAPI(
    title="Ent_RAG API",
    description="Enterprise AI Knowledge Base and Document Intelligence System",
    version="0.1.0",
    lifespan=lifespan,
)

frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
allowed_origins = [
    frontend_url,
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(PasswordExpiryMiddleware)
app.add_middleware(RBACMiddleware)
app.add_middleware(JWTAuthenticationMiddleware)

app.include_router(api_router)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(setup_router, prefix="/api/v1")
app.include_router(roles_router, prefix="/api/v1")
app.include_router(departments_router, prefix="/api/v1")


@app.exception_handler(IsolationViolationError)
async def isolation_violation_handler(request: Request, exc: IsolationViolationError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": exc.message})


@app.exception_handler(PermissionError)
async def permission_denied_handler(request: Request, exc: PermissionError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": str(exc) or "Permission denied"})


@app.get("/", tags=["root"])
async def root() -> dict[str, str]:
    return {"message": "Ent_RAG backend is running"}
