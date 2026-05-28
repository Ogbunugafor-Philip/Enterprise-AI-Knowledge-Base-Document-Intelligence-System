"""initial_schema_all_tables

Revision ID: ab083d428164
Revises: 
Create Date: 2026-05-28 09:24:32.431069

"""
from typing import Sequence, Union

from alembic import op
from app.core.database import Base
from app import models  # noqa: F401


# revision identifiers, used by Alembic.
revision: str = 'ab083d428164'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    """Downgrade schema."""
    Base.metadata.drop_all(bind=op.get_bind())
