from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine
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
    Base.metadata.create_all(get_engine(database_url))


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
