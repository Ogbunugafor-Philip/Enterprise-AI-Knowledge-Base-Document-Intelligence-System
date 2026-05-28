"""extend_document_status_phase6

Revision ID: f1a8c3d9b2e1
Revises: e5d7c41b2a90
Create Date: 2026-05-28 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "f1a8c3d9b2e1"
down_revision: Union[str, Sequence[str], None] = "e5d7c41b2a90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE document_status ADD VALUE IF NOT EXISTS 'failed'")
    op.execute("ALTER TYPE document_status ADD VALUE IF NOT EXISTS 'deleted'")
    op.execute("ALTER TYPE document_status ADD VALUE IF NOT EXISTS 'expired'")


def downgrade() -> None:
    pass
