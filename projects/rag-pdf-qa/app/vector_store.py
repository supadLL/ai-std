from dataclasses import dataclass
from pathlib import Path
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


class VectorStoreError(RuntimeError):
    pass


def get_qdrant_client(local_path: str) -> QdrantClient:
    Path(local_path).mkdir(parents=True, exist_ok=True)
    return QdrantClient(path=local_path)


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
) -> int:
    if not client.collection_exists(collection_name):
        return 0

    point_ids = []
    next_offset = None
    while True:
        points, next_offset = client.scroll(
            collection_name=collection_name,
            scroll_filter=_document_id_filter(document_id),
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
) -> list[SearchResult]:
    if not client.collection_exists(collection_name):
        raise VectorStoreError(f"Collection {collection_name!r} does not exist. Index a document first.")

    response = client.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=limit,
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
                file_type=str(payload.get("file_type", "pdf")),
                filename=str(payload.get("filename", "")),
                page_number=int(payload.get("page_number", 0)),
                chunk_id=int(payload.get("chunk_id", 0)),
                text=str(payload.get("text", "")),
                extraction_method=str(payload.get("extraction_method", "text")),
            )
        )
    return results


def _document_id_filter(document_id: str) -> models.Filter:
    return models.Filter(
        must=[
            models.FieldCondition(
                key="document_id",
                match=models.MatchValue(value=document_id),
            )
        ]
    )


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
