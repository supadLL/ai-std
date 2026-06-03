from dataclasses import asdict
from hashlib import sha256
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from app.config import get_settings
from app.deepseek_client import DeepSeekClient, DeepSeekClientError
from app.document_store import DocumentRecord, DocumentStore, DocumentStoreError
from app.embedding_client import EmbeddingError, embed_text
from app.pdf_extractor import PdfExtractionError, extract_text_from_pdf_bytes
from app.text_splitter import TextSplitError, split_pdf_text
from app.vector_store import (
    SearchResult,
    VectorStoreError,
    delete_document_chunks,
    ensure_collection,
    get_qdrant_client,
    search_chunks,
    upsert_chunks,
)


class UTF8JSONResponse(JSONResponse):
    media_type = "application/json; charset=utf-8"


app = FastAPI(
    title="RAG PDF QA",
    version="0.1.0",
    default_response_class=UTF8JSONResponse,
)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    reply: str
    model: str
    usage: dict[str, Any] | None = None


class ExtractedPageResponse(BaseModel):
    page_number: int
    char_count: int
    preview: str


class PdfExtractResponse(BaseModel):
    filename: str
    page_count: int
    char_count: int
    preview: str
    scanned_like: bool
    pages: list[ExtractedPageResponse]


class TextChunkResponse(BaseModel):
    chunk_id: int
    page_number: int
    char_count: int
    text: str


class PdfChunkResponse(BaseModel):
    filename: str
    page_count: int
    char_count: int
    chunk_size: int
    overlap: int
    chunk_count: int
    scanned_like: bool
    chunks: list[TextChunkResponse]


class EmbeddingRequest(BaseModel):
    text: str = Field(min_length=1, max_length=8000)


class EmbeddingResponse(BaseModel):
    text: str
    model: str
    dimension: int
    embedding_preview: list[float]


class DocumentIndexResponse(BaseModel):
    document_id: str
    filename: str
    content_hash: str
    content_hash_prefix: str
    is_duplicate: bool = False
    indexed: bool = True
    message: str
    collection: str
    page_count: int | None = None
    chunk_count: int
    indexed_count: int
    deleted_chunks: int = 0
    dimension: int | None = None
    local_path: str


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=5, ge=1, le=20)


class SearchResultResponse(BaseModel):
    score: float
    document_id: str | None = None
    filename: str
    page_number: int
    chunk_id: int
    text: str


class SearchResponse(BaseModel):
    query: str
    collection: str
    limit: int
    results: list[SearchResultResponse]


class RagAskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=5, ge=1, le=10)
    score_threshold: float | None = Field(default=None, ge=0.0, le=1.0)


class RagSourceResponse(BaseModel):
    source_id: int
    score: float
    document_id: str | None = None
    filename: str
    page_number: int
    chunk_id: int
    preview: str


class RagAskResponse(BaseModel):
    question: str
    reply: str
    model: str
    collection: str
    score_threshold: float | None = None
    retrieved_count: int
    source_count: int
    sources: list[RagSourceResponse]
    usage: dict[str, Any] | None = None


class DocumentRecordResponse(BaseModel):
    document_id: str
    filename: str
    file_type: str
    content_hash: str
    content_hash_prefix: str
    chunk_count: int
    created_at: str
    indexed_at: str
    source_file_size: int
    collection: str
    chunk_size: int
    overlap: int
    embedding_model: str
    page_count: int
    indexed_count: int


class DocumentListResponse(BaseModel):
    documents: list[DocumentRecordResponse]


class DeleteDocumentResponse(BaseModel):
    document_id: str
    deleted_chunks: int
    deleted_metadata: bool


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    settings = get_settings()
    client = DeepSeekClient(settings)

    try:
        result = await client.chat(request.message)
    except DeepSeekClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return ChatResponse(**result)


