from dataclasses import dataclass
from pathlib import Path
import re
from uuid import uuid5, NAMESPACE_URL

from qdrant_client import QdrantClient, models

from app.text_splitter import TextChunk


@dataclass(frozen=True)
class SearchResult:
    point_id: str
    score: float
    document_id: str | None
    file_type: str
    filename: str
    page_number: int
    chunk_id: int
    text: str
    extraction_method: str = "text"
    knowledge_base_id: str | None = None
    tenant_id: str | None = None
    workspace_id: str | None = None


@dataclass(frozen=True)
class CollectionStatus:
    collection_name: str
    exists: bool
    vector_size: int | None = None
    points_count: int | None = None
    status: str | None = None
    expected_vector_size: int | None = None
    dimension_matches: bool | None = None


class VectorStoreError(RuntimeError):
    pass


def get_qdrant_client(
    local_path: str,
    *,
    mode: str = "local",
    url: str | None = None,
    api_key: str | None = None,
) -> QdrantClient:
    resolved_mode = (mode or "local").strip().lower()
    if resolved_mode == "local":
        Path(local_path).mkdir(parents=True, exist_ok=True)
        return QdrantClient(path=local_path)
    if resolved_mode == "server":
        return QdrantClient(
            url=(url or "http://127.0.0.1:6333").rstrip("/"),
            api_key=api_key.strip() if api_key and api_key.strip() else None,
        )
    raise VectorStoreError("QDRANT_MODE must be 'local' or 'server'")


def get_configured_qdrant_client(settings: object) -> QdrantClient:
    return get_qdrant_client(
        getattr(settings, "qdrant_local_path", ".qdrant"),
        mode=getattr(settings, "qdrant_mode", "local"),
        url=getattr(settings, "qdrant_url", "http://127.0.0.1:6333"),
        api_key=getattr(settings, "qdrant_api_key", ""),
    )


def build_collection_name(
    prefix: str = "rag",
    *,
    suffix: str = "chunks",
    tenant_id: str | None = None,
) -> str:
    parts = [_sanitize_collection_part(prefix) or "rag"]
    if tenant_id:
        parts.append(_sanitize_collection_part(tenant_id))
    parts.append(_sanitize_collection_part(suffix) or "chunks")
    return "_".join(parts)


def get_collection_status(
    client: QdrantClient,
    collection_name: str,
    *,
    expected_vector_size: int | None = None,
) -> CollectionStatus:
    if not client.collection_exists(collection_name):
        return CollectionStatus(
            collection_name=collection_name,
            exists=False,
            expected_vector_size=expected_vector_size,
        )

    info = client.get_collection(collection_name)
    vector_size = _extract_vector_size(info)
    points_count = _extract_points_count(client, collection_name, info)
    dimension_matches = None
    if expected_vector_size is not None and vector_size is not None:
        dimension_matches = vector_size == expected_vector_size
    return CollectionStatus(
        collection_name=collection_name,
        exists=True,
        vector_size=vector_size,
        points_count=points_count,
        status=_optional_str(getattr(info, "status", None)),
        expected_vector_size=expected_vector_size,
        dimension_matches=dimension_matches,
    )


def ensure_collection(client: QdrantClient, collection_name: str, vector_size: int) -> None:
    if client.collection_exists(collection_name):
        info = client.get_collection(collection_name)
        current_size = info.config.params.vectors.size
        if current_size != vector_size:
            raise VectorStoreError(
                f"Collection {collection_name!r} uses vector size {current_size}, "
                f"but current embedding dimension is {vector_size}. "
                "Rebuild the local Qdrant index, for example delete the old .qdrant directory "
                "or use a new QDRANT_COLLECTION after changing EMBEDDING_MODEL."
            )
        return

    client.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(
            size=vector_size,
            distance=models.Distance.COSINE,
        ),
    )


def upsert_chunks(
    client: QdrantClient,
    collection_name: str,
    filename: str,
    chunks: list[TextChunk],
    vectors: list[list[float]],
    document_id: str | None = None,
    content_hash: str | None = None,
    file_type: str = "pdf",
    tenant_id: str | None = None,
    workspace_id: str | None = None,
    knowledge_base_id: str | None = None,
) -> int:
    if len(chunks) != len(vectors):
        raise VectorStoreError("chunks and vectors length mismatch")

    points: list[models.PointStruct] = []
    for chunk, vector in zip(chunks, vectors):
        id_seed = document_id or filename
        point_id = str(uuid5(NAMESPACE_URL, f"{id_seed}:{chunk.page_number}:{chunk.chunk_id}:{chunk.text[:80]}"))
        points.append(
            models.PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    "tenant_id": tenant_id,
                    "organization_id": tenant_id,
                    "workspace_id": workspace_id,
                    "knowledge_base_id": knowledge_base_id,
                    "document_id": document_id,
                    "content_hash": content_hash,
                    "file_type": file_type,
                    "filename": filename,
                    "page_number": chunk.page_number,
                    "chunk_id": chunk.chunk_id,
                    "char_count": chunk.char_count,
                    "extraction_method": chunk.extraction_method,
                    "text": chunk.text,
                },
            )
        )

    if not points:
        return 0

    client.upsert(collection_name=collection_name, points=points)
    return len(points)


