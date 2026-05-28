"""add_performance_indexes

Revision ID: d90a2d156efb
Revises: a91f3c7d8e12
Create Date: 2026-05-28 17:08:33.248671

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd90a2d156efb'
down_revision: Union[str, Sequence[str], None] = 'a91f3c7d8e12'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # users
    op.create_index("ix_users_email",           "users", ["email"],           unique=True, if_not_exists=True)
    op.create_index("ix_users_organization_id", "users", ["organization_id"], if_not_exists=True)
    op.create_index("ix_users_is_active",       "users", ["is_active"],       if_not_exists=True)
    op.create_index("ix_users_role_id",         "users", ["role_id"],         if_not_exists=True)

    # documents
    op.create_index("ix_documents_organization_id", "documents", ["organization_id"], if_not_exists=True)
    op.create_index("ix_documents_status",          "documents", ["status"],          if_not_exists=True)
    op.create_index("ix_documents_department_id",   "documents", ["department_id"],   if_not_exists=True)
    op.create_index("ix_documents_created_at",      "documents", ["created_at"],      if_not_exists=True)

    # document_chunks
    op.create_index("ix_document_chunks_document_id",     "document_chunks", ["document_id"],     if_not_exists=True)
    op.create_index("ix_document_chunks_organization_id", "document_chunks", ["organization_id"], if_not_exists=True)

    # messages
    op.create_index("ix_messages_session_id",      "messages", ["session_id"],      if_not_exists=True)
    op.create_index("ix_messages_user_id",         "messages", ["user_id"],         if_not_exists=True)
    op.create_index("ix_messages_organization_id", "messages", ["organization_id"], if_not_exists=True)
    op.create_index("ix_messages_created_at",      "messages", ["created_at"],      if_not_exists=True)

    # audit_logs
    op.create_index("ix_audit_logs_organization_id", "audit_logs", ["organization_id"], if_not_exists=True)
    op.create_index("ix_audit_logs_user_id",         "audit_logs", ["user_id"],         if_not_exists=True)
    op.create_index("ix_audit_logs_action",          "audit_logs", ["action"],          if_not_exists=True)
    op.create_index("ix_audit_logs_created_at",      "audit_logs", ["created_at"],      if_not_exists=True)

    # monitoring_logs
    op.create_index("ix_monitoring_logs_organization_id", "monitoring_logs", ["organization_id"], if_not_exists=True)
    op.create_index("ix_monitoring_logs_event_type",      "monitoring_logs", ["event_type"],      if_not_exists=True)
    op.create_index("ix_monitoring_logs_created_at",      "monitoring_logs", ["created_at"],      if_not_exists=True)

    # chat_sessions
    op.create_index("ix_chat_sessions_user_id",         "chat_sessions", ["user_id"],         if_not_exists=True)
    op.create_index("ix_chat_sessions_organization_id", "chat_sessions", ["organization_id"], if_not_exists=True)
    op.create_index("ix_chat_sessions_created_at",      "chat_sessions", ["created_at"],      if_not_exists=True)


def downgrade() -> None:
    op.drop_index("ix_chat_sessions_created_at",      "chat_sessions",   if_exists=True)
    op.drop_index("ix_chat_sessions_organization_id", "chat_sessions",   if_exists=True)
    op.drop_index("ix_chat_sessions_user_id",         "chat_sessions",   if_exists=True)

    op.drop_index("ix_monitoring_logs_created_at",      "monitoring_logs", if_exists=True)
    op.drop_index("ix_monitoring_logs_event_type",      "monitoring_logs", if_exists=True)
    op.drop_index("ix_monitoring_logs_organization_id", "monitoring_logs", if_exists=True)

    op.drop_index("ix_audit_logs_created_at",      "audit_logs", if_exists=True)
    op.drop_index("ix_audit_logs_action",          "audit_logs", if_exists=True)
    op.drop_index("ix_audit_logs_user_id",         "audit_logs", if_exists=True)
    op.drop_index("ix_audit_logs_organization_id", "audit_logs", if_exists=True)

    op.drop_index("ix_messages_created_at",      "messages", if_exists=True)
    op.drop_index("ix_messages_organization_id", "messages", if_exists=True)
    op.drop_index("ix_messages_user_id",         "messages", if_exists=True)
    op.drop_index("ix_messages_session_id",      "messages", if_exists=True)

    op.drop_index("ix_document_chunks_organization_id", "document_chunks", if_exists=True)
    op.drop_index("ix_document_chunks_document_id",     "document_chunks", if_exists=True)

    op.drop_index("ix_documents_created_at",      "documents", if_exists=True)
    op.drop_index("ix_documents_department_id",   "documents", if_exists=True)
    op.drop_index("ix_documents_status",          "documents", if_exists=True)
    op.drop_index("ix_documents_organization_id", "documents", if_exists=True)

    op.drop_index("ix_users_role_id",         "users", if_exists=True)
    op.drop_index("ix_users_is_active",       "users", if_exists=True)
    op.drop_index("ix_users_organization_id", "users", if_exists=True)
    op.drop_index("ix_users_email",           "users", if_exists=True)
