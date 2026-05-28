import asyncio
import getpass
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sqlalchemy import select

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import hash_password, validate_password_strength
from app.models.audit import AuditLog
from app.models.auth import PasswordHistory
from app.models.role import Permission, Role, RolePermission, UserRole
from app.models.user import User

SUPER_ADMIN_ROLE = "SUPER_ADMIN"


async def super_admin_exists(db) -> bool:
    result = await db.execute(
        select(User)
        .join(Role, User.role_id == Role.id)
        .where(Role.name == SUPER_ADMIN_ROLE, Role.organization_id.is_(None))
        .limit(1)
    )
    return result.scalar_one_or_none() is not None


async def get_or_create_super_admin_role(db) -> Role:
    result = await db.execute(
        select(Role).where(Role.name == SUPER_ADMIN_ROLE, Role.organization_id.is_(None))
    )
    role = result.scalar_one_or_none()
    if role is not None:
        return role

    role = Role(
        organization_id=None,
        name=SUPER_ADMIN_ROLE,
        description="Platform-level administrator with full system permissions",
        is_system_role=True,
    )
    permission = Permission(
        organization_id=None,
        name="Full system access",
        description="Allows every platform-level action",
        resource="*",
        action="*",
    )
    db.add_all([role, permission])
    await db.flush()
    db.add(RolePermission(organization_id=None, role_id=role.id, permission_id=permission.id))
    await db.flush()
    return role


def prompt_password() -> str:
    while True:
        password = getpass.getpass("Super Admin password: ")
        confirm_password = getpass.getpass("Confirm Super Admin password: ")
        if password != confirm_password:
            print("Passwords do not match.")
            continue
        valid, errors = validate_password_strength(password)
        if not valid:
            print("Password does not meet policy:")
            for error in errors:
                print(f"- {error}")
            continue
        return password


async def main() -> None:
    print(f"Connecting to PostgreSQL at {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")
    async with SessionLocal() as db:
        if await super_admin_exists(db):
            print("Super Admin already exists. No changes made.")
            return

        first_name = input("Super Admin first name: ").strip()
        last_name = input("Super Admin last name: ").strip()
        email = input("Super Admin email: ").strip().lower()
        password = prompt_password()

        duplicate_result = await db.execute(
            select(User).where(User.email == email, User.organization_id.is_(None)).limit(1)
        )
        if duplicate_result.scalar_one_or_none() is not None:
            print("A platform-level Super Admin with this email already exists. No changes made.")
            return

        role = await get_or_create_super_admin_role(db)
        created_at = datetime.now(timezone.utc)
        user = User(
            organization_id=None,
            department_id=None,
            role_id=role.id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            hashed_password=hash_password(password),
            is_active=True,
            is_verified=True,
            is_first_login=False,
            must_change_password=False,
            failed_login_attempts=0,
            password_changed_at=created_at,
        )
        db.add(user)
        await db.flush()
        db.add(UserRole(organization_id=None, user_id=user.id, role_id=role.id, assigned_by=None))
        db.add(PasswordHistory(organization_id=None, user_id=user.id, hashed_password=user.hashed_password))
        db.add(
            AuditLog(
                organization_id=None,
                user_id=user.id,
                action="SUPER_ADMIN_CREATED",
                resource_type="setup",
                resource_id=str(user.id),
                status="success",
                new_value={"email": email, "role": SUPER_ADMIN_ROLE},
            )
        )
        await db.commit()

    print(f"Super Admin created successfully: {email}")


if __name__ == "__main__":
    asyncio.run(main())
