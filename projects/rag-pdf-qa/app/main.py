from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from app.agent import explain_agent_route
from app.config import get_settings
from app.deepseek_client import DeepSeekClient, DeepSeekClientError
from app.document_store import DocumentRecord, DocumentStore, DocumentStoreError
from app.document_loaders import DocumentLoadError, is_supported_document, load_document_from_bytes
from app.embedding_client import EmbeddingError, embed_text
from app.evaluation import (
    EvaluationError,
    load_evaluation_dataset,
    read_latest_evaluation,
    run_rag_search_evaluation,
)
from app.llm_providers import get_provider_options, normalize_provider
from app.pdf_extractor import PdfExtractionError, extract_text_from_pdf_bytes
from app.runtime_settings import (
    DEFAULT_LLM_PROFILE_ID,
    LlmRuntimeProfile,
    RuntimeSettings,
    apply_runtime_settings,
    load_runtime_settings,
    merge_runtime_settings,
    replace_llm_profiles,
    save_runtime_settings,
)
from app.text_splitter import TextChunk, TextSplitError, split_parsed_document, split_pdf_text
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
    title="Local Knowledge RAG Agent",
    version="0.1.0",
    default_response_class=UTF8JSONResponse,
)

WEB_DIR = Path(__file__).resolve().parent.parent / "web"
if WEB_DIR.exists():
    app.mount("/web", StaticFiles(directory=WEB_DIR), name="web")


DEFAULT_RAG_SYSTEM_PROMPT = (
    "You are a strict local knowledge-base QA assistant. "
    "Answer only from the retrieved context supplied by the user. "
    "If the context is insufficient, say so directly and do not invent facts. "
    "Prefer Chinese. Cite key claims with source ids, for example [Source 1]. "
    "For how-to, implementation, setup, debugging, or process questions, provide a detailed, actionable answer. "
    "Do not collapse rich retrieved context into a single short sentence. "
    "Preserve important steps, commands, file paths, parameters, caveats, and ordering from the sources. "
    "Always answer with exactly these three Markdown sections: "
    "答案：, 依据：, 资料不足之处：."
)

DEFAULT_RAG_ANSWER_INSTRUCTIONS = (
    "Use this output format:\n"
    "答案：\n"
    "- 先用 1-2 句话给出直接结论，并标注来源，例如 [Source 1]。\n"
    "- 如果问题是操作型或实现型，继续给出“操作步骤：”，按顺序列出可执行步骤。\n"
    "- 尽量保留 context 中的关键命令、路径、参数、注意事项和前后顺序。\n"
    "- 如果 sources 提供了较多细节，回答也要相应详尽，不要只回答一句话。\n\n"
    "依据：\n"
    "- [Source 1] 写出该来源支持了什么结论。\n"
    "- 如果使用多个来源，逐条列出。\n\n"
    "资料不足之处：\n"
    "- 如果资料足够，写“未发现明显不足”。\n"
    "- 如果资料不足，明确说明缺少什么，不要编造。"
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
    extraction_method: str = "text"


class PdfExtractResponse(BaseModel):
    filename: str
    page_count: int
    char_count: int
    preview: str
    scanned_like: bool
    extraction_mode: str = "text"
    ocr_page_count: int = 0
    pages: list[ExtractedPageResponse]


class TextChunkResponse(BaseModel):
    chunk_id: int
    page_number: int
    char_count: int
    text: str
    extraction_method: str = "text"


class PdfChunkResponse(BaseModel):
    filename: str
    page_count: int
    char_count: int
    chunk_size: int
    overlap: int
    chunk_count: int
    scanned_like: bool
    extraction_mode: str = "text"
    ocr_page_count: int = 0
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
    file_type: str
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
    extraction_mode: str | None = None
    ocr_page_count: int = 0
    image_ocr_count: int = 0
    extraction_methods: list[str] = Field(default_factory=list)


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=5, ge=1, le=20)
    document_id: str | None = Field(default=None, max_length=120)
    file_type: str | None = Field(default=None, max_length=40)


class SearchResultResponse(BaseModel):
    score: float
    document_id: str | None = None
    file_type: str
    filename: str
    page_number: int
    chunk_id: int
    text: str
    extraction_method: str = "text"


class SearchResponse(BaseModel):
    query: str
    collection: str
    limit: int
    document_id: str | None = None
    file_type: str | None = None
    results: list[SearchResultResponse]


class RagAskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=5, ge=1, le=10)
    score_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    document_id: str | None = Field(default=None, max_length=120)


class RagSourceResponse(BaseModel):
    source_id: int
    score: float
    document_id: str | None = None
    file_type: str
    filename: str
    page_number: int
    chunk_id: int
    preview: str
    extraction_method: str = "text"


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


class AgentAskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=5, ge=1, le=10)
    score_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    document_id: str | None = Field(default=None, max_length=120)


class AgentAskResponse(BaseModel):
    question: str
    route: str
    route_reason: str = ""
    tools_used: list[str] = Field(default_factory=list)
    routing_debug: dict[str, Any] = Field(default_factory=dict)
    reply: str
    model: str | None = None
    collection: str
    score_threshold: float | None = None
    retrieved_count: int = 0
    source_count: int = 0
    sources: list[RagSourceResponse] = Field(default_factory=list)
    usage: dict[str, Any] | None = None


