from fastapi.testclient import TestClient

import app.main as main
from app.audit import AuditLogStore
from app.auth import AuthenticatedUser, get_current_user
from app.config import Settings
from app.document_store import DocumentRecord, DocumentStore
from app.knowledge_base_snapshots import (
    KnowledgeBaseSnapshotStore,
    calculate_snapshot_hash,
    summarize_documents,
)
from app.permissions import (
    DEFAULT_KNOWLEDGE_BASE_ID,
    DEFAULT_ORGANIZATION_ID,
    DEFAULT_WORKSPACE_ID,
    PermissionStore,
)


def test_snapshot_store_creates_lists_and_reads_snapshots(tmp_path):
    database_url = f"sqlite:///{(tmp_path / 'app.db').as_posix()}"
    store = KnowledgeBaseSnapshotStore(database_url)
    documents = [
        _document_record(
            document_id="doc-1",
            filename="alpha.pdf",
            content_hash="a" * 64,
            indexed_count=3,
        ),
        _document_record(
            document_id="doc-2",
            filename="beta.md",
            file_type="markdown",
            content_hash="b" * 64,
            indexed_count=2,
        ),
    ]

    snapshot = store.create_snapshot(
        created_by_user_id="user-1",
        organization_id=DEFAULT_ORGANIZATION_ID,
        workspace_id=DEFAULT_WORKSPACE_ID,
        knowledge_base_id=DEFAULT_KNOWLEDGE_BASE_ID,
        documents=documents,
        reason="before rollout",
    )
    listed = store.list_snapshots(knowledge_base_id=DEFAULT_KNOWLEDGE_BASE_ID)
    loaded = store.get_snapshot(snapshot.snapshot_id, knowledge_base_id=DEFAULT_KNOWLEDGE_BASE_ID)

    assert snapshot.snapshot_id.startswith("kbsnap_")
    assert snapshot.document_count == 2
    assert snapshot.indexed_chunk_count == 5
    assert snapshot.reason == "before rollout"
    assert snapshot.documents[0]["document_id"] == "doc-1"
    assert listed[0].snapshot_id == snapshot.snapshot_id
    assert loaded is not None
    assert loaded.content_hash == snapshot.content_hash
    assert store.get_snapshot(snapshot.snapshot_id, knowledge_base_id="kb-other") is None


def test_snapshot_hash_is_stable_when_document_order_changes():
    first = _document_record(document_id="doc-1", filename="alpha.pdf", content_hash="a" * 64)
    second = _document_record(document_id="doc-2", filename="beta.md", content_hash="b" * 64)

    forward_hash = calculate_snapshot_hash(summarize_documents([first, second]))
    reverse_hash = calculate_snapshot_hash(summarize_documents([second, first]))

    assert forward_hash == reverse_hash


def test_snapshot_api_creates_lists_and_reads_details(tmp_path, monkeypatch):
    settings = Settings(
        database_url=f"sqlite:///{(tmp_path / 'app.db').as_posix()}",
        document_metadata_path=str(tmp_path / "documents.json"),
    )
    monkeypatch.setattr(main, "get_settings", lambda: settings)
    document_store = DocumentStore(settings.document_metadata_path, database_url=settings.database_url)
    document_store.add_document(
        document_id="doc-1",
        filename="demo.pdf",
        file_type="pdf",
        content_hash="a" * 64,
        chunk_count=3,
        collection="rag_chunks",
        chunk_size=800,
        overlap=100,
        embedding_model="BAAI/bge-small-zh-v1.5",
        page_count=2,
        indexed_count=3,
        source_file_size=120,
        organization_id=DEFAULT_ORGANIZATION_ID,
        workspace_id=DEFAULT_WORKSPACE_ID,
        knowledge_base_id=DEFAULT_KNOWLEDGE_BASE_ID,
        owner_user_id="test-user",
        source_storage_backend="local",
        source_storage_key="org/ws/kb/doc/demo.pdf",
    )

    client = TestClient(main.app)
    create_response = client.post(
        f"/knowledge-bases/{DEFAULT_KNOWLEDGE_BASE_ID}/snapshots",
        json={"reason": "before release"},
        headers={"X-Request-ID": "req-snapshot-1"},
    )

    assert create_response.status_code == 200
    created = create_response.json()
    assert created["document_count"] == 1
    assert created["indexed_chunk_count"] == 3
    assert created["reason"] == "before release"
    assert created["documents"][0]["source_storage_key"] == "org/ws/kb/doc/demo.pdf"

    list_response = client.get(f"/knowledge-bases/{DEFAULT_KNOWLEDGE_BASE_ID}/snapshots")
    detail_response = client.get(
        f"/knowledge-bases/{DEFAULT_KNOWLEDGE_BASE_ID}/snapshots/{created['snapshot_id']}"
    )
    logs = AuditLogStore(settings.database_url).list_logs(limit=5)

    assert list_response.status_code == 200
    assert list_response.json()["snapshots"][0]["snapshot_id"] == created["snapshot_id"]
    assert "documents" not in list_response.json()["snapshots"][0]
    assert detail_response.status_code == 200
    assert detail_response.json()["content_hash"] == created["content_hash"]
    assert logs[0].action == "knowledge_base.snapshot.create"
    assert logs[0].request_id == "req-snapshot-1"
    assert logs[0].details["document_count"] == 1


def test_snapshot_api_rejects_inaccessible_knowledge_base(tmp_path, monkeypatch):
    settings = Settings(
        database_url=f"sqlite:///{(tmp_path / 'app.db').as_posix()}",
        document_metadata_path=str(tmp_path / "documents.json"),
    )
    monkeypatch.setattr(main, "get_settings", lambda: settings)
    permission_store = PermissionStore(settings.database_url)
    alice = AuthenticatedUser(user_id="user-alice", username="alice", role="user")
    bob = AuthenticatedUser(user_id="user-bob", username="bob", role="user")
    alice_access = permission_store.ensure_default_access(
        user_id=alice.user_id,
        username=alice.username,
        role=alice.role,
    )
    permission_store.ensure_default_access(
        user_id=bob.user_id,
        username=bob.username,
        role=bob.role,
    )

    main.app.dependency_overrides[get_current_user] = lambda: bob
    client = TestClient(main.app)
    response = client.post(f"/knowledge-bases/{alice_access.knowledge_base_id}/snapshots", json={})

    assert response.status_code == 403


def _document_record(
    *,
    document_id: str,
    filename: str,
    content_hash: str,
    file_type: str = "pdf",
    indexed_count: int = 1,
) -> DocumentRecord:
    return DocumentRecord(
        document_id=document_id,
        filename=filename,
        file_type=file_type,
        content_hash=content_hash,
        content_hash_prefix=content_hash[:12],
        chunk_count=indexed_count,
        created_at="2026-06-07T00:00:00+00:00",
        indexed_at="2026-06-07T00:00:00+00:00",
        source_file_size=120,
        collection="rag_chunks",
        chunk_size=800,
        overlap=100,
        embedding_model="BAAI/bge-small-zh-v1.5",
        page_count=1,
        indexed_count=indexed_count,
        organization_id=DEFAULT_ORGANIZATION_ID,
        workspace_id=DEFAULT_WORKSPACE_ID,
        knowledge_base_id=DEFAULT_KNOWLEDGE_BASE_ID,
        owner_user_id="user-1",
        source_storage_backend="local",
        source_storage_key=f"org/ws/kb/{document_id}/{filename}",
    )
