import asyncio
import io
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.security import generate_temporary_password, hash_password, verify_password
from app.services.bulk_user_service import (
    generate_bulk_upload_template,
    parse_excel_file,
    validate_bulk_user_row,
)


# ---------------------------------------------------------------------------
# Helpers / Stubs
# ---------------------------------------------------------------------------

def _make_user(**kwargs):
    defaults = dict(
        id=uuid4(),
        organization_id=uuid4(),
        department_id=None,
        role_id=None,
        first_name="Jane",
        last_name="Doe",
        email="jane@example.com",
        hashed_password=hash_password("OldPass1!"),
        is_active=True,
        is_verified=False,
        is_first_login=True,
        must_change_password=True,
        failed_login_attempts=0,
        locked_until=None,
        last_login=None,
        password_changed_at=None,
        onboarding_completed=False,
        onboarding_step=0,
        role=None,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


class FakeDB:
    """Multi-call DB stub; each call to execute() pops from the queue."""

    def __init__(self, return_values=None):
        self._queue = list(return_values or [])
        self.added = []

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        pass

    async def execute(self, query):
        if self._queue:
            val = self._queue.pop(0)
        else:
            val = None
        return SimpleNamespace(scalar_one_or_none=lambda v=val: v)

    async def scalar(self, query):
        if self._queue:
            return self._queue.pop(0)
        return 0


# ---------------------------------------------------------------------------
# Security helpers
# ---------------------------------------------------------------------------

def test_generate_temporary_password_produces_strong_password():
    from app.core.security import validate_password_strength
    pw = generate_temporary_password()
    valid, errors = validate_password_strength(pw)
    assert valid, errors
    assert len(pw) >= 12


def test_generate_temporary_password_each_call_produces_unique_value():
    passwords = {generate_temporary_password() for _ in range(10)}
    assert len(passwords) == 10


# ---------------------------------------------------------------------------
# create_user
# ---------------------------------------------------------------------------

def test_create_user_sets_is_first_login_true_and_must_change_password_true():
    from app.services.user_management_service import create_user

    org_id = uuid4()
    # DB returns: None (email check), None (dept check skipped), None (role check skipped)
    db = FakeDB(return_values=[None])

    user = asyncio.run(
        create_user(
            db=db,
            first_name="Alice",
            last_name="Smith",
            email="alice@example.com",
            organization_id=org_id,
            role_id=None,
            department_id=None,
            send_welcome_email=False,
            created_by_user_id=uuid4(),
        )
    )

    assert user.is_first_login is True
    assert user.must_change_password is True


def test_create_user_sets_is_verified_false():
    from app.services.user_management_service import create_user

    org_id = uuid4()
    db = FakeDB(return_values=[None])

    user = asyncio.run(
        create_user(
            db=db,
            first_name="Bob",
            last_name="Brown",
            email="bob@example.com",
            organization_id=org_id,
            role_id=None,
            department_id=None,
            send_welcome_email=False,
        )
    )

    assert user.is_verified is False


def test_create_user_generates_temporary_password_and_hashes_it():
    from app.services.user_management_service import create_user

    org_id = uuid4()
    db = FakeDB(return_values=[None])

    user = asyncio.run(
        create_user(
            db=db,
            first_name="Carol",
            last_name="Jones",
            email="carol@example.com",
            organization_id=org_id,
            role_id=None,
            department_id=None,
            send_welcome_email=False,
        )
    )

    assert user.hashed_password
    assert not user.hashed_password.startswith("plain:")
    # Verify the hash is a valid bcrypt-sha256 hash
    from app.core.security import pwd_context
    assert pwd_context.identify(user.hashed_password) is not None


def test_create_user_raises_conflict_when_email_already_exists():
    from app.services.user_management_service import create_user
    from fastapi import HTTPException

    org_id = uuid4()
    existing_user = _make_user(organization_id=org_id)
    db = FakeDB(return_values=[existing_user])

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            create_user(
                db=db,
                first_name="Dupe",
                last_name="User",
                email="existing@example.com",
                organization_id=org_id,
                role_id=None,
                department_id=None,
                send_welcome_email=False,
            )
        )

    assert exc_info.value.status_code == 409


# ---------------------------------------------------------------------------
# update_user
# ---------------------------------------------------------------------------

def test_update_user_cannot_change_email():
    from app.services.user_management_service import update_user

    org_id = uuid4()
    user = _make_user(organization_id=org_id, email="original@example.com")
    original_email = user.email

    db = FakeDB(return_values=[user])

    result = asyncio.run(
        update_user(
            db=db,
            user_id=user.id,
            organization_id=org_id,
            first_name="Updated",
            last_name=None,
            department_id=None,
            role_id=None,
            is_active=None,
        )
    )

    assert result.email == original_email


def test_update_user_cannot_change_organization_id():
    from app.services.user_management_service import update_user

    org_id = uuid4()
    user = _make_user(organization_id=org_id)
    original_org = user.organization_id

    db = FakeDB(return_values=[user])

    result = asyncio.run(
        update_user(
            db=db,
            user_id=user.id,
            organization_id=org_id,
            first_name="NewName",
            last_name=None,
            department_id=None,
            role_id=None,
            is_active=None,
        )
    )

    assert result.organization_id == original_org


def test_update_user_updates_first_name():
    from app.services.user_management_service import update_user

    org_id = uuid4()
    user = _make_user(organization_id=org_id)
    db = FakeDB(return_values=[user])

    result = asyncio.run(
        update_user(
            db=db,
            user_id=user.id,
            organization_id=org_id,
            first_name="NewFirstName",
            last_name=None,
            department_id=None,
            role_id=None,
            is_active=None,
        )
    )

    assert result.first_name == "NewFirstName"


