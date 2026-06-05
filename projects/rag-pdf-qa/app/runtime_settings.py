import json
from dataclasses import asdict, dataclass
from pathlib import Path

from app.config import Settings


DEFAULT_RUNTIME_SETTINGS_PATH = "data/runtime_settings.json"


@dataclass(frozen=True)
class RuntimeSettings:
    deepseek_api_key: str | None = None
    deepseek_base_url: str | None = None
    deepseek_model: str | None = None
    llm_provider: str | None = None
    llm_api_key: str | None = None
    llm_base_url: str | None = None
    llm_model: str | None = None
    request_timeout_seconds: float | None = None
    rag_system_prompt: str | None = None
    rag_answer_instructions: str | None = None


def load_runtime_settings(path: str = DEFAULT_RUNTIME_SETTINGS_PATH) -> RuntimeSettings:
    settings_path = Path(path)
    if not settings_path.exists():
        return RuntimeSettings()

    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Failed to load runtime settings: {exc}") from exc

    return RuntimeSettings(
        deepseek_api_key=_optional_str(data.get("deepseek_api_key")),
        deepseek_base_url=_optional_str(data.get("deepseek_base_url")),
        deepseek_model=_optional_str(data.get("deepseek_model")),
        llm_provider=_optional_str(data.get("llm_provider")),
        llm_api_key=_optional_str(data.get("llm_api_key")),
        llm_base_url=_optional_str(data.get("llm_base_url")),
        llm_model=_optional_str(data.get("llm_model")),
        request_timeout_seconds=_optional_float(data.get("request_timeout_seconds")),
        rag_system_prompt=_optional_str(data.get("rag_system_prompt")),
        rag_answer_instructions=_optional_str(data.get("rag_answer_instructions")),
    )


def save_runtime_settings(
    runtime_settings: RuntimeSettings,
    path: str = DEFAULT_RUNTIME_SETTINGS_PATH,
) -> RuntimeSettings:
    settings_path = Path(path)
    data = {
        key: value
        for key, value in asdict(runtime_settings).items()
        if value is not None
    }
    try:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError as exc:
        raise RuntimeError(f"Failed to save runtime settings: {exc}") from exc
    return runtime_settings


def apply_runtime_settings(settings: Settings, runtime_settings: RuntimeSettings) -> Settings:
    llm_provider = runtime_settings.llm_provider or settings.llm_provider
    llm_api_key = runtime_settings.llm_api_key or runtime_settings.deepseek_api_key or settings.llm_api_key
    llm_base_url = (runtime_settings.llm_base_url or runtime_settings.deepseek_base_url or settings.llm_base_url).rstrip("/")
    llm_model = runtime_settings.llm_model or runtime_settings.deepseek_model or settings.llm_model
    return Settings(
        deepseek_api_key=llm_api_key,
        deepseek_base_url=llm_base_url,
        deepseek_model=llm_model,
        llm_provider=llm_provider,
        llm_api_key=llm_api_key,
        llm_base_url=llm_base_url,
        llm_model=llm_model,
        request_timeout_seconds=runtime_settings.request_timeout_seconds or settings.request_timeout_seconds,
        embedding_model=settings.embedding_model,
        qdrant_local_path=settings.qdrant_local_path,
        qdrant_collection=settings.qdrant_collection,
        document_metadata_path=settings.document_metadata_path,
    )


def merge_runtime_settings(
    current: RuntimeSettings,
    *,
    deepseek_api_key: str | None = None,
    clear_api_key: bool = False,
    deepseek_base_url: str | None = None,
    deepseek_model: str | None = None,
    llm_provider: str | None = None,
    llm_api_key: str | None = None,
    llm_base_url: str | None = None,
    llm_model: str | None = None,
    request_timeout_seconds: float | None = None,
    rag_system_prompt: str | None = None,
    rag_answer_instructions: str | None = None,
) -> RuntimeSettings:
    return RuntimeSettings(
        deepseek_api_key=None if clear_api_key else _coalesce_optional(deepseek_api_key, current.deepseek_api_key),
        deepseek_base_url=_coalesce_optional(deepseek_base_url, current.deepseek_base_url),
        deepseek_model=_coalesce_optional(deepseek_model, current.deepseek_model),
        llm_provider=_coalesce_optional(llm_provider, current.llm_provider),
        llm_api_key=None if clear_api_key else _coalesce_optional(llm_api_key, current.llm_api_key),
        llm_base_url=_coalesce_optional(llm_base_url, current.llm_base_url),
        llm_model=_coalesce_optional(llm_model, current.llm_model),
        request_timeout_seconds=request_timeout_seconds
        if request_timeout_seconds is not None
        else current.request_timeout_seconds,
        rag_system_prompt=_coalesce_optional(rag_system_prompt, current.rag_system_prompt),
        rag_answer_instructions=_coalesce_optional(rag_answer_instructions, current.rag_answer_instructions),
    )


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def _coalesce_optional(new_value: str | None, current_value: str | None) -> str | None:
    if new_value is None:
        return current_value
    stripped = new_value.strip()
    return stripped or None
