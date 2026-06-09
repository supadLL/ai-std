import pytest
from fastapi.testclient import TestClient

import app.auth as auth
import app.main as main
from app.config import Settings


pytestmark = pytest.mark.no_auth_override


def test_protected_endpoint_requires_bearer_token(tmp_path, monkeypatch):
    settings = Settings(
        user_store_path=str(tmp_path / "users.json"),
        database_url=f"sqlite:///{(tmp_path / 'app.db').as_posix()}",
        app_secret_key="test-secret",
    )
    _patch_settings(monkeypatch, settings)

    client = TestClient(main.app)
    response = client.get("/documents")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_bootstrap_login_and_me_flow(tmp_path, monkeypatch):
    settings = Settings(
        user_store_path=str(tmp_path / "users.json"),
        database_url=f"sqlite:///{(tmp_path / 'app.db').as_posix()}",
        app_secret_key="test-secret",
        access_token_expire_minutes=30,
    )
    _patch_settings(monkeypatch, settings)

    client = TestClient(main.app)

    bootstrap_response = client.post(
        "/auth/bootstrap-admin",
        json={"username": "admin", "password": "change-me-123"},
    )
    assert bootstrap_response.status_code == 200
    bootstrap_data = bootstrap_response.json()
    assert bootstrap_data["token_type"] == "bearer"
    assert bootstrap_data["user"]["username"] == "admin"
    assert "password" not in bootstrap_response.text
    assert "password_hash" not in bootstrap_response.text

    duplicate_response = client.post(
        "/auth/bootstrap-admin",
        json={"username": "other", "password": "change-me-123"},
    )
    assert duplicate_response.status_code == 409

    login_response = client.post(
        "/auth/login",
        json={"username": "admin", "password": "change-me-123"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    me_response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json()["user"]["role"] == "admin"

    bad_login_response = client.post(
        "/auth/login",
        json={"username": "admin", "password": "wrong-password"},
    )
    assert bad_login_response.status_code == 401


def test_register_user_after_admin_bootstrap_creates_default_access(tmp_path, monkeypatch):
    settings = Settings(
        user_store_path=str(tmp_path / "users.json"),
        database_url=f"sqlite:///{(tmp_path / 'app.db').as_posix()}",
        app_secret_key="test-secret",
        user_registration_enabled=True,
    )
    _patch_settings(monkeypatch, settings)

    client = TestClient(main.app)

    early_register_response = client.post(
        "/auth/register",
        json={"username": "alice", "password": "change-me-123"},
    )
    bootstrap_response = client.post(
        "/auth/bootstrap-admin",
        json={"username": "admin", "password": "change-me-123"},
    )
    register_response = client.post(
        "/auth/register",
        json={"username": "alice", "password": "change-me-123"},
    )
    duplicate_response = client.post(
        "/auth/register",
        json={"username": "alice", "password": "change-me-123"},
    )

    assert early_register_response.status_code == 409
    assert bootstrap_response.status_code == 200
    assert register_response.status_code == 200
    register_data = register_response.json()
    assert register_data["user"]["username"] == "alice"
    assert register_data["user"]["role"] == "user"
    assert "password" not in register_response.text
    assert "password_hash" not in register_response.text
    assert duplicate_response.status_code == 422

    token = register_data["access_token"]
    knowledge_bases_response = client.get(
        "/knowledge-bases",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert knowledge_bases_response.status_code == 200
    assert knowledge_bases_response.json()["knowledge_bases"][0]["role"] == "owner"


def test_register_user_can_be_disabled(tmp_path, monkeypatch):
    settings = Settings(
        user_store_path=str(tmp_path / "users.json"),
        database_url=f"sqlite:///{(tmp_path / 'app.db').as_posix()}",
        app_secret_key="test-secret",
        user_registration_enabled=False,
    )
    _patch_settings(monkeypatch, settings)

    client = TestClient(main.app)
    response = client.post(
        "/auth/register",
        json={"username": "alice", "password": "change-me-123"},
    )

    assert response.status_code == 403


def test_admin_can_create_and_list_users(tmp_path, monkeypatch):
    settings = Settings(
        user_store_path=str(tmp_path / "users.json"),
        database_url=f"sqlite:///{(tmp_path / 'app.db').as_posix()}",
        app_secret_key="test-secret",
    )
    _patch_settings(monkeypatch, settings)

    client = TestClient(main.app)
    bootstrap_response = client.post(
        "/auth/bootstrap-admin",
        json={"username": "admin", "password": "change-me-123"},
    )
    admin_token = bootstrap_response.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    create_response = client.post(
        "/admin/users",
        json={"username": "bob", "password": "change-me-123"},
        headers=admin_headers,
    )
    list_response = client.get("/admin/users", headers=admin_headers)
    bob_login_response = client.post(
        "/auth/login",
        json={"username": "bob", "password": "change-me-123"},
    )
    bob_token = bob_login_response.json()["access_token"]
    forbidden_response = client.get(
        "/admin/users",
        headers={"Authorization": f"Bearer {bob_token}"},
    )

    assert create_response.status_code == 200
    create_data = create_response.json()
    assert create_data["username"] == "bob"
    assert create_data["role"] == "user"
    assert create_data["status"] == "active"
    assert "password" not in create_response.text
    assert list_response.status_code == 200
    assert [user["username"] for user in list_response.json()["users"]] == ["admin", "bob"]
    assert bob_login_response.status_code == 200
    assert forbidden_response.status_code == 403


def test_openapi_exposes_auth_endpoints_and_bearer_scheme():
    client = TestClient(main.app)

    response = client.get("/openapi.json")

    assert response.status_code == 200
    data = response.json()
    assert "/auth/register" in data["paths"]
    assert "/auth/login" in data["paths"]
    assert "/auth/me" in data["paths"]
    assert "/admin/users" in data["paths"]
    assert any(
        scheme.get("type") == "http" and scheme.get("scheme") == "bearer"
        for scheme in data["components"]["securitySchemes"].values()
    )


def _patch_settings(monkeypatch, settings):
    monkeypatch.setattr(main, "get_settings", lambda: settings)
    main.app.dependency_overrides[auth.get_settings] = lambda: settings
    main.app.dependency_overrides.pop(auth.get_current_user, None)