@app.post("/documents/extract", response_model=PdfExtractResponse)
async def extract_document(file: UploadFile = File(...)) -> PdfExtractResponse:
    filename = file.filename or "uploaded.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    content = await file.read()
    max_size = 10 * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(status_code=413, detail="PDF file is too large; max size is 10 MB")

    try:
        extracted = extract_text_from_pdf_bytes(filename=filename, content=content)
    except PdfExtractionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return PdfExtractResponse(
        filename=extracted.filename,
        page_count=extracted.page_count,
        char_count=extracted.char_count,
        preview=extracted.preview,
        scanned_like=extracted.scanned_like,
        pages=[
            ExtractedPageResponse(
                page_number=page.page_number,
                char_count=page.char_count,
                preview=page.preview,
            )
            for page in extracted.pages
        ],
    )


@app.post("/documents/chunk", response_model=PdfChunkResponse)
async def chunk_document(
    file: UploadFile = File(...),
    chunk_size: int = Form(800),
    overlap: int = Form(100),
) -> PdfChunkResponse:
    filename = file.filename or "uploaded.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    content = await file.read()
    max_size = 10 * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(status_code=413, detail="PDF file is too large; max size is 10 MB")

    try:
        extracted = extract_text_from_pdf_bytes(filename=filename, content=content)
        chunks = split_pdf_text(extracted, chunk_size=chunk_size, overlap=overlap)
    except PdfExtractionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except TextSplitError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return PdfChunkResponse(
        filename=extracted.filename,
        page_count=extracted.page_count,
        char_count=extracted.char_count,
        chunk_size=chunk_size,
        overlap=overlap,
        chunk_count=len(chunks),
        scanned_like=extracted.scanned_like,
        chunks=[
            TextChunkResponse(
                chunk_id=chunk.chunk_id,
                page_number=chunk.page_number,
                char_count=chunk.char_count,
                text=chunk.text,
            )
            for chunk in chunks
        ],
    )


@app.post("/embeddings/text", response_model=EmbeddingResponse)
async def create_text_embedding(request: EmbeddingRequest) -> EmbeddingResponse:
    settings = get_settings()

    try:
        vector = await run_in_threadpool(
            embed_text,
            text=request.text,
            model_name=settings.embedding_model,
        )
    except EmbeddingError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return EmbeddingResponse(
        text=request.text,
        model=settings.embedding_model,
        dimension=len(vector),
        embedding_preview=vector[:10],
    )