def delete_document_chunks(
    client: QdrantClient,
    collection_name: str,
    document_id: str,
    knowledge_base_id: str | None = None,
    tenant_id: str | None = None,
) -> int:
    if not client.collection_exists(collection_name):
        return 0

    point_ids = []
    next_offset = None
    while True:
        points, next_offset = client.scroll(
            collection_name=collection_name,
            scroll_filter=_document_id_filter(
                document_id,
                knowledge_base_id=knowledge_base_id,
                tenant_id=tenant_id,
            ),
            limit=1000,
            offset=next_offset,
            with_payload=False,
            with_vectors=False,
        )
        point_ids.extend(point.id for point in points)
        if next_offset is None:
            break

    if not point_ids:
        return 0

    client.delete(
        collection_name=collection_name,
        points_selector=models.PointIdsList(points=point_ids),
    )
    return len(point_ids)


def search_chunks(
    client: QdrantClient,
    collection_name: str,
    query_vector: list[float],
    limit: int = 5,
    document_id: str | None = None,
    file_type: str | None = None,
    knowledge_base_id: str | None = None,
    tenant_id: str | None = None,
) -> list[SearchResult]:
    if not client.collection_exists(collection_name):
        raise VectorStoreError(f"Collection {collection_name!r} does not exist. Index a document first.")

    response = client.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=limit,
        query_filter=_search_filter(
            document_id=document_id,
            file_type=file_type,
            knowledge_base_id=knowledge_base_id,
            tenant_id=tenant_id,
        ),
        with_payload=True,
        with_vectors=False,
    )

    results: list[SearchResult] = []
    for point in response.points:
        payload = point.payload or {}
        results.append(
            SearchResult(
                point_id=str(point.id),
                score=float(point.score),
                document_id=_optional_str(payload.get("document_id")),
                knowledge_base_id=_optional_str(payload.get("knowledge_base_id")),
                tenant_id=_optional_str(payload.get("tenant_id") or payload.get("organization_id")),
                workspace_id=_optional_str(payload.get("workspace_id")),
                file_type=str(payload.get("file_type", "pdf")),
                filename=str(payload.get("filename", "")),
                page_number=int(payload.get("page_number", 0)),
                chunk_id=int(payload.get("chunk_id", 0)),
                text=str(payload.get("text", "")),
                extraction_method=str(payload.get("extraction_method", "text")),
            )
        )
    return results


def _document_id_filter(
    document_id: str,
    knowledge_base_id: str | None = None,
    tenant_id: str | None = None,
) -> models.Filter:
    conditions = [
        models.FieldCondition(
            key="document_id",
            match=models.MatchValue(value=document_id),
        )
    ]
    if knowledge_base_id:
        conditions.append(
            models.FieldCondition(
                key="knowledge_base_id",
                match=models.MatchValue(value=knowledge_base_id),
            )
        )
    if tenant_id:
        conditions.append(
            models.FieldCondition(
                key="tenant_id",
                match=models.MatchValue(value=tenant_id),
            )
        )
    return models.Filter(
        must=conditions
    )


def _search_filter(
    document_id: str | None = None,
    file_type: str | None = None,
    knowledge_base_id: str | None = None,
    tenant_id: str | None = None,
) -> models.Filter | None:
    conditions = []
    if tenant_id:
        conditions.append(
            models.FieldCondition(
                key="tenant_id",
                match=models.MatchValue(value=tenant_id),
            )
        )
    if knowledge_base_id:
        conditions.append(
            models.FieldCondition(
                key="knowledge_base_id",
                match=models.MatchValue(value=knowledge_base_id),
            )
        )
    if document_id:
        conditions.append(
            models.FieldCondition(
                key="document_id",
                match=models.MatchValue(value=document_id),
            )
        )
    if file_type:
        conditions.append(
            models.FieldCondition(
                key="file_type",
                match=models.MatchValue(value=file_type),
            )
        )
    if not conditions:
        return None
    return models.Filter(must=conditions)


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _sanitize_collection_part(value: str | None) -> str:
    text = (value or "").strip()
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", text).strip("_")


def _extract_vector_size(info: object) -> int | None:
    vectors = getattr(getattr(getattr(info, "config", None), "params", None), "vectors", None)
    size = getattr(vectors, "size", None)
    if size is not None:
        return int(size)
    if isinstance(vectors, dict) and vectors:
        first_vector = next(iter(vectors.values()))
        first_size = getattr(first_vector, "size", None)
        if first_size is not None:
            return int(first_size)
    return None


def _extract_points_count(client: QdrantClient, collection_name: str, info: object) -> int | None:
    points_count = getattr(info, "points_count", None)
    if points_count is not None:
        return int(points_count)
    if not hasattr(client, "count"):
        return None
    response = client.count(collection_name=collection_name, exact=True)
    count = getattr(response, "count", None)
    return int(count) if count is not None else None
