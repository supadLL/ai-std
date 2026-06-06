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


class DocumentModel(Base):
    __tablename__ = "documents"

    document_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(40), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
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
