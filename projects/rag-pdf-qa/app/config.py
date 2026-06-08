import os
from dataclasses import dataclass

from dotenv import load_dotenv

from app.llm_providers import get_provider_option, normalize_provider


load_dotenv(encoding="utf-8-sig")


@dataclass(frozen=True)
class Settings:
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
    qdrant_collection: str = "rag_chunks"
    document_metadata_path: str = "data/documents.json"
    user_store_path: str = "data/users.json"
    index_job_storage_path: str = "data/index_jobs"
    database_url: str = "sqlite:///data/app.db"
    app_secret_key: str = "change-this-local-development-secret"
    access_token_expire_minutes: int = 480

    def __post_init__(self) -> None:
        if not self.llm_api_key and self.deepseek_api_key:
            object.__setattr__(self, "llm_api_key", self.deepseek_api_key)
        if self.llm_base_url == "https://api.deepseek.com" and self.deepseek_base_url != self.llm_base_url:
            object.__setattr__(self, "llm_base_url", self.deepseek_base_url)
        if self.llm_model == "deepseek-v4-flash" and self.deepseek_model != self.llm_model:
            object.__setattr__(self, "llm_model", self.deepseek_model)


def get_settings() -> Settings:
    load_dotenv(override=True, encoding="utf-8-sig")

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
    qdrant_collection = os.getenv("QDRANT_COLLECTION", "rag_chunks").strip()
    document_metadata_path = os.getenv("DOCUMENT_METADATA_PATH", "data/documents.json").strip()
    user_store_path = os.getenv("USER_STORE_PATH", "data/users.json").strip()
    index_job_storage_path = os.getenv("INDEX_JOB_STORAGE_PATH", "data/index_jobs").strip()
    database_url = os.getenv("DATABASE_URL", "sqlite:///data/app.db").strip()
    app_secret_key = os.getenv("APP_SECRET_KEY", "change-this-local-development-secret").strip()
    access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

    return Settings(
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
        qdrant_collection=qdrant_collection,
        document_metadata_path=document_metadata_path,
        user_store_path=user_store_path,
        index_job_storage_path=index_job_storage_path,
        database_url=database_url,
        app_secret_key=app_secret_key,
        access_token_expire_minutes=access_token_expire_minutes,
    )
