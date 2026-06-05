from app.config import Settings
from app.runtime_settings import RuntimeSettings, apply_runtime_settings, merge_runtime_settings


def test_apply_runtime_settings_prefers_generic_llm_fields():
    base = Settings(
        deepseek_api_key="old-env-key",
        deepseek_base_url="https://api.deepseek.com",
        deepseek_model="deepseek-chat",
        llm_provider="deepseek",
        llm_api_key="env-key",
        llm_base_url="https://env.example/v1",
        llm_model="env-model",
    )
    runtime = RuntimeSettings(
        llm_provider="qwen",
        llm_api_key="runtime-key",
        llm_base_url="https://runtime.example/v1",
        llm_model="runtime-model",
    )

    effective = apply_runtime_settings(base, runtime)

    assert effective.llm_provider == "qwen"
    assert effective.llm_api_key == "runtime-key"
    assert effective.llm_base_url == "https://runtime.example/v1"
    assert effective.llm_model == "runtime-model"
    assert effective.deepseek_api_key == "runtime-key"
    assert effective.deepseek_model == "runtime-model"


def test_merge_runtime_settings_can_clear_generic_and_legacy_api_keys():
    current = RuntimeSettings(
        deepseek_api_key="old-runtime-key",
        llm_api_key="runtime-key",
        llm_provider="deepseek",
    )

    merged = merge_runtime_settings(
        current,
        clear_api_key=True,
        llm_provider="ollama",
        llm_base_url="http://127.0.0.1:11434/v1",
        llm_model="qwen2.5",
    )

    assert merged.deepseek_api_key is None
    assert merged.llm_api_key is None
    assert merged.llm_provider == "ollama"
    assert merged.llm_base_url == "http://127.0.0.1:11434/v1"
    assert merged.llm_model == "qwen2.5"
