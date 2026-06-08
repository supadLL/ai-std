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


def test_openapi_exposes_auth_endpoints_and_bearer_scheme():
    client = TestClient(main.app)

    response = client.get("/openapi.json")

    assert response.status_code == 200
    data = response.json()
    assert "/auth/login" in data["paths"]
    assert "/auth/me" in data["paths"]
    assert any(
        scheme.get("type") == "http" and scheme.get("scheme") == "bearer"
        for scheme in data["components"]["securitySchemes"].values()
    )


def _patch_settings(monkeypatch, settings):
    monkeypatch.setattr(main, "get_settings", lambda: settings)
    main.app.dependency_overrides[auth.get_settings] = lambda: settings
    main.app.dependency_overrides.pop(auth.get_current_user, None)