@app.post("/documents/index", response_model=DocumentIndexResponse)
async def index_document(
    file: UploadFile = File(...),
    chunk_size: int = Form(800),
    overlap: int = Form(100),
    reindex: bool = Form(False),
) -> DocumentIndexResponse:
    filename = file.filename or "uploaded.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    content = await file.read()
    max_size = 10 * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(status_code=413, detail="PDF file is too large; max size is 10 MB")

    settings = get_settings()
    content_hash = _calculate_content_hash(content)
    document_store = get_document_store(settings.document_metadata_path)

    try:
        existing_record = document_store.get_document_by_content_hash(content_hash)
        if existing_record is not None and not reindex:
            return DocumentIndexResponse(
                document_id=existing_record.document_id,
                filename=filename,
                content_hash=content_hash,
                content_hash_prefix=content_hash[:12],
                is_duplicate=True,
                indexed=False,
                message="Duplicate document content detected. Existing index was reused.",
                collection=existing_record.collection,
                page_count=existing_record.page_count,
                chunk_count=existing_record.chunk_count,
                indexed_count=0,
                deleted_chunks=0,
                dimension=None,
                local_path=settings.qdrant_local_path,
            )

        document_id = existing_record.document_id if existing_record is not None else str(uuid4())
        deleted_chunks = 0
        extracted = extract_text_from_pdf_bytes(filename=filename, content=content)
        chunks = split_pdf_text(extracted, chunk_size=chunk_size, overlap=overlap)
        if not chunks:
            raise VectorStoreError("No text chunks to index")

        vectors = await run_in_threadpool(
            lambda: [embed_text(chunk.text, settings.embedding_model) for chunk in chunks]
        )
        dimension = len(vectors[0])
        client = get_qdrant_client(settings.qdrant_local_path)
        ensure_collection(client, settings.qdrant_collection, dimension)
        if existing_record is not None and reindex:
            deleted_chunks = delete_document_chunks(
                client=client,
                collection_name=existing_record.collection,
                document_id=existing_record.document_id,
            )
            document_store.remove_document(existing_record.document_id)

        indexed_count = upsert_chunks(
            client=client,
            collection_name=settings.qdrant_collection,
            filename=filename,
            chunks=chunks,
            vectors=vectors,
            document_id=document_id,
            content_hash=content_hash,
        )
        document_store.add_document(
            document_id=document_id,
            filename=filename,
            file_type="pdf",
            content_hash=content_hash,
            chunk_count=len(chunks),
            collection=settings.qdrant_collection,
            chunk_size=chunk_size,
            overlap=overlap,
            embedding_model=settings.embedding_model,
            page_count=extracted.page_count,
            indexed_count=indexed_count,
            source_file_size=len(content),
        )
    except (PdfExtractionError, TextSplitError, EmbeddingError, VectorStoreError, DocumentStoreError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return DocumentIndexResponse(
        document_id=document_id,
        filename=filename,
        content_hash=content_hash,
        content_hash_prefix=content_hash[:12],
        is_duplicate=False,
        indexed=True,
        message="Document indexed successfully." if deleted_chunks == 0 else "Document reindexed successfully.",
        collection=settings.qdrant_collection,
        page_count=extracted.page_count,
        chunk_count=len(chunks),
        indexed_count=indexed_count,
        deleted_chunks=deleted_chunks,
        dimension=dimension,
        local_path=settings.qdrant_local_path,
    )


@app.get("/documents", response_model=DocumentListResponse)
async def list_documents() -> DocumentListResponse:
    settings = get_settings()
    try:
        records = get_document_store(settings.document_metadata_path).list_documents()
    except DocumentStoreError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return DocumentListResponse(documents=[_to_document_record_response(record) for record in records])


@app.get("/documents/{document_id}", response_model=DocumentRecordResponse)
async def get_document(document_id: str) -> DocumentRecordResponse:
    settings = get_settings()
    try:
        record = get_document_store(settings.document_metadata_path).get_document(document_id)
    except DocumentStoreError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if record is None:
        raise HTTPException(status_code=404, detail=f"Document {document_id!r} not found")
    return _to_document_record_response(record)


@app.delete("/documents/{document_id}", response_model=DeleteDocumentResponse)
async def delete_document(document_id: str) -> DeleteDocumentResponse:
    settings = get_settings()
    document_store = get_document_store(settings.document_metadata_path)

    try:
        record = document_store.get_document(document_id)
    except DocumentStoreError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if record is None:
        raise HTTPException(status_code=404, detail=f"Document {document_id!r} not found")

    try:
        client = get_qdrant_client(settings.qdrant_local_path)
        deleted_chunks = delete_document_chunks(
            client=client,
            collection_name=record.collection,
            document_id=document_id,
        )
        removed_record = document_store.remove_document(document_id)
    except (VectorStoreError, DocumentStoreError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return DeleteDocumentResponse(
        document_id=document_id,
        deleted_chunks=deleted_chunks,
        deleted_metadata=removed_record is not None,
    )


@app.post("/documents/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest) -> SearchResponse:
    settings = get_settings()
    try:
        query_vector = await run_in_threadpool(
            embed_text,
            text=request.query,
            model_name=settings.embedding_model,
        )
        client = get_qdrant_client(settings.qdrant_local_path)
        retrieved_results = search_chunks(
            client=client,
            collection_name=settings.qdrant_collection,
            query_vector=query_vector,
            limit=request.limit,
        )
    except (EmbeddingError, VectorStoreError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return SearchResponse(
        query=request.query,
        collection=settings.qdrant_collection,
        limit=request.limit,
        results=[
            _to_search_result_response(result)
            for result in retrieved_results
        ],
    )


@app.post("/rag/ask", response_model=RagAskResponse)
async def ask_with_rag(request: RagAskRequest) -> RagAskResponse:
    settings = get_settings()

    try:
        query_vector = await run_in_threadpool(
            embed_text,
            text=request.question,
            model_name=settings.embedding_model,
        )
        client = get_qdrant_client(settings.qdrant_local_path)
        retrieved_results = search_chunks(
            client=client,
            collection_name=settings.qdrant_collection,
            query_vector=query_vector,
            limit=request.limit,
        )
    except (EmbeddingError, VectorStoreError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    results = _filter_results_by_score(retrieved_results, request.score_threshold)

    if not retrieved_results:
        raise HTTPException(status_code=404, detail="No related document chunks found. Index a document first.")

    if not results:
        raise HTTPException(
            status_code=404,
            detail="No document chunks met score_threshold. Lower score_threshold or try another question.",
        )

    deepseek_client = DeepSeekClient(settings)
    messages = _build_rag_messages(question=request.question, results=results)

    try:
        answer = await deepseek_client.chat_messages(
            messages=messages,
            max_tokens=1200,
            temperature=0.1,
        )
    except DeepSeekClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return RagAskResponse(
        question=request.question,
        reply=answer["reply"],
        model=answer["model"],
        collection=settings.qdrant_collection,
        score_threshold=request.score_threshold,
        retrieved_count=len(retrieved_results),
        source_count=len(results),
        sources=[
            _to_rag_source_response(index, result)
            for index, result in enumerate(results, start=1)
        ],
        usage=answer.get("usage"),
    )


def _to_search_result_response(result: SearchResult) -> SearchResultResponse:
    return SearchResultResponse(
        score=result.score,
        document_id=result.document_id,
        filename=result.filename,
        page_number=result.page_number,
        chunk_id=result.chunk_id,
        text=result.text,
    )


def _to_rag_source_response(source_id: int, result: SearchResult, preview_chars: int = 180) -> RagSourceResponse:
    preview = " ".join(result.text.split())[:preview_chars]
    return RagSourceResponse(
        source_id=source_id,
        score=result.score,
        document_id=result.document_id,
        filename=result.filename,
        page_number=result.page_number,
        chunk_id=result.chunk_id,
        preview=preview,
    )


def get_document_store(metadata_path: str) -> DocumentStore:
    return DocumentStore(metadata_path)


def _to_document_record_response(record: DocumentRecord) -> DocumentRecordResponse:
    return DocumentRecordResponse(**asdict(record))


def _calculate_content_hash(content: bytes) -> str:
    return sha256(content).hexdigest()


def _filter_results_by_score(
    results: list[SearchResult],
    score_threshold: float | None,
) -> list[SearchResult]:
    if score_threshold is None:
        return results
    return [result for result in results if result.score >= score_threshold]


def _build_rag_messages(question: str, results: list[SearchResult]) -> list[dict[str, str]]:
    context = "\n\n".join(
        (
            f"[Source {index}] file: {result.filename} | page: {result.page_number} | "
            f"chunk_id: {result.chunk_id} | score: {result.score:.4f}\n{result.text}"
        )
        for index, result in enumerate(results, start=1)
    )

    system_prompt = (
        "You are a strict local knowledge-base QA assistant. "
        "Answer only from the retrieved context supplied by the user. "
        "If the context is insufficient, say so directly and do not invent facts. "
        "Prefer Chinese. Cite key claims with source ids, for example [Source 1]. "
        "Always answer with exactly these three Markdown sections: "
        "答案：, 依据：, 资料不足之处：."
    )
    user_prompt = (
        f"User question:\n{question}\n\n"
        f"Retrieved context:\n{context}\n\n"
        "Answer based on the retrieved context above.\n\n"
        "Use this output format:\n"
        "答案：\n"
        "- 用中文给出直接回答。关键结论后标注来源，例如 [Source 1]。\n\n"
        "依据：\n"
        "- [Source 1] 写出该来源支持了什么结论。\n"
        "- 如果使用多个来源，逐条列出。\n\n"
        "资料不足之处：\n"
        "- 如果资料足够，写“未发现明显不足”。\n"
        "- 如果资料不足，明确说明缺少什么，不要编造。"
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
