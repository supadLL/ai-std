from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class LlmProviderOption:
    provider: str
    label: str
    default_base_url: str
    default_models: list[str]
    api_key_required: bool = True
    note: str = ""


PROVIDER_OPTIONS = (
    LlmProviderOption(
        provider="deepseek",
        label="DeepSeek",
        default_base_url="https://api.deepseek.com",
        default_models=["deepseek-v4-flash", "deepseek-chat", "deepseek-reasoner"],
    ),
    LlmProviderOption(
        provider="qwen",
        label="Qwen / 通义千问",
        default_base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        default_models=["qwen-plus", "qwen-max", "qwen-turbo"],
    ),
    LlmProviderOption(
        provider="doubao",
        label="Doubao / 豆包",
        default_base_url="https://ark.cn-beijing.volces.com/api/v3",
        default_models=["doubao-1-5-pro-32k-250115", "doubao-1-5-lite-32k-250115"],
    ),
    LlmProviderOption(
        provider="openai",
        label="OpenAI / GPT",
        default_base_url="https://api.openai.com/v1",
        default_models=["gpt-4o-mini", "gpt-4.1-mini"],
    ),
    LlmProviderOption(
        provider="claude",
        label="Claude compatible",
        default_base_url="",
        default_models=["claude-sonnet-4-5", "claude-haiku-4-5"],
        note="Use an OpenAI-compatible Claude gateway endpoint.",
    ),
    LlmProviderOption(
        provider="ollama",
        label="Ollama local",
        default_base_url="http://127.0.0.1:11434/v1",
        default_models=["qwen2.5", "llama3.1", "mistral"],
        api_key_required=False,
    ),
    LlmProviderOption(
        provider="minimax",
        label="MiniMax",
        default_base_url="https://api.minimax.chat/v1",
        default_models=["minimax-text-01"],
    ),
    LlmProviderOption(
        provider="custom_openai_compatible",
        label="Custom OpenAI-compatible",
        default_base_url="",
        default_models=[],
        note="Fill API Base URL and model manually.",
    ),
)


def normalize_provider(provider: str | None) -> str:
    value = (provider or "deepseek").strip().lower()
    if value not in provider_map():
        return "custom_openai_compatible"
    return value


def get_provider_option(provider: str | None) -> LlmProviderOption:
    return provider_map()[normalize_provider(provider)]


def get_provider_options() -> list[dict[str, object]]:
    return [asdict(option) for option in PROVIDER_OPTIONS]


def provider_map() -> dict[str, LlmProviderOption]:
    return {option.provider: option for option in PROVIDER_OPTIONS}
