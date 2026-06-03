import pytest
from docx import Document
from openpyxl import Workbook
from io import BytesIO

from app.document_loaders import DocumentLoadError, load_document_from_bytes, load_text_document_from_bytes


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


def test_load_docx_document_extracts_paragraphs_and_tables():
    document = Document()
    document.add_paragraph("项目代号是 DocxFalcon。")
    table = document.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "负责人"
    table.cell(0, 1).text = "Carol"
    table.cell(1, 0).text = "预算"
    table.cell(1, 1).text = "900"
    buffer = BytesIO()
    document.save(buffer)

    parsed = load_document_from_bytes(filename="demo.docx", content=buffer.getvalue())

    assert parsed.file_type == "docx"
    assert "DocxFalcon" in parsed.sections[0].text
    assert "Carol" in parsed.sections[0].text


def test_load_csv_document_converts_rows_to_text():
    parsed = load_document_from_bytes(
        filename="demo.csv",
        content="name,owner\nCsvRocket,Dana\n".encode("utf-8"),
    )

    assert parsed.file_type == "csv"
    assert "name=CsvRocket" in parsed.sections[0].text
    assert "owner=Dana" in parsed.sections[0].text


def test_load_xlsx_document_converts_sheets_to_sections():
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Projects"
    sheet.append(["name", "owner"])
    sheet.append(["XlsxComet", "Eve"])
    buffer = BytesIO()
    workbook.save(buffer)

    parsed = load_document_from_bytes(filename="demo.xlsx", content=buffer.getvalue())

    assert parsed.file_type == "xlsx"
    assert parsed.sections[0].title == "Projects"
    assert "name=XlsxComet" in parsed.sections[0].text
    assert "owner=Eve" in parsed.sections[0].text