# ---------------------------------------------------------------------------
# activate_user / deactivate_user
# ---------------------------------------------------------------------------

def test_activate_user_sets_is_active_true_and_clears_lockout():
    from app.services.user_management_service import activate_user
    from datetime import datetime, timedelta, timezone

    org_id = uuid4()
    user = _make_user(
        organization_id=org_id,
        is_active=False,
        failed_login_attempts=5,
        locked_until=datetime.now(timezone.utc) + timedelta(minutes=10),
    )
    db = FakeDB(return_values=[user])

    result = asyncio.run(activate_user(db, user.id, org_id))

    assert result.is_active is True
    assert result.failed_login_attempts == 0
    assert result.locked_until is None


def test_deactivate_user_sets_is_active_false():
    from app.services.user_management_service import deactivate_user

    org_id = uuid4()
    user = _make_user(organization_id=org_id, is_active=True)
    db = FakeDB(return_values=[user])

    result = asyncio.run(deactivate_user(db, user.id, org_id, reason="Policy violation"))

    assert result.is_active is False


# ---------------------------------------------------------------------------
# reset_user_password_by_admin
# ---------------------------------------------------------------------------

def test_reset_user_password_by_admin_generates_new_password():
    from app.services.user_management_service import reset_user_password_by_admin

    org_id = uuid4()
    original_hash = hash_password("OldPassword1!")
    user = _make_user(organization_id=org_id, hashed_password=original_hash)
    db = FakeDB(return_values=[user])

    result = asyncio.run(reset_user_password_by_admin(db, user.id, org_id, force_change_on_login=True))

    assert result is not None
    assert result.user_id == user.id
    assert user.hashed_password != original_hash


def test_reset_user_password_by_admin_sets_must_change_password_true():
    from app.services.user_management_service import reset_user_password_by_admin

    org_id = uuid4()
    user = _make_user(organization_id=org_id, must_change_password=False)
    db = FakeDB(return_values=[user])

    asyncio.run(reset_user_password_by_admin(db, user.id, org_id, force_change_on_login=True))

    assert user.must_change_password is True


def test_reset_user_password_returns_none_when_user_not_found():
    from app.services.user_management_service import reset_user_password_by_admin

    db = FakeDB(return_values=[None])
    result = asyncio.run(reset_user_password_by_admin(db, uuid4(), uuid4(), force_change_on_login=True))
    assert result is None


# ---------------------------------------------------------------------------
# bulk_user_service: parse_excel_file
# ---------------------------------------------------------------------------

def _make_excel_bytes(rows: list[list]) -> bytes:
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_parse_excel_file_returns_correct_rows_from_valid_excel():
    headers = ["first_name", "last_name", "email", "department_name", "role_name"]
    data_row = ["Alice", "Smith", "alice@example.com", "Engineering", "USER"]
    excel_bytes = _make_excel_bytes([headers, data_row])

    parsed, errors = parse_excel_file(excel_bytes)

    assert len(errors) == 0
    assert len(parsed) == 1
    assert parsed[0]["first_name"] == "Alice"
    assert parsed[0]["email"] == "alice@example.com"
    assert parsed[0]["role_name"] == "USER"


def test_parse_excel_file_returns_error_for_missing_columns():
    excel_bytes = _make_excel_bytes([["first_name", "last_name"]])

    parsed, errors = parse_excel_file(excel_bytes)

    assert len(errors) > 0
    assert "Missing required columns" in errors[0].error_reason


def test_parse_excel_file_skips_empty_rows():
    headers = ["first_name", "last_name", "email", "department_name", "role_name"]
    excel_bytes = _make_excel_bytes([headers, ["Alice", "Smith", "alice@test.com", "Eng", "USER"], [None, None, None, None, None]])

    parsed, errors = parse_excel_file(excel_bytes)

    assert len(errors) == 0
    assert len(parsed) == 1


# ---------------------------------------------------------------------------
# bulk_user_service: validate_bulk_user_row
# ---------------------------------------------------------------------------

def test_validate_bulk_user_row_rejects_invalid_email_format():
    row = {"first_name": "Alice", "last_name": "Smith", "email": "not-an-email", "department_name": "Eng", "role_name": "USER"}
    is_valid, reason = validate_bulk_user_row(row, seen_emails=set())
    assert is_valid is False
    assert "Invalid email" in reason


def test_validate_bulk_user_row_rejects_duplicate_email_in_file():
    email = "dup@example.com"
    row = {"first_name": "Bob", "last_name": "Brown", "email": email, "department_name": "HR", "role_name": "USER"}
    is_valid, reason = validate_bulk_user_row(row, seen_emails={email})
    assert is_valid is False
    assert "Duplicate" in reason


def test_validate_bulk_user_row_rejects_empty_first_name():
    row = {"first_name": "", "last_name": "Smith", "email": "ok@example.com", "department_name": "Eng", "role_name": "USER"}
    is_valid, reason = validate_bulk_user_row(row, seen_emails=set())
    assert is_valid is False
    assert "first_name" in reason


def test_validate_bulk_user_row_accepts_valid_row():
    row = {"first_name": "Carol", "last_name": "Jones", "email": "carol@example.com", "department_name": "Finance", "role_name": "USER"}
    is_valid, reason = validate_bulk_user_row(row, seen_emails=set())
    assert is_valid is True
    assert reason == ""


def test_generate_bulk_upload_template_returns_valid_excel_bytes():
    template_bytes = generate_bulk_upload_template()
    assert len(template_bytes) > 0
    parsed, errors = parse_excel_file(template_bytes)
    assert len(errors) == 0
