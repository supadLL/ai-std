from fastapi.testclient import TestClient

import app.main as main
from app.audit import AUDIT_STATUS_FAILURE, AuditLogStore
from app.config import Settings
from app.runtime_settings import RuntimeSettings


def test_audit_log_store_records_and_summarizes_events(tmp_path):
    database_url = f"sqlite:///{(tmp_path / 'app.db').as_posix()}"
    store = AuditLogStore(database_url)

    record = store.record(
        action="document.index",
        request_id="req-1",
        user_id="user-1",
        username="alice",
        organization_id="org-1",
        workspace_id="ws-1",
        knowledge_base_id="kb-1",
        resource_type="document",
        resource_id="doc-1",
        duration_ms=12,
        details={"filename": "demo.pdf"},
    )
    store.record(action="rag.ask", status=AUDIT_STATUS_FAILURE, error_message="no chunks")

    logs = store.list_logs(limit=10)
    metrics = store.summarize()

    assert record.audit_log_id.startswith("audit_")
    assert logs[1].request_id == "req-1"
    assert logs[1].details == {"filename": "demo.pdf"}
    assert metrics.audit_log_count == 2
    assert metrics.failure_count == 1
    assert metrics.action_counts["document.index"] == 1
    assert metrics.action_counts["rag.ask"] == 1


def test_settings_update_writes_audit_log_with_request_id(tmp_path, monkeypatch):
    settings = Settings(
        database_url=f"sqlite:///{(tmp_path / 'app.db').as_posix()}",
        llm_api_key="env-secret",
    )
    saved = {}

    monkeypatch.setattr(main, "get_settings", lambda: settings)
    monkeypatch.setattr(main, "load_runtime_settings", lambda: RuntimeSettings())

    def fake_save_runtime_settings(runtime_settings):
        saved["runtime_settings"] = runtime_settings
        return runtime_settings

    monkeypatch.setattr(main, "save_runtime_settings", fake_save_runtime_settings)

    client = TestClient(main.app)
    response = client.put(
        "/settings",
        json={"llm_provider": "qwen", "llm_model": "qwen-plus"},
        headers={"X-Request-ID": "req-audit-1"},
    )

    logs = AuditLogStore(settings.database_url).list_logs(limit=5)

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "req-audit-1"
    assert saved["runtime_settings"].llm_provider == "qwen"
    assert logs[0].action == "settings.update"
    assert logs[0].request_id == "req-audit-1"
    assert logs[0].user_id == "test-user"
    assert logs[0].details["llm_model"] == "qwen-plus"
    assert "env-secret" not in response.text


def test_audit_logs_and_metrics_endpoints_return_observability_data(tmp_path, monkeypatch):
    settings = Settings(database_url=f"sqlite:///{(tmp_path / 'app.db').as_posix()}")
    monkeypatch.setattr(main, "get_settings", lambda: settings)
    AuditLogStore(settings.database_url).record(action="rag.ask", user_id="test-user")

    client = TestClient(main.app)
    audit_response = client.get("/audit-logs")
    metrics_response = client.get("/metrics")

    assert audit_response.status_code == 200
    assert audit_response.json()["logs"][0]["action"] == "rag.ask"
    assert metrics_response.status_code == 200
    assert metrics_response.json()["audit_log_count"] == 1
    assert metrics_response.json()["audit_action_counts"]["rag.ask"] == 1
