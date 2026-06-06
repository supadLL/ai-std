from collections import defaultdict, deque
from dataclasses import asdict
from datetime import timedelta
from hashlib import sha256
import logging
from pathlib import Path
import re
import time
from typing import Any
from uuid import uuid4

from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import text
from starlette.concurrency import run_in_threadpool

from app.agent import explain_agent_route
from app.audit import (
    AUDIT_STATUS_FAILURE,
    AUDIT_STATUS_SUCCESS,
    AuditLogError,
    AuditLogRecord,
    AuditLogStore,
)
from app.auth import AuthenticatedUser, get_current_user, get_user_store
from app.config import get_settings
from app.db import get_engine
from app.deepseek_client import DeepSeekClient, DeepSeekClientError
from app.document_store import DocumentRecord, DocumentStore, DocumentStoreError
from app.document_loaders import DocumentLoadError, is_supported_document, load_document_from_bytes
from app.embedding_client import EmbeddingError, embed_text
from app.evaluation import (
    EvaluationRunSummary,
    EvaluationError,
    list_evaluation_runs,
    load_evaluation_dataset,
    read_evaluation_run,
    read_latest_evaluation,
    run_rag_search_evaluation,
)
from app.feedback import AnswerFeedbackRecord, AnswerFeedbackStore, FeedbackError
from app.index_jobs import (
    JOB_STATUS_FAILED,
    IndexJobRecord,
    IndexJobStore,
    IndexJobStoreError,
    RETRYABLE_JOB_STATUSES,
)
from app.llm_providers import get_provider_options, normalize_provider
from app.logging_config import (
    configure_logging,
    create_request_id,
    get_request_id,
    reset_request_id,
    set_request_id,
)
from app.pdf_extractor import PdfExtractionError, extract_text_from_pdf_bytes
from app.permissions import (
    KnowledgeBaseAccess,
    PermissionStore,
    PermissionStoreError,
)
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
from app.security import create_access_token
from app.user_store import UserRecord, UserStoreError, public_user
from app.vector_store import (
    SearchResult,
    VectorStoreError,
    delete_document_chunks,
    ensure_collection,
    get_collection_status,
    get_qdrant_client,
    search_chunks,
    upsert_chunks,
)


configure_logging()
logger = logging.getLogger(__name__)


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

RATE_LIMIT_EXEMPT_PATHS = {"/health", "/openapi.json", "/docs", "/redoc"}
RATE_LIMIT_EXEMPT_PREFIXES = ("/web/",)
_rate_limit_hits: dict[str, deque[float]] = defaultdict(deque)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or create_request_id()
    token = set_request_id(request_id)
    started_at = time.perf_counter()
    rate_limited_response = _rate_limit_response(request)
    if rate_limited_response is not None:
        duration_ms = _elapsed_ms(started_at)
        rate_limited_response.headers["X-Request-ID"] = request_id
        logger.info(
            "request rate limited",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": rate_limited_response.status_code,
                "duration_ms": duration_ms,
            },
        )
        reset_request_id(token)
        return rate_limited_response

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = _elapsed_ms(started_at)
        logger.exception(
            "request failed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "duration_ms": duration_ms,
            },
        )
        reset_request_id(token)
        raise

    duration_ms = _elapsed_ms(started_at)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "request completed",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )
    reset_request_id(token)
    return response


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
    knowledge_base_id: str
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
    knowledge_base_id: str | None = Field(default=None, max_length=120)


class SearchResultResponse(BaseModel):
    score: float
    document_id: str | None = None
    knowledge_base_id: str | None = None
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
    knowledge_base_id: str
    document_id: str | None = None
    file_type: str | None = None
    results: list[SearchResultResponse]


class RagAskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=5, ge=1, le=10)
    score_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    document_id: str | None = Field(default=None, max_length=120)
    knowledge_base_id: str | None = Field(default=None, max_length=120)


class RagSourceResponse(BaseModel):
    source_id: int
    score: float
    document_id: str | None = None
    knowledge_base_id: str | None = None
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
    knowledge_base_id: str
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
    knowledge_base_id: str | None = Field(default=None, max_length=120)


class AgentAskResponse(BaseModel):
    question: str
    route: str
    route_reason: str = ""
    tools_used: list[str] = Field(default_factory=list)
    routing_debug: dict[str, Any] = Field(default_factory=dict)
    reply: str
    model: str | None = None
    collection: str
    knowledge_base_id: str | None = None
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
    knowledge_base_id: str | None = Field(default=None, max_length=120)


class EvaluationSourceResponse(BaseModel):
    score: float
    document_id: str | None = None
    knowledge_base_id: str | None = None
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
    run_id: str | None = None
    dataset_name: str
    dataset_version: str
    generated_at: str
    collection: str
    embedding_model: str
    llm_provider: str | None = None
    llm_model: str | None = None
    knowledge_base_id: str | None = None
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
    quality_gate: dict[str, Any] | None = None
    cases: list[EvaluationCaseResultResponse]


class EvaluationRunSummaryResponse(BaseModel):
    run_id: str
    generated_at: str
    dataset_name: str
    dataset_version: str
    knowledge_base_id: str | None = None
    collection: str
    embedding_model: str
    llm_provider: str | None = None
    llm_model: str | None = None
    limit: int
    score_threshold: float | None = None
    hit_rate: float
    page_hit_rate: float
    keyword_hit_rate: float
    quality_status: str


class EvaluationRunListResponse(BaseModel):
    runs: list[EvaluationRunSummaryResponse]


class AnswerFeedbackRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    answer: str = Field(min_length=1, max_length=12000)
    rating: str = Field(min_length=2, max_length=10)
    route: str | None = Field(default=None, max_length=80)
    knowledge_base_id: str | None = Field(default=None, max_length=120)
    details: dict[str, Any] = Field(default_factory=dict)


class AnswerFeedbackResponse(BaseModel):
    feedback_id: str
    created_at: str
    request_id: str | None = None
    knowledge_base_id: str
    rating: str
    route: str | None = None


class DocumentRecordResponse(BaseModel):
    document_id: str
    organization_id: str
    workspace_id: str
    knowledge_base_id: str
    owner_user_id: str
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


class IndexJobResponse(BaseModel):
    job_id: str
    status: str
    knowledge_base_id: str
    filename: str
    source_file_size: int
    content_hash: str
    chunk_size: int
    overlap: int
    reindex: bool
    enable_ocr: bool
    enable_image_ocr: bool
    ocr_language: str
    attempts: int
    progress_message: str
    created_at: str
    updated_at: str
    started_at: str | None = None
    finished_at: str | None = None
    document_id: str | None = None
    error_message: str | None = None
    result: dict[str, Any] | None = None


class IndexJobListResponse(BaseModel):
    jobs: list[IndexJobResponse]


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


class KnowledgeBaseResponse(BaseModel):
    organization_id: str
    workspace_id: str
    knowledge_base_id: str
    name: str
    role: str


class KnowledgeBaseListResponse(BaseModel):
    default_knowledge_base_id: str
    knowledge_bases: list[KnowledgeBaseResponse]


class KnowledgeBaseCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)


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


class VectorStoreStatusResponse(BaseModel):
    mode: str
    collection: str
    collection_prefix: str
    embedding_model: str
    reachable: bool
    api_key_configured: bool
    local_path: str | None = None
    url: str | None = None
    collection_exists: bool = False
    vector_size: int | None = None
    points_count: int | None = None
    status: str | None = None
    metadata_document_count: int | None = None
    metadata_indexed_chunk_count: int | None = None
    indexed_chunk_count_matches_metadata: bool | None = None
    error: str | None = None
    metadata_error: str | None = None


class AuditLogResponse(BaseModel):
    audit_log_id: str
    created_at: str
    request_id: str | None = None
    user_id: str | None = None
    username: str | None = None
    organization_id: str | None = None
    workspace_id: str | None = None
    knowledge_base_id: str | None = None
    action: str
    resource_type: str | None = None
    resource_id: str | None = None
    status: str
    duration_ms: int | None = None
    llm_provider: str | None = None
    llm_model: str | None = None
    usage: dict[str, Any] | None = None
    details: dict[str, Any] | None = None
    error_message: str | None = None


class AuditLogListResponse(BaseModel):
    logs: list[AuditLogResponse]


