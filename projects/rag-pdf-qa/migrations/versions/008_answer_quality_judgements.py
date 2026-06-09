"""answer quality judgements

Revision ID: 008_answer_quality_judgements
Revises: 007_knowledge_base_snapshots
Create Date: 2026-06-07
"""

from alembic import op
import sqlalchemy as sa


revision = "008_answer_quality_judgements"
down_revision = "007_knowledge_base_snapshots"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "answer_quality_judgements",
        sa.Column("judgement_id", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.String(length=40), nullable=False),
        sa.Column("request_id", sa.String(length=80), nullable=True),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("username", sa.String(length=120), nullable=False),
        sa.Column("organization_id", sa.String(length=80), nullable=False),
        sa.Column("workspace_id", sa.String(length=80), nullable=False),
        sa.Column("knowledge_base_id", sa.String(length=80), nullable=False),
        sa.Column("route", sa.String(length=80), nullable=True),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer_preview", sa.Text(), nullable=False),
        sa.Column("sources_json", sa.Text(), nullable=True),
        sa.Column("llm_provider", sa.String(length=80), nullable=False),
        sa.Column("llm_model", sa.String(length=240), nullable=False),
        sa.Column("groundedness", sa.Integer(), nullable=False),
        sa.Column("answer_quality", sa.Integer(), nullable=False),
        sa.Column("completeness", sa.Integer(), nullable=False),
        sa.Column("risk_level", sa.String(length=20), nullable=False),
        sa.Column("verdict", sa.String(length=20), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("raw_judge_json", sa.Text(), nullable=False),
        sa.Column("usage_json", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("judgement_id"),
    )
    op.create_index("ix_answer_quality_judgements_created_at", "answer_quality_judgements", ["created_at"])
    op.create_index("ix_answer_quality_judgements_request_id", "answer_quality_judgements", ["request_id"])
    op.create_index("ix_answer_quality_judgements_user_id", "answer_quality_judgements", ["user_id"])
    op.create_index("ix_answer_quality_judgements_organization_id", "answer_quality_judgements", ["organization_id"])
    op.create_index("ix_answer_quality_judgements_workspace_id", "answer_quality_judgements", ["workspace_id"])
    op.create_index("ix_answer_quality_judgements_knowledge_base_id", "answer_quality_judgements", ["knowledge_base_id"])
    op.create_index("ix_answer_quality_judgements_risk_level", "answer_quality_judgements", ["risk_level"])
    op.create_index("ix_answer_quality_judgements_verdict", "answer_quality_judgements", ["verdict"])


def downgrade() -> None:
    op.drop_index("ix_answer_quality_judgements_verdict", table_name="answer_quality_judgements")
    op.drop_index("ix_answer_quality_judgements_risk_level", table_name="answer_quality_judgements")
    op.drop_index("ix_answer_quality_judgements_knowledge_base_id", table_name="answer_quality_judgements")
    op.drop_index("ix_answer_quality_judgements_workspace_id", table_name="answer_quality_judgements")
    op.drop_index("ix_answer_quality_judgements_organization_id", table_name="answer_quality_judgements")
    op.drop_index("ix_answer_quality_judgements_user_id", table_name="answer_quality_judgements")
    op.drop_index("ix_answer_quality_judgements_request_id", table_name="answer_quality_judgements")
    op.drop_index("ix_answer_quality_judgements_created_at", table_name="answer_quality_judgements")
    op.drop_table("answer_quality_judgements")
