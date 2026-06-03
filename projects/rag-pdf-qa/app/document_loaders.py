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


def load_text_document_from_bytes(filename: str, content: bytes, preview_chars: int = 500) -> ParsedDocument:
    if not content:
        raise DocumentLoadError("Document file is empty")

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


def is_supported_text_document(filename: str) -> bool:
    suffix = Path(filename).suffix.lower()
    return suffix in {".md", ".markdown", ".txt"}


def _detect_text_file_type(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix in {".md", ".markdown"}:
        return "markdown"
    if suffix == ".txt":
        return "text"
    raise DocumentLoadError("Only Markdown and txt files are supported by the text document loader")


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