class EvaluationQuestionResponse(BaseModel):
    case_id: str
    question: str
    question_type: str = ""
    expected_pages: list[int] = Field(default_factory=list)
    expected_keywords: list[str] = Field(default_factory=list)


class EvaluationQuestionsResponse(BaseModel):
    dataset_name: str
    dataset_version: str
    case_count: int
    questions: list[EvaluationQuestionResponse]


class EvaluationRunRequest(BaseModel):
    limit: int = Field(default=5, ge=1, le=20)
    score_threshold: float | None = Field(default=None, ge=0.0, le=1.0)


class EvaluationSourceResponse(BaseModel):
    score: float
    document_id: str | None = None
    file_type: str
    filename: str
    page_number: int
    chunk_id: int
    extraction_method: str = "text"
    preview: str


class EvaluationCaseResultResponse(BaseModel):
    case_id: str
    question: str
    question_type: str = ""
    scored: bool
    hit: bool
    page_hit: bool
    keyword_hit: bool
    expected_pages: list[int]
    matched_keywords: list[str]
    top_pages: list[int]
    top_scores: list[float]
    top_sources: list[EvaluationSourceResponse]
    low_score_count: int


class EvaluationRunResponse(BaseModel):
    dataset_name: str
    dataset_version: str
    generated_at: str
    collection: str
    embedding_model: str
    limit: int
    score_threshold: float | None = None
    low_score_threshold: float
    case_count: int
    scored_case_count: int
    hit_count: int
    hit_rate: float
    page_hit_count: int
    page_hit_rate: float
    keyword_hit_count: int
    keyword_hit_rate: float
    low_score_result_count: int
    cases: list[EvaluationCaseResultResponse]


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


class BatchDeleteDocumentsRequest(BaseModel):
    document_ids: list[str] = Field(min_length=1, max_length=100)


class BatchDeleteDocumentsResponse(BaseModel):
    deleted_count: int
    deleted: list[DeleteDocumentResponse]
    missing_document_ids: list[str] = Field(default_factory=list)


class LlmProfileResponse(BaseModel):
    profile_id: str
    name: str
    provider: str
    base_url: str
    model: str
    enabled: bool
    api_key_configured: bool
    api_key_source: str
    api_key_label: str


class AppSettingsResponse(BaseModel):
    deepseek_base_url: str
    deepseek_model: str
    llm_provider: str
    llm_base_url: str
    llm_model: str
    request_timeout_seconds: float
    api_key_configured: bool
    api_key_source: str
    llm_api_key_configured: bool
    llm_api_key_source: str
    active_llm_profile_id: str
    llm_profiles: list[LlmProfileResponse]
    available_providers: list[dict[str, Any]]
    embedding_model: str
    qdrant_collection: str
    rag_system_prompt: str
    rag_answer_instructions: str


class UpdateAppSettingsRequest(BaseModel):
    deepseek_api_key: str | None = Field(default=None, max_length=4000)
    clear_api_key: bool = False
    deepseek_base_url: str | None = Field(default=None, max_length=500)
    deepseek_model: str | None = Field(default=None, max_length=200)
    llm_provider: str | None = Field(default=None, max_length=80)
    llm_api_key: str | None = Field(default=None, max_length=4000)
    llm_base_url: str | None = Field(default=None, max_length=500)
    llm_model: str | None = Field(default=None, max_length=200)
    request_timeout_seconds: float | None = Field(default=None, ge=1, le=300)
    rag_system_prompt: str | None = Field(default=None, max_length=12000)
    rag_answer_instructions: str | None = Field(default=None, max_length=12000)


