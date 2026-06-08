from pathlib import Path

from fastapi.testclient import TestClient

import app.main as main
from app.config import Settings
from app.index_jobs import IndexJobStore


def test_index_job_store_lifecycle(tmp_path):
    database_url = f"sqlite:///{(tmp_path / 'app.db').as_posix()}"
    store = IndexJobStore(database_url)

    job = store.create_job(
        organization_id="org-1",
        workspace_id="ws-1",
        knowledge_base_id="kb-1",
        owner_user_id="user-1",
        filename="demo.md",
        file_path=str(tmp_path / "demo.md"),
        source_file_size=12,
        content_hash="a" * 64,
        chunk_size=800,
        overlap=100,
        reindex=False,
        enable_ocr=False,
        enable_image_ocr=False,
        ocr_language="chi_sim+eng",
    )

    assert job.status == "queued"
    assert store.list_jobs(knowledge_base_id="kb-1")[0].job_id == job.job_id

    running = store.mark_running(job.job_id)
    assert running.status == "running"
    assert running.attempts == 1

    failed = store.mark_failed(job.job_id, error_message="parse failed")
    assert failed.status == "failed"
    assert failed.error_message == "parse failed"

    retried = store.reset_for_retry(job.job_id)
    assert retried.status == "queued"
    assert retried.error_message is None


def test_create_index_job_returns_queued_job_and_persists_upload(tmp_path, monkeypatch):
    settings = Settings(
        database_url=f"sqlite:///{(tmp_path / 'app.db').as_posix()}",
        index_job_storage_path=str(tmp_path / "jobs"),
    )
    monkeypatch.setattr(main, "get_settings", lambda: settings)
    monkeypatch.setattr(main, "_run_index_job_task", lambda job_id: None)

    client = TestClient(main.app)
    response = client.post(
        "/documents/index-jobs",
        files={"file": ("notes.txt", b"hello async index", "text/plain")},
        data={"chunk_size": "100", "overlap": "0"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "queued"
    assert data["knowledge_base_id"] == "kb_default"
    assert data["filename"] == "notes.txt"
    assert Path(settings.index_job_storage_path).exists()

    list_response = client.get("/documents/index-jobs")
    assert list_response.status_code == 200
    assert list_response.json()["jobs"][0]["job_id"] == data["job_id"]


def test_run_index_job_task_marks_success(tmp_path, monkeypatch):
    settings = Settings(
        database_url=f"sqlite:///{(tmp_path / 'app.db').as_posix()}",
        index_job_storage_path=str(tmp_path / "jobs"),
    )
    upload_path = tmp_path / "jobs" / "demo.md"
    upload_path.parent.mkdir(parents=True)
    upload_path.write_text("hello rag", encoding="utf-8")

    monkeypatch.setattr(main, "get_settings", lambda: settings)
    store = IndexJobStore(settings.database_url)
    job = store.create_job(
        organization_id="org_default",
        workspace_id="ws_default",
        knowledge_base_id="kb_default",
        owner_user_id="test-user",
        filename="demo.md",
        file_path=str(upload_path),
        source_file_size=9,
        content_hash="b" * 64,
        chunk_size=100,
        overlap=0,
        reindex=False,
        enable_ocr=False,
        enable_image_ocr=False,
        ocr_language="chi_sim+eng",
    )

    def fake_index_document_content(**kwargs):
        return main.DocumentIndexResponse(
            document_id="doc-async",
            knowledge_base_id=kwargs["access"].knowledge_base_id,
            filename=kwargs["filename"],
            file_type="markdown",
            content_hash="b" * 64,
            content_hash_prefix="b" * 12,
            is_duplicate=False,
            indexed=True,
            message="Document indexed successfully.",
            collection="rag_chunks",
            page_count=1,
            chunk_count=1,
            indexed_count=1,
            deleted_chunks=0,
            dimension=3,
            local_path=".qdrant",
            extraction_methods=["text"],
        )

    monkeypatch.setattr(main, "_index_document_content", fake_index_document_content)

    main._run_index_job_task(job.job_id)

    completed = store.get_job(job.job_id)
    assert completed.status == "succeeded"
    assert completed.document_id == "doc-async"
    assert completed.attempts == 1
    assert completed.result["indexed_count"] == 1


def test_retry_failed_index_job_requeues_job(tmp_path, monkeypatch):
    settings = Settings(database_url=f"sqlite:///{(tmp_path / 'app.db').as_posix()}")
    monkeypatch.setattr(main, "get_settings", lambda: settings)
    monkeypatch.setattr(main, "_run_index_job_task", lambda job_id: None)

    store = IndexJobStore(settings.database_url)
    job = store.create_job(
        organization_id="org_default",
        workspace_id="ws_default",
        knowledge_base_id="kb_default",
        owner_user_id="test-user",
        filename="demo.md",
        file_path=str(tmp_path / "missing.md"),
        source_file_size=0,
        content_hash="c" * 64,
        chunk_size=100,
        overlap=0,
        reindex=False,
        enable_ocr=False,
        enable_image_ocr=False,
        ocr_language="chi_sim+eng",
    )
    store.mark_failed(job.job_id, error_message="file missing")

    client = TestClient(main.app)
    response = client.post(f"/documents/index-jobs/{job.job_id}/retry")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "queued"
    assert data["error_message"] is None
