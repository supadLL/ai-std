from app.document_store import DocumentStore
from app.runtime_settings import (
    LlmRuntimeProfile,
    RuntimeSettings,
    load_runtime_settings,
    save_runtime_settings,
)
from app.user_store import UserStore


def test_user_store_persists_users_in_database(tmp_path):
    database_url = f"sqlite:///{(tmp_path / 'app.db').as_posix()}"
    store = UserStore("unused.json", database_url=database_url)

    user = store.create_user(username="admin", password="change-me-123", role="admin")

    assert user.user_id.startswith("u_")
    assert store.has_users() is True
    assert store.get_user(user.user_id).username == "admin"
    assert store.authenticate(username="admin", password="change-me-123") is not None
    assert store.authenticate(username="admin", password="bad-password") is None


def test_document_store_persists_document_metadata_in_database(tmp_path):
    database_url = f"sqlite:///{(tmp_path / 'app.db').as_posix()}"
    store = DocumentStore("unused.json", database_url=database_url)

    record = store.add_document(
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
    )

    assert record.content_hash_prefix == "a" * 12
    assert store.list_documents()[0].document_id == "doc-1"
    assert store.get_document_by_content_hash("a" * 64).filename == "demo.pdf"
    assert store.remove_document("doc-1").document_id == "doc-1"
    assert store.list_documents() == []


def test_runtime_settings_and_llm_profiles_persist_in_database(tmp_path):
    database_url = f"sqlite:///{(tmp_path / 'app.db').as_posix()}"
    runtime_settings = RuntimeSettings(
        llm_provider="qwen",
        llm_base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        llm_model="qwen-plus",
        active_llm_profile_id="qwen-profile",
        request_timeout_seconds=60,
        rag_system_prompt="system prompt",
        rag_answer_instructions="answer prompt",
        llm_profiles=(
            LlmRuntimeProfile(
                profile_id="qwen-profile",
                name="Qwen Plus",
                provider="qwen",
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                model="qwen-plus",
                api_key="secret",
            ),
        ),
    )

    save_runtime_settings(runtime_settings, database_url=database_url)
    loaded = load_runtime_settings(database_url=database_url)

    assert loaded.llm_provider == "qwen"
    assert loaded.llm_model == "qwen-plus"
    assert loaded.active_llm_profile_id == "qwen-profile"
    assert loaded.request_timeout_seconds == 60
    assert loaded.rag_system_prompt == "system prompt"
    assert loaded.llm_profiles[0].api_key == "secret"