class LlmProfileRequest(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    provider: str = Field(max_length=80)
    api_key: str | None = Field(default=None, max_length=4000)
    clear_api_key: bool = False
    base_url: str = Field(min_length=1, max_length=500)
    model: str = Field(min_length=1, max_length=200)
    activate: bool = False


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
@app.get("/app", include_in_schema=False)
async def web_app() -> FileResponse:
    index_path = WEB_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Web UI is not available")
    return FileResponse(index_path)


@app.get("/settings", response_model=AppSettingsResponse)
async def read_app_settings() -> AppSettingsResponse:
    base_settings = get_settings()
    runtime_settings = _load_runtime_settings_or_422()
    effective_settings = apply_runtime_settings(base_settings, runtime_settings)
    return _to_app_settings_response(
        base_settings=base_settings,
        runtime_settings=runtime_settings,
        effective_settings=effective_settings,
    )


@app.put("/settings", response_model=AppSettingsResponse)
async def update_app_settings(request: UpdateAppSettingsRequest) -> AppSettingsResponse:
    base_settings = get_settings()
    current_runtime_settings = _load_runtime_settings_or_422()
    next_runtime_settings = merge_runtime_settings(
        current_runtime_settings,
        deepseek_api_key=request.deepseek_api_key,
        clear_api_key=request.clear_api_key,
        deepseek_base_url=request.deepseek_base_url,
        deepseek_model=request.deepseek_model,
        llm_provider=request.llm_provider,
        llm_api_key=request.llm_api_key,
        llm_base_url=request.llm_base_url,
        llm_model=request.llm_model,
        request_timeout_seconds=request.request_timeout_seconds,
        rag_system_prompt=request.rag_system_prompt,
        rag_answer_instructions=request.rag_answer_instructions,
    )

    try:
        save_runtime_settings(next_runtime_settings)
    except RuntimeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    effective_settings = apply_runtime_settings(base_settings, next_runtime_settings)
    return _to_app_settings_response(
        base_settings=base_settings,
        runtime_settings=next_runtime_settings,
        effective_settings=effective_settings,
    )


@app.post("/settings/llm-profiles", response_model=AppSettingsResponse)
async def create_llm_profile(request: LlmProfileRequest) -> AppSettingsResponse:
    base_settings = get_settings()
    current_runtime_settings = _load_runtime_settings_or_422()
    effective_settings = apply_runtime_settings(base_settings, current_runtime_settings)
    profiles, active_profile_id = _materialize_llm_profiles(
        base_settings=base_settings,
        runtime_settings=current_runtime_settings,
        effective_settings=effective_settings,
    )
    provider = normalize_provider(request.provider)
    profile = LlmRuntimeProfile(
        profile_id=uuid4().hex[:12],
        name=(request.name or f"{provider} / {request.model}").strip(),
        provider=provider,
        base_url=request.base_url.strip().rstrip("/"),
        model=request.model.strip(),
        api_key=_optional_secret(request.api_key),
    )
    next_active_profile_id = profile.profile_id if request.activate else active_profile_id
    next_runtime_settings = replace_llm_profiles(
        current_runtime_settings,
        profiles=(*profiles, profile),
        active_profile_id=next_active_profile_id,
    )
    return _save_and_render_settings(base_settings, next_runtime_settings)


@app.put("/settings/llm-profiles/{profile_id}", response_model=AppSettingsResponse)
async def update_llm_profile(profile_id: str, request: LlmProfileRequest) -> AppSettingsResponse:
    base_settings = get_settings()
    current_runtime_settings = _load_runtime_settings_or_422()
    effective_settings = apply_runtime_settings(base_settings, current_runtime_settings)
    profiles, active_profile_id = _materialize_llm_profiles(
        base_settings=base_settings,
        runtime_settings=current_runtime_settings,
        effective_settings=effective_settings,
    )
    next_profiles: list[LlmRuntimeProfile] = []
    found = False
    for profile in profiles:
        if profile.profile_id != profile_id:
            next_profiles.append(profile)
            continue
        found = True
        provider = normalize_provider(request.provider)
        next_profiles.append(
            LlmRuntimeProfile(
                profile_id=profile.profile_id,
                name=(request.name or f"{provider} / {request.model}").strip(),
                provider=provider,
                base_url=request.base_url.strip().rstrip("/"),
                model=request.model.strip(),
                api_key=None
                if request.clear_api_key
                else _optional_secret(request.api_key) or profile.api_key,
            )
        )
    if not found:
        raise HTTPException(status_code=404, detail="LLM profile not found")

    next_runtime_settings = replace_llm_profiles(
        current_runtime_settings,
        profiles=tuple(next_profiles),
        active_profile_id=profile_id if request.activate else active_profile_id,
    )
    return _save_and_render_settings(base_settings, next_runtime_settings)


@app.post("/settings/llm-profiles/{profile_id}/activate", response_model=AppSettingsResponse)
async def activate_llm_profile(profile_id: str) -> AppSettingsResponse:
    base_settings = get_settings()
    current_runtime_settings = _load_runtime_settings_or_422()
    effective_settings = apply_runtime_settings(base_settings, current_runtime_settings)
    profiles, _active_profile_id = _materialize_llm_profiles(
        base_settings=base_settings,
        runtime_settings=current_runtime_settings,
        effective_settings=effective_settings,
    )
    if not any(profile.profile_id == profile_id for profile in profiles):
        raise HTTPException(status_code=404, detail="LLM profile not found")
    next_runtime_settings = replace_llm_profiles(
        current_runtime_settings,
        profiles=profiles,
        active_profile_id=profile_id,
    )
    return _save_and_render_settings(base_settings, next_runtime_settings)


@app.delete("/settings/llm-profiles/{profile_id}", response_model=AppSettingsResponse)
async def delete_llm_profile(profile_id: str) -> AppSettingsResponse:
    base_settings = get_settings()
    current_runtime_settings = _load_runtime_settings_or_422()
    effective_settings = apply_runtime_settings(base_settings, current_runtime_settings)
    profiles, active_profile_id = _materialize_llm_profiles(
        base_settings=base_settings,
        runtime_settings=current_runtime_settings,
        effective_settings=effective_settings,
    )
    if profile_id == active_profile_id:
        raise HTTPException(status_code=400, detail="Cannot delete active LLM profile")
    next_profiles = tuple(profile for profile in profiles if profile.profile_id != profile_id)
    if len(next_profiles) == len(profiles):
        raise HTTPException(status_code=404, detail="LLM profile not found")
    next_runtime_settings = replace_llm_profiles(
        current_runtime_settings,
        profiles=next_profiles,
        active_profile_id=active_profile_id,
    )
    return _save_and_render_settings(base_settings, next_runtime_settings)


@app.get("/evaluation/questions", response_model=EvaluationQuestionsResponse)
async def read_evaluation_questions() -> EvaluationQuestionsResponse:
    try:
        dataset = await run_in_threadpool(load_evaluation_dataset)
    except EvaluationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    questions = [
        EvaluationQuestionResponse(
            case_id=str(case.get("case_id", "")),
            question=str(case.get("question", "")),
            question_type=str(case.get("question_type", "")),
            expected_pages=[int(page) for page in case.get("expected_pages", [])],
            expected_keywords=[str(keyword) for keyword in case.get("expected_keywords", [])],
        )
        for case in dataset.get("cases", [])
    ]
    return EvaluationQuestionsResponse(
        dataset_name=str(dataset.get("dataset_name", "rag_eval")),
        dataset_version=str(dataset.get("version", "")),
        case_count=len(questions),
        questions=questions,
    )


@app.get("/evaluation/latest", response_model=EvaluationRunResponse)
async def read_latest_rag_evaluation() -> EvaluationRunResponse:
    try:
        result = await run_in_threadpool(read_latest_evaluation)
    except EvaluationError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return EvaluationRunResponse(**result)


@app.post("/evaluation/run", response_model=EvaluationRunResponse)
async def run_rag_evaluation(request: EvaluationRunRequest) -> EvaluationRunResponse:
    settings = get_settings()
    try:
        result = await run_in_threadpool(
            run_rag_search_evaluation,
            settings=settings,
            limit=request.limit,
            score_threshold=request.score_threshold,
        )
    except (EvaluationError, EmbeddingError, VectorStoreError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return EvaluationRunResponse(**result)


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    settings = _get_effective_settings()
    client = DeepSeekClient(settings)

    try:
        result = await client.chat(request.message)
    except DeepSeekClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return ChatResponse(**result)


@app.post("/documents/extract", response_model=PdfExtractResponse)
async def extract_document(
    file: UploadFile = File(...),
    enable_ocr: bool = Form(False),
    ocr_language: str = Form("chi_sim+eng"),
) -> PdfExtractResponse:
    filename = file.filename or "uploaded.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported by this extraction endpoint")

    content = await file.read()
    max_size = 10 * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(status_code=413, detail="PDF file is too large; max size is 10 MB")

    try:
        extracted = extract_text_from_pdf_bytes(
            filename=filename,
            content=content,
            enable_ocr=enable_ocr,
            ocr_language=ocr_language,
        )
    except PdfExtractionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return PdfExtractResponse(
        filename=extracted.filename,
        page_count=extracted.page_count,
        char_count=extracted.char_count,
        preview=extracted.preview,
        scanned_like=extracted.scanned_like,
        extraction_mode=extracted.extraction_mode,
        ocr_page_count=extracted.ocr_page_count,
        pages=[
            ExtractedPageResponse(
                page_number=page.page_number,
                char_count=page.char_count,
                preview=page.preview,
                extraction_method=page.extraction_method,
            )
            for page in extracted.pages
        ],
    )


@app.post("/documents/chunk", response_model=PdfChunkResponse)
async def chunk_document(
    file: UploadFile = File(...),
    chunk_size: int = Form(800),
    overlap: int = Form(100),
    enable_ocr: bool = Form(False),
    ocr_language: str = Form("chi_sim+eng"),
) -> PdfChunkResponse:
    filename = file.filename or "uploaded.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported by this chunk endpoint")

    content = await file.read()
    max_size = 10 * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(status_code=413, detail="PDF file is too large; max size is 10 MB")

    try:
        extracted = extract_text_from_pdf_bytes(
            filename=filename,
            content=content,
            enable_ocr=enable_ocr,
            ocr_language=ocr_language,
        )
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
        extraction_mode=extracted.extraction_mode,
        ocr_page_count=extracted.ocr_page_count,
        chunks=[
            TextChunkResponse(
                chunk_id=chunk.chunk_id,
                page_number=chunk.page_number,
                char_count=chunk.char_count,
                text=chunk.text,
                extraction_method=chunk.extraction_method,
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
    enable_ocr: bool = Form(False),
    enable_image_ocr: bool = Form(False),
    ocr_language: str = Form("chi_sim+eng"),
) -> DocumentIndexResponse:
    filename = file.filename or "uploaded.pdf"
    if not _is_supported_index_file(filename):
        raise HTTPException(status_code=400, detail="Only PDF, Markdown, txt, docx, csv, and xlsx files are supported")

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
                file_type=existing_record.file_type,
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
                extraction_mode=None,
                ocr_page_count=0,
                image_ocr_count=0,
                extraction_methods=[],
            )

        document_id = existing_record.document_id if existing_record is not None else str(uuid4())
        deleted_chunks = 0
        file_type, page_count, chunks, extraction_mode, ocr_page_count, image_ocr_count, extraction_methods = _parse_and_split_index_file(
            filename=filename,
            content=content,
            chunk_size=chunk_size,
            overlap=overlap,
            enable_ocr=enable_ocr,
            enable_image_ocr=enable_image_ocr,
            ocr_language=ocr_language,
        )
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
            file_type=file_type,
        )
        document_store.add_document(
            document_id=document_id,
            filename=filename,
            file_type=file_type,
            content_hash=content_hash,
            chunk_count=len(chunks),
            collection=settings.qdrant_collection,
            chunk_size=chunk_size,
            overlap=overlap,
            embedding_model=settings.embedding_model,
            page_count=page_count,
            indexed_count=indexed_count,
            source_file_size=len(content),
        )
    except (PdfExtractionError, DocumentLoadError, TextSplitError, EmbeddingError, VectorStoreError, DocumentStoreError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return DocumentIndexResponse(
        document_id=document_id,
        filename=filename,
        file_type=file_type,
        content_hash=content_hash,
        content_hash_prefix=content_hash[:12],
        is_duplicate=False,
        indexed=True,
        message="Document indexed successfully." if deleted_chunks == 0 else "Document reindexed successfully.",
        collection=settings.qdrant_collection,
        page_count=page_count,
        chunk_count=len(chunks),
        indexed_count=indexed_count,
        deleted_chunks=deleted_chunks,
        dimension=dimension,
        local_path=settings.qdrant_local_path,
        extraction_mode=extraction_mode,
        ocr_page_count=ocr_page_count,
        image_ocr_count=image_ocr_count,
        extraction_methods=extraction_methods,
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


@app.delete("/documents/batch", response_model=BatchDeleteDocumentsResponse)
async def batch_delete_documents(request: BatchDeleteDocumentsRequest) -> BatchDeleteDocumentsResponse:
    settings = get_settings()
    document_store = get_document_store(settings.document_metadata_path)
    client = get_qdrant_client(settings.qdrant_local_path)
    deleted: list[DeleteDocumentResponse] = []
    missing_document_ids: list[str] = []

    for document_id in dict.fromkeys(request.document_ids):
        try:
            record = document_store.get_document(document_id)
        except DocumentStoreError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        if record is None:
            missing_document_ids.append(document_id)
            continue

        try:
            deleted_chunks = delete_document_chunks(
                client=client,
                collection_name=record.collection,
                document_id=document_id,
            )
            removed_record = document_store.remove_document(document_id)
        except (VectorStoreError, DocumentStoreError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        deleted.append(
            DeleteDocumentResponse(
                document_id=document_id,
                deleted_chunks=deleted_chunks,
                deleted_metadata=removed_record is not None,
            )
        )

    return BatchDeleteDocumentsResponse(
        deleted_count=len(deleted),
        deleted=deleted,
        missing_document_ids=missing_document_ids,
    )


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


@app.post("/documents/{document_id}/reindex", response_model=DocumentIndexResponse)
async def reindex_document(
    document_id: str,
    file: UploadFile = File(...),
    chunk_size: int = Form(800),
    overlap: int = Form(100),
    enable_ocr: bool = Form(False),
    enable_image_ocr: bool = Form(False),
    ocr_language: str = Form("chi_sim+eng"),
) -> DocumentIndexResponse:
    filename = file.filename or "uploaded.pdf"
    if not _is_supported_index_file(filename):
        raise HTTPException(status_code=400, detail="Only PDF, Markdown, txt, docx, csv, and xlsx files are supported")

    content = await file.read()
    max_size = 10 * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(status_code=413, detail="File is too large; max size is 10 MB")

    settings = get_settings()
    document_store = get_document_store(settings.document_metadata_path)
    try:
        existing_record = document_store.get_document(document_id)
    except DocumentStoreError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if existing_record is None:
        raise HTTPException(status_code=404, detail=f"Document {document_id!r} not found")

    content_hash = _calculate_content_hash(content)
    try:
        file_type, page_count, chunks, extraction_mode, ocr_page_count, image_ocr_count, extraction_methods = _parse_and_split_index_file(
            filename=filename,
            content=content,
            chunk_size=chunk_size,
            overlap=overlap,
            enable_ocr=enable_ocr,
            enable_image_ocr=enable_image_ocr,
            ocr_language=ocr_language,
        )
        if not chunks:
            raise VectorStoreError("No text chunks to index")

        vectors = await run_in_threadpool(
            lambda: [embed_text(chunk.text, settings.embedding_model) for chunk in chunks]
        )
        dimension = len(vectors[0])
        client = get_qdrant_client(settings.qdrant_local_path)
        ensure_collection(client, settings.qdrant_collection, dimension)
        deleted_chunks = delete_document_chunks(
            client=client,
            collection_name=existing_record.collection,
            document_id=document_id,
        )
        document_store.remove_document(document_id)
        indexed_count = upsert_chunks(
            client=client,
            collection_name=settings.qdrant_collection,
            filename=filename,
            chunks=chunks,
            vectors=vectors,
            document_id=document_id,
            content_hash=content_hash,
            file_type=file_type,
        )
        document_store.add_document(
            document_id=document_id,
            filename=filename,
            file_type=file_type,
            content_hash=content_hash,
            chunk_count=len(chunks),
            collection=settings.qdrant_collection,
            chunk_size=chunk_size,
            overlap=overlap,
            embedding_model=settings.embedding_model,
            page_count=page_count,
            indexed_count=indexed_count,
            source_file_size=len(content),
        )
    except (PdfExtractionError, DocumentLoadError, TextSplitError, EmbeddingError, VectorStoreError, DocumentStoreError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return DocumentIndexResponse(
        document_id=document_id,
        filename=filename,
        file_type=file_type,
        content_hash=content_hash,
        content_hash_prefix=content_hash[:12],
        is_duplicate=False,
        indexed=True,
        message="Document reindexed successfully.",
        collection=settings.qdrant_collection,
        page_count=page_count,
        chunk_count=len(chunks),
        indexed_count=indexed_count,
        deleted_chunks=deleted_chunks,
        dimension=dimension,
        local_path=settings.qdrant_local_path,
        extraction_mode=extraction_mode,
        ocr_page_count=ocr_page_count,
        image_ocr_count=image_ocr_count,
        extraction_methods=extraction_methods,
    )


@app.post("/documents/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest) -> SearchResponse:
    settings = get_settings()
    try:
        retrieved_results = await _search_local_chunks(
            settings=settings,
            query=request.query,
            limit=request.limit,
            document_id=request.document_id,
            file_type=request.file_type,
        )
    except (EmbeddingError, VectorStoreError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return SearchResponse(
        query=request.query,
        collection=settings.qdrant_collection,
        limit=request.limit,
        document_id=request.document_id,
        file_type=request.file_type,
        results=[
            _to_search_result_response(result)
            for result in retrieved_results
        ],
    )


@app.post("/rag/ask", response_model=RagAskResponse)
async def ask_with_rag(request: RagAskRequest) -> RagAskResponse:
    settings = get_settings()
    runtime_settings = _load_runtime_settings_or_422()
    llm_settings = apply_runtime_settings(settings, runtime_settings)

    try:
        retrieved_results = await _search_local_chunks(
            settings=settings,
            query=request.question,
            limit=request.limit,
            document_id=request.document_id,
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

    deepseek_client = DeepSeekClient(llm_settings)
    messages = _build_rag_messages(
        question=request.question,
        results=results,
        runtime_settings=runtime_settings,
    )

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


@app.post("/agent/ask", response_model=AgentAskResponse)
async def ask_with_agent(request: AgentAskRequest) -> AgentAskResponse:
    settings = get_settings()
    runtime_settings = _load_runtime_settings_or_422()
    llm_settings = apply_runtime_settings(settings, runtime_settings)
    route_decision = explain_agent_route(request.question)
    selected_route = route_decision.route
    routing_debug: dict[str, Any] = {
        "selected_route": selected_route,
        "matched_keywords": route_decision.matched_keywords,
        "normalized_question": route_decision.normalized_question,
        "requested_limit": request.limit,
        "score_threshold": request.score_threshold,
        "document_id": request.document_id,
    }

    if selected_route == "chat":
        deepseek_client = DeepSeekClient(llm_settings)
        try:
            answer = await deepseek_client.chat(request.question)
        except DeepSeekClientError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        return AgentAskResponse(
            question=request.question,
            route="chat",
            route_reason=route_decision.reason,
            tools_used=["llm_chat"],
            routing_debug={
                **routing_debug,
                "retrieved_count": 0,
                "filtered_count": 0,
                "fallback": None,
            },
            reply=answer["reply"],
            model=answer["model"],
            collection=settings.qdrant_collection,
            score_threshold=request.score_threshold,
            usage=answer.get("usage"),
        )

    try:
        retrieved_results = await _search_local_chunks(
            settings=settings,
            query=request.question,
            limit=request.limit,
            document_id=request.document_id,
        )
    except (EmbeddingError, VectorStoreError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    results = _filter_results_by_score(retrieved_results, request.score_threshold)
    sources = [
        _to_rag_source_response(index, result)
        for index, result in enumerate(results, start=1)
    ]
    retrieval_debug = {
        **routing_debug,
        "retrieved_count": len(retrieved_results),
        "filtered_count": len(results),
        "top_score": float(retrieved_results[0].score) if retrieved_results else None,
    }

    if not retrieved_results:
        return AgentAskResponse(
            question=request.question,
            route="insufficient_context",
            route_reason="Agent 选择了本地知识库检索，但 Qdrant 没有返回任何相关 chunk。",
            tools_used=["local_embedding", "qdrant_search"],
            routing_debug={
                **retrieval_debug,
                "fallback": "no_retrieved_chunks",
            },
            reply="资料不足：本地知识库中没有检索到相关内容。请先上传并索引相关文档，或换一个更具体的问题。",
            collection=settings.qdrant_collection,
            score_threshold=request.score_threshold,
            retrieved_count=0,
            source_count=0,
            sources=[],
        )

    if not results:
        return AgentAskResponse(
            question=request.question,
            route="insufficient_context",
            route_reason="Agent 检索到了候选 chunk，但它们没有达到当前 score_threshold。",
            tools_used=["local_embedding", "qdrant_search"],
            routing_debug={
                **retrieval_debug,
                "fallback": "score_threshold_filtered_all",
            },
            reply="资料不足：检索结果没有达到当前 score_threshold。可以降低阈值，或补充更相关的资料后再问。",
            collection=settings.qdrant_collection,
            score_threshold=request.score_threshold,
            retrieved_count=len(retrieved_results),
            source_count=0,
            sources=[],
        )

    deepseek_client = DeepSeekClient(llm_settings)
    messages = _build_rag_messages(
        question=request.question,
        results=results,
        runtime_settings=runtime_settings,
    )

    try:
        answer = await deepseek_client.chat_messages(
            messages=messages,
            max_tokens=1200,
            temperature=0.1,
        )
    except DeepSeekClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return AgentAskResponse(
        question=request.question,
        route="rag",
        route_reason=route_decision.reason,
        tools_used=["local_embedding", "qdrant_search", "llm_rag"],
        routing_debug={
            **retrieval_debug,
            "fallback": None,
        },
        reply=answer["reply"],
        model=answer["model"],
        collection=settings.qdrant_collection,
        score_threshold=request.score_threshold,
        retrieved_count=len(retrieved_results),
        source_count=len(results),
        sources=sources,
        usage=answer.get("usage"),
    )


async def _search_local_chunks(
    *,
    settings: Any,
    query: str,
    limit: int,
    document_id: str | None = None,
    file_type: str | None = None,
) -> list[SearchResult]:
    query_vector = await run_in_threadpool(
        embed_text,
        text=query,
        model_name=settings.embedding_model,
    )
    client = get_qdrant_client(settings.qdrant_local_path)
    return search_chunks(
        client=client,
        collection_name=settings.qdrant_collection,
        query_vector=query_vector,
        limit=limit,
        document_id=document_id,
        file_type=file_type,
    )


def _load_runtime_settings_or_422() -> RuntimeSettings:
    try:
        return load_runtime_settings()
    except RuntimeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _get_effective_settings() -> Any:
    base_settings = get_settings()
    runtime_settings = _load_runtime_settings_or_422()
    return apply_runtime_settings(base_settings, runtime_settings)


def _save_and_render_settings(base_settings: Any, runtime_settings: RuntimeSettings) -> AppSettingsResponse:
    try:
        saved_runtime_settings = save_runtime_settings(runtime_settings)
    except RuntimeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    effective_settings = apply_runtime_settings(base_settings, saved_runtime_settings)
    return _to_app_settings_response(
        base_settings=base_settings,
        runtime_settings=saved_runtime_settings,
        effective_settings=effective_settings,
    )


def _materialize_llm_profiles(
    *,
    base_settings: Any,
    runtime_settings: RuntimeSettings,
    effective_settings: Any,
) -> tuple[tuple[LlmRuntimeProfile, ...], str]:
    if runtime_settings.llm_profiles:
        active_profile_id = runtime_settings.active_llm_profile_id or runtime_settings.llm_profiles[0].profile_id
        return runtime_settings.llm_profiles, active_profile_id

    profile = LlmRuntimeProfile(
        profile_id=DEFAULT_LLM_PROFILE_ID,
        name=f"{effective_settings.llm_provider} / {effective_settings.llm_model}",
        provider=effective_settings.llm_provider,
        base_url=effective_settings.llm_base_url,
        model=effective_settings.llm_model,
        api_key=runtime_settings.llm_api_key or runtime_settings.deepseek_api_key,
    )
    return (profile,), DEFAULT_LLM_PROFILE_ID


def _to_llm_profile_response(
    profile: LlmRuntimeProfile,
    *,
    active_profile_id: str,
    base_settings: Any,
) -> LlmProfileResponse:
    api_key_source = "runtime" if profile.api_key else "env" if base_settings.llm_api_key else "none"
    api_key_configured = api_key_source != "none"
    return LlmProfileResponse(
        profile_id=profile.profile_id,
        name=profile.name,
        provider=profile.provider,
        base_url=profile.base_url,
        model=profile.model,
        enabled=profile.profile_id == active_profile_id,
        api_key_configured=api_key_configured,
        api_key_source=api_key_source,
        api_key_label="SK-********" if api_key_configured else "",
    )


def _to_app_settings_response(
    *,
    base_settings: Any,
    runtime_settings: RuntimeSettings,
    effective_settings: Any,
) -> AppSettingsResponse:
    active_profile = next(
        (profile for profile in runtime_settings.llm_profiles if profile.profile_id == runtime_settings.active_llm_profile_id),
        None,
    )
    if active_profile and active_profile.api_key:
        api_key_source = "runtime"
    elif runtime_settings.llm_api_key or runtime_settings.deepseek_api_key:
        api_key_source = "runtime"
    elif base_settings.llm_api_key:
        api_key_source = "env"
    else:
        api_key_source = "none"

    profiles, active_profile_id = _materialize_llm_profiles(
        base_settings=base_settings,
        runtime_settings=runtime_settings,
        effective_settings=effective_settings,
    )

    return AppSettingsResponse(
        deepseek_base_url=effective_settings.deepseek_base_url,
        deepseek_model=effective_settings.deepseek_model,
        llm_provider=effective_settings.llm_provider,
        llm_base_url=effective_settings.llm_base_url,
        llm_model=effective_settings.llm_model,
        request_timeout_seconds=effective_settings.request_timeout_seconds,
        api_key_configured=bool(effective_settings.llm_api_key),
        api_key_source=api_key_source,
        llm_api_key_configured=bool(effective_settings.llm_api_key),
        llm_api_key_source=api_key_source,
        active_llm_profile_id=active_profile_id,
        llm_profiles=[
            _to_llm_profile_response(
                profile,
                active_profile_id=active_profile_id,
                base_settings=base_settings,
            )
            for profile in profiles
        ],
        available_providers=get_provider_options(),
        embedding_model=base_settings.embedding_model,
        qdrant_collection=base_settings.qdrant_collection,
        rag_system_prompt=runtime_settings.rag_system_prompt or DEFAULT_RAG_SYSTEM_PROMPT,
        rag_answer_instructions=runtime_settings.rag_answer_instructions or DEFAULT_RAG_ANSWER_INSTRUCTIONS,
    )


def _optional_secret(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _to_search_result_response(result: SearchResult) -> SearchResultResponse:
    return SearchResultResponse(
        score=result.score,
        document_id=result.document_id,
        file_type=result.file_type,
        filename=result.filename,
        page_number=result.page_number,
        chunk_id=result.chunk_id,
        text=result.text,
        extraction_method=result.extraction_method,
    )


def _to_rag_source_response(source_id: int, result: SearchResult, preview_chars: int = 180) -> RagSourceResponse:
    preview = " ".join(result.text.split())[:preview_chars]
    return RagSourceResponse(
        source_id=source_id,
        score=result.score,
        document_id=result.document_id,
        file_type=result.file_type,
        filename=result.filename,
        page_number=result.page_number,
        chunk_id=result.chunk_id,
        preview=preview,
        extraction_method=result.extraction_method,
    )


def get_document_store(metadata_path: str) -> DocumentStore:
    return DocumentStore(metadata_path)


def _to_document_record_response(record: DocumentRecord) -> DocumentRecordResponse:
    return DocumentRecordResponse(**asdict(record))


def _calculate_content_hash(content: bytes) -> str:
    return sha256(content).hexdigest()


def _is_supported_index_file(filename: str) -> bool:
    lower_filename = filename.lower()
    return lower_filename.endswith(".pdf") or is_supported_document(filename)


def _parse_and_split_index_file(
    *,
    filename: str,
    content: bytes,
    chunk_size: int,
    overlap: int,
    enable_ocr: bool = False,
    enable_image_ocr: bool = False,
    ocr_language: str = "chi_sim+eng",
) -> tuple[str, int, list[TextChunk], str | None, int, int, list[str]]:
    if filename.lower().endswith(".pdf"):
        extracted = extract_text_from_pdf_bytes(
            filename=filename,
            content=content,
            enable_ocr=enable_ocr,
            ocr_language=ocr_language,
        )
        chunks = split_pdf_text(extracted, chunk_size=chunk_size, overlap=overlap)
        return (
            "pdf",
            extracted.page_count,
            chunks,
            extracted.extraction_mode,
            extracted.ocr_page_count,
            0,
            _chunk_extraction_methods(chunks),
        )

    parsed = load_document_from_bytes(
        filename=filename,
        content=content,
        enable_image_ocr=enable_image_ocr,
        ocr_language=ocr_language,
    )
    chunks = split_parsed_document(parsed, chunk_size=chunk_size, overlap=overlap)
    return (
        parsed.file_type,
        len(parsed.sections),
        chunks,
        None,
        0,
        sum(1 for section in parsed.sections if section.extraction_method == "image_ocr"),
        _chunk_extraction_methods(chunks),
    )


def _chunk_extraction_methods(chunks: list[TextChunk]) -> list[str]:
    return sorted({chunk.extraction_method for chunk in chunks})


def _filter_results_by_score(
    results: list[SearchResult],
    score_threshold: float | None,
) -> list[SearchResult]:
    if score_threshold is None:
        return results
    return [result for result in results if result.score >= score_threshold]


def _build_rag_messages(
    question: str,
    results: list[SearchResult],
    runtime_settings: RuntimeSettings | None = None,
) -> list[dict[str, str]]:
    context = "\n\n".join(
        (
            f"[Source {index}] type: {result.file_type} | file: {result.filename} | page: {result.page_number} | "
            f"chunk_id: {result.chunk_id} | extraction: {result.extraction_method} | "
            f"score: {result.score:.4f}\n{result.text}"
        )
        for index, result in enumerate(results, start=1)
    )

    system_prompt = (
        runtime_settings.rag_system_prompt
        if runtime_settings and runtime_settings.rag_system_prompt
        else DEFAULT_RAG_SYSTEM_PROMPT
    )
    answer_instructions = (
        runtime_settings.rag_answer_instructions
        if runtime_settings and runtime_settings.rag_answer_instructions
        else DEFAULT_RAG_ANSWER_INSTRUCTIONS
    )
    user_prompt = (
        f"User question:\n{question}\n\n"
        f"Retrieved context:\n{context}\n\n"
        "Answer based on the retrieved context above.\n\n"
        f"{answer_instructions}"
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
