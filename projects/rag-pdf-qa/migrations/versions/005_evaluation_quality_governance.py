"""evaluation quality governance

Revision ID: 005_evaluation_quality_governance
Revises: 004_audit_logs
Create Date: 2026-06-06
"""

from alembic import op
import sqlalchemy as sa


revision = "005_evaluation_quality_governance"
down_revision = "004_audit_logs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "evaluation_cases",
        sa.Column("evaluation_case_id", sa.String(length=80), primary_key=True),
        sa.Column("dataset_name", sa.String(length=160), nullable=False),
        sa.Column("dataset_version", sa.String(length=80), nullable=False),
        sa.Column("knowledge_base_id", sa.String(length=80), nullable=True),
        sa.Column("case_id", sa.String(length=120), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("question_type", sa.String(length=80), nullable=False),
        sa.Column("expected_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.String(length=40), nullable=False),
        sa.Column("updated_at", sa.String(length=40), nullable=False),
        sa.UniqueConstraint(
            "dataset_name",
            "dataset_version",
            "knowledge_base_id",
            "case_id",
            name="uq_evaluation_cases_dataset_kb_case",
        ),
    )
    op.create_index("ix_evaluation_cases_dataset_name", "evaluation_cases", ["dataset_name"])
    op.create_index("ix_evaluation_cases_knowledge_base_id", "evaluation_cases", ["knowledge_base_id"])

    op.create_table(
        "evaluation_runs",
        sa.Column("run_id", sa.String(length=80), primary_key=True),
        sa.Column("generated_at", sa.String(length=40), nullable=False),
        sa.Column("dataset_name", sa.String(length=160), nullable=False),
        sa.Column("dataset_version", sa.String(length=80), nullable=False),
        sa.Column("knowledge_base_id", sa.String(length=80), nullable=True),
        sa.Column("collection", sa.String(length=120), nullable=False),
        sa.Column("embedding_model", sa.String(length=240), nullable=False),
        sa.Column("llm_provider", sa.String(length=80), nullable=True),
        sa.Column("llm_model", sa.String(length=240), nullable=True),
        sa.Column("limit", sa.Integer(), nullable=False),
        sa.Column("score_threshold", sa.String(length=40), nullable=True),
        sa.Column("hit_rate", sa.String(length=40), nullable=False),
        sa.Column("page_hit_rate", sa.String(length=40), nullable=False),
        sa.Column("keyword_hit_rate", sa.String(length=40), nullable=False),
        sa.Column("quality_status", sa.String(length=40), nullable=False),
        sa.Column("result_json", sa.Text(), nullable=False),
    )
    op.create_index("ix_evaluation_runs_generated_at", "evaluation_runs", ["generated_at"])
    op.create_index("ix_evaluation_runs_dataset_name", "evaluation_runs", ["dataset_name"])
    op.create_index("ix_evaluation_runs_knowledge_base_id", "evaluation_runs", ["knowledge_base_id"])
    op.create_index("ix_evaluation_runs_quality_status", "evaluation_runs", ["quality_status"])

    op.create_table(
        "answer_feedback",
        sa.Column("feedback_id", sa.String(length=80), primary_key=True),
        sa.Column("created_at", sa.String(length=40), nullable=False),
        sa.Column("request_id", sa.String(length=80), nullable=True),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("username", sa.String(length=120), nullable=False),
        sa.Column("organization_id", sa.String(length=80), nullable=False),
        sa.Column("workspace_id", sa.String(length=80), nullable=False),
        sa.Column("knowledge_base_id", sa.String(length=80), nullable=False),
        sa.Column("rating", sa.String(length=20), nullable=False),
        sa.Column("route", sa.String(length=80), nullable=True),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer_preview", sa.Text(), nullable=False),
        sa.Column("details_json", sa.Text(), nullable=True),
    )
    op.create_index("ix_answer_feedback_created_at", "answer_feedback", ["created_at"])
    op.create_index("ix_answer_feedback_request_id", "answer_feedback", ["request_id"])
    op.create_index("ix_answer_feedback_user_id", "answer_feedback", ["user_id"])
    op.create_index("ix_answer_feedback_organization_id", "answer_feedback", ["organization_id"])
    op.create_index("ix_answer_feedback_workspace_id", "answer_feedback", ["workspace_id"])
    op.create_index("ix_answer_feedback_knowledge_base_id", "answer_feedback", ["knowledge_base_id"])
    op.create_index("ix_answer_feedback_rating", "answer_feedback", ["rating"])


def downgrade() -> None:
    op.drop_index("ix_answer_feedback_rating", table_name="answer_feedback")
    op.drop_index("ix_answer_feedback_knowledge_base_id", table_name="answer_feedback")
    op.drop_index("ix_answer_feedback_workspace_id", table_name="answer_feedback")
    op.drop_index("ix_answer_feedback_organization_id", table_name="answer_feedback")
    op.drop_index("ix_answer_feedback_user_id", table_name="answer_feedback")
    op.drop_index("ix_answer_feedback_request_id", table_name="answer_feedback")
    op.drop_index("ix_answer_feedback_created_at", table_name="answer_feedback")
    op.drop_table("answer_feedback")

    op.drop_index("ix_evaluation_runs_quality_status", table_name="evaluation_runs")
    op.drop_index("ix_evaluation_runs_knowledge_base_id", table_name="evaluation_runs")
    op.drop_index("ix_evaluation_runs_dataset_name", table_name="evaluation_runs")
    op.drop_index("ix_evaluation_runs_generated_at", table_name="evaluation_runs")
    op.drop_table("evaluation_runs")

    op.drop_index("ix_evaluation_cases_knowledge_base_id", table_name="evaluation_cases")
    op.drop_index("ix_evaluation_cases_dataset_name", table_name="evaluation_cases")
    op.drop_table("evaluation_cases")
