from pathlib import Path

from app.source_storage import store_source_file


def test_store_source_file_writes_relative_object_key(tmp_path):
    stored = store_source_file(
        storage_path=str(tmp_path / "source_files"),
        backend="local",
        organization_id="org_default",
        workspace_id="ws_default",
        knowledge_base_id="kb_default",
        document_id="doc-1",
        filename="../demo file.pdf",
        content_hash="a" * 64,
        content=b"source-content",
    )

    assert stored.backend == "local"
    assert stored.object_key == "org_default/ws_default/kb_default/doc-1/aaaaaaaaaaaa-demo_file.pdf"
    assert stored.size == len(b"source-content")
    assert Path(tmp_path / "source_files" / stored.object_key).read_bytes() == b"source-content"
