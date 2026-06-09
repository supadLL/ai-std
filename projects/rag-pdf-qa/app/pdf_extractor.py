from dataclasses import dataclass, field
from io import BytesIO

import pdfplumber

from app.ocr_extractor import OcrImage, OcrPage


@dataclass(frozen=True)
class ExtractedTable:
    table_number: int
    row_count: int
    char_count: int
    preview: str
    text: str


@dataclass(frozen=True)
class ExtractedImage:
    image_number: int
    char_count: int
    preview: str
    text: str
    extraction_method: str = "pdf_image_ocr"


@dataclass(frozen=True)
class ExtractedPage:
    page_number: int
    char_count: int
    preview: str
    text: str
    extraction_method: str = "text"
    tables: list[ExtractedTable] = field(default_factory=list)
    images: list[ExtractedImage] = field(default_factory=list)

    @property
    def table_count(self) -> int:
        return len(self.tables)

    @property
    def image_ocr_count(self) -> int:
        return len(self.images)


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
    table_count: int = 0
    image_ocr_count: int = 0


class PdfExtractionError(RuntimeError):
    pass


def extract_text_from_pdf_bytes(
    filename: str,
    content: bytes,
    preview_chars: int = 500,
    enable_ocr: bool = False,
    ocr_language: str = "chi_sim+eng",
    extract_tables: bool = False,
    enable_image_ocr: bool = False,
) -> ExtractedPdf:
    if not content:
        raise PdfExtractionError("PDF file is empty")

    pages: list[ExtractedPage] = []
    try:
        with pdfplumber.open(BytesIO(content)) as pdf:
            for index, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                normalized_text = text.strip()
                tables = (
                    _extract_tables_from_page(page=page, page_number=index, preview_chars=preview_chars)
                    if extract_tables
                    else []
                )
                pages.append(
                    ExtractedPage(
                        page_number=index,
                        char_count=len(normalized_text),
                        preview=normalized_text[:preview_chars],
                        text=normalized_text,
                        tables=tables,
                    )
                )
    except Exception as exc:
        raise PdfExtractionError(f"Failed to extract text from PDF: {exc}") from exc

    if enable_image_ocr:
        try:
            image_ocr_pages = _extract_image_ocr_from_pdf(
                filename=filename,
                content=content,
                language=ocr_language,
                preview_chars=preview_chars,
            )
        except PdfExtractionError:
            raise
        pages = [
            _merge_image_ocr_page(page=page, images=image_ocr_pages.get(page.page_number, []))
            for page in pages
        ]

    ocr_page_count = 0
    if enable_ocr:
        empty_page_numbers = {
            page.page_number
            for page in pages
            if not page.text.strip() and not page.tables and not page.images
        }
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

    full_text = "\n\n".join(_iter_page_text_parts(pages))
    return ExtractedPdf(
        filename=filename,
        page_count=len(pages),
        char_count=len(full_text),
        preview=full_text[:preview_chars],
        pages=pages,
        scanned_like=not bool(full_text.strip()),
        extraction_mode=_detect_extraction_mode(pages),
        ocr_page_count=ocr_page_count,
        table_count=sum(page.table_count for page in pages),
        image_ocr_count=sum(page.image_ocr_count for page in pages),
    )


def _extract_image_ocr_from_pdf(
    *,
    filename: str,
    content: bytes,
    language: str,
    preview_chars: int,
) -> dict[int, list[ExtractedImage]]:
    try:
        import fitz
        from app.ocr_extractor import OcrExtractionError, extract_ocr_text_from_image_bytes
    except ImportError as exc:
        raise PdfExtractionError(
            "PDF image OCR dependencies are not installed. Install PyMuPDF, pytesseract, Pillow, "
            "and the Tesseract OCR system package before enabling image OCR."
        ) from exc

    images_by_page: dict[int, list[ExtractedImage]] = {}
    image_number = 0
    try:
        with fitz.open(stream=content, filetype="pdf") as document:
            for page_index in range(document.page_count):
                page = document.load_page(page_index)
                page_number = page_index + 1
                for image_info in page.get_images(full=True):
                    xref = int(image_info[0])
                    image_number += 1
                    image = document.extract_image(xref)
                    image_bytes = image.get("image", b"")
                    if not image_bytes:
                        continue
                    try:
                        ocr_image = extract_ocr_text_from_image_bytes(
                            filename=filename,
                            image_number=image_number,
                            content=image_bytes,
                            language=language,
                            preview_chars=preview_chars,
                        )
                    except OcrExtractionError as exc:
                        raise PdfExtractionError(str(exc)) from exc

                    extracted_image = _to_extracted_image(ocr_image)
                    if not extracted_image.text.strip():
                        continue
                    images_by_page.setdefault(page_number, []).append(extracted_image)
    except PdfExtractionError:
        raise
    except Exception as exc:
        raise PdfExtractionError(f"Failed to extract images from PDF: {exc}") from exc

    return images_by_page


