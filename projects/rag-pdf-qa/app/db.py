from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.models import Base


DEFAULT_DATABASE_URL = "sqlite:///data/app.db"


def database_url_from_legacy_path(path: str, default_filename: str = "app.db") -> str:
    legacy_path = Path(path)
    if legacy_path.suffix:
        db_path = legacy_path.with_suffix(".db")
    else:
        db_path = legacy_path / default_filename
    return f"sqlite:///{db_path.as_posix()}"


@lru_cache(maxsize=8)
def get_engine(database_url: str = DEFAULT_DATABASE_URL) -> Engine:
    database_url = database_url or DEFAULT_DATABASE_URL
    _ensure_sqlite_parent(database_url)
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args, future=True)


@lru_cache(maxsize=8)
def get_session_factory(database_url: str = DEFAULT_DATABASE_URL) -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(database_url), autoflush=False, expire_on_commit=False, future=True)


def initialize_database(database_url: str = DEFAULT_DATABASE_URL) -> None:
    engine = get_engine(database_url)
    Base.metadata.create_all(engine)
    _ensure_sqlite_enterprise_schema(engine, database_url)


@contextmanager
def session_scope(database_url: str = DEFAULT_DATABASE_URL) -> Iterator[Session]:
    initialize_database(database_url)
    session = get_session_factory(database_url)()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _ensure_sqlite_parent(database_url: str) -> None:
    if database_url == "sqlite:///:memory:" or not database_url.startswith("sqlite:///"):
        return
    path_text = database_url.removeprefix("sqlite:///")
    if not path_text:
        return
    Path(path_text).parent.mkdir(parents=True, exist_ok=True)


def _ensure_sqlite_enterprise_schema(engine: Engine, database_url: str) -> None:
    if not database_url.startswith("sqlite:///") or database_url == "sqlite:///:memory:":
        return

    with engine.begin() as connection:
        existing_columns = {
            row[1]
            for row in connection.execute(text("PRAGMA table_info(documents)")).fetchall()
        }
        if not existing_columns:
            return

        column_specs = {
            "organization_id": "VARCHAR(80) NOT NULL DEFAULT 'org_default'",
            "workspace_id": "VARCHAR(80) NOT NULL DEFAULT 'ws_default'",
            "knowledge_base_id": "VARCHAR(80) NOT NULL DEFAULT 'kb_default'",
            "owner_user_id": "VARCHAR(64) NOT NULL DEFAULT 'system'",
            "source_storage_backend": "VARCHAR(40)",
            "source_storage_key": "TEXT",
        }
        for column_name, column_spec in column_specs.items():
            if column_name not in existing_columns:
                connection.execute(text(f"ALTER TABLE documents ADD COLUMN {column_name} {column_spec}"))

        connection.execute(text("DROP INDEX IF EXISTS ix_documents_content_hash"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_documents_content_hash ON documents (content_hash)"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_documents_organization_id ON documents (organization_id)"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_documents_workspace_id ON documents (workspace_id)"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_documents_knowledge_base_id ON documents (knowledge_base_id)"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_documents_owner_user_id ON documents (owner_user_id)"))
        connection.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_documents_kb_content_hash "
                "ON documents (knowledge_base_id, content_hash)"
            )
        )
