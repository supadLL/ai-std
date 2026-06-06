from dataclasses import dataclass, field

from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError

from app.config import Settings, get_settings
from app.db import database_url_from_legacy_path, session_scope
from app.models import LlmProfileModel, RuntimeSettingModel
from app.security import SecurityError, decrypt_secret, encrypt_secret


DEFAULT_RUNTIME_SETTINGS_PATH = "data/runtime_settings.json"
DEFAULT_LLM_PROFILE_ID = "default"
SECRET_RUNTIME_SETTING_KEYS = {"deepseek_api_key", "llm_api_key"}


@dataclass(frozen=True)
class LlmRuntimeProfile:
    profile_id: str
    name: str
    provider: str
    base_url: str
    model: str
    api_key: str | None = None


@dataclass(frozen=True)
class RuntimeSettings:
    deepseek_api_key: str | None = None
    deepseek_base_url: str | None = None
    deepseek_model: str | None = None
    llm_provider: str | None = None
    llm_api_key: str | None = None
    llm_base_url: str | None = None
    llm_model: str | None = None
    active_llm_profile_id: str | None = None
    llm_profiles: tuple[LlmRuntimeProfile, ...] = field(default_factory=tuple)
    request_timeout_seconds: float | None = None
    rag_system_prompt: str | None = None
    rag_answer_instructions: str | None = None


def load_runtime_settings(
    path: str = DEFAULT_RUNTIME_SETTINGS_PATH,
    database_url: str | None = None,
) -> RuntimeSettings:
    resolved_database_url = _resolve_database_url(path=path, database_url=database_url)
    secret_key = _runtime_secret_key()
    try:
        with session_scope(resolved_database_url) as session:
            data = {
                item.key: item.value
                for item in session.scalars(select(RuntimeSettingModel)).all()
            }
            profiles = tuple(
                LlmRuntimeProfile(
                    profile_id=profile.profile_id,
                    name=profile.name,
                    provider=profile.provider,
                    base_url=profile.base_url,
                    model=profile.model,
                    api_key=_optional_secret(profile.api_key, secret_key),
                )
                for profile in session.scalars(select(LlmProfileModel).order_by(LlmProfileModel.name)).all()
            )
    except SQLAlchemyError as exc:
        raise RuntimeError(f"Failed to load runtime settings from database: {exc}") from exc
    except SecurityError as exc:
        raise RuntimeError(f"Failed to decrypt runtime settings secret: {exc}") from exc

    return RuntimeSettings(
        deepseek_api_key=_optional_secret(data.get("deepseek_api_key"), secret_key),
        deepseek_base_url=_optional_str(data.get("deepseek_base_url")),
        deepseek_model=_optional_str(data.get("deepseek_model")),
        llm_provider=_optional_str(data.get("llm_provider")),
        llm_api_key=_optional_secret(data.get("llm_api_key"), secret_key),
        llm_base_url=_optional_str(data.get("llm_base_url")),
        llm_model=_optional_str(data.get("llm_model")),
        active_llm_profile_id=_optional_str(data.get("active_llm_profile_id")),
        llm_profiles=profiles,
        request_timeout_seconds=_optional_float(data.get("request_timeout_seconds")),
        rag_system_prompt=_optional_str(data.get("rag_system_prompt")),
        rag_answer_instructions=_optional_str(data.get("rag_answer_instructions")),
    )


def save_runtime_settings(
    runtime_settings: RuntimeSettings,
    path: str = DEFAULT_RUNTIME_SETTINGS_PATH,
    database_url: str | None = None,
) -> RuntimeSettings:
    resolved_database_url = _resolve_database_url(path=path, database_url=database_url)
    secret_key = _runtime_secret_key()
    scalar_values = _runtime_scalar_values(runtime_settings, secret_key=secret_key)
    try:
        with session_scope(resolved_database_url) as session:
            session.execute(delete(RuntimeSettingModel))
            session.execute(delete(LlmProfileModel))
            for key, value in scalar_values.items():
                session.add(RuntimeSettingModel(key=key, value=value))
            for profile in runtime_settings.llm_profiles:
                session.add(
                    LlmProfileModel(
                        profile_id=profile.profile_id,
                        name=profile.name,
                        provider=profile.provider,
                        base_url=profile.base_url,
                        model=profile.model,
                        api_key=encrypt_secret(profile.api_key, secret_key),
                    )
                )
    except SQLAlchemyError as exc:
        raise RuntimeError(f"Failed to save runtime settings to database: {exc}") from exc
    except SecurityError as exc:
        raise RuntimeError(f"Failed to encrypt runtime settings secret: {exc}") from exc
    return runtime_settings


