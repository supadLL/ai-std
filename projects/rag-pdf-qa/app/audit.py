from dataclasses import dataclass
from datetime import UTC, datetime
import json
from typing import Any
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from app.db import session_scope
from app.models import AuditLogModel


AUDIT_STATUS_FAILURE = "failure"
AUDIT_STATUS_SUCCESS = "success"


@dataclass(frozen=True)
class AuditLogRecord:
    audit_log_id: str
    created_at: str
    request_id: str | None
    user_id: str | None
    username: str | None
    organization_id: str | None
    workspace_id: str | None
    knowledge_base_id: str | None
    action: str
    resource_type: str | None
    resource_id: str | None
    status: str
    duration_ms: int | None = None
    llm_provider: str | None = None
    llm_model: str | None = None
    usage: dict[str, Any] | None = None
    details: dict[str, Any] | None = None
    error_message: str | None = None


@dataclass(frozen=True)
class AuditMetrics:
    audit_log_count: int
    failure_count: int
    action_counts: dict[str, int]


class AuditLogError(RuntimeError):
    pass


class AuditLogStore:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def record(
        self,
        *,
        action: str,
        status: str = AUDIT_STATUS_SUCCESS,
        request_id: str | None = None,
        user_id: str | None = None,
        username: str | None = None,
        organization_id: str | None = None,
        workspace_id: str | None = None,
        knowledge_base_id: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        duration_ms: int | None = None,
        llm_provider: str | None = None,
        llm_model: str | None = None,
        usage: dict[str, Any] | None = None,
        details: dict[str, Any] | None = None,
        error_message: str | None = None,
    ) -> AuditLogRecord:
        log = AuditLogModel(
            audit_log_id=f"audit_{uuid4().hex}",
            created_at=datetime.now(UTC).isoformat(),
            request_id=_optional_str(request_id),
            user_id=_optional_str(user_id),
            username=_optional_str(username),
            organization_id=_optional_str(organization_id),
            workspace_id=_optional_str(workspace_id),
            knowledge_base_id=_optional_str(knowledge_base_id),
            action=action,
            resource_type=_optional_str(resource_type),
            resource_id=_optional_str(resource_id),
            status=status,
            duration_ms=duration_ms,
            llm_provider=_optional_str(llm_provider),
            llm_model=_optional_str(llm_model),
            usage_json=_json_or_none(usage),
            details_json=_json_or_none(details),
            error_message=_optional_str(error_message),
        )
        try:
            with session_scope(self.database_url) as session:
                session.add(log)
                session.flush()
                return _record_from_model(log)
        except SQLAlchemyError as exc:
            raise AuditLogError(f"Failed to write audit log: {exc}") from exc

    def list_logs(
        self,
        *,
        limit: int = 50,
        user_id: str | None = None,
        knowledge_base_id: str | None = None,
        action: str | None = None,
    ) -> list[AuditLogRecord]:
        try:
            with session_scope(self.database_url) as session:
                statement = select(AuditLogModel)
                if user_id:
                    statement = statement.where(AuditLogModel.user_id == user_id)
                if knowledge_base_id:
                    statement = statement.where(AuditLogModel.knowledge_base_id == knowledge_base_id)
                if action:
                    statement = statement.where(AuditLogModel.action == action)
                rows = session.scalars(
                    statement.order_by(AuditLogModel.created_at.desc()).limit(limit)
                ).all()
                return [_record_from_model(row) for row in rows]
        except SQLAlchemyError as exc:
            raise AuditLogError(f"Failed to list audit logs: {exc}") from exc

    def summarize(self) -> AuditMetrics:
        try:
            with session_scope(self.database_url) as session:
                audit_log_count = int(session.scalar(select(func.count()).select_from(AuditLogModel)) or 0)
                failure_count = int(
                    session.scalar(
                        select(func.count())
                        .select_from(AuditLogModel)
                        .where(AuditLogModel.status == AUDIT_STATUS_FAILURE)
                    )
                    or 0
                )
                action_rows = session.execute(
                    select(AuditLogModel.action, func.count()).group_by(AuditLogModel.action)
                ).all()
                return AuditMetrics(
                    audit_log_count=audit_log_count,
                    failure_count=failure_count,
                    action_counts={str(action): int(count) for action, count in action_rows},
                )
        except SQLAlchemyError as exc:
            raise AuditLogError(f"Failed to summarize audit logs: {exc}") from exc


def _record_from_model(log: AuditLogModel) -> AuditLogRecord:
    return AuditLogRecord(
        audit_log_id=log.audit_log_id,
        created_at=log.created_at,
        request_id=log.request_id,
        user_id=log.user_id,
        username=log.username,
        organization_id=log.organization_id,
        workspace_id=log.workspace_id,
        knowledge_base_id=log.knowledge_base_id,
        action=log.action,
        resource_type=log.resource_type,
        resource_id=log.resource_id,
        status=log.status,
        duration_ms=log.duration_ms,
        llm_provider=log.llm_provider,
        llm_model=log.llm_model,
        usage=_json_dict_or_none(log.usage_json),
        details=_json_dict_or_none(log.details_json),
        error_message=log.error_message,
    )


def _json_or_none(value: dict[str, Any] | None) -> str | None:
    if not value:
        return None
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _json_dict_or_none(value: str | None) -> dict[str, Any] | None:
    if not value:
        return None
    loaded = json.loads(value)
    return loaded if isinstance(loaded, dict) else None


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
