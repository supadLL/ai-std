from sqlalchemy import Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    username: Mapped[str] = mapped_column(String(120), nullable=False)
    username_normalized: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(40), nullable=False, default="user")
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="active")
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)


class OrganizationModel(Base):
    __tablename__ = "organizations"

    organization_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True, nullable=False)
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)


class WorkspaceModel(Base):
    __tablename__ = "workspaces"
    __table_args__ = (UniqueConstraint("organization_id", "slug", name="uq_workspaces_org_slug"),)

    workspace_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(160), nullable=False)
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)


class KnowledgeBaseModel(Base):
    __tablename__ = "knowledge_bases"
    __table_args__ = (UniqueConstraint("workspace_id", "slug", name="uq_knowledge_bases_workspace_slug"),)

    knowledge_base_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    workspace_id: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(180), nullable=False)
    created_by_user_id: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="active")
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)


class KnowledgeBaseMembershipModel(Base):
    __tablename__ = "knowledge_base_memberships"
    __table_args__ = (UniqueConstraint("user_id", "knowledge_base_id", name="uq_kb_memberships_user_kb"),)

    membership_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    organization_id: Mapped[str] = mapped_column(String(80), nullable=False)
    workspace_id: Mapped[str] = mapped_column(String(80), nullable=False)
    knowledge_base_id: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(40), nullable=False, default="owner")
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)


class DocumentModel(Base):
    __tablename__ = "documents"
    __table_args__ = (UniqueConstraint("knowledge_base_id", "content_hash", name="uq_documents_kb_content_hash"),)

    document_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(80), index=True, nullable=False, default="org_default")
    workspace_id: Mapped[str] = mapped_column(String(80), index=True, nullable=False, default="ws_default")
    knowledge_base_id: Mapped[str] = mapped_column(String(80), index=True, nullable=False, default="kb_default")
    owner_user_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False, default="system")
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(40), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    content_hash_prefix: Mapped[str] = mapped_column(String(32), nullable=False)
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)
    indexed_at: Mapped[str] = mapped_column(String(40), nullable=False)
    source_file_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    collection: Mapped[str] = mapped_column(String(120), nullable=False)
    chunk_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    overlap: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    embedding_model: Mapped[str] = mapped_column(String(240), nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    indexed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class IndexJobModel(Base):
    __tablename__ = "index_jobs"

    job_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    status: Mapped[str] = mapped_column(String(40), index=True, nullable=False, default="queued")
    organization_id: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    workspace_id: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    knowledge_base_id: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    owner_user_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    source_file_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    content_hash: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    chunk_size: Mapped[int] = mapped_column(Integer, nullable=False, default=800)
    overlap: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    reindex: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    enable_ocr: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    enable_image_ocr: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ocr_language: Mapped[str] = mapped_column(String(80), nullable=False, default="chi_sim+eng")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    document_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    progress_message: Mapped[str] = mapped_column(String(200), nullable=False, default="queued")
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(40), nullable=False)
    started_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    finished_at: Mapped[str | None] = mapped_column(String(40), nullable=True)


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    audit_log_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    created_at: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    request_id: Mapped[str | None] = mapped_column(String(80), index=True, nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    username: Mapped[str | None] = mapped_column(String(120), nullable=True)
    organization_id: Mapped[str | None] = mapped_column(String(80), index=True, nullable=True)
    workspace_id: Mapped[str | None] = mapped_column(String(80), index=True, nullable=True)
    knowledge_base_id: Mapped[str | None] = mapped_column(String(80), index=True, nullable=True)
    action: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(160), index=True, nullable=True)
    status: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    llm_provider: Mapped[str | None] = mapped_column(String(80), nullable=True)
    llm_model: Mapped[str | None] = mapped_column(String(240), nullable=True)
    usage_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    details_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class EvaluationCaseModel(Base):
    __tablename__ = "evaluation_cases"
    __table_args__ = (
        UniqueConstraint(
            "dataset_name",
            "dataset_version",
            "knowledge_base_id",
            "case_id",
            name="uq_evaluation_cases_dataset_kb_case",
        ),
    )

    evaluation_case_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    dataset_name: Mapped[str] = mapped_column(String(160), index=True, nullable=False)
    dataset_version: Mapped[str] = mapped_column(String(80), nullable=False)
    knowledge_base_id: Mapped[str | None] = mapped_column(String(80), index=True, nullable=True)
    case_id: Mapped[str] = mapped_column(String(120), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    expected_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(40), nullable=False)


class EvaluationRunModel(Base):
    __tablename__ = "evaluation_runs"

    run_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    generated_at: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    dataset_name: Mapped[str] = mapped_column(String(160), index=True, nullable=False)
    dataset_version: Mapped[str] = mapped_column(String(80), nullable=False)
    knowledge_base_id: Mapped[str | None] = mapped_column(String(80), index=True, nullable=True)
    collection: Mapped[str] = mapped_column(String(120), nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(240), nullable=False)
    llm_provider: Mapped[str | None] = mapped_column(String(80), nullable=True)
    llm_model: Mapped[str | None] = mapped_column(String(240), nullable=True)
    limit: Mapped[int] = mapped_column(Integer, nullable=False)
    score_threshold: Mapped[str | None] = mapped_column(String(40), nullable=True)
    hit_rate: Mapped[str] = mapped_column(String(40), nullable=False)
    page_hit_rate: Mapped[str] = mapped_column(String(40), nullable=False)
    keyword_hit_rate: Mapped[str] = mapped_column(String(40), nullable=False)
    quality_status: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    result_json: Mapped[str] = mapped_column(Text, nullable=False)


class AnswerFeedbackModel(Base):
    __tablename__ = "answer_feedback"

    feedback_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    created_at: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    request_id: Mapped[str | None] = mapped_column(String(80), index=True, nullable=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(120), nullable=False)
    organization_id: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    workspace_id: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    knowledge_base_id: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    rating: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    route: Mapped[str | None] = mapped_column(String(80), nullable=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer_preview: Mapped[str] = mapped_column(Text, nullable=False)
    details_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class RuntimeSettingModel(Base):
    __tablename__ = "runtime_settings"

    key: Mapped[str] = mapped_column(String(120), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)


class LlmProfileModel(Base):
    __tablename__ = "llm_profiles"
    __table_args__ = (UniqueConstraint("profile_id", name="uq_llm_profiles_profile_id"),)

    profile_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    base_url: Mapped[str] = mapped_column(String(600), nullable=False)
    model: Mapped[str] = mapped_column(String(240), nullable=False)
    api_key: Mapped[str | None] = mapped_column(Text, nullable=True)