def _to_extracted_image(image: OcrImage) -> ExtractedImage:
    return ExtractedImage(
        image_number=image.image_number,
        char_count=image.char_count,
        preview=image.preview,
        text=image.text,
    )


def _extract_tables_from_page(
    *,
    page: object,
    page_number: int,
    preview_chars: int,
) -> list[ExtractedTable]:
    try:
        raw_tables = page.extract_tables() or []
    except Exception as exc:
        raise PdfExtractionError(f"Failed to extract tables from PDF page {page_number}: {exc}") from exc

    tables: list[ExtractedTable] = []
    for table_index, raw_table in enumerate(raw_tables, start=1):
        table_text, row_count = _table_to_text(
            raw_table=raw_table,
            table_number=table_index,
            page_number=page_number,
        )
        if not table_text:
            continue
        tables.append(
            ExtractedTable(
                table_number=table_index,
                row_count=row_count,
                char_count=len(table_text),
                preview=table_text[:preview_chars],
                text=table_text,
            )
        )
    return tables


def _table_to_text(
    *,
    raw_table: list[list[object | None]] | None,
    table_number: int,
    page_number: int,
) -> tuple[str, int]:
    rows = [
        [_normalize_table_cell(cell) for cell in (row or [])]
        for row in (raw_table or [])
    ]
    rows = [row for row in rows if any(row)]
    if not rows:
        return "", 0

    headers = rows[0]
    has_headers = any(headers)
    if has_headers and len(rows) == 1:
        values = [value for value in headers if value]
        if not values:
            return "", len(rows)
        return (
            f"pdf table {table_number} page {page_number} headers: " + " | ".join(values),
            len(rows),
        )

    data_rows = rows[1:] if has_headers else rows
    start_row_number = 2 if has_headers else 1
    lines: list[str] = []
    for row_index, row in enumerate(data_rows, start=start_row_number):
        if has_headers:
            pairs = _table_row_to_header_pairs(headers=headers, row=row)
            if pairs:
                lines.append(
                    f"pdf table {table_number} page {page_number} row {row_index}: "
                    + "; ".join(pairs)
                )
        else:
            values = [value for value in row if value]
            if values:
                lines.append(
                    f"pdf table {table_number} page {page_number} row {row_index}: "
                    + " | ".join(values)
                )
    return "\n".join(lines), len(rows)


def _table_row_to_header_pairs(*, headers: list[str], row: list[str]) -> list[str]:
    pairs: list[str] = []
    for index in range(max(len(headers), len(row))):
        value = row[index] if index < len(row) else ""
        if not value:
            continue
        header = headers[index] if index < len(headers) and headers[index] else f"column_{index + 1}"
        pairs.append(f"{header}={value}")
    return pairs


def _normalize_table_cell(cell: object | None) -> str:
    if cell is None:
        return ""
    return " ".join(str(cell).split())


def _iter_page_text_parts(pages: list[ExtractedPage]) -> list[str]:
    parts: list[str] = []
    for page in pages:
        if page.text.strip():
            parts.append(page.text)
        parts.extend(table.text for table in page.tables if table.text.strip())
        parts.extend(image.text for image in page.images if image.text.strip())
    return parts


def _merge_image_ocr_page(*, page: ExtractedPage, images: list[ExtractedImage]) -> ExtractedPage:
    if not images:
        return page
    return ExtractedPage(
        page_number=page.page_number,
        char_count=page.char_count,
        preview=page.preview,
        text=page.text,
        extraction_method=page.extraction_method,
        tables=page.tables,
        images=images,
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
        tables=page.tables,
        images=page.images,
    )


def _detect_extraction_mode(pages: list[ExtractedPage]) -> str:
    if not pages:
        return "text"
    methods: set[str] = set()
    for page in pages:
        if page.text.strip():
            methods.add(page.extraction_method)
        if page.tables:
            methods.add("pdf_table")
        if page.images:
            methods.add("pdf_image_ocr")

    if not methods:
        return "text"
    if methods == {"text"}:
        return "text"
    if methods == {"pdf_ocr"}:
        return "ocr"
    if methods == {"pdf_table"}:
        return "table"
    if methods == {"text", "pdf_table"}:
        return "text_table"
    if methods == {"pdf_ocr", "pdf_table"}:
        return "ocr_table"
    if methods == {"pdf_image_ocr"}:
        return "image_ocr"
    if methods == {"text", "pdf_image_ocr"}:
        return "text_image_ocr"
    if methods == {"text", "pdf_table", "pdf_image_ocr"}:
        return "text_table_image_ocr"
    return "mixed"
