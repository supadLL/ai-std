from fastapi.testclient import TestClient

import app.main as main
from app.auth import AuthenticatedUser, get_current_user
from app.config import Settings
from app.document_store import DocumentStore
from app.permissions import PermissionStore
from app.text_splitter import TextChunk
from app.vector_store import upsert_chunks


def test_user_cannot_access_another_users_knowledge_base_documents(tmp_path, monkeypatch):
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
    bob_access = permission_store.ensure_default_access(
        user_id=bob.user_id,
        username=bob.username,
        role=bob.role,
    )

    document_store = DocumentStore(settings.document_metadata_path, database_url=settings.database_url)
    document_store.add_document(
        document_id="doc-alice",
        filename="alice.md",
        file_type="markdown",
        content_hash="a" * 64,
        chunk_count=1,
        collection="rag_chunks",
        chunk_size=800,
        overlap=100,
        embedding_model="BAAI/bge-small-zh-v1.5",
        page_count=1,
        indexed_count=1,
        source_file_size=120,
        organization_id=alice_access.organization_id,
        workspace_id=alice_access.workspace_id,
        knowledge_base_id=alice_access.knowledge_base_id,
        owner_user_id=alice.user_id,
    )

    main.app.dependency_overrides[get_current_user] = lambda: bob
    client = TestClient(main.app)

    forbidden_response = client.get(f"/knowledge-bases/{alice_access.knowledge_base_id}/documents")
    own_response = client.get(f"/knowledge-bases/{bob_access.knowledge_base_id}/documents")

    assert forbidden_response.status_code == 403
    assert own_response.status_code == 200
    assert own_response.json()["documents"] == []


def test_qdrant_payload_carries_tenant_and_knowledge_base_ids():
    class FakeClient:
        def __init__(self):
            self.points = []

        def upsert(self, collection_name, points):
            self.collection_name = collection_name
            self.points = points

    fake_client = FakeClient()

    indexed_count = upsert_chunks(
        client=fake_client,
        collection_name="rag_chunks",
        filename="demo.md",
        chunks=[TextChunk(chunk_id=1, page_number=1, char_count=10, text="hello rag")],
        vectors=[[0.1, 0.2, 0.3]],
        document_id="doc-1",
        content_hash="a" * 64,
        file_type="markdown",
        tenant_id="org-1",
        workspace_id="ws-1",
        knowledge_base_id="kb-1",
    )

    payload = fake_client.points[0].payload
    assert indexed_count == 1
    assert payload["tenant_id"] == "org-1"
    assert payload["organization_id"] == "org-1"
    assert payload["workspace_id"] == "ws-1"
    assert payload["knowledge_base_id"] == "kb-1"
