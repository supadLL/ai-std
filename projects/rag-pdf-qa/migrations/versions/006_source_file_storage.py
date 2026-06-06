"""source file storage metadata

Revision ID: 006_source_file_storage
Revises: 005_evaluation_quality_governance
Create Date: 2026-06-07
"""

from alembic import op
import sqlalchemy as sa


revision = "006_source_file_storage"
down_revision = "005_evaluation_quality_governance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("source_storage_backend", sa.String(length=40), nullable=True))
    op.add_column("documents", sa.Column("source_storage_key", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("documents", "source_storage_key")
    op.drop_column("documents", "source_storage_backend")
