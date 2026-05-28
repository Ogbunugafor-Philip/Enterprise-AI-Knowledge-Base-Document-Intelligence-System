from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.deps import verify_own_resource
from app.core.data_isolation import IsolationViolationError, TenantScope
from app.core.permissions import PermissionEnum, RoleEnum, has_permission
from app.services.rbac_service import check_chat_isolation


def test_user_role_has_chat_ask_question_permission():
    assert has_permission(RoleEnum.USER, PermissionEnum.CHAT_ASK_QUESTION)


def test_user_role_does_not_have_document_approve_permission():
    assert not has_permission(RoleEnum.USER, PermissionEnum.DOCUMENT_APPROVE)


def test_admin_role_has_document_approve_permission():
    assert has_permission(RoleEnum.ADMIN, PermissionEnum.DOCUMENT_APPROVE)


def test_admin_role_does_not_have_system_governance_permission():
    assert not has_permission(RoleEnum.ADMIN, PermissionEnum.SYSTEM_GOVERNANCE)


def test_super_admin_role_has_all_permissions():
    for permission in PermissionEnum:
        assert has_permission(RoleEnum.SUPER_ADMIN, permission)


def test_has_permission_returns_correct_results_for_each_role():
    assert has_permission("USER", PermissionEnum.DOCUMENT_VIEW)
    assert has_permission("ADMIN", PermissionEnum.AUDIT_LOG_VIEW)
    assert has_permission("SUPER_ADMIN", PermissionEnum.SUPER_ADMIN_ONLY)
    assert not has_permission("USER", PermissionEnum.USER_MANAGE)
    assert not has_permission(None, PermissionEnum.DOCUMENT_VIEW)


def test_verify_own_resource_blocks_user_from_accessing_another_users_resource():
    with pytest.raises(HTTPException) as exc:
        verify_own_resource(uuid4(), uuid4(), RoleEnum.USER)

    assert exc.value.status_code == 403


def test_verify_own_resource_allows_admin_to_access_org_scoped_resource():
    verify_own_resource(uuid4(), uuid4(), RoleEnum.ADMIN)


def test_check_chat_isolation_blocks_user_from_accessing_another_users_chat():
    org_id = uuid4()
    user = SimpleNamespace(
        id=uuid4(),
        organization_id=org_id,
        role=SimpleNamespace(name=RoleEnum.USER),
    )
    session = SimpleNamespace(user_id=uuid4(), organization_id=org_id)

    assert not check_chat_isolation(user, session)


def test_tenant_scope_raises_isolation_violation_on_cross_tenant_query_attempt():
    scope = TenantScope(organization_id=uuid4(), user_id=uuid4(), role=RoleEnum.ADMIN)

    with pytest.raises(IsolationViolationError):
        scope.assert_same_tenant(uuid4())
