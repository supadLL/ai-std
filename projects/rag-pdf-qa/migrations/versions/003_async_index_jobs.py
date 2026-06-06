"""async index jobs

Revision ID: 003_async_index_jobs
Revises: 002_tenant_knowledge_base_isolation
Create Date: 2026-06-06
"""

from alembic import op
import sqlalchemy as sa


revision = "003_async_index_jobs"
down_revision = "002_tenant_knowledge_base_isolation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "index_jobs",
        sa.Column("job_id", sa.String(length=80), primary_key=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("organization_id", sa.String(length=80), nullable=False),
        sa.Column("workspace_id", sa.String(length=80), nullable=False),
        sa.Column("knowledge_base_id", sa.String(length=80), nullable=False),
        sa.Column("owner_user_id", sa.String(length=64), nullable=False),
        sa.Column("filename", sa.String(length=500), nullable=False),
        sa.Column("file_path", sa.String(length=1000), nullable=False),
        sa.Column("source_file_size", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(length=128), nullable=False),
        sa.Column("chunk_size", sa.Integer(), nullable=False),
        sa.Column("overlap", sa.Integer(), nullable=False),
        sa.Column("reindex", sa.Integer(), nullable=False),
        sa.Column("enable_ocr", sa.Integer(), nullable=False),
        sa.Column("enable_image_ocr", sa.Integer(), nullable=False),
        sa.Column("ocr_language", sa.String(length=80), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.String(length=80), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("progress_message", sa.String(length=200), nullable=False),
        sa.Column("result_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.String(length=40), nullable=False),
        sa.Column("updated_at", sa.String(length=40), nullable=False),
        sa.Column("started_at", sa.String(length=40), nullable=True),
        sa.Column("finished_at", sa.String(length=40), nullable=True),
    )
    op.create_index("ix_index_jobs_status", "index_jobs", ["status"])
    op.create_index("ix_index_jobs_organization_id", "index_jobs", ["organization_id"])
    op.create_index("ix_index_jobs_workspace_id", "index_jobs", ["workspace_id"])
    op.create_index("ix_index_jobs_knowledge_base_id", "index_jobs", ["knowledge_base_id"])
    op.create_index("ix_index_jobs_owner_user_id", "index_jobs", ["owner_user_id"])
    op.create_index("ix_index_jobs_content_hash", "index_jobs", ["content_hash"])


def downgrade() -> None:
    op.drop_index("ix_index_jobs_content_hash", table_name="index_jobs")
    op.drop_index("ix_index_jobs_owner_user_id", table_name="index_jobs")
    op.drop_index("ix_index_jobs_knowledge_base_id", table_name="index_jobs")
    op.drop_index("ix_index_jobs_workspace_id", table_name="index_jobs")
    op.drop_index("ix_index_jobs_organization_id", table_name="index_jobs")
    op.drop_index("ix_index_jobs_status", table_name="index_jobs")
    op.drop_table("index_jobs")
