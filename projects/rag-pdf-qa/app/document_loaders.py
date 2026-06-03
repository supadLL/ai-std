import csv
from io import BytesIO, StringIO
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ParsedSection:
    section_number: int
    title: str | None
    text: str


@dataclass(frozen=True)
class ParsedDocument:
    filename: str
    file_type: str
    char_count: int
    preview: str
    sections: list[ParsedSection]


class DocumentLoadError(RuntimeError):
    pass


def load_document_from_bytes(filename: str, content: bytes, preview_chars: int = 500) -> ParsedDocument:
    if not content:
        raise DocumentLoadError("Document file is empty")

    suffix = Path(filename).suffix.lower()
    if suffix in {".md", ".markdown", ".txt"}:
        return _load_text_document_from_bytes(filename=filename, content=content, preview_chars=preview_chars)
    if suffix == ".docx":
        return _load_docx_document_from_bytes(filename=filename, content=content, preview_chars=preview_chars)
    if suffix == ".csv":
        return _load_csv_document_from_bytes(filename=filename, content=content, preview_chars=preview_chars)
    if suffix == ".xlsx":
        return _load_xlsx_document_from_bytes(filename=filename, content=content, preview_chars=preview_chars)
    raise DocumentLoadError("Only Markdown, txt, docx, csv, and xlsx files are supported by document loaders")


def load_text_document_from_bytes(filename: str, content: bytes, preview_chars: int = 500) -> ParsedDocument:
    return _load_text_document_from_bytes(filename=filename, content=content, preview_chars=preview_chars)


def is_supported_document(filename: str) -> bool:
    suffix = Path(filename).suffix.lower()
    return suffix in {".md", ".markdown", ".txt", ".docx", ".csv", ".xlsx"}


def is_supported_text_document(filename: str) -> bool:
    suffix = Path(filename).suffix.lower()
    return suffix in {".md", ".markdown", ".txt"}


def _load_text_document_from_bytes(filename: str, content: bytes, preview_chars: int = 500) -> ParsedDocument:
    file_type = _detect_text_file_type(filename)
    text = _decode_text(content)
    normalized = text.strip()
    if not normalized:
        raise DocumentLoadError("Document has no text content")

    if file_type == "markdown":
        sections = _parse_markdown_sections(normalized)
    else:
        sections = [ParsedSection(section_number=1, title=None, text=normalized)]

    return ParsedDocument(
        filename=filename,
        file_type=file_type,
        char_count=len(normalized),
        preview=normalized[:preview_chars],
        sections=sections,
    )


def _detect_text_file_type(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix in {".md", ".markdown"}:
        return "markdown"
    if suffix == ".txt":
        return "text"
    raise DocumentLoadError("Only Markdown and txt files are supported by the text document loader")


def _load_docx_document_from_bytes(filename: str, content: bytes, preview_chars: int = 500) -> ParsedDocument:
    try:
        from docx import Document

        doc = Document(BytesIO(content))
    except Exception as exc:
        raise DocumentLoadError(f"Failed to load docx document: {exc}") from exc

    parts: list[str] = []
    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if text:
            parts.append(text)

    for table_index, table in enumerate(doc.tables, start=1):
        for row_index, row in enumerate(table.rows, start=1):
            values = [cell.text.strip() for cell in row.cells]
            values = [value for value in values if value]
            if values:
                parts.append(f"table {table_index} row {row_index}: " + " | ".join(values))

    full_text = "\n".join(parts).strip()
    if not full_text:
        raise DocumentLoadError("docx document has no text content")

    return ParsedDocument(
        filename=filename,
        file_type="docx",
        char_count=len(full_text),
        preview=full_text[:preview_chars],
        sections=[ParsedSection(section_number=1, title=None, text=full_text)],
    )


def _load_csv_document_from_bytes(filename: str, content: bytes, preview_chars: int = 500) -> ParsedDocument:
    text = _decode_text(content)
    rows = list(csv.reader(StringIO(text)))
    if not rows:
        raise DocumentLoadError("csv document has no rows")

    lines = _rows_to_text_lines(rows, sheet_name=None)
    full_text = "\n".join(lines).strip()
    if not full_text:
        raise DocumentLoadError("csv document has no text content")

    return ParsedDocument(
        filename=filename,
        file_type="csv",
        char_count=len(full_text),
        preview=full_text[:preview_chars],
        sections=[ParsedSection(section_number=1, title="csv rows", text=full_text)],
    )


def _load_xlsx_document_from_bytes(filename: str, content: bytes, preview_chars: int = 500) -> ParsedDocument:
    try:
        from openpyxl import load_workbook

        workbook = load_workbook(BytesIO(content), data_only=True, read_only=True)
    except Exception as exc:
        raise DocumentLoadError(f"Failed to load xlsx document: {exc}") from exc

    sections: list[ParsedSection] = []
    for sheet in workbook.worksheets:
        rows = [
            ["" if value is None else str(value) for value in row]
            for row in sheet.iter_rows(values_only=True)
        ]
        lines = _rows_to_text_lines(rows, sheet_name=sheet.title)
        section_text = "\n".join(lines).strip()
        if section_text:
            sections.append(
                ParsedSection(
                    section_number=len(sections) + 1,
                    title=sheet.title,
                    text=section_text,
                )
            )

    if not sections:
        raise DocumentLoadError("xlsx document has no text content")

    full_text = "\n\n".join(section.text for section in sections)
    return ParsedDocument(
        filename=filename,
        file_type="xlsx",
        char_count=len(full_text),
        preview=full_text[:preview_chars],
        sections=sections,
    )


def _rows_to_text_lines(rows: list[list[str]], sheet_name: str | None) -> list[str]:
    if not rows:
        return []

    headers = [str(value).strip() for value in rows[0]]
    has_headers = any(headers)
    lines: list[str] = []
    for row_index, row in enumerate(rows[1:] if has_headers else rows, start=2 if has_headers else 1):
        values = [str(value).strip() for value in row]
        if not any(values):
            continue
        if has_headers:
            pairs = [
                f"{header or f'column_{index + 1}'}={value}"
                for index, (header, value) in enumerate(zip(headers, values))
                if value
            ]
        else:
            pairs = [value for value in values if value]
        prefix = f"sheet {sheet_name} " if sheet_name else ""
        lines.append(f"{prefix}row {row_index}: " + "; ".join(pairs))
    return lines


def _decode_text(content: bytes) -> str:
    try:
        return content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise DocumentLoadError("Only UTF-8 text files are supported") from exc


def _parse_markdown_sections(text: str) -> list[ParsedSection]:
    sections: list[ParsedSection] = []
    current_title: str | None = None
    current_lines: list[str] = []

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            title = stripped.lstrip("#").strip()
            if title:
                _append_markdown_section(sections, current_title, current_lines)
                current_title = title
                current_lines = [line]
                continue
        current_lines.append(line)

    _append_markdown_section(sections, current_title, current_lines)
    if not sections:
        sections.append(ParsedSection(section_number=1, title=None, text=text))
    return sections


def _append_markdown_section(
    sections: list[ParsedSection],
    title: str | None,
    lines: list[str],
) -> None:
    section_text = "\n".join(lines).strip()
    if not section_text:
        return
    sections.append(
        ParsedSection(
            section_number=len(sections) + 1,
            title=title,
            text=section_text,
        )
    )
