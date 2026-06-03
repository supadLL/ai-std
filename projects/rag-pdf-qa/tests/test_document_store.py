from app.document_store import DocumentStore


def test_document_store_add_list_get_remove(tmp_path):
    store = DocumentStore(str(tmp_path / "documents.json"))

    record = store.add_document(
        document_id="doc-1",
        filename="demo.pdf",
        file_type="pdf",
        content_hash="a" * 64,
        chunk_count=3,
        collection="rag_chunks",
        chunk_size=800,
        overlap=100,
        embedding_model="BAAI/bge-small-zh-v1.5",
        page_count=2,
        indexed_count=3,
        source_file_size=120,
    )

    assert record.document_id == "doc-1"
    assert record.content_hash_prefix == "a" * 12
    assert store.list_documents()[0].filename == "demo.pdf"
    assert store.get_document("doc-1") is not None
    assert store.get_document_by_content_hash("a" * 64) is not None

    removed = store.remove_document("doc-1")

    assert removed is not None
    assert removed.document_id == "doc-1"
    assert store.get_document("doc-1") is None
    assert store.get_document_by_content_hash("a" * 64) is None
