from app.ocr_extractor import extract_ocr_text_by_page_numbers


def test_extract_ocr_text_by_page_numbers_skips_empty_page_set():
    result = extract_ocr_text_by_page_numbers(
        filename="scan.pdf",
        content=b"%PDF",
        page_numbers=set(),
    )

    assert result == {}
