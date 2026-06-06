from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
import json
from typing import Any, Sequence
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.db import DEFAULT_DATABASE_URL, session_scope
from app.document_store import DocumentRecord
from app.models import KnowledgeBaseSnapshotModel


@dataclass(frozen=True)
class KnowledgeBaseSnapshotRecord:
    snapshot_id: str
    created_at: str
    created_by_user_id: str
    organization_id: str
    workspace_id: str
    knowledge_base_id: str
    reason: str | None
    document_count: int
    indexed_chunk_count: int
    content_hash: str
    documents: list[dict[str, Any]]


class KnowledgeBaseSnapshotStoreError(RuntimeError):
    pass


class KnowledgeBaseSnapshotStore:
    def __init__(self, database_url: str | None = None) -> None:
        self.database_url = database_url or DEFAULT_DATABASE_URL

    def create_snapshot(
        self,
        *,
        created_by_user_id: str,
        organization_id: str,
        workspace_id: str,
        knowledge_base_id: str,
        documents: Sequence[DocumentRecord],
        reason: str | None = None,
    ) -> KnowledgeBaseSnapshotRecord:
        summaries = summarize_documents(documents)
        content_hash = calculate_snapshot_hash(summaries)
        snapshot = KnowledgeBaseSnapshotModel(
            snapshot_id=f"kbsnap_{uuid4().hex[:16]}",
            created_at=_now(),
            created_by_user_id=created_by_user_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            knowledge_base_id=knowledge_base_id,
            reason=_optional_reason(reason),
            document_count=len(summaries),
            indexed_chunk_count=sum(_safe_int(document.get("indexed_count")) for document in summaries),
            content_hash=content_hash,
            documents_json=json.dumps(summaries, ensure_ascii=False, sort_keys=True),
        )

        try:
            with session_scope(self.database_url) as session:
                session.add(snapshot)
                session.flush()
                return _record_from_model(snapshot)
        except SQLAlchemyError as exc:
            raise KnowledgeBaseSnapshotStoreError(f"Failed to create knowledge base snapshot: {exc}") from exc

    def list_snapshots(
        self,
        *,
        knowledge_base_id: str,
        limit: int = 50,
    ) -> list[KnowledgeBaseSnapshotRecord]:
        try:
            with session_scope(self.database_url) as session:
                rows = session.scalars(
                    select(KnowledgeBaseSnapshotModel)
                    .where(KnowledgeBaseSnapshotModel.knowledge_base_id == knowledge_base_id)
                    .order_by(KnowledgeBaseSnapshotModel.created_at.desc())
                    .limit(max(1, limit))
                ).all()
                return [_record_from_model(row) for row in rows]
        except SQLAlchemyError as exc:
            raise KnowledgeBaseSnapshotStoreError(f"Failed to list knowledge base snapshots: {exc}") from exc

    def get_snapshot(
        self,
        snapshot_id: str,
        *,
        knowledge_base_id: str | None = None,
    ) -> KnowledgeBaseSnapshotRecord | None:
        try:
            with session_scope(self.database_url) as session:
                statement = select(KnowledgeBaseSnapshotModel).where(
                    KnowledgeBaseSnapshotModel.snapshot_id == snapshot_id
                )
                if knowledge_base_id:
                    statement = statement.where(
                        KnowledgeBaseSnapshotModel.knowledge_base_id == knowledge_base_id
                    )
                snapshot = session.scalar(statement)
                return _record_from_model(snapshot) if snapshot else None
        except SQLAlchemyError as exc:
            raise KnowledgeBaseSnapshotStoreError(f"Failed to get knowledge base snapshot: {exc}") from exc


def summarize_documents(documents: Sequence[DocumentRecord]) -> list[dict[str, Any]]:
    summaries = [
        {
            "document_id": document.document_id,
            "filename": document.filename,
            "file_type": document.file_type,
            "content_hash": document.content_hash,
            "chunk_count": document.chunk_count,
            "indexed_count": document.indexed_count,
            "source_file_size": document.source_file_size,
            "source_storage_backend": document.source_storage_backend,
            "source_storage_key": document.source_storage_key,
            "indexed_at": document.indexed_at,
        }
        for document in documents
    ]
    return sorted(
        summaries,
        key=lambda item: (
            str(item["document_id"]),
            str(item["content_hash"]),
            str(item["filename"]),
        ),
    )


def calculate_snapshot_hash(document_summaries: Sequence[dict[str, Any]]) -> str:
    payload = {
        "schema_version": 1,
        "documents": list(document_summaries),
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _record_from_model(snapshot: KnowledgeBaseSnapshotModel) -> KnowledgeBaseSnapshotRecord:
    return KnowledgeBaseSnapshotRecord(
        snapshot_id=snapshot.snapshot_id,
        created_at=snapshot.created_at,
        created_by_user_id=snapshot.created_by_user_id,
        organization_id=snapshot.organization_id,
        workspace_id=snapshot.workspace_id,
        knowledge_base_id=snapshot.knowledge_base_id,
        reason=snapshot.reason,
        document_count=snapshot.document_count,
        indexed_chunk_count=snapshot.indexed_chunk_count,
        content_hash=snapshot.content_hash,
        documents=_load_documents(snapshot.documents_json),
    )


def _load_documents(value: str) -> list[dict[str, Any]]:
    loaded = json.loads(value)
    if not isinstance(loaded, list):
        return []
    return [item for item in loaded if isinstance(item, dict)]


def _safe_int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _optional_reason(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _now() -> str:
    return datetime.now(UTC).isoformat()