class MetricsResponse(BaseModel):
    status: str
    request_id: str | None = None
    qdrant_mode: str
    qdrant_collection: str
    document_count: int
    index_job_counts: dict[str, int]
    audit_log_count: int
    audit_failure_count: int
    audit_action_counts: dict[str, int]


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


class AuthCredentialsRequest(BaseModel):
    username: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=8, max_length=200)


class AuthUserResponse(BaseModel):
    user_id: str
    username: str
    role: str


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthUserResponse


class AuthMeResponse(BaseModel):
    user: AuthUserResponse


class AuthLogoutResponse(BaseModel):
    message: str


class HealthResponse(BaseModel):
    status: str
    app_env: str
    database_reachable: bool
    qdrant_mode: str
    qdrant_url: str | None = None
    redis_configured: bool
    secret_encryption_configured: bool
    max_upload_bytes: int
    rate_limit_enabled: bool
    rate_limit_requests: int
    rate_limit_window_seconds: int
    warnings: list[str] = Field(default_factory=list)


@app.get("/health", response_model=HealthResponse)
async def health(response: Response) -> HealthResponse:
    settings = get_settings()
    database_reachable = True
    try:
        await run_in_threadpool(_check_database_connection, settings.database_url)
    except Exception:
        database_reachable = False

    warnings = _deployment_warnings(settings)
    if not database_reachable:
        response.status_code = 503
        warnings = [*warnings, "database_unreachable"]

    return HealthResponse(
        status="ok" if database_reachable else "degraded",
        app_env=settings.app_env,
        database_reachable=database_reachable,
        qdrant_mode=settings.qdrant_mode,
        qdrant_url=settings.qdrant_url if settings.qdrant_mode == "server" else None,
        redis_configured=bool(settings.redis_url),
        secret_encryption_configured=bool(settings.secret_encryption_key),
        max_upload_bytes=settings.max_upload_bytes,
        rate_limit_enabled=settings.rate_limit_enabled,
        rate_limit_requests=settings.rate_limit_requests,
        rate_limit_window_seconds=settings.rate_limit_window_seconds,
        warnings=warnings,
    )


@app.get("/", include_in_schema=False)
@app.get("/app", include_in_schema=False)
async def web_app() -> FileResponse:
    index_path = WEB_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Web UI is not available")
    return FileResponse(index_path)


@app.post("/auth/bootstrap-admin", response_model=AuthTokenResponse)
async def bootstrap_admin(request: AuthCredentialsRequest) -> AuthTokenResponse:
    settings = get_settings()
    user_store = get_user_store(settings.user_store_path, settings.database_url)
    try:
        if user_store.has_users():
            raise HTTPException(status_code=409, detail="Admin user already exists")
        user = user_store.create_user(username=request.username, password=request.password, role="admin")
        get_permission_store().ensure_default_access(
            user_id=user.user_id,
            username=user.username,
            role=user.role,
        )
    except UserStoreError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except PermissionStoreError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _to_auth_token_response(user)


@app.post("/auth/login", response_model=AuthTokenResponse)
async def login(request: AuthCredentialsRequest) -> AuthTokenResponse:
    settings = get_settings()
    try:
        user = get_user_store(settings.user_store_path, settings.database_url).authenticate(
            username=request.username,
            password=request.password,
        )
    except UserStoreError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if user is None:
        _record_audit_event(
            settings=settings,
            action="auth.login",
            status=AUDIT_STATUS_FAILURE,
            resource_type="user",
            details={"username": request.username},
            error_message="Invalid username or password",
        )
        raise HTTPException(status_code=401, detail="Invalid username or password")
    try:
        get_permission_store().ensure_default_access(
            user_id=user.user_id,
            username=user.username,
            role=user.role,
        )
    except PermissionStoreError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    _record_audit_event(
        settings=settings,
        action="auth.login",
        current_user=AuthenticatedUser(user_id=user.user_id, username=user.username, role=user.role),
        resource_type="user",
        resource_id=user.user_id,
        details={"role": user.role},
    )
    return _to_auth_token_response(user)


@app.post("/auth/logout", response_model=AuthLogoutResponse)
async def logout(_current_user: AuthenticatedUser = Depends(get_current_user)) -> AuthLogoutResponse:
    return AuthLogoutResponse(message="Logged out. Clear the bearer token on the client.")


@app.get("/auth/me", response_model=AuthMeResponse)
async def read_current_user(current_user: AuthenticatedUser = Depends(get_current_user)) -> AuthMeResponse:
    _ensure_default_knowledge_base(current_user)
    return AuthMeResponse(user=AuthUserResponse(**asdict(current_user)))


