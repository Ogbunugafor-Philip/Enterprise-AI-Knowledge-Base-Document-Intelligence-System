"""
Phase 14 deployment tests — all run without live server or database connections.
"""
import asyncio
import os
import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent


# ---------------------------------------------------------------------------
# Health endpoint logic
# ---------------------------------------------------------------------------

from app.api.v1.health import _build_base_response


def test_health_build_base_response_returns_status_field():
    response = _build_base_response()
    assert "status" in response


def test_health_build_base_response_returns_ok_status():
    response = _build_base_response()
    assert response["status"] == "ok"


def test_health_build_base_response_returns_version():
    response = _build_base_response()
    assert response["version"] == "1.0.0"


def test_health_build_base_response_returns_timestamp():
    response = _build_base_response()
    assert "timestamp" in response
    assert response["timestamp"]


def test_health_build_base_response_returns_environment():
    response = _build_base_response()
    assert "environment" in response


# ---------------------------------------------------------------------------
# Environment config (frontend JS file exists and has production defaults)
# ---------------------------------------------------------------------------

ENVIRONMENT_JS = PROJECT_ROOT / "frontend" / "src" / "config" / "environment.js"


def test_environment_js_file_exists():
    assert ENVIRONMENT_JS.exists(), f"{ENVIRONMENT_JS} not found"


def test_environment_js_contains_api_base_url():
    content = ENVIRONMENT_JS.read_text()
    assert "API_BASE_URL" in content


def test_environment_js_defaults_to_production_api_url():
    content = ENVIRONMENT_JS.read_text()
    assert "https://docintel.space/api" in content


def test_environment_js_defaults_to_production_app_url():
    content = ENVIRONMENT_JS.read_text()
    assert "https://docintel.space" in content


# ---------------------------------------------------------------------------
# CORS — docintel.space must be allowed in production
# ---------------------------------------------------------------------------

from app.core import cors_config


def test_cors_allows_docintel_space_in_production(monkeypatch):
    monkeypatch.setattr(
        cors_config,
        "settings",
        SimpleNamespace(FRONTEND_URL="https://docintel.space", ENVIRONMENT="production"),
    )
    origins = cors_config.get_cors_origins()
    assert "https://docintel.space" in origins


def test_cors_blocks_unknown_origin_in_production(monkeypatch):
    monkeypatch.setattr(
        cors_config,
        "settings",
        SimpleNamespace(FRONTEND_URL="https://docintel.space", ENVIRONMENT="production"),
    )
    origins = cors_config.get_cors_origins()
    assert "https://evil.example.com" not in origins


def test_cors_never_returns_wildcard_in_production(monkeypatch):
    monkeypatch.setattr(
        cors_config,
        "settings",
        SimpleNamespace(FRONTEND_URL="https://docintel.space", ENVIRONMENT="production"),
    )
    assert "*" not in cors_config.get_cors_origins()


def test_cors_does_not_include_localhost_in_production(monkeypatch):
    monkeypatch.setattr(
        cors_config,
        "settings",
        SimpleNamespace(FRONTEND_URL="https://docintel.space", ENVIRONMENT="production"),
    )
    origins = cors_config.get_cors_origins()
    assert not any("localhost" in o for o in origins)


# ---------------------------------------------------------------------------
# SLA document
# ---------------------------------------------------------------------------

SLA_DOC = PROJECT_ROOT / "docs" / "sla_and_performance.md"


def test_sla_document_exists():
    assert SLA_DOC.exists(), f"{SLA_DOC} not found"


def test_sla_document_defines_uptime_target():
    content = SLA_DOC.read_text()
    assert "99.5%" in content


def test_sla_document_defines_rto():
    content = SLA_DOC.read_text()
    assert "RTO" in content


def test_sla_document_defines_rpo():
    content = SLA_DOC.read_text()
    assert "RPO" in content


def test_sla_document_defines_chat_response_time_under_10_seconds():
    content = SLA_DOC.read_text()
    # The SLA doc should mention an AI query target (8 seconds)
    assert "8 second" in content


# ---------------------------------------------------------------------------
# Deployment scripts exist and are executable
# ---------------------------------------------------------------------------

SCRIPTS_DIR = PROJECT_ROOT / "deployment" / "scripts"

REQUIRED_SCRIPTS = [
    "install_server.sh",
    "deploy.sh",
    "rollback.sh",
    "backup_now.sh",
    "health_check.sh",
]


@pytest.mark.parametrize("script_name", REQUIRED_SCRIPTS)
def test_deployment_script_exists(script_name):
    script_path = SCRIPTS_DIR / script_name
    assert script_path.exists(), f"{script_path} not found"


@pytest.mark.parametrize("script_name", REQUIRED_SCRIPTS)
def test_deployment_script_is_executable(script_name):
    script_path = SCRIPTS_DIR / script_name
    if script_path.exists():
        file_stat = script_path.stat()
        is_executable = bool(file_stat.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))
        assert is_executable, f"{script_path} is not executable"


# ---------------------------------------------------------------------------
# Docker Compose production file — required services present
# ---------------------------------------------------------------------------

COMPOSE_FILE = PROJECT_ROOT / "deployment" / "docker-compose.prod.yml"

REQUIRED_SERVICES = [
    "backend",
    "frontend",
    "postgres",
    "redis",
    "qdrant",
    "celery_worker",
    "celery_beat",
    "nginx",
    "certbot",
]


def test_docker_compose_prod_file_exists():
    assert COMPOSE_FILE.exists(), f"{COMPOSE_FILE} not found"


@pytest.mark.parametrize("service", REQUIRED_SERVICES)
def test_docker_compose_prod_contains_required_service(service):
    content = COMPOSE_FILE.read_text()
    assert service in content, f"Service '{service}' not found in {COMPOSE_FILE}"


def test_docker_compose_prod_defines_ent_rag_network():
    content = COMPOSE_FILE.read_text()
    assert "ent_rag_network" in content


def test_docker_compose_prod_exposes_http_and_https_ports():
    content = COMPOSE_FILE.read_text()
    assert "80:80" in content
    assert "443:443" in content


# ---------------------------------------------------------------------------
# Production checklist exists
# ---------------------------------------------------------------------------

CHECKLIST = PROJECT_ROOT / "docs" / "production_checklist.md"


def test_production_checklist_exists():
    assert CHECKLIST.exists(), f"{CHECKLIST} not found"


def test_production_checklist_references_docintel_domain():
    content = CHECKLIST.read_text()
    assert "docintel.space" in content
