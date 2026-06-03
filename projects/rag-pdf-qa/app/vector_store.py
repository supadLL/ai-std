from dataclasses import dataclass
from pathlib import Path
from uuid import uuid5, NAMESPACE_URL

from qdrant_client import QdrantClient, models

from app.text_splitter import TextChunk


@dataclass(frozen=True)
class SearchResult:
    point_id: str
    score: float
    filename: str
    page_number: int
    chunk_id: int
    text: str


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
) -> int:
    if len(chunks) != len(vectors):
        raise VectorStoreError("chunks and vectors length mismatch")

    points: list[models.PointStruct] = []
    for chunk, vector in zip(chunks, vectors):
        point_id = str(uuid5(NAMESPACE_URL, f"{filename}:{chunk.page_number}:{chunk.chunk_id}:{chunk.text[:80]}"))
        points.append(
            models.PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    "filename": filename,
                    "page_number": chunk.page_number,
                    "chunk_id": chunk.chunk_id,
                    "char_count": chunk.char_count,
                    "text": chunk.text,
                },
            )
        )

    if not points:
        return 0

    client.upsert(collection_name=collection_name, points=points)
    return len(points)


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
                filename=str(payload.get("filename", "")),
                page_number=int(payload.get("page_number", 0)),
                chunk_id=int(payload.get("chunk_id", 0)),
                text=str(payload.get("text", "")),
            )
        )
    return results
