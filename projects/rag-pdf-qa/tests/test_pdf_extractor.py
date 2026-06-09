from types import SimpleNamespace
import sys

from app import pdf_extractor
from app.ocr_extractor import OcrImage
from app.pdf_extractor import extract_text_from_pdf_bytes


class _FakePdf:
    def __init__(self, pages):
        self.pages = pages

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


class _FakePage:
    def __init__(self, text, tables):
        self._text = text
        self._tables = tables

    def extract_text(self):
        return self._text

    def extract_tables(self):
        return self._tables


def test_extract_pdf_tables_as_structured_text(monkeypatch):
    page = _FakePage(
        text="Project pricing summary",
        tables=[
            [
                ["Project", "Owner", "Price"],
                ["Falcon", "Alice", "999"],
                ["Comet", "Bob", "499"],
            ]
        ],
    )
    monkeypatch.setattr(pdf_extractor.pdfplumber, "open", lambda stream: _FakePdf([page]))

    extracted = extract_text_from_pdf_bytes(
        filename="pricing.pdf",
        content=b"%PDF fake",
        extract_tables=True,
    )

    assert extracted.table_count == 1
    assert extracted.extraction_mode == "text_table"
    assert extracted.pages[0].table_count == 1
    assert "Project=Falcon" in extracted.pages[0].tables[0].text
    assert "Owner=Alice" in extracted.pages[0].tables[0].text
    assert "Price=999" in extracted.preview


def test_extract_pdf_tables_disabled_by_default(monkeypatch):
    class PageThatRejectsTableExtraction(_FakePage):
        def extract_tables(self):
            raise AssertionError("table extraction should be opt-in")

    page = PageThatRejectsTableExtraction(text="Plain PDF text", tables=[])
    monkeypatch.setattr(pdf_extractor.pdfplumber, "open", lambda stream: _FakePdf([page]))

    extracted = extract_text_from_pdf_bytes(filename="plain.pdf", content=b"%PDF fake")

    assert extracted.table_count == 0
    assert extracted.extraction_mode == "text"
    assert extracted.pages[0].text == "Plain PDF text"


def test_extract_pdf_embedded_images_with_ocr(monkeypatch):
    page = _FakePage(text="Architecture overview", tables=[])
    monkeypatch.setattr(pdf_extractor.pdfplumber, "open", lambda stream: _FakePdf([page]))

    class FakeFitzDocument:
        page_count = 1

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def load_page(self, page_index):
            assert page_index == 0
            return SimpleNamespace(get_images=lambda full=True: [(7,)])

        def extract_image(self, xref):
            assert xref == 7
            return {"image": b"fake-image-bytes"}

    monkeypatch.setitem(sys.modules, "fitz", SimpleNamespace(open=lambda stream, filetype: FakeFitzDocument()))

    def fake_ocr_image(filename, image_number, content, language, preview_chars=500):
        assert filename == "diagram.pdf"
        assert image_number == 1
        assert content == b"fake-image-bytes"
        assert language == "eng"
        return OcrImage(
            image_number=image_number,
            char_count=23,
            preview="Gateway to Qdrant",
            text="Gateway to Qdrant diagram",
        )

    monkeypatch.setattr("app.ocr_extractor.extract_ocr_text_from_image_bytes", fake_ocr_image)

    extracted = extract_text_from_pdf_bytes(
        filename="diagram.pdf",
        content=b"%PDF fake",
        enable_image_ocr=True,
        ocr_language="eng",
    )

    assert extracted.image_ocr_count == 1
    assert extracted.extraction_mode == "text_image_ocr"
    assert extracted.pages[0].image_ocr_count == 1
    assert extracted.pages[0].images[0].extraction_method == "pdf_image_ocr"
    assert "Gateway to Qdrant" in extracted.preview
