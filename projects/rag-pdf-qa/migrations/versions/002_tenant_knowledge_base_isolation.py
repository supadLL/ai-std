"""tenant and knowledge base isolation

Revision ID: 002_tenant_knowledge_base_isolation
Revises: 001_enterprise_persistence
Create Date: 2026-06-06
"""

from alembic import op
import sqlalchemy as sa


revision = "002_tenant_knowledge_base_isolation"
down_revision = "001_enterprise_persistence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("organization_id", sa.String(length=80), primary_key=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("created_at", sa.String(length=40), nullable=False),
    )
    op.create_index("ix_organizations_slug", "organizations", ["slug"], unique=True)

    op.create_table(
        "workspaces",
        sa.Column("workspace_id", sa.String(length=80), primary_key=True),
        sa.Column("organization_id", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("created_at", sa.String(length=40), nullable=False),
        sa.UniqueConstraint("organization_id", "slug", name="uq_workspaces_org_slug"),
    )
    op.create_index("ix_workspaces_organization_id", "workspaces", ["organization_id"])

    op.create_table(
        "knowledge_bases",
        sa.Column("knowledge_base_id", sa.String(length=80), primary_key=True),
        sa.Column("organization_id", sa.String(length=80), nullable=False),
        sa.Column("workspace_id", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("slug", sa.String(length=180), nullable=False),
        sa.Column("created_by_user_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.String(length=40), nullable=False),
        sa.UniqueConstraint("workspace_id", "slug", name="uq_knowledge_bases_workspace_slug"),
    )
    op.create_index("ix_knowledge_bases_organization_id", "knowledge_bases", ["organization_id"])
    op.create_index("ix_knowledge_bases_workspace_id", "knowledge_bases", ["workspace_id"])

    op.create_table(
        "knowledge_base_memberships",
        sa.Column("membership_id", sa.String(length=80), primary_key=True),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("organization_id", sa.String(length=80), nullable=False),
        sa.Column("workspace_id", sa.String(length=80), nullable=False),
        sa.Column("knowledge_base_id", sa.String(length=80), nullable=False),
        sa.Column("role", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.String(length=40), nullable=False),
        sa.UniqueConstraint("user_id", "knowledge_base_id", name="uq_kb_memberships_user_kb"),
    )
    op.create_index("ix_knowledge_base_memberships_user_id", "knowledge_base_memberships", ["user_id"])
    op.create_index(
        "ix_knowledge_base_memberships_knowledge_base_id",
        "knowledge_base_memberships",
        ["knowledge_base_id"],
    )

    op.add_column(
        "documents",
        sa.Column("organization_id", sa.String(length=80), nullable=False, server_default="org_default"),
    )
    op.add_column(
        "documents",
        sa.Column("workspace_id", sa.String(length=80), nullable=False, server_default="ws_default"),
    )
    op.add_column(
        "documents",
        sa.Column("knowledge_base_id", sa.String(length=80), nullable=False, server_default="kb_default"),
    )
    op.add_column(
        "documents",
        sa.Column("owner_user_id", sa.String(length=64), nullable=False, server_default="system"),
    )
    op.create_index("ix_documents_organization_id", "documents", ["organization_id"])
    op.create_index("ix_documents_workspace_id", "documents", ["workspace_id"])
    op.create_index("ix_documents_knowledge_base_id", "documents", ["knowledge_base_id"])
    op.create_index("ix_documents_owner_user_id", "documents", ["owner_user_id"])
    op.drop_index("ix_documents_content_hash", table_name="documents")
    op.create_index("ix_documents_content_hash", "documents", ["content_hash"])
    op.create_index(
        "uq_documents_kb_content_hash",
        "documents",
        ["knowledge_base_id", "content_hash"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_documents_kb_content_hash", table_name="documents")
    op.drop_index("ix_documents_content_hash", table_name="documents")
    op.create_index("ix_documents_content_hash", "documents", ["content_hash"], unique=True)
    op.drop_index("ix_documents_owner_user_id", table_name="documents")
    op.drop_index("ix_documents_knowledge_base_id", table_name="documents")
    op.drop_index("ix_documents_workspace_id", table_name="documents")
    op.drop_index("ix_documents_organization_id", table_name="documents")
    op.drop_column("documents", "owner_user_id")
    op.drop_column("documents", "knowledge_base_id")
    op.drop_column("documents", "workspace_id")
    op.drop_column("documents", "organization_id")
    op.drop_index("ix_knowledge_base_memberships_knowledge_base_id", table_name="knowledge_base_memberships")
    op.drop_index("ix_knowledge_base_memberships_user_id", table_name="knowledge_base_memberships")
    op.drop_table("knowledge_base_memberships")
    op.drop_index("ix_knowledge_bases_workspace_id", table_name="knowledge_bases")
    op.drop_index("ix_knowledge_bases_organization_id", table_name="knowledge_bases")
    op.drop_table("knowledge_bases")
    op.drop_index("ix_workspaces_organization_id", table_name="workspaces")
    op.drop_table("workspaces")
    op.drop_index("ix_organizations_slug", table_name="organizations")
    op.drop_table("organizations")
