from dataclasses import dataclass
from io import BytesIO
import os


@dataclass(frozen=True)
class OcrPage:
    page_number: int
    char_count: int
    preview: str
    text: str


@dataclass(frozen=True)
class OcrImage:
    image_number: int
    char_count: int
    preview: str
    text: str


class OcrExtractionError(RuntimeError):
    pass


def extract_ocr_text_by_page_numbers(
    *,
    filename: str,
    content: bytes,
    page_numbers: set[int],
    language: str = "chi_sim+eng",
    dpi: int = 200,
    preview_chars: int = 500,
) -> dict[int, OcrPage]:
    if not content:
        raise OcrExtractionError("PDF file is empty")
    if not page_numbers:
        return {}

    try:
        import fitz
        import pytesseract
        from PIL import Image
    except ImportError as exc:
        raise OcrExtractionError(
            "OCR dependencies are not installed. Install PyMuPDF, pytesseract, Pillow, "
            "and the Tesseract OCR system package before enabling OCR."
        ) from exc

    tesseract_cmd = os.getenv("TESSERACT_CMD", "").strip()
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    zoom = dpi / 72
    results: dict[int, OcrPage] = {}

    try:
        with fitz.open(stream=content, filetype="pdf") as document:
            for page_number in sorted(page_numbers):
                if page_number < 1 or page_number > document.page_count:
                    continue

                page = document.load_page(page_number - 1)
                pixmap = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
                image = Image.open(BytesIO(pixmap.tobytes("png")))
                text = pytesseract.image_to_string(image, lang=language)
                normalized_text = text.strip()
                results[page_number] = OcrPage(
                    page_number=page_number,
                    char_count=len(normalized_text),
                    preview=normalized_text[:preview_chars],
                    text=normalized_text,
                )
    except OcrExtractionError:
        raise
    except Exception as exc:
        raise OcrExtractionError(
            f"Failed to OCR PDF {filename!r}. Ensure Tesseract is installed and language data {language!r} is available: {exc}"
        ) from exc

    if not any(page.text.strip() for page in results.values()):
        raise OcrExtractionError(
            f"OCR did not extract text from PDF {filename!r}. Check scan quality or OCR language {language!r}."
        )

    return results


def extract_ocr_text_from_image_bytes(
    *,
    filename: str,
    image_number: int,
    content: bytes,
    language: str = "chi_sim+eng",
    preview_chars: int = 500,
) -> OcrImage:
    if not content:
        raise OcrExtractionError("Image content is empty")

    try:
        import pytesseract
        from PIL import Image
    except ImportError as exc:
        raise OcrExtractionError(
            "OCR dependencies are not installed. Install pytesseract, Pillow, "
            "and the Tesseract OCR system package before enabling image OCR."
        ) from exc

    tesseract_cmd = os.getenv("TESSERACT_CMD", "").strip()
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    try:
        image = Image.open(BytesIO(content))
        text = pytesseract.image_to_string(image, lang=language)
    except Exception as exc:
        raise OcrExtractionError(
            f"Failed to OCR image {image_number} from {filename!r}. "
            f"Ensure Tesseract is installed and language data {language!r} is available: {exc}"
        ) from exc

    normalized_text = text.strip()
    return OcrImage(
        image_number=image_number,
        char_count=len(normalized_text),
        preview=normalized_text[:preview_chars],
        text=normalized_text,
    )
