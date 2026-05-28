"""phase11_compliance_fields

Revision ID: a91f3c7d8e12
Revises: f1a8c3d9b2e1
Create Date: 2026-05-28 16:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "a91f3c7d8e12"
down_revision: Union[str, Sequence[str], None] = "f1a8c3d9b2e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _existing_columns(table_name: str) -> set:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    return {col["name"] for col in inspector.get_columns(table_name)}


def _existing_indexes(table_name: str) -> set:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    return {idx["name"] for idx in inspector.get_indexes(table_name)}


def upgrade() -> None:
    users_cols = _existing_columns("users")
    if "email_encrypted" not in users_cols:
        op.add_column("users", sa.Column("email_encrypted", sa.String(length=2048), nullable=True))

    otp_cols = _existing_columns("otp_verifications")
    if "otp_code_hash" not in otp_cols:
        op.add_column("otp_verifications", sa.Column("otp_code_hash", sa.String(length=255), nullable=True))

    audit_cols = _existing_columns("audit_logs")
    if "previous_hash" not in audit_cols:
        op.add_column("audit_logs", sa.Column("previous_hash", sa.String(length=128), nullable=True))
    if "audit_hash" not in audit_cols:
        op.add_column("audit_logs", sa.Column("audit_hash", sa.String(length=128), nullable=True))

    otp_indexes = _existing_indexes("otp_verifications")
    if "ix_otp_verifications_otp_code_hash" not in otp_indexes:
        op.create_index("ix_otp_verifications_otp_code_hash", "otp_verifications", ["otp_code_hash"])

    audit_indexes = _existing_indexes("audit_logs")
    if "ix_audit_logs_previous_hash" not in audit_indexes:
        op.create_index("ix_audit_logs_previous_hash", "audit_logs", ["previous_hash"])
    if "ix_audit_logs_audit_hash" not in audit_indexes:
        op.create_index("ix_audit_logs_audit_hash", "audit_logs", ["audit_hash"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_audit_hash", table_name="audit_logs")
    op.drop_index("ix_audit_logs_previous_hash", table_name="audit_logs")
    op.drop_index("ix_otp_verifications_otp_code_hash", table_name="otp_verifications")
    op.drop_column("audit_logs", "audit_hash")
    op.drop_column("audit_logs", "previous_hash")
    op.drop_column("otp_verifications", "otp_code_hash")
    op.drop_column("users", "email_encrypted")
