from dataclasses import dataclass

from app.pdf_extractor import ExtractedPdf


@dataclass(frozen=True)
class TextChunk:
    chunk_id: int
    page_number: int
    char_count: int
    text: str


class TextSplitError(ValueError):
    pass


def split_pdf_text(extracted: ExtractedPdf, chunk_size: int = 800, overlap: int = 100) -> list[TextChunk]:
    if chunk_size < 100:
        raise TextSplitError("chunk_size must be at least 100")
    if chunk_size > 3000:
        raise TextSplitError("chunk_size must be at most 3000")
    if overlap < 0:
        raise TextSplitError("overlap must be greater than or equal to 0")
    if overlap >= chunk_size:
        raise TextSplitError("overlap must be smaller than chunk_size")

    chunks: list[TextChunk] = []
    for page in extracted.pages:
        for chunk_text in _split_text_by_page(page.text, chunk_size=chunk_size, overlap=overlap):
            chunks.append(
                TextChunk(
                    chunk_id=len(chunks) + 1,
                    page_number=page.page_number,
                    char_count=len(chunk_text),
                    text=chunk_text,
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
