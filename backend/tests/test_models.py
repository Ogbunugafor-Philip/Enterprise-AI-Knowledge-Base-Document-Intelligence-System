from sqlalchemy import inspect

from app.core.database import Base
from app.models import (
    AuditLog,
    ChatSession,
    Department,
    Document,
    DocumentAccess,
    DocumentChunk,
    IncidentReport,
    Message,
    MonitoringLog,
    OTPVerification,
    Organization,
    PasswordHistory,
    Permission,
    Role,
    RolePermission,
    SystemAlert,
    User,
    UserRole,
)


ALL_MODELS = [
    Organization,
    Department,
    Role,
    Permission,
    RolePermission,
    UserRole,
    User,
    Document,
    DocumentChunk,
    DocumentAccess,
    ChatSession,
    Message,
    AuditLog,
    OTPVerification,
    PasswordHistory,
    MonitoringLog,
    SystemAlert,
    IncidentReport,
]


PLATFORM_SCOPED_MODELS = {
    AuditLog,
    OTPVerification,
    PasswordHistory,
    Permission,
    Role,
    RolePermission,
    User,
    UserRole,
}
TENANT_SCOPED_MODELS = [model for model in ALL_MODELS if model is not Organization]


def test_all_models_import_and_register_with_metadata():
    registered_tables = set(Base.metadata.tables)
    expected_tables = {model.__tablename__ for model in ALL_MODELS}

    assert expected_tables.issubset(registered_tables)


def test_tenant_scoped_models_have_organization_id():
    for model in TENANT_SCOPED_MODELS:
        assert "organization_id" in model.__table__.columns, model.__name__
        if model not in PLATFORM_SCOPED_MODELS:
            assert not model.__table__.columns["organization_id"].nullable, model.__name__


def test_core_relationships_are_defined():
    assert "organization" in inspect(Department).relationships
    assert "organization" in inspect(User).relationships
    assert "department" in inspect(User).relationships
    assert "role" in inspect(User).relationships
    assert "organization" in inspect(Role).relationships
    assert "role_permissions" in inspect(Role).relationships
    assert "permission" in inspect(RolePermission).relationships
    assert "uploader" in inspect(Document).relationships
    assert "approver" in inspect(Document).relationships
    assert "chunks" in inspect(Document).relationships
    assert "document" in inspect(DocumentChunk).relationships
    assert "access_rules" in inspect(Document).relationships
    assert "user" in inspect(ChatSession).relationships
    assert "messages" in inspect(ChatSession).relationships
    assert "session" in inspect(Message).relationships


def test_foreign_key_relationship_columns_exist():
    assert Department.__table__.columns["organization_id"].foreign_keys
    assert User.__table__.columns["organization_id"].foreign_keys
    assert User.__table__.columns["department_id"].foreign_keys
    assert User.__table__.columns["role_id"].foreign_keys
    assert Document.__table__.columns["uploaded_by"].foreign_keys
    assert Document.__table__.columns["approved_by"].foreign_keys
    assert DocumentChunk.__table__.columns["document_id"].foreign_keys
    assert RolePermission.__table__.columns["role_id"].foreign_keys
    assert RolePermission.__table__.columns["permission_id"].foreign_keys
    assert UserRole.__table__.columns["user_id"].foreign_keys
    assert UserRole.__table__.columns["role_id"].foreign_keys
