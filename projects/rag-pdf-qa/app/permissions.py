from dataclasses import dataclass
from datetime import UTC, datetime
import re
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from app.db import DEFAULT_DATABASE_URL, session_scope
from app.models import (
    KnowledgeBaseMembershipModel,
    KnowledgeBaseModel,
    OrganizationModel,
    UserModel,
    WorkspaceModel,
)


DEFAULT_ORGANIZATION_ID = "org_default"
DEFAULT_WORKSPACE_ID = "ws_default"
DEFAULT_KNOWLEDGE_BASE_ID = "kb_default"


@dataclass(frozen=True)
class KnowledgeBaseAccess:
    organization_id: str
    workspace_id: str
    knowledge_base_id: str
    name: str
    role: str


@dataclass(frozen=True)
class KnowledgeBaseMember:
    membership_id: str
    user_id: str
    username: str
    role: str
    created_at: str


class PermissionStoreError(RuntimeError):
    pass


class KnowledgeBaseAccessError(PermissionStoreError):
    pass


class PermissionStore:
    def __init__(self, database_url: str | None = None) -> None:
        self.database_url = database_url or DEFAULT_DATABASE_URL

    def ensure_default_access(self, *, user_id: str, username: str, role: str) -> KnowledgeBaseAccess:
        try:
            with session_scope(self.database_url) as session:
                _ensure_default_organization_and_workspace(session)
                knowledge_base_id = DEFAULT_KNOWLEDGE_BASE_ID if role == "admin" else _personal_knowledge_base_id(user_id)
                name = "Default Knowledge Base" if role == "admin" else f"{username}'s Knowledge Base"
                knowledge_base = session.get(KnowledgeBaseModel, knowledge_base_id)
                now = _now()
                if knowledge_base is None:
                    knowledge_base = KnowledgeBaseModel(
                        knowledge_base_id=knowledge_base_id,
                        organization_id=DEFAULT_ORGANIZATION_ID,
                        workspace_id=DEFAULT_WORKSPACE_ID,
                        name=name,
                        slug=_slugify(name),
                        created_by_user_id=user_id,
                        status="active",
                        created_at=now,
                    )
                    session.add(knowledge_base)
                    session.flush()

                membership = session.scalar(
                    select(KnowledgeBaseMembershipModel).where(
                        KnowledgeBaseMembershipModel.user_id == user_id,
                        KnowledgeBaseMembershipModel.knowledge_base_id == knowledge_base.knowledge_base_id,
                    )
                )
                if membership is None:
                    membership = KnowledgeBaseMembershipModel(
                        membership_id=f"mb_{uuid4().hex[:16]}",
                        user_id=user_id,
                        organization_id=knowledge_base.organization_id,
                        workspace_id=knowledge_base.workspace_id,
                        knowledge_base_id=knowledge_base.knowledge_base_id,
                        role="owner",
                        created_at=now,
                    )
                    session.add(membership)
                    session.flush()

                return _access_from_models(knowledge_base, membership.role)
        except SQLAlchemyError as exc:
            raise PermissionStoreError(f"Failed to ensure default knowledge base access: {exc}") from exc

    def list_knowledge_bases(self, *, user_id: str) -> list[KnowledgeBaseAccess]:
        try:
            with session_scope(self.database_url) as session:
                rows = session.execute(
                    select(KnowledgeBaseModel, KnowledgeBaseMembershipModel.role)
                    .join(
                        KnowledgeBaseMembershipModel,
                        KnowledgeBaseMembershipModel.knowledge_base_id == KnowledgeBaseModel.knowledge_base_id,
                    )
                    .where(
                        KnowledgeBaseMembershipModel.user_id == user_id,
                        KnowledgeBaseModel.status == "active",
                    )
                    .order_by(KnowledgeBaseModel.created_at)
                ).all()
                return [_access_from_models(knowledge_base, role) for knowledge_base, role in rows]
        except SQLAlchemyError as exc:
            raise PermissionStoreError(f"Failed to list knowledge bases: {exc}") from exc

    def get_knowledge_base_for_user(self, *, user_id: str, knowledge_base_id: str) -> KnowledgeBaseAccess | None:
        try:
            with session_scope(self.database_url) as session:
                row = session.execute(
                    select(KnowledgeBaseModel, KnowledgeBaseMembershipModel.role)
                    .join(
                        KnowledgeBaseMembershipModel,
                        KnowledgeBaseMembershipModel.knowledge_base_id == KnowledgeBaseModel.knowledge_base_id,
                    )
                    .where(
                        KnowledgeBaseMembershipModel.user_id == user_id,
                        KnowledgeBaseMembershipModel.knowledge_base_id == knowledge_base_id,
                        KnowledgeBaseModel.status == "active",
                    )
                ).first()
                if row is None:
                    return None
                knowledge_base, role = row
                return _access_from_models(knowledge_base, role)
        except SQLAlchemyError as exc:
            raise PermissionStoreError(f"Failed to get knowledge base access: {exc}") from exc

    def get_knowledge_base(self, *, knowledge_base_id: str, role: str = "admin") -> KnowledgeBaseAccess | None:
        try:
            with session_scope(self.database_url) as session:
                knowledge_base = session.get(KnowledgeBaseModel, knowledge_base_id)
                if knowledge_base is None or knowledge_base.status != "active":
                    return None
                return _access_from_models(knowledge_base, role)
        except SQLAlchemyError as exc:
            raise PermissionStoreError(f"Failed to get knowledge base: {exc}") from exc

    def create_knowledge_base(self, *, user_id: str, name: str) -> KnowledgeBaseAccess:
        name = name.strip()
        if not name:
            raise PermissionStoreError("Knowledge base name must not be empty")

        try:
            with session_scope(self.database_url) as session:
                _ensure_default_organization_and_workspace(session)
                now = _now()
                knowledge_base = KnowledgeBaseModel(
                    knowledge_base_id=f"kb_{uuid4().hex[:16]}",
                    organization_id=DEFAULT_ORGANIZATION_ID,
                    workspace_id=DEFAULT_WORKSPACE_ID,
                    name=name,
                    slug=_unique_slug(session, name),
                    created_by_user_id=user_id,
                    status="active",
                    created_at=now,
                )
                session.add(knowledge_base)
                session.flush()
                membership = KnowledgeBaseMembershipModel(
                    membership_id=f"mb_{uuid4().hex[:16]}",
                    user_id=user_id,
                    organization_id=knowledge_base.organization_id,
                    workspace_id=knowledge_base.workspace_id,
                    knowledge_base_id=knowledge_base.knowledge_base_id,
                    role="owner",
                    created_at=now,
                )
                session.add(membership)
                session.flush()
                return _access_from_models(knowledge_base, membership.role)
        except SQLAlchemyError as exc:
            raise PermissionStoreError(f"Failed to create knowledge base: {exc}") from exc

    def list_members(self, *, knowledge_base_id: str) -> list[KnowledgeBaseMember]:
        try:
            with session_scope(self.database_url) as session:
                rows = session.execute(
                    select(KnowledgeBaseMembershipModel, UserModel.username)
                    .join(UserModel, UserModel.user_id == KnowledgeBaseMembershipModel.user_id)
                    .where(KnowledgeBaseMembershipModel.knowledge_base_id == knowledge_base_id)
                    .order_by(KnowledgeBaseMembershipModel.created_at)
                ).all()
                return [_member_from_models(membership, username) for membership, username in rows]
        except SQLAlchemyError as exc:
            raise PermissionStoreError(f"Failed to list knowledge base members: {exc}") from exc

    def add_member(
        self,
        *,
        knowledge_base_id: str,
        user_id: str,
        role: str = "member",
    ) -> KnowledgeBaseMember:
        role = _normalize_member_role(role)
        try:
            with session_scope(self.database_url) as session:
                knowledge_base = session.get(KnowledgeBaseModel, knowledge_base_id)
                if knowledge_base is None or knowledge_base.status != "active":
                    raise PermissionStoreError(f"Knowledge base {knowledge_base_id!r} not found")
                user = session.get(UserModel, user_id)
                if user is None:
                    raise PermissionStoreError(f"User {user_id!r} not found")

                membership = session.scalar(
                    select(KnowledgeBaseMembershipModel).where(
                        KnowledgeBaseMembershipModel.user_id == user_id,
                        KnowledgeBaseMembershipModel.knowledge_base_id == knowledge_base_id,
                    )
                )
                if membership is None:
                    membership = KnowledgeBaseMembershipModel(
                        membership_id=f"mb_{uuid4().hex[:16]}",
                        user_id=user_id,
                        organization_id=knowledge_base.organization_id,
                        workspace_id=knowledge_base.workspace_id,
                        knowledge_base_id=knowledge_base.knowledge_base_id,
                        role=role,
                        created_at=_now(),
                    )
                    session.add(membership)
                    session.flush()
                return _member_from_models(membership, user.username)
        except PermissionStoreError:
            raise
        except SQLAlchemyError as exc:
            raise PermissionStoreError(f"Failed to add knowledge base member: {exc}") from exc

    def remove_member(self, *, knowledge_base_id: str, user_id: str) -> KnowledgeBaseMember | None:
        try:
            with session_scope(self.database_url) as session:
                membership = session.scalar(
                    select(KnowledgeBaseMembershipModel).where(
                        KnowledgeBaseMembershipModel.user_id == user_id,
                        KnowledgeBaseMembershipModel.knowledge_base_id == knowledge_base_id,
                    )
                )
                if membership is None:
                    return None
                if membership.role == "owner":
                    owner_count = int(
                        session.scalar(
                            select(func.count())
                            .select_from(KnowledgeBaseMembershipModel)
                            .where(
                                KnowledgeBaseMembershipModel.knowledge_base_id == knowledge_base_id,
                                KnowledgeBaseMembershipModel.role == "owner",
                            )
                        )
                        or 0
                    )
                    if owner_count <= 1:
                        raise PermissionStoreError("Cannot remove the last owner from a knowledge base")

                user = session.get(UserModel, user_id)
                record = _member_from_models(membership, user.username if user else user_id)
                session.delete(membership)
                return record
        except PermissionStoreError:
            raise
        except SQLAlchemyError as exc:
            raise PermissionStoreError(f"Failed to remove knowledge base member: {exc}") from exc


