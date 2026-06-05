from dataclasses import dataclass

from app.document_loaders import ParsedDocument
from app.pdf_extractor import ExtractedPdf


@dataclass(frozen=True)
class TextChunk:
    chunk_id: int
    page_number: int
    char_count: int
    text: str
    extraction_method: str = "text"


class TextSplitError(ValueError):
    pass


def split_pdf_text(extracted: ExtractedPdf, chunk_size: int = 800, overlap: int = 100) -> list[TextChunk]:
    _validate_split_params(chunk_size=chunk_size, overlap=overlap)

    chunks: list[TextChunk] = []
    for page in extracted.pages:
        chunks.extend(
            _split_text_unit(
                unit_number=page.page_number,
                text=page.text,
                extraction_method=page.extraction_method,
                current_count=len(chunks),
                chunk_size=chunk_size,
                overlap=overlap,
            )
        )

    return chunks


def split_parsed_document(document: ParsedDocument, chunk_size: int = 800, overlap: int = 100) -> list[TextChunk]:
    _validate_split_params(chunk_size=chunk_size, overlap=overlap)

    chunks: list[TextChunk] = []
    for section in document.sections:
        chunks.extend(
            _split_text_unit(
                unit_number=section.section_number,
                text=section.text,
                extraction_method=section.extraction_method,
                current_count=len(chunks),
                chunk_size=chunk_size,
                overlap=overlap,
            )
        )
    return chunks


def _validate_split_params(chunk_size: int, overlap: int) -> None:
    if chunk_size < 100:
        raise TextSplitError("chunk_size must be at least 100")
    if chunk_size > 3000:
        raise TextSplitError("chunk_size must be at most 3000")
    if overlap < 0:
        raise TextSplitError("overlap must be greater than or equal to 0")
    if overlap >= chunk_size:
        raise TextSplitError("overlap must be smaller than chunk_size")


def _split_text_unit(
    *,
    unit_number: int,
    text: str,
    extraction_method: str,
    current_count: int,
    chunk_size: int,
    overlap: int,
) -> list[TextChunk]:
    chunks: list[TextChunk] = []
    for chunk_text in _split_text_by_page(text, chunk_size=chunk_size, overlap=overlap):
        chunks.append(
            TextChunk(
                chunk_id=current_count + len(chunks) + 1,
                page_number=unit_number,
                char_count=len(chunk_text),
                text=chunk_text,
                extraction_method=extraction_method,
            )
        )
    return chunks


def _split_text_by_page(text: str, chunk_size: int, overlap: int) -> list[str]:
    normalized = text.strip()
    if not normalized:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(start + chunk_size, len(normalized))
        if end < len(normalized):
            end = _find_reasonable_boundary(normalized, start=start, end=end, chunk_size=chunk_size)

        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= len(normalized):
            break

        next_start = max(end - overlap, start + 1)
        start = next_start

    return chunks


def _find_reasonable_boundary(text: str, start: int, end: int, chunk_size: int) -> int:
    min_boundary = start + max(chunk_size // 2, 1)
    if min_boundary >= end:
        return end

    separators = ["\n\n", "\n", "。", "；", "，", ". ", " "]

    best_index = -1
    best_separator_length = 0
    for separator in separators:
        index = text.rfind(separator, min_boundary, end)
        if index > best_index:
            best_index = index
            best_separator_length = len(separator)

    if best_index <= start:
        return end

    return best_index + best_separator_length
