"""knowledge base snapshots

Revision ID: 007_knowledge_base_snapshots
Revises: 006_source_file_storage
Create Date: 2026-06-07
"""

from alembic import op
import sqlalchemy as sa


revision = "007_knowledge_base_snapshots"
down_revision = "006_source_file_storage"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "knowledge_base_snapshots",
        sa.Column("snapshot_id", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.String(length=40), nullable=False),
        sa.Column("created_by_user_id", sa.String(length=64), nullable=False),
        sa.Column("organization_id", sa.String(length=80), nullable=False),
        sa.Column("workspace_id", sa.String(length=80), nullable=False),
        sa.Column("knowledge_base_id", sa.String(length=80), nullable=False),
        sa.Column("reason", sa.String(length=240), nullable=True),
        sa.Column("document_count", sa.Integer(), nullable=False),
        sa.Column("indexed_chunk_count", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(length=128), nullable=False),
        sa.Column("documents_json", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("snapshot_id"),
    )
    op.create_index(
        "ix_knowledge_base_snapshots_created_at",
        "knowledge_base_snapshots",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_knowledge_base_snapshots_created_by_user_id",
        "knowledge_base_snapshots",
        ["created_by_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_knowledge_base_snapshots_organization_id",
        "knowledge_base_snapshots",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        "ix_knowledge_base_snapshots_workspace_id",
        "knowledge_base_snapshots",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        "ix_knowledge_base_snapshots_knowledge_base_id",
        "knowledge_base_snapshots",
        ["knowledge_base_id"],
        unique=False,
    )
    op.create_index(
        "ix_knowledge_base_snapshots_content_hash",
        "knowledge_base_snapshots",
        ["content_hash"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_knowledge_base_snapshots_content_hash", table_name="knowledge_base_snapshots")
    op.drop_index("ix_knowledge_base_snapshots_knowledge_base_id", table_name="knowledge_base_snapshots")
    op.drop_index("ix_knowledge_base_snapshots_workspace_id", table_name="knowledge_base_snapshots")
    op.drop_index("ix_knowledge_base_snapshots_organization_id", table_name="knowledge_base_snapshots")
    op.drop_index("ix_knowledge_base_snapshots_created_by_user_id", table_name="knowledge_base_snapshots")
    op.drop_index("ix_knowledge_base_snapshots_created_at", table_name="knowledge_base_snapshots")
    op.drop_table("knowledge_base_snapshots")
