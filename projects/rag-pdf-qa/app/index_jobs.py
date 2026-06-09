from dataclasses import dataclass
from datetime import UTC, datetime
import json
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.db import DEFAULT_DATABASE_URL, session_scope
from app.models import IndexJobModel


JOB_STATUS_QUEUED = "queued"
JOB_STATUS_RUNNING = "running"
JOB_STATUS_SUCCEEDED = "succeeded"
JOB_STATUS_FAILED = "failed"
RETRYABLE_JOB_STATUSES = {JOB_STATUS_FAILED}


@dataclass(frozen=True)
class IndexJobRecord:
    job_id: str
    status: str
    organization_id: str
    workspace_id: str
    knowledge_base_id: str
    owner_user_id: str
    filename: str
    file_path: str
    source_file_size: int
    content_hash: str
    chunk_size: int
    overlap: int
    reindex: bool
    enable_ocr: bool
    enable_image_ocr: bool
    extract_tables: bool
    ocr_language: str
    attempts: int
    created_at: str
    updated_at: str
    progress_message: str
    document_id: str | None = None
    error_message: str | None = None
    result: dict[str, Any] | None = None
    started_at: str | None = None
    finished_at: str | None = None


class IndexJobStoreError(RuntimeError):
    pass


class IndexJobStore:
    def __init__(self, database_url: str | None = None) -> None:
        self.database_url = database_url or DEFAULT_DATABASE_URL

    def create_job(
        self,
        *,
        organization_id: str,
        workspace_id: str,
        knowledge_base_id: str,
        owner_user_id: str,
        filename: str,
        file_path: str,
        source_file_size: int,
        content_hash: str,
        chunk_size: int,
        overlap: int,
        reindex: bool,
        enable_ocr: bool,
        enable_image_ocr: bool,
        extract_tables: bool,
        ocr_language: str,
    ) -> IndexJobRecord:
        now = _now()
        job = IndexJobModel(
            job_id=f"job_{uuid4().hex[:16]}",
            status=JOB_STATUS_QUEUED,
            organization_id=organization_id,
            workspace_id=workspace_id,
            knowledge_base_id=knowledge_base_id,
            owner_user_id=owner_user_id,
            filename=filename,
            file_path=file_path,
            source_file_size=source_file_size,
            content_hash=content_hash,
            chunk_size=chunk_size,
            overlap=overlap,
            reindex=1 if reindex else 0,
            enable_ocr=1 if enable_ocr else 0,
            enable_image_ocr=1 if enable_image_ocr else 0,
            extract_tables=1 if extract_tables else 0,
            ocr_language=ocr_language,
            attempts=0,
            progress_message=JOB_STATUS_QUEUED,
            created_at=now,
            updated_at=now,
        )

        try:
            with session_scope(self.database_url) as session:
                session.add(job)
                session.flush()
                return _record_from_model(job)
        except SQLAlchemyError as exc:
            raise IndexJobStoreError(f"Failed to create index job: {exc}") from exc

    def list_jobs(self, *, knowledge_base_id: str | None = None, limit: int = 50) -> list[IndexJobRecord]:
        try:
            with session_scope(self.database_url) as session:
                statement = select(IndexJobModel)
                if knowledge_base_id:
                    statement = statement.where(IndexJobModel.knowledge_base_id == knowledge_base_id)
                jobs = session.scalars(
                    statement.order_by(IndexJobModel.created_at.desc()).limit(limit)
                ).all()
                return [_record_from_model(job) for job in jobs]
        except SQLAlchemyError as exc:
            raise IndexJobStoreError(f"Failed to list index jobs: {exc}") from exc

    def get_job(self, job_id: str, *, knowledge_base_id: str | None = None) -> IndexJobRecord | None:
        try:
            with session_scope(self.database_url) as session:
                statement = select(IndexJobModel).where(IndexJobModel.job_id == job_id)
                if knowledge_base_id:
                    statement = statement.where(IndexJobModel.knowledge_base_id == knowledge_base_id)
                job = session.scalar(statement)
                return _record_from_model(job) if job else None
        except SQLAlchemyError as exc:
            raise IndexJobStoreError(f"Failed to get index job: {exc}") from exc

    def mark_running(self, job_id: str) -> IndexJobRecord | None:
        return self._update_job(
            job_id,
            status=JOB_STATUS_RUNNING,
            progress_message="running",
            started_at=_now(),
            finished_at=None,
            error_message=None,
            increment_attempts=True,
        )

    def mark_succeeded(self, job_id: str, *, document_id: str, result: dict[str, Any]) -> IndexJobRecord | None:
        return self._update_job(
            job_id,
            status=JOB_STATUS_SUCCEEDED,
            progress_message="succeeded",
            document_id=document_id,
            result_json=json.dumps(result, ensure_ascii=False),
            error_message=None,
            finished_at=_now(),
        )

    def mark_failed(self, job_id: str, *, error_message: str) -> IndexJobRecord | None:
        return self._update_job(
            job_id,
            status=JOB_STATUS_FAILED,
            progress_message="failed",
            error_message=error_message[:4000],
            finished_at=_now(),
        )

    def reset_for_retry(self, job_id: str) -> IndexJobRecord | None:
        return self._update_job(
            job_id,
            status=JOB_STATUS_QUEUED,
            progress_message="queued",
            error_message=None,
            result_json=None,
            document_id=None,
            started_at=None,
            finished_at=None,
        )

    def _update_job(self, job_id: str, **values: Any) -> IndexJobRecord | None:
        increment_attempts = bool(values.pop("increment_attempts", False))
        try:
            with session_scope(self.database_url) as session:
                job = session.get(IndexJobModel, job_id)
                if job is None:
                    return None
                for key, value in values.items():
                    setattr(job, key, value)
                if increment_attempts:
                    job.attempts += 1
                job.updated_at = _now()
                session.flush()
                return _record_from_model(job)
        except SQLAlchemyError as exc:
            raise IndexJobStoreError(f"Failed to update index job: {exc}") from exc


def _record_from_model(job: IndexJobModel) -> IndexJobRecord:
    result = None
    if job.result_json:
        try:
            loaded = json.loads(job.result_json)
            result = loaded if isinstance(loaded, dict) else None
        except json.JSONDecodeError:
            result = None

    return IndexJobRecord(
        job_id=job.job_id,
        status=job.status,
        organization_id=job.organization_id,
        workspace_id=job.workspace_id,
        knowledge_base_id=job.knowledge_base_id,
        owner_user_id=job.owner_user_id,
        filename=job.filename,
        file_path=job.file_path,
        source_file_size=job.source_file_size,
        content_hash=job.content_hash,
        chunk_size=job.chunk_size,
        overlap=job.overlap,
        reindex=bool(job.reindex),
        enable_ocr=bool(job.enable_ocr),
        enable_image_ocr=bool(job.enable_image_ocr),
        extract_tables=bool(job.extract_tables),
        ocr_language=job.ocr_language,
        attempts=job.attempts,
        document_id=job.document_id,
        error_message=job.error_message,
        progress_message=job.progress_message,
        result=result,
        created_at=job.created_at,
        updated_at=job.updated_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
    )


def _now() -> str:
    return datetime.now(UTC).isoformat()
