from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.db import database_url_from_legacy_path, session_scope
from app.models import UserModel
from app.security import hash_password, verify_password


@dataclass(frozen=True)
class UserRecord:
    user_id: str
    username: str
    role: str
    password_hash: str
    created_at: str
    status: str = "active"


class UserStoreError(RuntimeError):
    pass


class UserStore:
    def __init__(self, path: str, database_url: str | None = None) -> None:
        self.path = path
        self.database_url = database_url or database_url_from_legacy_path(path)

    def has_users(self) -> bool:
        return bool(self.list_users())

    def list_users(self) -> list[UserRecord]:
        try:
            with session_scope(self.database_url) as session:
                users = session.scalars(select(UserModel).order_by(UserModel.created_at)).all()
                return [_record_from_model(user) for user in users]
        except SQLAlchemyError as exc:
            raise UserStoreError(f"Failed to list users: {exc}") from exc

    def get_user(self, user_id: str) -> UserRecord | None:
        try:
            with session_scope(self.database_url) as session:
                user = session.get(UserModel, user_id)
                return _record_from_model(user) if user else None
        except SQLAlchemyError as exc:
            raise UserStoreError(f"Failed to get user: {exc}") from exc

    def get_user_by_username(self, username: str) -> UserRecord | None:
        normalized = _normalize_username(username)
        try:
            with session_scope(self.database_url) as session:
                user = session.scalar(
                    select(UserModel).where(UserModel.username_normalized == normalized)
                )
                return _record_from_model(user) if user else None
        except SQLAlchemyError as exc:
            raise UserStoreError(f"Failed to get user by username: {exc}") from exc

    def create_user(self, *, username: str, password: str, role: str = "admin") -> UserRecord:
        username = username.strip()
        if not username:
            raise UserStoreError("Username must not be empty")
        if self.get_user_by_username(username):
            raise UserStoreError("Username already exists")

        now = datetime.now(UTC).isoformat()
        user = UserModel(
            user_id=f"u_{uuid4().hex[:12]}",
            username=username,
            username_normalized=_normalize_username(username),
            role=role,
            status="active",
            password_hash=hash_password(password),
            created_at=now,
        )
        try:
            with session_scope(self.database_url) as session:
                session.add(user)
                session.flush()
                return _record_from_model(user)
        except SQLAlchemyError as exc:
            raise UserStoreError(f"Failed to create user: {exc}") from exc

    def authenticate(self, *, username: str, password: str) -> UserRecord | None:
        user = self.get_user_by_username(username)
        if user is None or user.status != "active":
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user


def public_user(user: UserRecord) -> dict[str, str]:
    return {
        "user_id": user.user_id,
        "username": user.username,
        "role": user.role,
    }


def _record_from_model(user: UserModel) -> UserRecord:
    return UserRecord(
        user_id=user.user_id,
        username=user.username,
        role=user.role,
        status=user.status,
        password_hash=user.password_hash,
        created_at=user.created_at,
    )


def _normalize_username(username: str) -> str:
    return username.strip().lower()
