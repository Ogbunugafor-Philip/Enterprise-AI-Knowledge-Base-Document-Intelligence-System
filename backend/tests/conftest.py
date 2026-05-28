"""
Shared pytest fixtures for all tests.
All external dependencies (DB, Redis, Qdrant, Cerebras, SMTP) are mocked.
"""
import io
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.permissions import RoleEnum
from app.core.security import hash_password
from app.models.chat import ChatSession, Message
from app.models.document import Document
from app.models.organization import Organization
from app.models.user import User


# ---------------------------------------------------------------------------
# Helper to build a Role-like namespace
# ---------------------------------------------------------------------------

def _role_ns(name: str) -> SimpleNamespace:
    return SimpleNamespace(id=uuid4(), name=name)


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

class FakeResult:
    def __init__(self, value=None, rows=None):
        self._value = value
        self._rows = rows or []

    def scalar_one_or_none(self):
        return self._value

    def scalar_one(self):
        return self._value or 0

    def scalars(self):
        return SimpleNamespace(all=lambda: self._rows)

    def first(self):
        return self._rows[0] if self._rows else None


class FakeDB:
    """Async-compatible SQLAlchemy session stub."""

    def __init__(self, return_values=None):
        self._queue = list(return_values or [])
        self.added = []
        self.committed = False
        self.flushed = False

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        self.flushed = True

    async def commit(self):
        self.committed = True

    async def execute(self, query):
        val = self._queue.pop(0) if self._queue else None
        return FakeResult(value=val)

    async def scalar(self, query):
        return self._queue.pop(0) if self._queue else 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


@pytest.fixture
def mock_db_session():
    return FakeDB()


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_organization():
    return Organization(
        id=uuid4(),
        name="Test Corp",
        slug="test-corp",
        is_active=True,
    )


@pytest.fixture
def mock_current_user(mock_organization):
    user = SimpleNamespace(
        id=uuid4(),
        organization_id=mock_organization.id,
        first_name="Jane",
        last_name="Doe",
        email="user@testcorp.com",
        hashed_password=hash_password("UserPass1!"),
        is_active=True,
        is_verified=True,
        is_first_login=False,
        must_change_password=False,
        failed_login_attempts=0,
        locked_until=None,
        last_login=datetime.now(timezone.utc),
        password_changed_at=datetime.now(timezone.utc),
        onboarding_completed=True,
        onboarding_step=5,
        role=_role_ns(RoleEnum.USER),
        department_id=None,
    )
    return user


@pytest.fixture
def mock_admin_user(mock_organization):
    user = SimpleNamespace(
        id=uuid4(),
        organization_id=mock_organization.id,
        first_name="Admin",
        last_name="Smith",
        email="admin@testcorp.com",
        hashed_password=hash_password("AdminPass1!"),
        is_active=True,
        is_verified=True,
        is_first_login=False,
        must_change_password=False,
        failed_login_attempts=0,
        locked_until=None,
        last_login=datetime.now(timezone.utc),
        password_changed_at=datetime.now(timezone.utc),
        onboarding_completed=True,
        onboarding_step=5,
        role=_role_ns(RoleEnum.ADMIN),
        department_id=None,
    )
    return user


@pytest.fixture
def mock_superadmin_user():
    user = SimpleNamespace(
        id=uuid4(),
        organization_id=None,
        first_name="Super",
        last_name="Admin",
        email="superadmin@system.local",
        hashed_password=hash_password("SuperAdmin1!"),
        is_active=True,
        is_verified=True,
        is_first_login=False,
        must_change_password=False,
        failed_login_attempts=0,
        locked_until=None,
        last_login=datetime.now(timezone.utc),
        password_changed_at=datetime.now(timezone.utc),
        onboarding_completed=True,
        onboarding_step=5,
        role=_role_ns(RoleEnum.SUPER_ADMIN),
        department_id=None,
    )
    return user


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_document(mock_organization):
    doc = SimpleNamespace(
        id=uuid4(),
        organization_id=mock_organization.id,
        department_id=None,
        title="Employee Policy Manual",
        file_name="policy.pdf",
        file_type="application/pdf",
        file_size=102400,
        storage_path="/app/uploads/policy.pdf",
        status="approved",
        version=1,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    return doc


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_chat_session(mock_current_user, mock_organization):
    session = ChatSession(
        id=uuid4(),
        user_id=mock_current_user.id,
        organization_id=mock_organization.id,
        title="Leave Policy Questions",
    )
    return session


@pytest.fixture
def mock_message(mock_chat_session, mock_current_user, mock_organization):
    msg = Message(
        id=uuid4(),
        session_id=mock_chat_session.id,
        user_id=mock_current_user.id,
        organization_id=mock_organization.id,
        role="assistant",
        content="Your leave policy allows 20 days per year.",
        confidence_score=0.88,
        hallucination_risk=0.12,
    )
    return msg


# ---------------------------------------------------------------------------
# External service mocks
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_qdrant_client():
    client = SimpleNamespace(
        search=lambda **kw: [],
        upsert=lambda **kw: SimpleNamespace(status="completed"),
        delete=lambda **kw: None,
        get_collection=lambda name: SimpleNamespace(
            vectors_count=100,
            status="green",
            config=SimpleNamespace(
                params=SimpleNamespace(
                    vectors=SimpleNamespace(size=384)
                )
            ),
        ),
        recreate_collection=lambda **kw: None,
        create_collection=lambda **kw: None,
        create_payload_index=lambda **kw: None,
    )
    return client


@pytest.fixture
def mock_cerebras_client():
    choice = SimpleNamespace(
        message=SimpleNamespace(
            content='{"answer": "Your policy allows 20 days leave.", "sources": ["doc-001"]}'
        )
    )
    return SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=lambda **kw: SimpleNamespace(
                    choices=[choice],
                    usage=SimpleNamespace(total_tokens=120),
                )
            )
        )
    )


@pytest.fixture
def mock_email_service(monkeypatch):
    sent = []

    async def fake_send(to_email, subject, body, **kw):
        sent.append({"to": to_email, "subject": subject, "body": body})

    import app.services.auth_service as auth_svc
    monkeypatch.setattr(auth_svc, "send_email", fake_send, raising=False)
    return sent


@pytest.fixture
def mock_redis_client():
    store = {}

    async def get(key):
        return store.get(key)

    async def set(key, value, ex=None):
        store[key] = value

    async def delete(*keys):
        for k in keys:
            store.pop(k, None)

    async def keys(pattern):
        import fnmatch
        return [k for k in store if fnmatch.fnmatch(k, pattern.replace("*", "**"))]

    return SimpleNamespace(get=get, set=set, delete=delete, keys=keys, _store=store)


# ---------------------------------------------------------------------------
# Binary file fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_pdf_bytes():
    """Minimal syntactically valid PDF."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\n"
        b"xref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n"
        b"0000000058 00000 n\n0000000115 00000 n\n"
        b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%EOF"
    )


@pytest.fixture
def sample_excel_bytes():
    """Minimal in-memory Excel workbook with user upload columns."""
    try:
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["first_name", "last_name", "email", "role", "department"])
        ws.append(["Alice", "Tester", "alice@testcorp.com", "USER", "Engineering"])
        ws.append(["Bob", "Reviewer", "bob@testcorp.com", "ADMIN", "Legal"])
        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()
    except ImportError:
        return b""
