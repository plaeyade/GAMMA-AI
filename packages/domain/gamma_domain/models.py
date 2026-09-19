from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class SourceType(StrEnum):
    DOCUMENT = "document"
    DATASET = "dataset"
    WEB = "web"
    OTHER = "other"


class GovernanceClassification(StrEnum):
    PUBLIC = "public"
    DEIDENTIFIED = "deidentified"
    GOVERNED = "governed"
    RESTRICTED = "restricted"


class IngestionStatus(StrEnum):
    REGISTERED = "registered"
    QUEUED = "queued"
    PROCESSING = "processing"
    QUALITY_CHECK = "quality_check"
    READY = "ready"
    INDEXING = "indexing"
    PUBLISHED = "published"
    FAILED = "failed"
    RETRY = "retry"
    QUARANTINED = "quarantined"


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class Source:
    source_id: str
    source_type: SourceType
    origin: dict[str, Any]
    domain: str
    governance: GovernanceClassification
    checksum: str | None = None
    language: str | None = None
    owner: str | None = None
    created_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not self.source_id.startswith("source_"):
            raise ValueError("source_id must use source_ prefix")
        if not self.origin:
            raise ValueError("origin metadata is required")
        if not self.domain.strip():
            raise ValueError("domain is required")
        if self.checksum is not None and len(self.checksum.strip()) < 8:
            raise ValueError("checksum must be meaningful when provided")


@dataclass(frozen=True, slots=True)
class Artifact:
    artifact_id: str
    source_id: str
    storage_uri: str
    checksum: str
    mime_type: str
    size_bytes: int
    created_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not self.artifact_id.startswith("artifact_"):
            raise ValueError("artifact_id must use artifact_ prefix")
        if not self.source_id.startswith("source_"):
            raise ValueError("source_id must reference a Source")
        if self.size_bytes < 0:
            raise ValueError("size_bytes cannot be negative")


@dataclass(frozen=True, slots=True)
class Document:
    document_id: str
    source_id: str
    current_version_id: str | None = None
    created_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not self.document_id.startswith("document_"):
            raise ValueError("document_id must use document_ prefix")
        if not self.source_id.startswith("source_"):
            raise ValueError("source_id must reference a Source")


@dataclass(frozen=True, slots=True)
class DocumentVersion:
    document_version_id: str
    document_id: str
    artifact_id: str
    version_number: int
    pipeline_version: str
    content_hash: str
    created_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not self.document_version_id.startswith("document_version_"):
            raise ValueError("document_version_id must use document_version_ prefix")
        if self.version_number < 1:
            raise ValueError("version_number starts at 1")
        if not self.pipeline_version.strip():
            raise ValueError("pipeline_version is required")


@dataclass(frozen=True, slots=True)
class IngestionJob:
    job_id: str
    source_id: str
    pipeline_version: str
    requested_operations: tuple[str, ...]
    priority: int = 5
    status: IngestionStatus = IngestionStatus.QUEUED
    idempotency_key: str | None = None
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not self.job_id.startswith("job_"):
            raise ValueError("job_id must use job_ prefix")
        if not self.source_id.startswith("source_"):
            raise ValueError("source_id must reference a Source")
        if not self.pipeline_version.strip():
            raise ValueError("pipeline_version is required")
        if not self.requested_operations:
            raise ValueError("requested_operations cannot be empty")
        if self.priority < 0 or self.priority > 10:
            raise ValueError("priority must be between 0 and 10")
