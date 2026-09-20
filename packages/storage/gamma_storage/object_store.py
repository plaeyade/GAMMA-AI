from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Protocol

from gamma_core.errors import ConflictError


class ObjectStore(Protocol):
    def put_immutable(self, key: str, data: bytes, content_type: str) -> str:
        """Store bytes at an immutable key and return a storage URI."""

    def exists(self, key: str) -> bool:
        """Return whether the object key already exists."""


class LocalImmutableObjectStore:
    """Filesystem-backed immutable store used for local development and tests."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def put_immutable(self, key: str, data: bytes, content_type: str) -> str:
        del content_type
        normalized = _normalize_key(key)
        destination = self.root / normalized
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            existing = destination.read_bytes()
            if existing != data:
                raise ConflictError(
                    "IMMUTABLE_ARTIFACT_CONFLICT",
                    "An immutable object key already contains different bytes.",
                    {"key": normalized},
                )
        else:
            destination.write_bytes(data)
        return f"file://{destination.resolve().as_posix()}"

    def exists(self, key: str) -> bool:
        return (self.root / _normalize_key(key)).is_file()


def content_addressed_key(checksum: str) -> str:
    if len(checksum) != 64 or any(c not in "0123456789abcdef" for c in checksum):
        raise ValueError("checksum must be a lowercase SHA-256 hex digest")
    return f"sha256/{checksum[:2]}/{checksum}"


def sha256_digest(data: bytes) -> str:
    return sha256(data).hexdigest()


def _normalize_key(key: str) -> str:
    if not key or key.startswith("/") or ".." in key.split("/"):
        raise ValueError("object key must be relative and normalized")
    return key


@dataclass(frozen=True, slots=True)
class S3ObjectStoreConfig:
    endpoint_url: str
    bucket: str
    access_key_id: str
    secret_access_key: str

    def uri_for(self, key: str) -> str:
        if key.startswith("/") or ".." in key.split("/"):
            raise ValueError("object key must be relative and normalized")
        return f"s3://{self.bucket}/{key}"