def _ensure_default_organization_and_workspace(session) -> None:
    now = _now()
    organization = session.get(OrganizationModel, DEFAULT_ORGANIZATION_ID)
    if organization is None:
        session.add(
            OrganizationModel(
                organization_id=DEFAULT_ORGANIZATION_ID,
                name="Default Organization",
                slug="default",
                created_at=now,
            )
        )

    workspace = session.get(WorkspaceModel, DEFAULT_WORKSPACE_ID)
    if workspace is None:
        session.add(
            WorkspaceModel(
                workspace_id=DEFAULT_WORKSPACE_ID,
                organization_id=DEFAULT_ORGANIZATION_ID,
                name="Default Workspace",
                slug="default",
                created_at=now,
            )
        )
    session.flush()


def _access_from_models(knowledge_base: KnowledgeBaseModel, role: str) -> KnowledgeBaseAccess:
    return KnowledgeBaseAccess(
        organization_id=knowledge_base.organization_id,
        workspace_id=knowledge_base.workspace_id,
        knowledge_base_id=knowledge_base.knowledge_base_id,
        name=knowledge_base.name,
        role=role,
    )


def _member_from_models(membership: KnowledgeBaseMembershipModel, username: str) -> KnowledgeBaseMember:
    return KnowledgeBaseMember(
        membership_id=membership.membership_id,
        user_id=membership.user_id,
        username=username,
        role=membership.role,
        created_at=membership.created_at,
    )


def _normalize_member_role(role: str) -> str:
    normalized = role.strip().lower()
    if normalized not in {"owner", "member"}:
        raise PermissionStoreError("Knowledge base member role must be owner or member")
    return normalized


def _personal_knowledge_base_id(user_id: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9_]+", "_", user_id).strip("_")[:48]
    return f"kb_{safe or uuid4().hex[:12]}"


def _unique_slug(session, name: str) -> str:
    base_slug = _slugify(name)
    slug = base_slug
    suffix = 2
    while session.scalar(
        select(KnowledgeBaseModel).where(
            KnowledgeBaseModel.workspace_id == DEFAULT_WORKSPACE_ID,
            KnowledgeBaseModel.slug == slug,
        )
    ):
        slug = f"{base_slug}-{suffix}"
        suffix += 1
    return slug


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or f"kb-{uuid4().hex[:8]}"


def _now() -> str:
    return datetime.now(UTC).isoformat()
