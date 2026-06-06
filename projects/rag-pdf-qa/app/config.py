import os
import re
from dataclasses import dataclass

from dotenv import load_dotenv

from app.llm_providers import get_provider_option, normalize_provider


load_dotenv(encoding="utf-8-sig")


@dataclass(frozen=True)
class Settings:
    app_env: str = "development"
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-v4-flash"
    llm_provider: str = "deepseek"
    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com"
    llm_model: str = "deepseek-v4-flash"
    request_timeout_seconds: float = 30.0
    embedding_model: str = "BAAI/bge-small-zh-v1.5"
    qdrant_local_path: str = ".qdrant"
    qdrant_mode: str = "local"
    qdrant_url: str = "http://127.0.0.1:6333"
    qdrant_api_key: str = ""
    qdrant_collection_prefix: str = "rag"
    qdrant_collection: str = "rag_chunks"
    document_metadata_path: str = "data/documents.json"
    user_store_path: str = "data/users.json"
    index_job_storage_path: str = "data/index_jobs"
    database_url: str = "sqlite:///data/app.db"
    redis_url: str = "redis://127.0.0.1:6379/0"
    app_secret_key: str = "change-this-local-development-secret"
    secret_encryption_key: str = ""
    access_token_expire_minutes: int = 480
    max_upload_bytes: int = 10 * 1024 * 1024
    rate_limit_enabled: bool = False
    rate_limit_requests: int = 120
    rate_limit_window_seconds: int = 60
    source_storage_enabled: bool = False
    source_storage_backend: str = "local"
    source_storage_path: str = "data/source_files"

    def __post_init__(self) -> None:
        if not self.llm_api_key and self.deepseek_api_key:
            object.__setattr__(self, "llm_api_key", self.deepseek_api_key)
        if self.llm_base_url == "https://api.deepseek.com" and self.deepseek_base_url != self.llm_base_url:
            object.__setattr__(self, "llm_base_url", self.deepseek_base_url)
        if self.llm_model == "deepseek-v4-flash" and self.deepseek_model != self.llm_model:
            object.__setattr__(self, "llm_model", self.deepseek_model)


def get_settings() -> Settings:
    load_dotenv(override=True, encoding="utf-8-sig")

    app_env = os.getenv("APP_ENV", "development").strip().lower() or "development"
    provider = normalize_provider(os.getenv("LLM_PROVIDER", "deepseek"))
    provider_option = get_provider_option(provider)
    api_key = (os.getenv("LLM_API_KEY") or os.getenv("DEEPSEEK_API_KEY", "")).strip()
    base_url = (
        os.getenv("LLM_BASE_URL")
        or os.getenv("DEEPSEEK_BASE_URL")
        or provider_option.default_base_url
    ).rstrip("/")
    model = (
        os.getenv("LLM_MODEL")
        or os.getenv("DEEPSEEK_MODEL")
        or (provider_option.default_models[0] if provider_option.default_models else "")
    ).strip()
    timeout = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))
    embedding_model = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5").strip()
    qdrant_local_path = os.getenv("QDRANT_LOCAL_PATH", ".qdrant").strip()
    qdrant_mode = os.getenv("QDRANT_MODE", "local").strip().lower() or "local"
    qdrant_url = os.getenv("QDRANT_URL", "http://127.0.0.1:6333").strip().rstrip("/")
    qdrant_api_key = os.getenv("QDRANT_API_KEY", "").strip()
    qdrant_collection_prefix = _sanitize_qdrant_collection_part(
        os.getenv("QDRANT_COLLECTION_PREFIX", "rag")
    ) or "rag"
    qdrant_collection_env = os.getenv("QDRANT_COLLECTION")
    qdrant_collection = (
        qdrant_collection_env.strip()
        if qdrant_collection_env and qdrant_collection_env.strip()
        else f"{qdrant_collection_prefix}_chunks"
    )
    document_metadata_path = os.getenv("DOCUMENT_METADATA_PATH", "data/documents.json").strip()
    user_store_path = os.getenv("USER_STORE_PATH", "data/users.json").strip()
    index_job_storage_path = os.getenv("INDEX_JOB_STORAGE_PATH", "data/index_jobs").strip()
    database_url = os.getenv("DATABASE_URL", "sqlite:///data/app.db").strip()
    redis_url = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0").strip()
    app_secret_key = os.getenv("APP_SECRET_KEY", "change-this-local-development-secret").strip()
    secret_encryption_key = os.getenv("SECRET_ENCRYPTION_KEY", "").strip()
    access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))
    max_upload_bytes = max(1, int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024))))
    rate_limit_enabled = _parse_bool(
        os.getenv("RATE_LIMIT_ENABLED"),
        default=app_env == "production",
    )
    rate_limit_requests = max(1, int(os.getenv("RATE_LIMIT_REQUESTS", "120")))
    rate_limit_window_seconds = max(1, int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60")))
    source_storage_enabled = _parse_bool(os.getenv("SOURCE_STORAGE_ENABLED"), default=app_env == "production")
    source_storage_backend = os.getenv("SOURCE_STORAGE_BACKEND", "local").strip().lower() or "local"
    source_storage_path = os.getenv("SOURCE_STORAGE_PATH", "data/source_files").strip()

    return Settings(
        app_env=app_env,
        deepseek_api_key=api_key,
        deepseek_base_url=base_url,
        deepseek_model=model,
        llm_provider=provider,
        llm_api_key=api_key,
        llm_base_url=base_url,
        llm_model=model,
        request_timeout_seconds=timeout,
        embedding_model=embedding_model,
        qdrant_local_path=qdrant_local_path,
        qdrant_mode=qdrant_mode,
        qdrant_url=qdrant_url,
        qdrant_api_key=qdrant_api_key,
        qdrant_collection_prefix=qdrant_collection_prefix,
        qdrant_collection=qdrant_collection,
        document_metadata_path=document_metadata_path,
        user_store_path=user_store_path,
        index_job_storage_path=index_job_storage_path,
        database_url=database_url,
        redis_url=redis_url,
        app_secret_key=app_secret_key,
        secret_encryption_key=secret_encryption_key,
        access_token_expire_minutes=access_token_expire_minutes,
        max_upload_bytes=max_upload_bytes,
        rate_limit_enabled=rate_limit_enabled,
        rate_limit_requests=rate_limit_requests,
        rate_limit_window_seconds=rate_limit_window_seconds,
        source_storage_enabled=source_storage_enabled,
        source_storage_backend=source_storage_backend,
        source_storage_path=source_storage_path,
    )


def _sanitize_qdrant_collection_part(value: str | None) -> str:
    text = (value or "").strip()
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", text).strip("_")


def _parse_bool(value: str | None, *, default: bool) -> bool:
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}
