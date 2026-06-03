from types import SimpleNamespace

import pytest

from app.vector_store import VectorStoreError, ensure_collection


class FakeClient:
    def collection_exists(self, collection_name):
        return True

    def get_collection(self, collection_name):
        return SimpleNamespace(
            config=SimpleNamespace(
                params=SimpleNamespace(
                    vectors=SimpleNamespace(size=384),
                )
            )
        )


def test_ensure_collection_dimension_mismatch_has_rebuild_hint():
    with pytest.raises(VectorStoreError) as exc_info:
        ensure_collection(FakeClient(), "rag_chunks", vector_size=768)

    message = str(exc_info.value)
    assert "vector size 384" in message
    assert "current embedding dimension is 768" in message
    assert "Rebuild the local Qdrant index" in message

