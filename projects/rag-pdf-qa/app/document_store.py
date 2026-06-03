import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4


@dataclass(frozen=True)
class DocumentRecord:
    document_id: str
    filename: str
    file_type: str
    chunk_count: int
    created_at: str
    collection: str
    chunk_size: int
    overlap: int
    embedding_model: str
    page_count: int
    indexed_count: int


class DocumentStoreError(RuntimeError):
    pass


class DocumentStore:
    def __init__(self, path: str) -> None:
        self.path = Path(path)

    def list_documents(self) -> list[DocumentRecord]:
        data = self._read_data()
        return [DocumentRecord(**item) for item in data.get("documents", [])]

    def get_document(self, document_id: str) -> DocumentRecord | None:
        for record in self.list_documents():
            if record.document_id == document_id:
                return record
        return None

    def add_document(
        self,
        *,
        document_id: str | None = None,
        filename: str,
        file_type: str,
        chunk_count: int,
        collection: str,
        chunk_size: int,
        overlap: int,
        embedding_model: str,
        page_count: int,
        indexed_count: int,
    ) -> DocumentRecord:
        record = DocumentRecord(
            document_id=document_id or str(uuid4()),
            filename=filename,
            file_type=file_type,
            chunk_count=chunk_count,
            created_at=datetime.now(UTC).isoformat(),
            collection=collection,
            chunk_size=chunk_size,
            overlap=overlap,
            embedding_model=embedding_model,
            page_count=page_count,
            indexed_count=indexed_count,
        )

        data = self._read_data()
        documents = data.setdefault("documents", [])
        documents.append(asdict(record))
        self._write_data(data)
        return record

    def remove_document(self, document_id: str) -> DocumentRecord | None:
        data = self._read_data()
        documents = data.get("documents", [])
        kept_documents = [item for item in documents if item.get("document_id") != document_id]
        if len(kept_documents) == len(documents):
            return None

        removed = next(item for item in documents if item.get("document_id") == document_id)
        data["documents"] = kept_documents
        self._write_data(data)
        return DocumentRecord(**removed)

    def _read_data(self) -> dict[str, list[dict[str, object]]]:
        if not self.path.exists():
            return {"documents": []}
        try:
            with self.path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except json.JSONDecodeError as exc:
            raise DocumentStoreError(f"Invalid document metadata JSON: {self.path}") from exc

        if not isinstance(data, dict) or not isinstance(data.get("documents", []), list):
            raise DocumentStoreError(f"Invalid document metadata structure: {self.path}")
        return data

    def _write_data(self, data: dict[str, list[dict[str, object]]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
