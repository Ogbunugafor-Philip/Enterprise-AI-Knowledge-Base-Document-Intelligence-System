"""allow_platform_level_super_admin

Revision ID: cf2b6a9d4e10
Revises: ab083d428164
Create Date: 2026-05-28 10:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "cf2b6a9d4e10"
down_revision: Union[str, Sequence[str], None] = "ab083d428164"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PLATFORM_SCOPED_TABLES = (
    "audit_logs",
    "otp_verifications",
    "password_history",
    "permissions",
    "role_permissions",
    "roles",
    "user_roles",
    "users",
)


def upgrade() -> None:
    """Allow platform-level super admin records with organization_id NULL."""
    for table_name in PLATFORM_SCOPED_TABLES:
        op.alter_column(
            table_name,
            "organization_id",
            existing_type=sa.UUID(),
            nullable=True,
        )


def downgrade() -> None:
    """Restore strict non-null organization_id for tenant-scoped records."""
    for table_name in PLATFORM_SCOPED_TABLES:
        op.alter_column(
            table_name,
            "organization_id",
            existing_type=sa.UUID(),
            nullable=False,
        )
