from app.pdf_extractor import ExtractedPage, ExtractedPdf
from app.text_splitter import _find_reasonable_boundary, split_pdf_text


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


def test_find_reasonable_boundary_returns_end_when_search_window_is_too_short():
    assert _find_reasonable_boundary("short text", start=0, end=5, chunk_size=100) == 5

