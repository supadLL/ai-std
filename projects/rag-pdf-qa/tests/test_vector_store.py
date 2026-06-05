from types import SimpleNamespace

import pytest

from app.text_splitter import TextChunk
from app.vector_store import VectorStoreError, _document_id_filter, ensure_collection, upsert_chunks


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


def test_upsert_chunks_stores_extraction_method_payload():
    captured = {}

    class FakeUpsertClient:
        def upsert(self, collection_name, points):
            captured["collection_name"] = collection_name
            captured["points"] = points

    count = upsert_chunks(
        client=FakeUpsertClient(),
        collection_name="rag_chunks",
        filename="scan.pdf",
        chunks=[TextChunk(chunk_id=1, page_number=1, char_count=8, text="ocr text", extraction_method="pdf_ocr")],
        vectors=[[0.1, 0.2, 0.3]],
        document_id="doc-1",
        content_hash="a" * 64,
        file_type="pdf",
    )

    assert count == 1
    assert captured["collection_name"] == "rag_chunks"
    assert captured["points"][0].payload["extraction_method"] == "pdf_ocr"
