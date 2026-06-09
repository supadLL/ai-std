from fastapi.testclient import TestClient

import app.main as main
from app.auth import AuthenticatedUser, get_current_user
from app.config import Settings
from app.document_store import DocumentStore
from app.permissions import PermissionStore
from app.text_splitter import TextChunk
from app.user_store import UserStore
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


def test_knowledge_base_owner_can_manage_members(tmp_path, monkeypatch):
    settings = Settings(
        database_url=f"sqlite:///{(tmp_path / 'app.db').as_posix()}",
        document_metadata_path=str(tmp_path / "documents.json"),
        user_store_path=str(tmp_path / "users.json"),
    )
    monkeypatch.setattr(main, "get_settings", lambda: settings)

    user_store = UserStore(settings.user_store_path, database_url=settings.database_url)
    owner_record = user_store.create_user(username="owner", password="change-me-123", role="user")
    member_record = user_store.create_user(username="member", password="change-me-123", role="user")
    owner = AuthenticatedUser(user_id=owner_record.user_id, username=owner_record.username, role=owner_record.role)
    member = AuthenticatedUser(user_id=member_record.user_id, username=member_record.username, role=member_record.role)
    permission_store = PermissionStore(settings.database_url)
    owner_access = permission_store.ensure_default_access(
        user_id=owner.user_id,
        username=owner.username,
        role=owner.role,
    )

    main.app.dependency_overrides[get_current_user] = lambda: owner
    client = TestClient(main.app)
    list_before_response = client.get(f"/knowledge-bases/{owner_access.knowledge_base_id}/members")
    add_response = client.post(
        f"/knowledge-bases/{owner_access.knowledge_base_id}/members",
        json={"username": "member"},
    )

    main.app.dependency_overrides[get_current_user] = lambda: member
    member_kb_response = client.get("/knowledge-bases")
    forbidden_member_manage_response = client.get(f"/knowledge-bases/{owner_access.knowledge_base_id}/members")

    main.app.dependency_overrides[get_current_user] = lambda: owner
    remove_response = client.delete(
        f"/knowledge-bases/{owner_access.knowledge_base_id}/members/{member.user_id}"
    )

    main.app.dependency_overrides[get_current_user] = lambda: member
    forbidden_after_remove_response = client.get(f"/knowledge-bases/{owner_access.knowledge_base_id}/documents")

    assert list_before_response.status_code == 200
    assert list_before_response.json()["members"][0]["username"] == "owner"
    assert list_before_response.json()["members"][0]["role"] == "owner"
    assert add_response.status_code == 200
    assert add_response.json()["username"] == "member"
    assert add_response.json()["role"] == "member"
    assert owner_access.knowledge_base_id in {
        knowledge_base["knowledge_base_id"]
        for knowledge_base in member_kb_response.json()["knowledge_bases"]
    }
    assert forbidden_member_manage_response.status_code == 403
    assert remove_response.status_code == 200
    assert remove_response.json()["user_id"] == member.user_id
    assert forbidden_after_remove_response.status_code == 403


def test_admin_can_manage_any_knowledge_base_members(tmp_path, monkeypatch):
    settings = Settings(
        database_url=f"sqlite:///{(tmp_path / 'app.db').as_posix()}",
        user_store_path=str(tmp_path / "users.json"),
    )
    monkeypatch.setattr(main, "get_settings", lambda: settings)

    user_store = UserStore(settings.user_store_path, database_url=settings.database_url)
    admin_record = user_store.create_user(username="admin", password="change-me-123", role="admin")
    owner_record = user_store.create_user(username="owner", password="change-me-123", role="user")
    target_record = user_store.create_user(username="target", password="change-me-123", role="user")
    admin = AuthenticatedUser(user_id=admin_record.user_id, username=admin_record.username, role=admin_record.role)
    owner = AuthenticatedUser(user_id=owner_record.user_id, username=owner_record.username, role=owner_record.role)
    permission_store = PermissionStore(settings.database_url)
    owner_access = permission_store.ensure_default_access(
        user_id=owner.user_id,
        username=owner.username,
        role=owner.role,
    )

    main.app.dependency_overrides[get_current_user] = lambda: admin
    client = TestClient(main.app)
    add_response = client.post(
        f"/knowledge-bases/{owner_access.knowledge_base_id}/members",
        json={"username": target_record.username},
    )
    missing_response = client.post(
        f"/knowledge-bases/{owner_access.knowledge_base_id}/members",
        json={"username": "missing"},
    )

    assert add_response.status_code == 200
    assert add_response.json()["username"] == target_record.username
    assert missing_response.status_code == 404


def test_cannot_remove_last_knowledge_base_owner(tmp_path):
    settings = Settings(
        database_url=f"sqlite:///{(tmp_path / 'app.db').as_posix()}",
        user_store_path=str(tmp_path / "users.json"),
    )
    user_store = UserStore(settings.user_store_path, database_url=settings.database_url)
    owner = user_store.create_user(username="owner", password="change-me-123", role="user")
    permission_store = PermissionStore(settings.database_url)
    owner_access = permission_store.ensure_default_access(
        user_id=owner.user_id,
        username=owner.username,
        role=owner.role,
    )

    try:
        permission_store.remove_member(
            knowledge_base_id=owner_access.knowledge_base_id,
            user_id=owner.user_id,
        )
    except Exception as exc:
        assert "last owner" in str(exc)
    else:
        raise AssertionError("Expected last owner removal to fail")


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
