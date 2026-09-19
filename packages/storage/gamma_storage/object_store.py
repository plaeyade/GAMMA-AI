from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class ObjectStore(Protocol):
    def put_immutable(self, key: str, data: bytes, content_type: str) -> str:
        """Store bytes at an immutable key and return a storage URI."""

    def exists(self, key: str) -> bool:
        """Return whether the object key already exists."""


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
