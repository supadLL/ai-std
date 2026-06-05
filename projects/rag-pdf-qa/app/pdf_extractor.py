from dataclasses import dataclass
from io import BytesIO

import pdfplumber

from app.ocr_extractor import OcrPage


@dataclass(frozen=True)
class ExtractedPage:
    page_number: int
    char_count: int
    preview: str
    text: str
    extraction_method: str = "text"


@dataclass(frozen=True)
class ExtractedPdf:
    filename: str
    page_count: int
    char_count: int
    preview: str
    pages: list[ExtractedPage]
    scanned_like: bool
    extraction_mode: str = "text"
    ocr_page_count: int = 0


class PdfExtractionError(RuntimeError):
    pass


def extract_text_from_pdf_bytes(
    filename: str,
    content: bytes,
    preview_chars: int = 500,
    enable_ocr: bool = False,
    ocr_language: str = "chi_sim+eng",
) -> ExtractedPdf:
    if not content:
        raise PdfExtractionError("PDF file is empty")

    pages: list[ExtractedPage] = []
    try:
        with pdfplumber.open(BytesIO(content)) as pdf:
            for index, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                normalized_text = text.strip()
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

    ocr_page_count = 0
    if enable_ocr:
        empty_page_numbers = {page.page_number for page in pages if not page.text.strip()}
        if empty_page_numbers:
            try:
                from app.ocr_extractor import OcrExtractionError, extract_ocr_text_by_page_numbers

                ocr_pages = extract_ocr_text_by_page_numbers(
                    filename=filename,
                    content=content,
                    page_numbers=empty_page_numbers,
                    language=ocr_language,
                    preview_chars=preview_chars,
                )
            except OcrExtractionError as exc:
                raise PdfExtractionError(str(exc)) from exc

            pages = [
                _merge_ocr_page(page=page, ocr_pages=ocr_pages, preview_chars=preview_chars)
                for page in pages
            ]
            ocr_page_count = sum(1 for page in pages if page.extraction_method == "pdf_ocr")

    full_text = "\n\n".join(page.text for page in pages if page.text.strip())
    return ExtractedPdf(
        filename=filename,
        page_count=len(pages),
        char_count=len(full_text),
        preview=full_text[:preview_chars],
        pages=pages,
        scanned_like=not bool(full_text.strip()),
        extraction_mode=_detect_extraction_mode(pages),
        ocr_page_count=ocr_page_count,
    )


def _merge_ocr_page(
    *,
    page: ExtractedPage,
    ocr_pages: dict[int, OcrPage],
    preview_chars: int,
) -> ExtractedPage:
    ocr_page = ocr_pages.get(page.page_number)
    if ocr_page is None or not ocr_page.text.strip():
        return page

    text = ocr_page.text.strip()
    return ExtractedPage(
        page_number=page.page_number,
        char_count=len(text),
        preview=text[:preview_chars],
        text=text,
        extraction_method="pdf_ocr",
    )


def _detect_extraction_mode(pages: list[ExtractedPage]) -> str:
    if not pages:
        return "text"
    ocr_count = sum(1 for page in pages if page.extraction_method == "pdf_ocr")
    if ocr_count == 0:
        return "text"
    if ocr_count == len(pages):
        return "ocr"
    return "mixed"