@app.get("/knowledge-bases", response_model=KnowledgeBaseListResponse)
async def list_knowledge_bases(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> KnowledgeBaseListResponse:
    default_access = _ensure_default_knowledge_base(current_user)
    try:
        knowledge_bases = get_permission_store().list_knowledge_bases(user_id=current_user.user_id)
    except PermissionStoreError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return KnowledgeBaseListResponse(
        default_knowledge_base_id=default_access.knowledge_base_id,
        knowledge_bases=[_to_knowledge_base_response(knowledge_base) for knowledge_base in knowledge_bases],
    )


@app.post("/knowledge-bases", response_model=KnowledgeBaseResponse)
async def create_knowledge_base(
    request: KnowledgeBaseCreateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> KnowledgeBaseResponse:
    _ensure_default_knowledge_base(current_user)
    try:
        knowledge_base = get_permission_store().create_knowledge_base(
            user_id=current_user.user_id,
            name=request.name,
        )
    except PermissionStoreError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _to_knowledge_base_response(knowledge_base)


@app.get("/settings", response_model=AppSettingsResponse)
async def read_app_settings(_current_user: AuthenticatedUser = Depends(get_current_user)) -> AppSettingsResponse:
    base_settings = get_settings()
    runtime_settings = _load_runtime_settings_or_422()
    effective_settings = apply_runtime_settings(base_settings, runtime_settings)
    return _to_app_settings_response(
        base_settings=base_settings,
        runtime_settings=runtime_settings,
        effective_settings=effective_settings,
    )


@app.get("/settings/vector-store/status", response_model=VectorStoreStatusResponse)
async def read_vector_store_status(
    _current_user: AuthenticatedUser = Depends(get_current_user),
) -> VectorStoreStatusResponse:
    settings = get_settings()
    collection_status = None
    error = None
    try:
        collection_status = await run_in_threadpool(_read_qdrant_collection_status, settings)
    except Exception as exc:
        error = str(exc)

    metadata_document_count = None
    metadata_indexed_chunk_count = None
    metadata_error = None
    try:
        metadata_document_count, metadata_indexed_chunk_count = await run_in_threadpool(
            _read_vector_store_metadata_counts,
            settings,
        )
    except DocumentStoreError as exc:
        metadata_error = str(exc)

    points_count = collection_status.points_count if collection_status else None
    indexed_chunk_count_matches_metadata = None
    if points_count is not None and metadata_indexed_chunk_count is not None:
        indexed_chunk_count_matches_metadata = points_count == metadata_indexed_chunk_count

    return VectorStoreStatusResponse(
        mode=settings.qdrant_mode,
        collection=settings.qdrant_collection,
        collection_prefix=settings.qdrant_collection_prefix,
        embedding_model=settings.embedding_model,
        reachable=collection_status is not None,
        api_key_configured=bool(settings.qdrant_api_key),
        local_path=settings.qdrant_local_path if settings.qdrant_mode == "local" else None,
        url=settings.qdrant_url if settings.qdrant_mode == "server" else None,
        collection_exists=collection_status.exists if collection_status else False,
        vector_size=collection_status.vector_size if collection_status else None,
        points_count=points_count,
        status=collection_status.status if collection_status else None,
        metadata_document_count=metadata_document_count,
        metadata_indexed_chunk_count=metadata_indexed_chunk_count,
        indexed_chunk_count_matches_metadata=indexed_chunk_count_matches_metadata,
        error=error,
        metadata_error=metadata_error,
    )


@app.get("/audit-logs", response_model=AuditLogListResponse)
async def list_audit_logs(
    limit: int = 50,
    action: str | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AuditLogListResponse:
    settings = get_settings()
    user_id = None if current_user.role == "admin" else current_user.user_id
    try:
        logs = AuditLogStore(settings.database_url).list_logs(
            limit=max(1, min(limit, 200)),
            user_id=user_id,
            action=action,
        )
    except AuditLogError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return AuditLogListResponse(logs=[_to_audit_log_response(log) for log in logs])


@app.get("/metrics", response_model=MetricsResponse)
async def read_metrics(
    _current_user: AuthenticatedUser = Depends(get_current_user),
) -> MetricsResponse:
    settings = get_settings()
    try:
        return _read_metrics(settings)
    except (AuditLogError, DocumentStoreError, IndexJobStoreError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.put("/settings", response_model=AppSettingsResponse)
async def update_app_settings(
    request: UpdateAppSettingsRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AppSettingsResponse:
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
    _record_audit_event(
        settings=base_settings,
        action="settings.update",
        current_user=current_user,
        resource_type="settings",
        details={
            "llm_provider": effective_settings.llm_provider,
            "llm_model": effective_settings.llm_model,
            "api_key_changed": bool(request.llm_api_key or request.deepseek_api_key or request.clear_api_key),
        },
    )
    return _to_app_settings_response(
        base_settings=base_settings,
        runtime_settings=next_runtime_settings,
        effective_settings=effective_settings,
    )


@app.post("/settings/llm-profiles", response_model=AppSettingsResponse)
async def create_llm_profile(
    request: LlmProfileRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AppSettingsResponse:
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
    response = _save_and_render_settings(base_settings, next_runtime_settings)
    _record_audit_event(
        settings=base_settings,
        action="llm_profile.create",
        current_user=current_user,
        resource_type="llm_profile",
        resource_id=profile.profile_id,
        details={"provider": profile.provider, "model": profile.model, "activated": request.activate},
    )
    return response


@app.put("/settings/llm-profiles/{profile_id}", response_model=AppSettingsResponse)
async def update_llm_profile(
    profile_id: str,
    request: LlmProfileRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AppSettingsResponse:
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
    response = _save_and_render_settings(base_settings, next_runtime_settings)
    _record_audit_event(
        settings=base_settings,
        action="llm_profile.update",
        current_user=current_user,
        resource_type="llm_profile",
        resource_id=profile_id,
        details={"provider": normalize_provider(request.provider), "model": request.model.strip(), "activated": request.activate},
    )
    return response


@app.post("/settings/llm-profiles/{profile_id}/activate", response_model=AppSettingsResponse)
async def activate_llm_profile(
    profile_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AppSettingsResponse:
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
    response = _save_and_render_settings(base_settings, next_runtime_settings)
    activated_profile = next(profile for profile in profiles if profile.profile_id == profile_id)
    _record_audit_event(
        settings=base_settings,
        action="llm_profile.activate",
        current_user=current_user,
        resource_type="llm_profile",
        resource_id=profile_id,
        details={"provider": activated_profile.provider, "model": activated_profile.model},
    )
    return response


@app.delete("/settings/llm-profiles/{profile_id}", response_model=AppSettingsResponse)
async def delete_llm_profile(
    profile_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AppSettingsResponse:
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
    response = _save_and_render_settings(base_settings, next_runtime_settings)
    _record_audit_event(
        settings=base_settings,
        action="llm_profile.delete",
        current_user=current_user,
        resource_type="llm_profile",
        resource_id=profile_id,
    )
    return response


@app.get("/evaluation/questions", response_model=EvaluationQuestionsResponse)
async def read_evaluation_questions(
    _current_user: AuthenticatedUser = Depends(get_current_user),
) -> EvaluationQuestionsResponse:
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
async def read_latest_rag_evaluation(
    _current_user: AuthenticatedUser = Depends(get_current_user),
) -> EvaluationRunResponse:
    try:
        result = await run_in_threadpool(read_latest_evaluation)
    except EvaluationError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return EvaluationRunResponse(**result)


@app.get("/evaluation/runs", response_model=EvaluationRunListResponse)
async def list_rag_evaluation_runs(
    knowledge_base_id: str | None = None,
    limit: int = 20,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> EvaluationRunListResponse:
    settings = get_settings()
    access = _resolve_knowledge_base_context(current_user, knowledge_base_id)
    try:
        runs = await run_in_threadpool(
            list_evaluation_runs,
            settings=settings,
            knowledge_base_id=access.knowledge_base_id,
            limit=max(1, min(limit, 100)),
        )
    except EvaluationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return EvaluationRunListResponse(runs=[_to_evaluation_run_summary_response(run) for run in runs])


@app.get("/evaluation/runs/{run_id}", response_model=EvaluationRunResponse)
async def read_rag_evaluation_run(
    run_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> EvaluationRunResponse:
    settings = get_settings()
    try:
        result = await run_in_threadpool(read_evaluation_run, settings=settings, run_id=run_id)
    except EvaluationError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    result_knowledge_base_id = result.get("knowledge_base_id")
    if result_knowledge_base_id:
        _resolve_knowledge_base_context(current_user, str(result_knowledge_base_id))
    return EvaluationRunResponse(**result)


@app.post("/evaluation/run", response_model=EvaluationRunResponse)
async def run_rag_evaluation(
    request: EvaluationRunRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> EvaluationRunResponse:
    settings = get_settings()
    access = _resolve_knowledge_base_context(current_user, request.knowledge_base_id)
    try:
        result = await run_in_threadpool(
            run_rag_search_evaluation,
            settings=settings,
            limit=request.limit,
            score_threshold=request.score_threshold,
            knowledge_base_id=access.knowledge_base_id,
        )
    except (EvaluationError, EmbeddingError, VectorStoreError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return EvaluationRunResponse(**result)


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    _current_user: AuthenticatedUser = Depends(get_current_user),
) -> ChatResponse:
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
    _current_user: AuthenticatedUser = Depends(get_current_user),
) -> PdfExtractResponse:
    filename = file.filename or "uploaded.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported by this extraction endpoint")

    settings = get_settings()
    content = await _read_upload_content(file, settings)

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
    _current_user: AuthenticatedUser = Depends(get_current_user),
) -> PdfChunkResponse:
    filename = file.filename or "uploaded.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported by this chunk endpoint")

    settings = get_settings()
    content = await _read_upload_content(file, settings)

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
async def create_text_embedding(
    request: EmbeddingRequest,
    _current_user: AuthenticatedUser = Depends(get_current_user),
) -> EmbeddingResponse:
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


@app.post("/knowledge-bases/{knowledge_base_id}/documents/index", response_model=DocumentIndexResponse)
@app.post("/documents/index", response_model=DocumentIndexResponse)
async def index_document(
    knowledge_base_id: str | None = None,
    file: UploadFile = File(...),
    chunk_size: int = Form(800),
    overlap: int = Form(100),
    reindex: bool = Form(False),
    enable_ocr: bool = Form(False),
    enable_image_ocr: bool = Form(False),
    ocr_language: str = Form("chi_sim+eng"),
    knowledge_base_id_form: str | None = Form(default=None, alias="knowledge_base_id"),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> DocumentIndexResponse:
    filename = file.filename or "uploaded.pdf"
    if not _is_supported_index_file(filename):
        raise HTTPException(status_code=400, detail="Only PDF, Markdown, txt, docx, csv, and xlsx files are supported")

    settings = get_settings()
    content = await _read_upload_content(file, settings)
    access = _resolve_knowledge_base_context(
        current_user,
        _select_knowledge_base_id(knowledge_base_id, knowledge_base_id_form),
    )
    started_at = time.perf_counter()
    try:
        result = await run_in_threadpool(
            _index_document_content,
            settings=settings,
            access=access,
            owner_user_id=current_user.user_id,
            filename=filename,
            content=content,
            chunk_size=chunk_size,
            overlap=overlap,
            reindex=reindex,
            enable_ocr=enable_ocr,
            enable_image_ocr=enable_image_ocr,
            ocr_language=ocr_language,
        )
    except (PdfExtractionError, DocumentLoadError, TextSplitError, EmbeddingError, VectorStoreError, DocumentStoreError) as exc:
        _record_audit_event(
            settings=settings,
            action="document.index",
            current_user=current_user,
            access=access,
            status=AUDIT_STATUS_FAILURE,
            resource_type="document",
            duration_ms=_elapsed_ms(started_at),
            details={"filename": filename, "reindex": reindex},
            error_message=str(exc),
        )
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    _record_audit_event(
        settings=settings,
        action="document.index",
        current_user=current_user,
        access=access,
        resource_type="document",
        resource_id=result.document_id,
        duration_ms=_elapsed_ms(started_at),
        details={
            "filename": result.filename,
            "file_type": result.file_type,
            "indexed": result.indexed,
            "is_duplicate": result.is_duplicate,
            "chunk_count": result.chunk_count,
            "indexed_count": result.indexed_count,
            "collection": result.collection,
        },
    )
    return result


@app.post("/knowledge-bases/{knowledge_base_id}/documents/index-jobs", response_model=IndexJobResponse)
@app.post("/documents/index-jobs", response_model=IndexJobResponse)
async def create_index_job(
    background_tasks: BackgroundTasks,
    knowledge_base_id: str | None = None,
    file: UploadFile = File(...),
    chunk_size: int = Form(800),
    overlap: int = Form(100),
    reindex: bool = Form(False),
    enable_ocr: bool = Form(False),
    enable_image_ocr: bool = Form(False),
    ocr_language: str = Form("chi_sim+eng"),
    knowledge_base_id_form: str | None = Form(default=None, alias="knowledge_base_id"),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> IndexJobResponse:
    filename = file.filename or "uploaded.pdf"
    if not _is_supported_index_file(filename):
        raise HTTPException(status_code=400, detail="Only PDF, Markdown, txt, docx, csv, and xlsx files are supported")

    settings = get_settings()
    content = await _read_upload_content(file, settings)
    access = _resolve_knowledge_base_context(
        current_user,
        _select_knowledge_base_id(knowledge_base_id, knowledge_base_id_form),
    )
    content_hash = _calculate_content_hash(content)
    file_path = _write_index_job_file(
        storage_path=settings.index_job_storage_path,
        filename=filename,
        content=content,
    )

    try:
        job = get_index_job_store().create_job(
            organization_id=access.organization_id,
            workspace_id=access.workspace_id,
            knowledge_base_id=access.knowledge_base_id,
            owner_user_id=current_user.user_id,
            filename=filename,
            file_path=file_path,
            source_file_size=len(content),
            content_hash=content_hash,
            chunk_size=chunk_size,
            overlap=overlap,
            reindex=reindex,
            enable_ocr=enable_ocr,
            enable_image_ocr=enable_image_ocr,
            ocr_language=ocr_language,
        )
    except IndexJobStoreError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    background_tasks.add_task(_run_index_job_task, job.job_id)
    _record_audit_event(
        settings=settings,
        action="document.index_job.create",
        current_user=current_user,
        access=access,
        resource_type="index_job",
        resource_id=job.job_id,
        details={
            "filename": filename,
            "source_file_size": len(content),
            "reindex": reindex,
            "enable_ocr": enable_ocr,
            "enable_image_ocr": enable_image_ocr,
        },
    )
    return _to_index_job_response(job)


@app.get("/knowledge-bases/{knowledge_base_id}/documents/index-jobs", response_model=IndexJobListResponse)
@app.get("/documents/index-jobs", response_model=IndexJobListResponse)
async def list_index_jobs(
    knowledge_base_id: str | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> IndexJobListResponse:
    access = _resolve_knowledge_base_context(current_user, knowledge_base_id)
    try:
        jobs = get_index_job_store().list_jobs(knowledge_base_id=access.knowledge_base_id)
    except IndexJobStoreError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return IndexJobListResponse(jobs=[_to_index_job_response(job) for job in jobs])


@app.get("/knowledge-bases/{knowledge_base_id}/documents/index-jobs/{job_id}", response_model=IndexJobResponse)
@app.get("/documents/index-jobs/{job_id}", response_model=IndexJobResponse)
async def get_index_job(
    job_id: str,
    knowledge_base_id: str | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> IndexJobResponse:
    access = _resolve_knowledge_base_context(current_user, knowledge_base_id)
    job = _get_index_job_or_404(job_id=job_id, knowledge_base_id=access.knowledge_base_id)
    return _to_index_job_response(job)


@app.post("/knowledge-bases/{knowledge_base_id}/documents/index-jobs/{job_id}/retry", response_model=IndexJobResponse)
@app.post("/documents/index-jobs/{job_id}/retry", response_model=IndexJobResponse)
async def retry_index_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    knowledge_base_id: str | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> IndexJobResponse:
    access = _resolve_knowledge_base_context(current_user, knowledge_base_id)
    job = _get_index_job_or_404(job_id=job_id, knowledge_base_id=access.knowledge_base_id)
    if job.status not in RETRYABLE_JOB_STATUSES:
        raise HTTPException(status_code=400, detail="Only failed index jobs can be retried")

    try:
        retried_job = get_index_job_store().reset_for_retry(job_id)
    except IndexJobStoreError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if retried_job is None:
        raise HTTPException(status_code=404, detail=f"Index job {job_id!r} not found")

    background_tasks.add_task(_run_index_job_task, retried_job.job_id)
    return _to_index_job_response(retried_job)


@app.get("/knowledge-bases/{knowledge_base_id}/documents", response_model=DocumentListResponse)
@app.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    knowledge_base_id: str | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> DocumentListResponse:
    settings = get_settings()
    access = _resolve_knowledge_base_context(current_user, knowledge_base_id)
    try:
        records = get_document_store(settings.document_metadata_path).list_documents(
            knowledge_base_id=access.knowledge_base_id,
        )
    except DocumentStoreError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return DocumentListResponse(documents=[_to_document_record_response(record) for record in records])


@app.get("/knowledge-bases/{knowledge_base_id}/documents/{document_id}", response_model=DocumentRecordResponse)
@app.get("/documents/{document_id}", response_model=DocumentRecordResponse)
async def get_document(
    document_id: str,
    knowledge_base_id: str | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> DocumentRecordResponse:
    settings = get_settings()
    access = _resolve_knowledge_base_context(current_user, knowledge_base_id)
    try:
        record = get_document_store(settings.document_metadata_path).get_document(
            document_id,
            knowledge_base_id=access.knowledge_base_id,
        )
    except DocumentStoreError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if record is None:
        raise HTTPException(status_code=404, detail=f"Document {document_id!r} not found")
    return _to_document_record_response(record)


@app.delete("/knowledge-bases/{knowledge_base_id}/documents/batch", response_model=BatchDeleteDocumentsResponse)
@app.delete("/documents/batch", response_model=BatchDeleteDocumentsResponse)
async def batch_delete_documents(
    request: BatchDeleteDocumentsRequest,
    knowledge_base_id: str | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> BatchDeleteDocumentsResponse:
    settings = get_settings()
    access = _resolve_knowledge_base_context(current_user, knowledge_base_id)
    document_store = get_document_store(settings.document_metadata_path)
    client = _get_qdrant_client_from_settings(settings)
    deleted: list[DeleteDocumentResponse] = []
    missing_document_ids: list[str] = []

    for document_id in dict.fromkeys(request.document_ids):
        try:
            record = document_store.get_document(
                document_id,
                knowledge_base_id=access.knowledge_base_id,
            )
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
                knowledge_base_id=access.knowledge_base_id,
                tenant_id=access.organization_id,
            )
            removed_record = document_store.remove_document(
                document_id,
                knowledge_base_id=access.knowledge_base_id,
            )
        except (VectorStoreError, DocumentStoreError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        deleted.append(
            DeleteDocumentResponse(
                document_id=document_id,
                deleted_chunks=deleted_chunks,
                deleted_metadata=removed_record is not None,
            )
        )
        _record_audit_event(
            settings=settings,
            action="document.delete",
            current_user=current_user,
            access=access,
            resource_type="document",
            resource_id=document_id,
            details={
                "filename": record.filename,
                "deleted_chunks": deleted_chunks,
                "deleted_metadata": removed_record is not None,
                "batch": True,
            },
        )

    return BatchDeleteDocumentsResponse(
        deleted_count=len(deleted),
        deleted=deleted,
        missing_document_ids=missing_document_ids,
    )


@app.delete("/knowledge-bases/{knowledge_base_id}/documents/{document_id}", response_model=DeleteDocumentResponse)
@app.delete("/documents/{document_id}", response_model=DeleteDocumentResponse)
async def delete_document(
    document_id: str,
    knowledge_base_id: str | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> DeleteDocumentResponse:
    settings = get_settings()
    access = _resolve_knowledge_base_context(current_user, knowledge_base_id)
    document_store = get_document_store(settings.document_metadata_path)

    try:
        record = document_store.get_document(
            document_id,
            knowledge_base_id=access.knowledge_base_id,
        )
    except DocumentStoreError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if record is None:
        raise HTTPException(status_code=404, detail=f"Document {document_id!r} not found")

    try:
        client = _get_qdrant_client_from_settings(settings)
        deleted_chunks = delete_document_chunks(
            client=client,
            collection_name=record.collection,
            document_id=document_id,
            knowledge_base_id=access.knowledge_base_id,
            tenant_id=access.organization_id,
        )
        removed_record = document_store.remove_document(
            document_id,
            knowledge_base_id=access.knowledge_base_id,
        )
    except (VectorStoreError, DocumentStoreError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    _record_audit_event(
        settings=settings,
        action="document.delete",
        current_user=current_user,
        access=access,
        resource_type="document",
        resource_id=document_id,
        details={
            "filename": record.filename,
            "deleted_chunks": deleted_chunks,
            "deleted_metadata": removed_record is not None,
        },
    )
    return DeleteDocumentResponse(
        document_id=document_id,
        deleted_chunks=deleted_chunks,
        deleted_metadata=removed_record is not None,
    )


@app.post("/knowledge-bases/{knowledge_base_id}/documents/{document_id}/reindex", response_model=DocumentIndexResponse)
@app.post("/documents/{document_id}/reindex", response_model=DocumentIndexResponse)
async def reindex_document(
    document_id: str,
    knowledge_base_id: str | None = None,
    file: UploadFile = File(...),
    chunk_size: int = Form(800),
    overlap: int = Form(100),
    enable_ocr: bool = Form(False),
    enable_image_ocr: bool = Form(False),
    ocr_language: str = Form("chi_sim+eng"),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> DocumentIndexResponse:
    filename = file.filename or "uploaded.pdf"
    if not _is_supported_index_file(filename):
        raise HTTPException(status_code=400, detail="Only PDF, Markdown, txt, docx, csv, and xlsx files are supported")

    settings = get_settings()
    content = await _read_upload_content(file, settings)
    access = _resolve_knowledge_base_context(current_user, knowledge_base_id)
    document_store = get_document_store(settings.document_metadata_path)
    try:
        existing_record = document_store.get_document(
            document_id,
            knowledge_base_id=access.knowledge_base_id,
        )
    except DocumentStoreError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if existing_record is None:
        raise HTTPException(status_code=404, detail=f"Document {document_id!r} not found")

    content_hash = _calculate_content_hash(content)
    started_at = time.perf_counter()
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
        client = _get_qdrant_client_from_settings(settings)
        ensure_collection(client, settings.qdrant_collection, dimension)
        deleted_chunks = delete_document_chunks(
            client=client,
            collection_name=existing_record.collection,
            document_id=document_id,
            knowledge_base_id=access.knowledge_base_id,
            tenant_id=access.organization_id,
        )
        document_store.remove_document(document_id, knowledge_base_id=access.knowledge_base_id)
        indexed_count = upsert_chunks(
            client=client,
            collection_name=settings.qdrant_collection,
            filename=filename,
            chunks=chunks,
            vectors=vectors,
            document_id=document_id,
            content_hash=content_hash,
            file_type=file_type,
            tenant_id=access.organization_id,
            workspace_id=access.workspace_id,
            knowledge_base_id=access.knowledge_base_id,
        )
        document_store.add_document(
            document_id=document_id,
            organization_id=access.organization_id,
            workspace_id=access.workspace_id,
            knowledge_base_id=access.knowledge_base_id,
            owner_user_id=current_user.user_id,
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
        _record_audit_event(
            settings=settings,
            action="document.reindex",
            current_user=current_user,
            access=access,
            status=AUDIT_STATUS_FAILURE,
            resource_type="document",
            resource_id=document_id,
            duration_ms=_elapsed_ms(started_at),
            details={"filename": filename, "previous_filename": existing_record.filename},
            error_message=str(exc),
        )
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    response = DocumentIndexResponse(
        document_id=document_id,
        knowledge_base_id=access.knowledge_base_id,
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
    _record_audit_event(
        settings=settings,
        action="document.reindex",
        current_user=current_user,
        access=access,
        resource_type="document",
        resource_id=document_id,
        duration_ms=_elapsed_ms(started_at),
        details={
            "filename": filename,
            "previous_filename": existing_record.filename,
            "deleted_chunks": deleted_chunks,
            "indexed_count": indexed_count,
            "chunk_count": len(chunks),
        },
    )
    return response


@app.post("/knowledge-bases/{knowledge_base_id}/documents/search", response_model=SearchResponse)
@app.post("/documents/search", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    knowledge_base_id: str | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> SearchResponse:
    settings = get_settings()
    access = _resolve_knowledge_base_context(
        current_user,
        _select_knowledge_base_id(knowledge_base_id, request.knowledge_base_id),
    )
    if request.document_id:
        _require_document_in_knowledge_base(
            document_id=request.document_id,
            knowledge_base=access,
            settings=settings,
        )
    try:
        retrieved_results = await _search_local_chunks(
            settings=settings,
            query=request.query,
            limit=request.limit,
            document_id=request.document_id,
            file_type=request.file_type,
            knowledge_base_id=access.knowledge_base_id,
            tenant_id=access.organization_id,
        )
    except (EmbeddingError, VectorStoreError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return SearchResponse(
        query=request.query,
        collection=settings.qdrant_collection,
        limit=request.limit,
        knowledge_base_id=access.knowledge_base_id,
        document_id=request.document_id,
        file_type=request.file_type,
        results=[
            _to_search_result_response(result)
            for result in retrieved_results
        ],
    )


@app.post("/knowledge-bases/{knowledge_base_id}/rag/ask", response_model=RagAskResponse)
@app.post("/rag/ask", response_model=RagAskResponse)
async def ask_with_rag(
    request: RagAskRequest,
    knowledge_base_id: str | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> RagAskResponse:
    settings = get_settings()
    access = _resolve_knowledge_base_context(
        current_user,
        _select_knowledge_base_id(knowledge_base_id, request.knowledge_base_id),
    )
    if request.document_id:
        _require_document_in_knowledge_base(
            document_id=request.document_id,
            knowledge_base=access,
            settings=settings,
        )
    runtime_settings = _load_runtime_settings_or_422()
    llm_settings = apply_runtime_settings(settings, runtime_settings)

    total_started_at = time.perf_counter()
    retrieval_started_at = time.perf_counter()
    try:
        retrieved_results = await _search_local_chunks(
            settings=settings,
            query=request.question,
            limit=request.limit,
            document_id=request.document_id,
            knowledge_base_id=access.knowledge_base_id,
            tenant_id=access.organization_id,
        )
    except (EmbeddingError, VectorStoreError) as exc:
        _record_audit_event(
            settings=settings,
            action="rag.ask",
            current_user=current_user,
            access=access,
            status=AUDIT_STATUS_FAILURE,
            resource_type="rag_query",
            duration_ms=_elapsed_ms(total_started_at),
            details={"limit": request.limit, "document_id": request.document_id},
            error_message=str(exc),
        )
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    retrieval_ms = _elapsed_ms(retrieval_started_at)

    results = _filter_results_by_score(retrieved_results, request.score_threshold)

    if not retrieved_results:
        _record_audit_event(
            settings=settings,
            action="rag.ask",
            current_user=current_user,
            access=access,
            status=AUDIT_STATUS_FAILURE,
            resource_type="rag_query",
            duration_ms=_elapsed_ms(total_started_at),
            details={
                "limit": request.limit,
                "document_id": request.document_id,
                "retrieved_count": 0,
                "retrieval_ms": retrieval_ms,
            },
            error_message="No related document chunks found",
        )
        raise HTTPException(status_code=404, detail="No related document chunks found. Index a document first.")

    if not results:
        _record_audit_event(
            settings=settings,
            action="rag.ask",
            current_user=current_user,
            access=access,
            status=AUDIT_STATUS_FAILURE,
            resource_type="rag_query",
            duration_ms=_elapsed_ms(total_started_at),
            details={
                "limit": request.limit,
                "document_id": request.document_id,
                "retrieved_count": len(retrieved_results),
                "source_count": 0,
                "score_threshold": request.score_threshold,
                "retrieval_ms": retrieval_ms,
            },
            error_message="No document chunks met score_threshold",
        )
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

    llm_started_at = time.perf_counter()
    try:
        answer = await deepseek_client.chat_messages(
            messages=messages,
            max_tokens=1200,
            temperature=0.1,
        )
    except DeepSeekClientError as exc:
        _record_audit_event(
            settings=settings,
            action="rag.ask",
            current_user=current_user,
            access=access,
            status=AUDIT_STATUS_FAILURE,
            resource_type="rag_query",
            duration_ms=_elapsed_ms(total_started_at),
            llm_provider=llm_settings.llm_provider,
            llm_model=llm_settings.llm_model,
            details={
                "limit": request.limit,
                "document_id": request.document_id,
                "retrieved_count": len(retrieved_results),
                "source_count": len(results),
                "score_threshold": request.score_threshold,
                "retrieval_ms": retrieval_ms,
                "llm_ms": _elapsed_ms(llm_started_at),
            },
            error_message=str(exc),
        )
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    llm_ms = _elapsed_ms(llm_started_at)

    response = RagAskResponse(
        question=request.question,
        reply=answer["reply"],
        model=answer["model"],
        collection=settings.qdrant_collection,
        knowledge_base_id=access.knowledge_base_id,
        score_threshold=request.score_threshold,
        retrieved_count=len(retrieved_results),
        source_count=len(results),
        sources=[
            _to_rag_source_response(index, result)
            for index, result in enumerate(results, start=1)
        ],
        usage=answer.get("usage"),
    )
    _record_audit_event(
        settings=settings,
        action="rag.ask",
        current_user=current_user,
        access=access,
        resource_type="rag_query",
        duration_ms=_elapsed_ms(total_started_at),
        llm_provider=llm_settings.llm_provider,
        llm_model=answer["model"],
        usage=answer.get("usage"),
        details={
            "limit": request.limit,
            "document_id": request.document_id,
            "retrieved_count": len(retrieved_results),
            "source_count": len(results),
            "score_threshold": request.score_threshold,
            "retrieval_ms": retrieval_ms,
            "llm_ms": llm_ms,
        },
    )
    return response


@app.post("/knowledge-bases/{knowledge_base_id}/agent/ask", response_model=AgentAskResponse)
@app.post("/agent/ask", response_model=AgentAskResponse)
async def ask_with_agent(
    request: AgentAskRequest,
    knowledge_base_id: str | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AgentAskResponse:
    settings = get_settings()
    access = _resolve_knowledge_base_context(
        current_user,
        _select_knowledge_base_id(knowledge_base_id, request.knowledge_base_id),
    )
    if request.document_id:
        _require_document_in_knowledge_base(
            document_id=request.document_id,
            knowledge_base=access,
            settings=settings,
        )
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
        "knowledge_base_id": access.knowledge_base_id,
    }

    total_started_at = time.perf_counter()
    if selected_route == "chat":
        deepseek_client = DeepSeekClient(llm_settings)
        llm_started_at = time.perf_counter()
        try:
            answer = await deepseek_client.chat(request.question)
        except DeepSeekClientError as exc:
            _record_audit_event(
                settings=settings,
                action="agent.ask",
                current_user=current_user,
                access=access,
                status=AUDIT_STATUS_FAILURE,
                resource_type="agent_query",
                duration_ms=_elapsed_ms(total_started_at),
                llm_provider=llm_settings.llm_provider,
                llm_model=llm_settings.llm_model,
                details={"route": "chat", "llm_ms": _elapsed_ms(llm_started_at)},
                error_message=str(exc),
            )
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        response = AgentAskResponse(
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
            knowledge_base_id=access.knowledge_base_id,
            score_threshold=request.score_threshold,
            usage=answer.get("usage"),
        )
        _record_audit_event(
            settings=settings,
            action="agent.ask",
            current_user=current_user,
            access=access,
            resource_type="agent_query",
            duration_ms=_elapsed_ms(total_started_at),
            llm_provider=llm_settings.llm_provider,
            llm_model=answer["model"],
            usage=answer.get("usage"),
            details={"route": "chat", "llm_ms": _elapsed_ms(llm_started_at)},
        )
        return response

    retrieval_started_at = time.perf_counter()
    try:
        retrieved_results = await _search_local_chunks(
            settings=settings,
            query=request.question,
            limit=request.limit,
            document_id=request.document_id,
            knowledge_base_id=access.knowledge_base_id,
            tenant_id=access.organization_id,
        )
    except (EmbeddingError, VectorStoreError) as exc:
        _record_audit_event(
            settings=settings,
            action="agent.ask",
            current_user=current_user,
            access=access,
            status=AUDIT_STATUS_FAILURE,
            resource_type="agent_query",
            duration_ms=_elapsed_ms(total_started_at),
            details={
                "route": selected_route,
                "limit": request.limit,
                "document_id": request.document_id,
                "retrieval_ms": _elapsed_ms(retrieval_started_at),
            },
            error_message=str(exc),
        )
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    retrieval_ms = _elapsed_ms(retrieval_started_at)

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
        _record_audit_event(
            settings=settings,
            action="agent.ask",
            current_user=current_user,
            access=access,
            resource_type="agent_query",
            duration_ms=_elapsed_ms(total_started_at),
            details={
                "route": "insufficient_context",
                "fallback": "no_retrieved_chunks",
                "limit": request.limit,
                "document_id": request.document_id,
                "retrieved_count": 0,
                "source_count": 0,
                "retrieval_ms": retrieval_ms,
            },
        )
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
            knowledge_base_id=access.knowledge_base_id,
            score_threshold=request.score_threshold,
            retrieved_count=0,
            source_count=0,
            sources=[],
        )

    if not results:
        _record_audit_event(
            settings=settings,
            action="agent.ask",
            current_user=current_user,
            access=access,
            resource_type="agent_query",
            duration_ms=_elapsed_ms(total_started_at),
            details={
                "route": "insufficient_context",
                "fallback": "score_threshold_filtered_all",
                "limit": request.limit,
                "document_id": request.document_id,
                "retrieved_count": len(retrieved_results),
                "source_count": 0,
                "score_threshold": request.score_threshold,
                "retrieval_ms": retrieval_ms,
            },
        )
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
            knowledge_base_id=access.knowledge_base_id,
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

    llm_started_at = time.perf_counter()
    try:
        answer = await deepseek_client.chat_messages(
            messages=messages,
            max_tokens=1200,
            temperature=0.1,
        )
    except DeepSeekClientError as exc:
        _record_audit_event(
            settings=settings,
            action="agent.ask",
            current_user=current_user,
            access=access,
            status=AUDIT_STATUS_FAILURE,
            resource_type="agent_query",
            duration_ms=_elapsed_ms(total_started_at),
            llm_provider=llm_settings.llm_provider,
            llm_model=llm_settings.llm_model,
            details={
                "route": "rag",
                "limit": request.limit,
                "document_id": request.document_id,
                "retrieved_count": len(retrieved_results),
                "source_count": len(results),
                "score_threshold": request.score_threshold,
                "retrieval_ms": retrieval_ms,
                "llm_ms": _elapsed_ms(llm_started_at),
            },
            error_message=str(exc),
        )
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    llm_ms = _elapsed_ms(llm_started_at)

    response = AgentAskResponse(
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
        knowledge_base_id=access.knowledge_base_id,
        score_threshold=request.score_threshold,
        retrieved_count=len(retrieved_results),
        source_count=len(results),
        sources=sources,
        usage=answer.get("usage"),
    )
    _record_audit_event(
        settings=settings,
        action="agent.ask",
        current_user=current_user,
        access=access,
        resource_type="agent_query",
        duration_ms=_elapsed_ms(total_started_at),
        llm_provider=llm_settings.llm_provider,
        llm_model=answer["model"],
        usage=answer.get("usage"),
        details={
            "route": "rag",
            "limit": request.limit,
            "document_id": request.document_id,
            "retrieved_count": len(retrieved_results),
            "source_count": len(results),
            "score_threshold": request.score_threshold,
            "retrieval_ms": retrieval_ms,
            "llm_ms": llm_ms,
        },
    )
    return response


@app.post("/feedback/answers", response_model=AnswerFeedbackResponse)
async def create_answer_feedback(
    request: AnswerFeedbackRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AnswerFeedbackResponse:
    settings = get_settings()
    access = _resolve_knowledge_base_context(current_user, request.knowledge_base_id)
    try:
        feedback = AnswerFeedbackStore(settings.database_url).record(
            request_id=get_request_id(),
            user_id=current_user.user_id,
            username=current_user.username,
            organization_id=access.organization_id,
            workspace_id=access.workspace_id,
            knowledge_base_id=access.knowledge_base_id,
            rating=request.rating,
            question=request.question,
            answer=request.answer,
            route=request.route,
            details=request.details,
        )
    except FeedbackError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    _record_audit_event(
        settings=settings,
        action="feedback.answer",
        current_user=current_user,
        access=access,
        resource_type="answer_feedback",
        resource_id=feedback.feedback_id,
        details={"rating": feedback.rating, "route": feedback.route},
    )
    return _to_answer_feedback_response(feedback)


async def _search_local_chunks(
    *,
    settings: Any,
    query: str,
    limit: int,
    document_id: str | None = None,
    file_type: str | None = None,
    knowledge_base_id: str | None = None,
    tenant_id: str | None = None,
) -> list[SearchResult]:
    query_vector = await run_in_threadpool(
        embed_text,
        text=query,
        model_name=settings.embedding_model,
    )
    client = _get_qdrant_client_from_settings(settings)
    return search_chunks(
        client=client,
        collection_name=settings.qdrant_collection,
        query_vector=query_vector,
        limit=limit,
        document_id=document_id,
        file_type=file_type,
        knowledge_base_id=knowledge_base_id,
        tenant_id=tenant_id,
    )


def _elapsed_ms(started_at: float) -> int:
    return int((time.perf_counter() - started_at) * 1000)


async def _read_upload_content(file: UploadFile, settings: Any) -> bytes:
    max_upload_bytes = max(1, int(getattr(settings, "max_upload_bytes", 10 * 1024 * 1024)))
    content = await file.read(max_upload_bytes + 1)
    if len(content) > max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File is too large; max upload size is {_format_bytes(max_upload_bytes)}",
        )
    return content


def _rate_limit_response(request: Request) -> JSONResponse | None:
    settings = get_settings()
    if not getattr(settings, "rate_limit_enabled", False) or _is_rate_limit_exempt(request):
        return None

    now = time.perf_counter()
    window_seconds = max(1, int(getattr(settings, "rate_limit_window_seconds", 60)))
    request_limit = max(1, int(getattr(settings, "rate_limit_requests", 120)))
    key = _rate_limit_key(request)
    hits = _rate_limit_hits[key]
    while hits and now - hits[0] >= window_seconds:
        hits.popleft()

    if len(hits) >= request_limit:
        retry_after = max(1, int(window_seconds - (now - hits[0]))) if hits else window_seconds
        return UTF8JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
            headers={"Retry-After": str(retry_after)},
        )

    hits.append(now)
    return None


def _rate_limit_key(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For", "").split(",", 1)[0].strip()
    client_host = forwarded_for or (request.client.host if request.client else "unknown")
    return client_host or "unknown"


def _is_rate_limit_exempt(request: Request) -> bool:
    if request.method.upper() == "OPTIONS":
        return True
    path = request.url.path
    return path in RATE_LIMIT_EXEMPT_PATHS or any(path.startswith(prefix) for prefix in RATE_LIMIT_EXEMPT_PREFIXES)


def _format_bytes(value: int) -> str:
    if value % (1024 * 1024) == 0:
        return f"{value // (1024 * 1024)} MB"
    if value % 1024 == 0:
        return f"{value // 1024} KB"
    return f"{value} bytes"


def _get_qdrant_client_from_settings(settings: Any) -> Any:
    return get_qdrant_client(
        settings.qdrant_local_path,
        mode=settings.qdrant_mode,
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
    )


def _record_audit_event(
    *,
    settings: Any,
    action: str,
    current_user: AuthenticatedUser | None = None,
    access: KnowledgeBaseAccess | None = None,
    status: str = AUDIT_STATUS_SUCCESS,
    resource_type: str | None = None,
    resource_id: str | None = None,
    duration_ms: int | None = None,
    llm_provider: str | None = None,
    llm_model: str | None = None,
    usage: dict[str, Any] | None = None,
    details: dict[str, Any] | None = None,
    error_message: str | None = None,
) -> AuditLogRecord | None:
    try:
        return AuditLogStore(settings.database_url).record(
            action=action,
            status=status,
            request_id=get_request_id(),
            user_id=current_user.user_id if current_user else None,
            username=current_user.username if current_user else None,
            organization_id=access.organization_id if access else None,
            workspace_id=access.workspace_id if access else None,
            knowledge_base_id=access.knowledge_base_id if access else None,
            resource_type=resource_type,
            resource_id=resource_id,
            duration_ms=duration_ms,
            llm_provider=llm_provider,
            llm_model=llm_model,
            usage=usage,
            details=details,
            error_message=error_message,
        )
    except AuditLogError:
        logger.warning("audit log write failed", exc_info=True)
        return None


def _to_audit_log_response(log: AuditLogRecord) -> AuditLogResponse:
    return AuditLogResponse(**asdict(log))


def _to_evaluation_run_summary_response(run: EvaluationRunSummary) -> EvaluationRunSummaryResponse:
    return EvaluationRunSummaryResponse(**asdict(run))


def _to_answer_feedback_response(feedback: AnswerFeedbackRecord) -> AnswerFeedbackResponse:
    return AnswerFeedbackResponse(
        feedback_id=feedback.feedback_id,
        created_at=feedback.created_at,
        request_id=feedback.request_id,
        knowledge_base_id=feedback.knowledge_base_id,
        rating=feedback.rating,
        route=feedback.route,
    )


def _read_metrics(settings: Any) -> MetricsResponse:
    documents = get_document_store(settings.document_metadata_path).list_documents()
    index_jobs = IndexJobStore(settings.database_url).list_jobs(limit=10000)
    index_job_counts: dict[str, int] = {}
    for job in index_jobs:
        index_job_counts[job.status] = index_job_counts.get(job.status, 0) + 1
    audit_metrics = AuditLogStore(settings.database_url).summarize()
    return MetricsResponse(
        status="ok",
        request_id=get_request_id(),
        qdrant_mode=settings.qdrant_mode,
        qdrant_collection=settings.qdrant_collection,
        document_count=len(documents),
        index_job_counts=index_job_counts,
        audit_log_count=audit_metrics.audit_log_count,
        audit_failure_count=audit_metrics.failure_count,
        audit_action_counts=audit_metrics.action_counts,
    )


def _check_database_connection(database_url: str) -> None:
    with get_engine(database_url).connect() as connection:
        connection.execute(text("SELECT 1"))


def _deployment_warnings(settings: Any) -> list[str]:
    warnings: list[str] = []
    if settings.app_env == "production":
        if settings.app_secret_key == "change-this-local-development-secret":
            warnings.append("app_secret_key_uses_development_default")
        if not settings.secret_encryption_key:
            warnings.append("secret_encryption_key_not_configured")
        if settings.qdrant_mode == "local":
            warnings.append("qdrant_local_mode_in_production")
        if settings.llm_api_key in {"", "your_llm_api_key_here", "your_deepseek_api_key_here"}:
            warnings.append("llm_api_key_not_configured")
    return warnings


def _read_qdrant_collection_status(settings: Any) -> Any:
    client = _get_qdrant_client_from_settings(settings)
    return get_collection_status(
        client=client,
        collection_name=settings.qdrant_collection,
    )


def _read_vector_store_metadata_counts(settings: Any) -> tuple[int, int]:
    documents = [
        document
        for document in get_document_store(settings.document_metadata_path).list_documents()
        if document.collection == settings.qdrant_collection
    ]
    return len(documents), sum(document.indexed_count for document in documents)


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


def _to_auth_token_response(user: UserRecord) -> AuthTokenResponse:
    settings = get_settings()
    token = create_access_token(
        subject=user.user_id,
        username=user.username,
        role=user.role,
        secret_key=settings.app_secret_key,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    return AuthTokenResponse(
        access_token=token,
        user=AuthUserResponse(**public_user(user)),
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


def get_permission_store() -> PermissionStore:
    settings = get_settings()
    return PermissionStore(settings.database_url)


def get_index_job_store() -> IndexJobStore:
    settings = get_settings()
    return IndexJobStore(settings.database_url)


def _ensure_default_knowledge_base(current_user: AuthenticatedUser) -> KnowledgeBaseAccess:
    try:
        return get_permission_store().ensure_default_access(
            user_id=current_user.user_id,
            username=current_user.username,
            role=current_user.role,
        )
    except PermissionStoreError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _resolve_knowledge_base_context(
    current_user: AuthenticatedUser,
    knowledge_base_id: str | None,
) -> KnowledgeBaseAccess:
    default_access = _ensure_default_knowledge_base(current_user)
    if not knowledge_base_id:
        return default_access
    try:
        access = get_permission_store().get_knowledge_base_for_user(
            user_id=current_user.user_id,
            knowledge_base_id=knowledge_base_id,
        )
    except PermissionStoreError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if access is None:
        raise HTTPException(status_code=403, detail="No access to this knowledge base")
    return access


def _require_document_in_knowledge_base(
    *,
    document_id: str,
    knowledge_base: KnowledgeBaseAccess,
    settings: Any,
) -> DocumentRecord:
    try:
        record = get_document_store(settings.document_metadata_path).get_document(
            document_id,
            knowledge_base_id=knowledge_base.knowledge_base_id,
        )
    except DocumentStoreError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if record is None:
        raise HTTPException(status_code=404, detail=f"Document {document_id!r} not found")
    return record


def _select_knowledge_base_id(*candidates: str | None) -> str | None:
    for candidate in candidates:
        if candidate and candidate.strip():
            return candidate.strip()
    return None


def _to_knowledge_base_response(knowledge_base: KnowledgeBaseAccess) -> KnowledgeBaseResponse:
    return KnowledgeBaseResponse(
        organization_id=knowledge_base.organization_id,
        workspace_id=knowledge_base.workspace_id,
        knowledge_base_id=knowledge_base.knowledge_base_id,
        name=knowledge_base.name,
        role=knowledge_base.role,
    )


def _get_index_job_or_404(*, job_id: str, knowledge_base_id: str) -> IndexJobRecord:
    try:
        job = get_index_job_store().get_job(job_id, knowledge_base_id=knowledge_base_id)
    except IndexJobStoreError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if job is None:
        raise HTTPException(status_code=404, detail=f"Index job {job_id!r} not found")
    return job


def _to_index_job_response(job: IndexJobRecord) -> IndexJobResponse:
    return IndexJobResponse(
        job_id=job.job_id,
        status=job.status,
        knowledge_base_id=job.knowledge_base_id,
        filename=job.filename,
        source_file_size=job.source_file_size,
        content_hash=job.content_hash,
        chunk_size=job.chunk_size,
        overlap=job.overlap,
        reindex=job.reindex,
        enable_ocr=job.enable_ocr,
        enable_image_ocr=job.enable_image_ocr,
        ocr_language=job.ocr_language,
        attempts=job.attempts,
        progress_message=job.progress_message,
        created_at=job.created_at,
        updated_at=job.updated_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
        document_id=job.document_id,
        error_message=job.error_message,
        result=job.result,
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
        knowledge_base_id=result.knowledge_base_id,
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
        knowledge_base_id=result.knowledge_base_id,
        file_type=result.file_type,
        filename=result.filename,
        page_number=result.page_number,
        chunk_id=result.chunk_id,
        preview=preview,
        extraction_method=result.extraction_method,
    )


def get_document_store(metadata_path: str) -> DocumentStore:
    settings = get_settings()
    return DocumentStore(metadata_path, database_url=settings.database_url)


def _to_document_record_response(record: DocumentRecord) -> DocumentRecordResponse:
    return DocumentRecordResponse(**asdict(record))


def _write_index_job_file(*, storage_path: str, filename: str, content: bytes) -> str:
    storage_dir = Path(storage_path)
    storage_dir.mkdir(parents=True, exist_ok=True)
    safe_filename = re.sub(r"[^a-zA-Z0-9_.-]+", "_", Path(filename).name).strip("._")
    if not safe_filename:
        safe_filename = "upload.bin"
    file_path = storage_dir / f"{uuid4().hex[:16]}-{safe_filename}"
    file_path.write_bytes(content)
    return file_path.as_posix()


def _run_index_job_task(job_id: str) -> None:
    store = get_index_job_store()
    try:
        job = store.get_job(job_id)
        if job is None:
            return
        running_job = store.mark_running(job_id) or job
        content = Path(running_job.file_path).read_bytes()
        settings = get_settings()
        access = KnowledgeBaseAccess(
            organization_id=running_job.organization_id,
            workspace_id=running_job.workspace_id,
            knowledge_base_id=running_job.knowledge_base_id,
            name="",
            role="owner",
        )
        result = _index_document_content(
            settings=settings,
            access=access,
            owner_user_id=running_job.owner_user_id,
            filename=running_job.filename,
            content=content,
            chunk_size=running_job.chunk_size,
            overlap=running_job.overlap,
            reindex=running_job.reindex,
            enable_ocr=running_job.enable_ocr,
            enable_image_ocr=running_job.enable_image_ocr,
            ocr_language=running_job.ocr_language,
        )
        store.mark_succeeded(
            job_id,
            document_id=result.document_id,
            result=result.model_dump(),
        )
    except Exception as exc:
        try:
            store.mark_failed(job_id, error_message=str(exc))
        except IndexJobStoreError:
            pass


def _index_document_content(
    *,
    settings: Any,
    access: KnowledgeBaseAccess,
    owner_user_id: str,
    filename: str,
    content: bytes,
    chunk_size: int,
    overlap: int,
    reindex: bool,
    enable_ocr: bool,
    enable_image_ocr: bool,
    ocr_language: str,
) -> DocumentIndexResponse:
    content_hash = _calculate_content_hash(content)
    document_store = get_document_store(settings.document_metadata_path)
    existing_record = document_store.get_document_by_content_hash(
        content_hash,
        knowledge_base_id=access.knowledge_base_id,
    )
    if existing_record is not None and not reindex:
        return DocumentIndexResponse(
            document_id=existing_record.document_id,
            knowledge_base_id=existing_record.knowledge_base_id,
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

    vectors = [embed_text(chunk.text, settings.embedding_model) for chunk in chunks]
    dimension = len(vectors[0])
    client = _get_qdrant_client_from_settings(settings)
    ensure_collection(client, settings.qdrant_collection, dimension)
    if existing_record is not None and reindex:
        deleted_chunks = delete_document_chunks(
            client=client,
            collection_name=existing_record.collection,
            document_id=existing_record.document_id,
            knowledge_base_id=existing_record.knowledge_base_id,
            tenant_id=existing_record.organization_id,
        )
        document_store.remove_document(
            existing_record.document_id,
            knowledge_base_id=existing_record.knowledge_base_id,
        )

    indexed_count = upsert_chunks(
        client=client,
        collection_name=settings.qdrant_collection,
        filename=filename,
        chunks=chunks,
        vectors=vectors,
        document_id=document_id,
        content_hash=content_hash,
        file_type=file_type,
        tenant_id=access.organization_id,
        workspace_id=access.workspace_id,
        knowledge_base_id=access.knowledge_base_id,
    )
    document_store.add_document(
        document_id=document_id,
        organization_id=access.organization_id,
        workspace_id=access.workspace_id,
        knowledge_base_id=access.knowledge_base_id,
        owner_user_id=owner_user_id,
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

    return DocumentIndexResponse(
        document_id=document_id,
        knowledge_base_id=access.knowledge_base_id,
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
    _record_audit_event(
        settings=settings,
        action="document.reindex",
        current_user=current_user,
        access=access,
        resource_type="document",
        resource_id=document_id,
        duration_ms=_elapsed_ms(started_at),
        details={
            "filename": filename,
            "previous_filename": existing_record.filename,
            "deleted_chunks": deleted_chunks,
            "indexed_count": indexed_count,
            "chunk_count": len(chunks),
        },
    )
    return response


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
