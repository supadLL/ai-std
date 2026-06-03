from functools import lru_cache

from fastembed import TextEmbedding


class EmbeddingError(RuntimeError):
    pass


@lru_cache(maxsize=4)
def _get_embedding_model(model_name: str) -> TextEmbedding:
    return TextEmbedding(model_name=model_name)


def embed_text(text: str, model_name: str) -> list[float]:
    normalized_text = text.strip()
    if not normalized_text:
        raise EmbeddingError("text must not be empty")

    try:
        model = _get_embedding_model(model_name)
        embeddings = list(model.embed([normalized_text]))
    except Exception as exc:
        raise EmbeddingError(f"Failed to create embedding: {exc}") from exc

    if not embeddings:
        raise EmbeddingError("embedding model returned no vectors")

    return embeddings[0].tolist()
