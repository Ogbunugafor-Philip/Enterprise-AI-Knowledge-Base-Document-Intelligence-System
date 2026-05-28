"""add_user_onboarding_fields

Revision ID: e5d7c41b2a90
Revises: cf2b6a9d4e10
Create Date: 2026-05-28 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e5d7c41b2a90"
down_revision: Union[str, Sequence[str], None] = "cf2b6a9d4e10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing = {col["name"] for col in inspector.get_columns("users")}
    if "onboarding_completed" not in existing:
        op.add_column("users", sa.Column("onboarding_completed", sa.Boolean(), nullable=False, server_default=sa.false()))
    if "onboarding_step" not in existing:
        op.add_column("users", sa.Column("onboarding_step", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("users", "onboarding_step")
    op.drop_column("users", "onboarding_completed")
