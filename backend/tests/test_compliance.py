import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.core.encryption import decrypt_field, encrypt_field, generate_secure_token
from app.models.audit import AuditLog
from app.models.user import User
from app.services import audit_service, compliance_service, data_privacy_service


class ScalarList:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return self.rows

    def first(self):
        return self.rows[0] if self.rows else None


class FakeResult:
    def __init__(self, rows=None, scalar=None):
        self.rows = rows or []
        self.scalar = scalar

    def scalar_one_or_none(self):
        return self.scalar

    def scalar_one(self):
        return self.scalar if self.scalar is not None else len(self.rows)

    def scalars(self):
        return ScalarList(self.rows)

    def all(self):
        return self.rows


class FakeDB:
    def __init__(self, execute_results=None):
        self.added = []
        self.flushed = 0
        self.executed = []
        self.execute_results = list(execute_results or [])

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        self.flushed += 1
        for obj in self.added:
            if getattr(obj, "id", None) is None:
                obj.id = uuid4()
            if getattr(obj, "created_at", None) is None:
                obj.created_at = datetime.now(timezone.utc)

    async def execute(self, statement):
        self.executed.append(statement)
        if self.execute_results:
            return self.execute_results.pop(0)
        return FakeResult([])


def _user(role_name="ADMIN", organization_id=None):
    return SimpleNamespace(
        id=uuid4(),
        organization_id=organization_id or uuid4(),
        role=SimpleNamespace(name=role_name),
    )


def test_audit_service_log_action_saves_correct_action_and_resource_fields():
    db = FakeDB([FakeResult(scalar=None)])
    org_id = uuid4()
    user_id = uuid4()

    asyncio.run(
        audit_service.log_action(
            db,
            user_id=user_id,
            organization_id=org_id,
            action="TEST_ACTION",
            resource_type="document",
            resource_id="doc-1",
            status="success",
        )
    )

    log = db.added[0]
    assert log.action == "TEST_ACTION"
    assert log.resource_type == "document"
    assert log.resource_id == "doc-1"
    assert log.organization_id == org_id
    assert log.user_id == user_id


def test_audit_service_log_action_never_raises_exceptions_on_failure():
    class BrokenDB:
        async def execute(self, statement):
            raise RuntimeError("db down")

        def add(self, obj):
            raise RuntimeError("db down")

    asyncio.run(
        audit_service.log_action(
            BrokenDB(),
            user_id=uuid4(),
            organization_id=uuid4(),
            action="WILL_NOT_RAISE",
            resource_type="test",
        )
    )


def test_audit_service_user_role_cannot_access_audit_logs():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(audit_service.get_audit_logs(FakeDB(), _user("USER")))

    assert exc.value.status_code == 403


def test_data_privacy_service_anonymize_user_data_replaces_personal_data_correctly():
    org_id = uuid4()
    user_id = uuid4()
    user = User(
        id=user_id,
        organization_id=org_id,
        first_name="Jane",
        last_name="Doe",
        email="jane@example.com",
        hashed_password="hashed",
    )
    db = FakeDB([FakeResult(scalar=user), FakeResult(scalar=None)])

    result = asyncio.run(data_privacy_service.anonymize_user_data(db, user_id, org_id))

    assert result.email == f"ANONYMIZED_USER_{user_id}"
    assert result.first_name == "Anonymized"
    assert result.last_name == "User"


def test_data_privacy_service_mask_sensitive_field_masks_email_correctly():
    assert data_privacy_service.mask_sensitive_field("jane@example.com") == "j***@example.com"


def test_data_privacy_service_mask_sensitive_field_masks_phone_correctly():
    assert data_privacy_service.mask_sensitive_field("555-123-1234") == "***-***-1234"


def test_encryption_encrypt_field_returns_different_value_from_input():
    encrypted = encrypt_field("secret@example.com")

    assert encrypted != "secret@example.com"


def test_encryption_decrypt_field_returns_original_value_after_encryption():
    encrypted = encrypt_field("secret@example.com")

    assert decrypt_field(encrypted) == "secret@example.com"


def test_encryption_generate_secure_token_returns_string_of_correct_length():
    token = generate_secure_token(32)

    assert isinstance(token, str)
    assert len(token) >= 32


def test_compliance_service_generate_activity_report_returns_correct_structure():
    logs = [
        AuditLog(
            id=uuid4(),
            organization_id=uuid4(),
            user_id=uuid4(),
            action="LOGIN_SUCCESS",
            resource_type="auth",
            resource_id=None,
            status="success",
            created_at=datetime.now(timezone.utc),
        )
    ]
    db = FakeDB([FakeResult(rows=logs)])

    report = asyncio.run(compliance_service.generate_activity_report(db, logs[0].organization_id))

    assert report["total_actions"] == 1
    assert "actions_by_type" in report
    assert "login_history" in report


def test_audit_log_retention_respects_configured_retention_days():
    old_id = uuid4()
    db = FakeDB([FakeResult(rows=[old_id]), FakeResult()])

    deleted = asyncio.run(data_privacy_service.apply_audit_log_retention(db, uuid4(), retention_days=1))

    assert deleted == 1
    assert len(db.executed) >= 2
