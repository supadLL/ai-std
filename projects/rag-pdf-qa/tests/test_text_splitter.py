from app.pdf_extractor import ExtractedImage, ExtractedPage, ExtractedPdf, ExtractedTable
from app.document_loaders import ParsedDocument, ParsedSection
from app.text_splitter import _find_reasonable_boundary, split_parsed_document, split_pdf_text


def test_split_pdf_text_preserves_page_number_and_chunk_ids():
    extracted = ExtractedPdf(
        filename="demo.pdf",
        page_count=1,
        char_count=260,
        preview="",
        pages=[
            ExtractedPage(
                page_number=5,
                char_count=260,
                preview="",
                text="第一段内容。" * 20,
            )
        ],
        scanned_like=False,
    )

    chunks = split_pdf_text(extracted, chunk_size=120, overlap=20)

    assert chunks
    assert chunks[0].chunk_id == 1
    assert all(chunk.page_number == 5 for chunk in chunks)
    assert all(chunk.char_count == len(chunk.text) for chunk in chunks)


def test_split_pdf_text_preserves_extraction_method():
    extracted = ExtractedPdf(
        filename="scan.pdf",
        page_count=1,
        char_count=12,
        preview="",
        pages=[
            ExtractedPage(
                page_number=1,
                char_count=12,
                preview="",
                text="OCR page text",
                extraction_method="pdf_ocr",
            )
        ],
        scanned_like=False,
        extraction_mode="ocr",
        ocr_page_count=1,
    )

    chunks = split_pdf_text(extracted, chunk_size=100, overlap=0)

    assert chunks[0].extraction_method == "pdf_ocr"


def test_split_pdf_text_creates_pdf_table_chunks():
    extracted = ExtractedPdf(
        filename="table.pdf",
        page_count=1,
        char_count=60,
        preview="Project pricing",
        pages=[
            ExtractedPage(
                page_number=2,
                char_count=15,
                preview="Project pricing",
                text="Project pricing",
                tables=[
                    ExtractedTable(
                        table_number=1,
                        row_count=2,
                        char_count=45,
                        preview="pdf table 1 page 2 row 2: Project=Falcon",
                        text="pdf table 1 page 2 row 2: Project=Falcon; Price=999",
                    )
                ],
            )
        ],
        scanned_like=False,
        extraction_mode="text_table",
        table_count=1,
    )

    chunks = split_pdf_text(extracted, chunk_size=100, overlap=0)

    assert [chunk.extraction_method for chunk in chunks] == ["text", "pdf_table"]
    assert chunks[1].page_number == 2
    assert "Project=Falcon" in chunks[1].text


def test_split_pdf_text_creates_pdf_image_ocr_chunks():
    extracted = ExtractedPdf(
        filename="diagram.pdf",
        page_count=1,
        char_count=45,
        preview="Architecture overview",
        pages=[
            ExtractedPage(
                page_number=3,
                char_count=21,
                preview="Architecture overview",
                text="Architecture overview",
                images=[
                    ExtractedImage(
                        image_number=1,
                        char_count=24,
                        preview="Gateway to Qdrant",
                        text="Gateway to Qdrant diagram",
                    )
                ],
            )
        ],
        scanned_like=False,
        extraction_mode="text_image_ocr",
        image_ocr_count=1,
    )

    chunks = split_pdf_text(extracted, chunk_size=100, overlap=0)

    assert [chunk.extraction_method for chunk in chunks] == ["text", "pdf_image_ocr"]
    assert chunks[1].page_number == 3
    assert "Gateway to Qdrant" in chunks[1].text


def test_split_parsed_document_preserves_section_extraction_method():
    document = ParsedDocument(
        filename="demo.docx",
        file_type="docx",
        char_count=16,
        preview="Image OCR text",
        sections=[
            ParsedSection(
                section_number=1,
                title="docx image 1 OCR",
                text="Image OCR text",
                extraction_method="image_ocr",
            )
        ],
    )

    chunks = split_parsed_document(document, chunk_size=100, overlap=0)

    assert chunks[0].extraction_method == "image_ocr"


def test_find_reasonable_boundary_returns_end_when_search_window_is_too_short():
    assert _find_reasonable_boundary("short text", start=0, end=5, chunk_size=100) == 5
