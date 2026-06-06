from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.db import database_url_from_legacy_path, session_scope
from app.models import DocumentModel


@dataclass(frozen=True)
class DocumentRecord:
    document_id: str
    filename: str
    file_type: str
    content_hash: str
    content_hash_prefix: str
    chunk_count: int
    created_at: str
    indexed_at: str
    source_file_size: int
    collection: str
    chunk_size: int
    overlap: int
    embedding_model: str
    page_count: int
    indexed_count: int


class DocumentStoreError(RuntimeError):
    pass


class DocumentStore:
    def __init__(self, path: str, database_url: str | None = None) -> None:
        self.path = path
        self.database_url = database_url or database_url_from_legacy_path(path)

    def list_documents(self) -> list[DocumentRecord]:
        try:
            with session_scope(self.database_url) as session:
                documents = session.scalars(select(DocumentModel).order_by(DocumentModel.indexed_at.desc())).all()
                return [_record_from_model(document) for document in documents]
        except SQLAlchemyError as exc:
            raise DocumentStoreError(f"Failed to list document metadata: {exc}") from exc

    def get_document(self, document_id: str) -> DocumentRecord | None:
        try:
            with session_scope(self.database_url) as session:
                document = session.get(DocumentModel, document_id)
                return _record_from_model(document) if document else None
        except SQLAlchemyError as exc:
            raise DocumentStoreError(f"Failed to get document metadata: {exc}") from exc

    def get_document_by_content_hash(self, content_hash: str) -> DocumentRecord | None:
        try:
            with session_scope(self.database_url) as session:
                document = session.scalar(
                    select(DocumentModel).where(DocumentModel.content_hash == content_hash)
                )
                return _record_from_model(document) if document else None
        except SQLAlchemyError as exc:
            raise DocumentStoreError(f"Failed to get document metadata by content hash: {exc}") from exc

    def add_document(
        self,
        *,
        document_id: str | None = None,
        filename: str,
        file_type: str,
        content_hash: str,
        chunk_count: int,
        collection: str,
        chunk_size: int,
        overlap: int,
        embedding_model: str,
        page_count: int,
        indexed_count: int,
        source_file_size: int,
    ) -> DocumentRecord:
        now = datetime.now(UTC).isoformat()
        document = DocumentModel(
            document_id=document_id or str(uuid4()),
            filename=filename,
            file_type=file_type,
            content_hash=content_hash,
            content_hash_prefix=content_hash[:12],
            chunk_count=chunk_count,
            created_at=now,
            indexed_at=now,
            source_file_size=source_file_size,
            collection=collection,
            chunk_size=chunk_size,
            overlap=overlap,
            embedding_model=embedding_model,
            page_count=page_count,
            indexed_count=indexed_count,
        )

        try:
            with session_scope(self.database_url) as session:
                session.add(document)
                session.flush()
                return _record_from_model(document)
        except SQLAlchemyError as exc:
            raise DocumentStoreError(f"Failed to add document metadata: {exc}") from exc

    def remove_document(self, document_id: str) -> DocumentRecord | None:
        try:
            with session_scope(self.database_url) as session:
                document = session.get(DocumentModel, document_id)
                if document is None:
                    return None
                record = _record_from_model(document)
                session.delete(document)
                return record
        except SQLAlchemyError as exc:
            raise DocumentStoreError(f"Failed to remove document metadata: {exc}") from exc


def _record_from_model(document: DocumentModel) -> DocumentRecord:
    return DocumentRecord(
        document_id=document.document_id,
        filename=document.filename,
        file_type=document.file_type,
        content_hash=document.content_hash,
        content_hash_prefix=document.content_hash_prefix,
        chunk_count=document.chunk_count,
        created_at=document.created_at,
        indexed_at=document.indexed_at,
        source_file_size=document.source_file_size,
        collection=document.collection,
        chunk_size=document.chunk_size,
        overlap=document.overlap,
        embedding_model=document.embedding_model,
        page_count=document.page_count,
        indexed_count=document.indexed_count,
    )
