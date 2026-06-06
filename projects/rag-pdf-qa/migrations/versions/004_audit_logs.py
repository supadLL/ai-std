"""audit logs

Revision ID: 004_audit_logs
Revises: 003_async_index_jobs
Create Date: 2026-06-06
"""

from alembic import op
import sqlalchemy as sa


revision = "004_audit_logs"
down_revision = "003_async_index_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("audit_log_id", sa.String(length=80), primary_key=True),
        sa.Column("created_at", sa.String(length=40), nullable=False),
        sa.Column("request_id", sa.String(length=80), nullable=True),
        sa.Column("user_id", sa.String(length=64), nullable=True),
        sa.Column("username", sa.String(length=120), nullable=True),
        sa.Column("organization_id", sa.String(length=80), nullable=True),
        sa.Column("workspace_id", sa.String(length=80), nullable=True),
        sa.Column("knowledge_base_id", sa.String(length=80), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("resource_type", sa.String(length=80), nullable=True),
        sa.Column("resource_id", sa.String(length=160), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("llm_provider", sa.String(length=80), nullable=True),
        sa.Column("llm_model", sa.String(length=240), nullable=True),
        sa.Column("usage_json", sa.Text(), nullable=True),
        sa.Column("details_json", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])
    op.create_index("ix_audit_logs_request_id", "audit_logs", ["request_id"])
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_organization_id", "audit_logs", ["organization_id"])
    op.create_index("ix_audit_logs_workspace_id", "audit_logs", ["workspace_id"])
    op.create_index("ix_audit_logs_knowledge_base_id", "audit_logs", ["knowledge_base_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_resource_id", "audit_logs", ["resource_id"])
    op.create_index("ix_audit_logs_status", "audit_logs", ["status"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_status", table_name="audit_logs")
    op.drop_index("ix_audit_logs_resource_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_index("ix_audit_logs_knowledge_base_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_workspace_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_organization_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_user_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_request_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_table("audit_logs")
