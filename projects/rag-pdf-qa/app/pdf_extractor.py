from dataclasses import dataclass
from io import BytesIO

import pdfplumber


@dataclass(frozen=True)
class ExtractedPage:
    page_number: int
    char_count: int
    preview: str
    text: str


@dataclass(frozen=True)
class ExtractedPdf:
    filename: str
    page_count: int
    char_count: int
    preview: str
    pages: list[ExtractedPage]
    scanned_like: bool


class PdfExtractionError(RuntimeError):
    pass


def extract_text_from_pdf_bytes(filename: str, content: bytes, preview_chars: int = 500) -> ExtractedPdf:
    if not content:
        raise PdfExtractionError("PDF file is empty")

    pages: list[ExtractedPage] = []
    all_text_parts: list[str] = []

    try:
        with pdfplumber.open(BytesIO(content)) as pdf:
            for index, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                normalized_text = text.strip()
                all_text_parts.append(normalized_text)
                pages.append(
                    ExtractedPage(
                        page_number=index,
                        char_count=len(normalized_text),
                        preview=normalized_text[:preview_chars],
                        text=normalized_text,
                    )
                )
    except Exception as exc:
        raise PdfExtractionError(f"Failed to extract text from PDF: {exc}") from exc

    full_text = "\n\n".join(part for part in all_text_parts if part)
    return ExtractedPdf(
        filename=filename,
        page_count=len(pages),
        char_count=len(full_text),
        preview=full_text[:preview_chars],
        pages=pages,
        scanned_like=not bool(full_text.strip()),
    )
