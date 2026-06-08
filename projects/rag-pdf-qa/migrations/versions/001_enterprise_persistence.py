"""enterprise persistence tables

Revision ID: 001_enterprise_persistence
Revises:
Create Date: 2026-06-06
"""

from alembic import op
import sqlalchemy as sa


revision = "001_enterprise_persistence"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("user_id", sa.String(length=64), primary_key=True),
        sa.Column("username", sa.String(length=120), nullable=False),
        sa.Column("username_normalized", sa.String(length=120), nullable=False),
        sa.Column("role", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(length=40), nullable=False),
    )
    op.create_index("ix_users_username_normalized", "users", ["username_normalized"], unique=True)

    op.create_table(
        "documents",
        sa.Column("document_id", sa.String(length=80), primary_key=True),
        sa.Column("filename", sa.String(length=500), nullable=False),
        sa.Column("file_type", sa.String(length=40), nullable=False),
        sa.Column("content_hash", sa.String(length=128), nullable=False),
        sa.Column("content_hash_prefix", sa.String(length=32), nullable=False),
        sa.Column("chunk_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.String(length=40), nullable=False),
        sa.Column("indexed_at", sa.String(length=40), nullable=False),
        sa.Column("source_file_size", sa.Integer(), nullable=False),
        sa.Column("collection", sa.String(length=120), nullable=False),
        sa.Column("chunk_size", sa.Integer(), nullable=False),
        sa.Column("overlap", sa.Integer(), nullable=False),
        sa.Column("embedding_model", sa.String(length=240), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=False),
        sa.Column("indexed_count", sa.Integer(), nullable=False),
    )
    op.create_index("ix_documents_content_hash", "documents", ["content_hash"], unique=True)

    op.create_table(
        "runtime_settings",
        sa.Column("key", sa.String(length=120), primary_key=True),
        sa.Column("value", sa.Text(), nullable=False),
    )

    op.create_table(
        "llm_profiles",
        sa.Column("profile_id", sa.String(length=80), primary_key=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("base_url", sa.String(length=600), nullable=False),
        sa.Column("model", sa.String(length=240), nullable=False),
        sa.Column("api_key", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("llm_profiles")
    op.drop_table("runtime_settings")
    op.drop_index("ix_documents_content_hash", table_name="documents")
    op.drop_table("documents")
    op.drop_index("ix_users_username_normalized", table_name="users")
    op.drop_table("users")
