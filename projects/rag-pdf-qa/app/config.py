import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv(encoding="utf-8-sig")


@dataclass(frozen=True)
class Settings:
    deepseek_api_key: str
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-v4-flash"
    request_timeout_seconds: float = 30.0
    embedding_model: str = "BAAI/bge-small-zh-v1.5"
    qdrant_local_path: str = ".qdrant"
    qdrant_collection: str = "rag_chunks"


def get_settings() -> Settings:
    load_dotenv(override=True, encoding="utf-8-sig")

    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
    model = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash").strip()
    timeout = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))
    embedding_model = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5").strip()
    qdrant_local_path = os.getenv("QDRANT_LOCAL_PATH", ".qdrant").strip()
    qdrant_collection = os.getenv("QDRANT_COLLECTION", "rag_chunks").strip()

    return Settings(
        deepseek_api_key=api_key,
        deepseek_base_url=base_url,
        deepseek_model=model,
        request_timeout_seconds=timeout,
        embedding_model=embedding_model,
        qdrant_local_path=qdrant_local_path,
        qdrant_collection=qdrant_collection,
    )
