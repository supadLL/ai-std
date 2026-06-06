from dataclasses import dataclass
from pathlib import Path
import re


class SourceStorageError(RuntimeError):
    pass


@dataclass(frozen=True)
class StoredSourceFile:
    backend: str
    object_key: str
    size: int


def store_source_file(
    *,
    storage_path: str,
    backend: str,
    organization_id: str,
    workspace_id: str,
    knowledge_base_id: str,
    document_id: str,
    filename: str,
    content_hash: str,
    content: bytes,
) -> StoredSourceFile:
    if backend != "local":
        raise SourceStorageError(f"Unsupported source storage backend: {backend}")

    safe_filename = _safe_filename(filename)
    object_key = "/".join(
        [
            _safe_key_part(organization_id),
            _safe_key_part(workspace_id),
            _safe_key_part(knowledge_base_id),
            _safe_key_part(document_id),
            f"{content_hash[:12]}-{safe_filename}",
        ]
    )
    root = Path(storage_path)
    target_path = root.joinpath(*object_key.split("/"))
    resolved_root = root.resolve()
    target_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_target = target_path.resolve()
    if resolved_root not in resolved_target.parents and resolved_target != resolved_root:
        raise SourceStorageError("Resolved source file path escapes storage root")
    target_path.write_bytes(content)
    return StoredSourceFile(backend=backend, object_key=object_key, size=len(content))


def _safe_filename(filename: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9_.-]+", "_", Path(filename).name).strip("._")
    return safe or "upload.bin"


def _safe_key_part(value: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9_-]+", "_", value).strip("_")
    return safe or "unknown"