def apply_runtime_settings(settings: Settings, runtime_settings: RuntimeSettings) -> Settings:
    active_profile = get_active_llm_profile(runtime_settings)
    llm_provider = active_profile.provider if active_profile else runtime_settings.llm_provider or settings.llm_provider
    llm_api_key = (
        (active_profile.api_key if active_profile else None)
        or runtime_settings.llm_api_key
        or runtime_settings.deepseek_api_key
        or settings.llm_api_key
    )
    llm_base_url = (
        (active_profile.base_url if active_profile else None)
        or runtime_settings.llm_base_url
        or runtime_settings.deepseek_base_url
        or settings.llm_base_url
    ).rstrip("/")
    llm_model = active_profile.model if active_profile else runtime_settings.llm_model or runtime_settings.deepseek_model or settings.llm_model
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
        qdrant_mode=settings.qdrant_mode,
        qdrant_url=settings.qdrant_url,
        qdrant_api_key=settings.qdrant_api_key,
        qdrant_collection_prefix=settings.qdrant_collection_prefix,
        qdrant_collection=settings.qdrant_collection,
        document_metadata_path=settings.document_metadata_path,
        user_store_path=settings.user_store_path,
        database_url=settings.database_url,
        app_secret_key=settings.app_secret_key,
        access_token_expire_minutes=settings.access_token_expire_minutes,
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
        active_llm_profile_id=current.active_llm_profile_id,
        llm_profiles=current.llm_profiles,
        request_timeout_seconds=request_timeout_seconds
        if request_timeout_seconds is not None
        else current.request_timeout_seconds,
        rag_system_prompt=_coalesce_optional(rag_system_prompt, current.rag_system_prompt),
        rag_answer_instructions=_coalesce_optional(rag_answer_instructions, current.rag_answer_instructions),
    )


def get_active_llm_profile(runtime_settings: RuntimeSettings) -> LlmRuntimeProfile | None:
    if not runtime_settings.llm_profiles:
        return None
    active_profile_id = runtime_settings.active_llm_profile_id
    if active_profile_id:
        for profile in runtime_settings.llm_profiles:
            if profile.profile_id == active_profile_id:
                return profile
    return runtime_settings.llm_profiles[0]


def replace_llm_profiles(
    runtime_settings: RuntimeSettings,
    *,
    profiles: tuple[LlmRuntimeProfile, ...],
    active_profile_id: str | None,
) -> RuntimeSettings:
    return RuntimeSettings(
        deepseek_api_key=runtime_settings.deepseek_api_key,
        deepseek_base_url=runtime_settings.deepseek_base_url,
        deepseek_model=runtime_settings.deepseek_model,
        llm_provider=runtime_settings.llm_provider,
        llm_api_key=runtime_settings.llm_api_key,
        llm_base_url=runtime_settings.llm_base_url,
        llm_model=runtime_settings.llm_model,
        active_llm_profile_id=active_profile_id,
        llm_profiles=profiles,
        request_timeout_seconds=runtime_settings.request_timeout_seconds,
        rag_system_prompt=runtime_settings.rag_system_prompt,
        rag_answer_instructions=runtime_settings.rag_answer_instructions,
    )


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_secret(value: object, secret_key: str) -> str | None:
    text = _optional_str(value)
    if text is None:
        return None
    try:
        decrypted = decrypt_secret(text, secret_key)
    except SecurityError as exc:
        raise RuntimeError(f"Failed to decrypt runtime settings secret: {exc}") from exc
    return _optional_str(decrypted)


def _optional_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def _coalesce_optional(new_value: str | None, current_value: str | None) -> str | None:
    if new_value is None:
        return current_value
    stripped = new_value.strip()
    return stripped or None


def _runtime_scalar_values(runtime_settings: RuntimeSettings, *, secret_key: str) -> dict[str, str]:
    values: dict[str, object | None] = {
        "deepseek_api_key": runtime_settings.deepseek_api_key,
        "deepseek_base_url": runtime_settings.deepseek_base_url,
        "deepseek_model": runtime_settings.deepseek_model,
        "llm_provider": runtime_settings.llm_provider,
        "llm_api_key": runtime_settings.llm_api_key,
        "llm_base_url": runtime_settings.llm_base_url,
        "llm_model": runtime_settings.llm_model,
        "active_llm_profile_id": runtime_settings.active_llm_profile_id,
        "request_timeout_seconds": runtime_settings.request_timeout_seconds,
        "rag_system_prompt": runtime_settings.rag_system_prompt,
        "rag_answer_instructions": runtime_settings.rag_answer_instructions,
    }
    serialized: dict[str, str] = {}
    for key, value in values.items():
        if value is None:
            continue
        text = str(value)
        if key in SECRET_RUNTIME_SETTING_KEYS:
            encrypted = encrypt_secret(text, secret_key)
            if encrypted is None:
                continue
            serialized[key] = encrypted
        else:
            serialized[key] = text
    return serialized


def _resolve_database_url(path: str, database_url: str | None) -> str:
    if database_url:
        return database_url
    if path != DEFAULT_RUNTIME_SETTINGS_PATH:
        return database_url_from_legacy_path(path)
    return get_settings().database_url


def _runtime_secret_key() -> str:
    settings = get_settings()
    return settings.secret_encryption_key or settings.app_secret_key
