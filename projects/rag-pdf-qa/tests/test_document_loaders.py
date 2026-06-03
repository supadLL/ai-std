import pytest

from app.document_loaders import DocumentLoadError, load_text_document_from_bytes


def test_load_markdown_document_splits_heading_sections():
    document = load_text_document_from_bytes(
        filename="notes.md",
        content="# 标题\n第一段\n\n## 子标题\n第二段".encode("utf-8"),
    )

    assert document.file_type == "markdown"
    assert len(document.sections) == 2
    assert document.sections[0].title == "标题"
    assert "第一段" in document.sections[0].text
    assert document.sections[1].title == "子标题"


def test_load_txt_document_as_single_section():
    document = load_text_document_from_bytes(
        filename="notes.txt",
        content="纯文本知识库内容".encode("utf-8"),
    )

    assert document.file_type == "text"
    assert len(document.sections) == 1
    assert document.sections[0].text == "纯文本知识库内容"


def test_load_text_document_rejects_non_utf8():
    with pytest.raises(DocumentLoadError):
        load_text_document_from_bytes(filename="bad.txt", content=b"\xff\xfe\x00")
