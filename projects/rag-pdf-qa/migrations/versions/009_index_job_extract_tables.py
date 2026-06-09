"""index job extract tables option

Revision ID: 009_index_job_extract_tables
Revises: 008_answer_quality_judgements
Create Date: 2026-06-07
"""

from alembic import op
import sqlalchemy as sa


revision = "009_index_job_extract_tables"
down_revision = "008_answer_quality_judgements"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "index_jobs",
        sa.Column("extract_tables", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("index_jobs", "extract_tables")
