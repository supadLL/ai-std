from types import SimpleNamespace

import pytest

from app.vector_store import VectorStoreError, _document_id_filter, ensure_collection


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


def test_document_id_filter_targets_document_payload():
    filter_model = _document_id_filter("doc-1")

    assert filter_model.must[0].key == "document_id"
    assert filter_model.must[0].match.value == "doc-1"
