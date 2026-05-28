import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.approval_service import enforce_approval_gate
from app.services.ai_guard_service import (
    enforce_no_source_no_answer,
    validate_document_eligibility,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_document(
    *,
    status="approved",
    is_approved=True,
    rejection_reason=None,
    expires_at=None,
    organization_id=None,
    department_id=None,
):
    return SimpleNamespace(
        id=uuid4(),
        organization_id=organization_id or uuid4(),
        department_id=department_id,
        status=status,
        is_approved=is_approved,
        rejection_reason=rejection_reason,
        expires_at=expires_at,
    )


def _make_user(*, organization_id=None, department_id=None, role_name="USER", role_id=None):
    org_id = organization_id or uuid4()
    return SimpleNamespace(
        id=uuid4(),
        organization_id=org_id,
        department_id=department_id,
        role_id=role_id or uuid4(),
        role=SimpleNamespace(name=role_name),
    )


class _FakeDB:
    """Minimal async DB stub that returns None for all queries."""

    def __init__(self, scalar=None):
        self.added = []
        self._scalar = scalar

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        pass

    async def execute(self, query):
        return SimpleNamespace(
            scalar_one_or_none=lambda: self._scalar,
            scalars=lambda: SimpleNamespace(
                first=lambda: None,
                all=lambda: [],
            ),
        )

    async def scalar(self, query):
        return self._scalar


# ---------------------------------------------------------------------------
# enforce_approval_gate
# ---------------------------------------------------------------------------

def test_enforce_approval_gate_returns_false_for_unapproved_document():
    doc = _make_document(status="reviewed", is_approved=False)
    assert enforce_approval_gate(doc) is False


def test_enforce_approval_gate_returns_false_for_rejected_document():
    doc = _make_document(status="rejected", is_approved=False)
    assert enforce_approval_gate(doc) is False


def test_enforce_approval_gate_returns_false_for_archived_document():
    doc = _make_document(status="archived", is_approved=False)
    assert enforce_approval_gate(doc) is False


def test_enforce_approval_gate_returns_true_for_approved_document():
    doc = _make_document(status="approved", is_approved=True)
    assert enforce_approval_gate(doc) is True


def test_enforce_approval_gate_returns_false_for_expired_document():
    expired = datetime.now(timezone.utc) - timedelta(hours=1)
    doc = _make_document(status="approved", is_approved=True, expires_at=expired)
    assert enforce_approval_gate(doc) is False


def test_enforce_approval_gate_returns_true_for_non_expired_document():
    future = datetime.now(timezone.utc) + timedelta(days=30)
    doc = _make_document(status="approved", is_approved=True, expires_at=future)
    assert enforce_approval_gate(doc) is True


# ---------------------------------------------------------------------------
# approve_document / reject_document (service layer, no live DB)
# ---------------------------------------------------------------------------

def test_approve_document_sets_correct_fields():
    """approval_service.approve_document mutates the document correctly."""
    from app.services.approval_service import approve_document

    org_id = uuid4()
    user = _make_user(organization_id=org_id, role_name="ADMIN")
    doc = _make_document(status="reviewed", is_approved=False, organization_id=org_id)

    class _DBStub(_FakeDB):
        async def execute(self, query):
            return SimpleNamespace(scalar_one_or_none=lambda: doc)

    result = asyncio.run(approve_document(_DBStub(), doc.id, user, "organization"))

    assert result is doc
    assert result.status == "approved"
    assert result.is_approved is True
    assert result.approved_by == user.id
    assert result.approved_at is not None


def test_approve_document_returns_none_when_document_not_found():
    from app.services.approval_service import approve_document

    user = _make_user(role_name="ADMIN")
    result = asyncio.run(approve_document(_FakeDB(scalar=None), uuid4(), user))
    assert result is None


def test_reject_document_sets_rejected_status_and_saves_reason():
    from app.services.approval_service import reject_document

    org_id = uuid4()
    user = _make_user(organization_id=org_id, role_name="ADMIN")
    doc = _make_document(
        status="reviewed",
        is_approved=False,
        organization_id=org_id,
    )
    # patch missing fields required by reject logic
    doc.approved_by = None
    doc.approved_at = None

    class _DBStub(_FakeDB):
        async def execute(self, query):
            return SimpleNamespace(scalar_one_or_none=lambda: doc)

    reason = "Document does not meet policy standards"
    result = asyncio.run(reject_document(_DBStub(), doc.id, user, reason))

    assert result is doc
    assert result.status == "rejected"
    assert result.is_approved is False
    assert result.rejection_reason == reason


def test_reject_document_returns_none_when_document_not_found():
    from app.services.approval_service import reject_document

    user = _make_user(role_name="ADMIN")
    result = asyncio.run(reject_document(_FakeDB(scalar=None), uuid4(), user, "reason"))
    assert result is None


# ---------------------------------------------------------------------------
# versioning_service
# ---------------------------------------------------------------------------

def test_create_document_version_increments_version_number():
    from app.services.versioning_service import create_document_version

    org_id = uuid4()
    user = _make_user(organization_id=org_id, role_name="ADMIN")
    parent_id = uuid4()
    parent = _make_document(status="approved", is_approved=True, organization_id=org_id)
    parent.id = parent_id
    parent.version_number = 2
    parent.department_id = None
    parent.title = "Original"

    existing = [parent]

    class _DBStub(_FakeDB):
        async def execute(self, query):
            # first call: find parent; second call: list all versions
            return SimpleNamespace(
                scalar_one_or_none=lambda: parent,
                scalars=lambda: SimpleNamespace(all=lambda: existing),
            )

    new_doc = asyncio.run(
        create_document_version(
            db=_DBStub(),
            parent_document_id=parent_id,
            current_user=user,
            file_content=b"content",
            file_name="v2.pdf",
            title="Version 2",
            file_type="pdf",
            file_path="/tmp/v2.pdf",
        )
    )

    assert new_doc is not None
    assert new_doc.version_number == 3
    assert new_doc.parent_document_id == parent_id
    assert new_doc.status == "uploaded"
    assert new_doc.is_approved is False


def test_get_current_version_returns_latest_approved_version():
    from app.services.versioning_service import get_current_version

    org_id = uuid4()
    approved_doc = _make_document(status="approved", is_approved=True, organization_id=org_id)
    approved_doc.version_number = 3

    class _DBStub(_FakeDB):
        async def execute(self, query):
            return SimpleNamespace(scalar_one_or_none=lambda: approved_doc)

    result = asyncio.run(get_current_version(_DBStub(), uuid4(), org_id))
    assert result is approved_doc


# ---------------------------------------------------------------------------
# access_rule_service: check_user_document_access
# ---------------------------------------------------------------------------

def test_check_user_document_access_returns_false_for_restricted_document():
    """User in dept A cannot access a dept B document with no access rule."""
    from app.services.access_rule_service import check_user_document_access

    org_id = uuid4()
    dept_a = uuid4()
    dept_b = uuid4()
    user = _make_user(organization_id=org_id, department_id=dept_a)
    doc = _make_document(status="approved", is_approved=True, organization_id=org_id, department_id=dept_b)

    class _DBStub(_FakeDB):
        async def execute(self, query):
            return SimpleNamespace(
                scalars=lambda: SimpleNamespace(first=lambda: None)
            )

    result = asyncio.run(check_user_document_access(_DBStub(), user, doc))
    assert result is False


def test_check_user_document_access_returns_true_for_own_department():
    from app.services.access_rule_service import check_user_document_access

    org_id = uuid4()
    dept_id = uuid4()
    user = _make_user(organization_id=org_id, department_id=dept_id)
    doc = _make_document(status="approved", is_approved=True, organization_id=org_id, department_id=dept_id)

    result = asyncio.run(check_user_document_access(_FakeDB(), user, doc))
    assert result is True


def test_check_user_document_access_returns_true_for_org_wide_document():
    from app.services.access_rule_service import check_user_document_access

    org_id = uuid4()
    user = _make_user(organization_id=org_id)
    doc = _make_document(status="approved", is_approved=True, organization_id=org_id, department_id=None)

    result = asyncio.run(check_user_document_access(_FakeDB(), user, doc))
    assert result is True


def test_check_user_document_access_returns_false_for_cross_tenant():
    from app.services.access_rule_service import check_user_document_access

    user = _make_user(organization_id=uuid4())
    doc = _make_document(status="approved", is_approved=True, organization_id=uuid4())

    result = asyncio.run(check_user_document_access(_FakeDB(), user, doc))
    assert result is False


# ---------------------------------------------------------------------------
# AI guard: validate_document_eligibility blocks specific statuses
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bad_status", [
    "uploaded", "processing", "reviewed", "rejected", "archived", "deleted", "failed",
])
def test_ai_guard_blocks_documents_with_ineligible_status(bad_status):
    user = _make_user()
    doc = _make_document(status=bad_status, is_approved=False, organization_id=user.organization_id)

    is_eligible, reason = asyncio.run(validate_document_eligibility(_FakeDB(), user, doc))
    assert is_eligible is False
    assert reason


def test_ai_guard_blocks_unapproved_document_regardless_of_status():
    user = _make_user()
    # status field says "approved" but flag is False — gate must block
    doc = _make_document(status="approved", is_approved=False, organization_id=user.organization_id)

    is_eligible, _ = asyncio.run(validate_document_eligibility(_FakeDB(), user, doc))
    assert is_eligible is False


def test_ai_guard_service_blocks_rejected_document():
    user = _make_user()
    doc = _make_document(status="rejected", is_approved=False, organization_id=user.organization_id)

    is_eligible, reason = asyncio.run(validate_document_eligibility(_FakeDB(), user, doc))
    assert is_eligible is False


def test_ai_guard_service_blocks_archived_document():
    user = _make_user()
    doc = _make_document(status="archived", is_approved=False, organization_id=user.organization_id)

    is_eligible, reason = asyncio.run(validate_document_eligibility(_FakeDB(), user, doc))
    assert is_eligible is False


def test_enforce_no_source_no_answer_blocks_empty_sources():
    blocked, fallback = enforce_no_source_no_answer([])
    assert blocked is True
    assert fallback
