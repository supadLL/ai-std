from types import SimpleNamespace

import pytest

import app.vector_store as vector_store
from app.text_splitter import TextChunk
from app.vector_store import (
    VectorStoreError,
    _document_id_filter,
    _search_filter,
    build_collection_name,
    ensure_collection,
    get_collection_status,
    search_chunks,
    upsert_chunks,
)


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


def test_get_qdrant_client_uses_server_configuration(monkeypatch):
    captured = {}

    class FakeQdrantClient:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(vector_store, "QdrantClient", FakeQdrantClient)

    vector_store.get_qdrant_client(
        ".qdrant",
        mode="server",
        url="http://qdrant:6333/",
        api_key=" secret ",
    )

    assert captured["url"] == "http://qdrant:6333"
    assert captured["api_key"] == "secret"
    assert "path" not in captured


def test_get_qdrant_client_rejects_unknown_mode():
    with pytest.raises(VectorStoreError):
        vector_store.get_qdrant_client(".qdrant", mode="remote")


def test_build_collection_name_supports_environment_and_tenant_parts():
    assert build_collection_name("prod rag", tenant_id="org/default") == "prod_rag_org_default_chunks"


def test_get_collection_status_reads_vector_and_point_counts():
    class FakeStatusClient:
        def collection_exists(self, collection_name):
            return True

        def get_collection(self, collection_name):
            return SimpleNamespace(
                config=SimpleNamespace(
                    params=SimpleNamespace(
                        vectors=SimpleNamespace(size=384),
                    )
                ),
                points_count=12,
                status="green",
            )

    status = get_collection_status(FakeStatusClient(), "rag_chunks", expected_vector_size=384)

    assert status.exists is True
    assert status.vector_size == 384
    assert status.points_count == 12
    assert status.dimension_matches is True


def test_document_id_filter_targets_document_payload():
    filter_model = _document_id_filter("doc-1")

    assert filter_model.must[0].key == "document_id"
    assert filter_model.must[0].match.value == "doc-1"


def test_document_id_filter_can_target_tenant_and_knowledge_base():
    filter_model = _document_id_filter("doc-1", knowledge_base_id="kb-1", tenant_id="org-1")

    assert [condition.key for condition in filter_model.must] == [
        "document_id",
        "knowledge_base_id",
        "tenant_id",
    ]
    assert [condition.match.value for condition in filter_model.must] == ["doc-1", "kb-1", "org-1"]


def test_search_filter_can_target_document_and_file_type():
    filter_model = _search_filter(document_id="doc-1", file_type="pdf")

    assert filter_model is not None
    assert filter_model.must[0].key == "document_id"
    assert filter_model.must[0].match.value == "doc-1"
    assert filter_model.must[1].key == "file_type"
    assert filter_model.must[1].match.value == "pdf"


def test_search_chunks_passes_optional_payload_filters():
    captured = {}

    class FakeSearchClient:
        def collection_exists(self, collection_name):
            return True

        def query_points(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(points=[])

    results = search_chunks(
        client=FakeSearchClient(),
        collection_name="rag_chunks",
        query_vector=[0.1, 0.2, 0.3],
        limit=3,
        document_id="doc-1",
        file_type="pdf",
    )

    assert results == []
    assert captured["collection_name"] == "rag_chunks"
    assert captured["limit"] == 3
    assert captured["query_filter"].must[0].match.value == "doc-1"
    assert captured["query_filter"].must[1].match.value == "pdf"


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
